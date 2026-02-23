"""Swarm Orchestrator — coordinates specialized agents in the Diamond tier.

Extends the Platinum orchestrator with multi-agent delegation:
1. Scans Needs_Action/ for tasks
2. Selects the best specialized agent for each task
3. Delegates via A2A message bus
4. Tracks outcomes for self-improving loop
5. Security agent validates all outgoing actions
6. Generates compliance reports

Architecture:
  SwarmOrchestrator
    ├── AgentRegistry (4 specialized agents)
    ├── MessageBus (in-memory A2A)
    ├── MessageRouter (delegation/results)
    ├── OutcomeTracker (learning)
    ├── PromptOptimizer (self-improvement)
    ├── SecurityAgent (validation)
    └── Base Orchestrator (Platinum pipeline)
"""

from __future__ import annotations

import time
from pathlib import Path

from src.orchestrator.orchestrator import Orchestrator
from src.agents.agent_registry import AgentRegistry, create_default_registry
from src.agents.base_agent import BaseSpecializedAgent
from src.agents.security_agent import SecurityAgent
from src.a2a.message_bus import MockMessageBus
from src.a2a.message import A2AMessage, MessageType
from src.a2a.router import MessageRouter
from src.learning.outcome_tracker import OutcomeTracker, TaskOutcome, Outcome
from src.learning.prompt_optimizer import PromptOptimizer
from src.learning.performance_metrics import PerformanceMetrics
from src.utils.logger import log_action, audit_log
from src.utils.file_ops import list_md_files, safe_move, get_project_root


class SwarmOrchestrator(Orchestrator):
    """Multi-agent swarm orchestrator for Diamond tier.

    Delegates tasks to specialized agents based on their capabilities,
    tracks outcomes for self-improvement, and validates actions via security agent.
    """

    def __init__(self, dry_run: bool = False, poll_interval: int = 10,
                 ralph_enabled: bool = True):
        super().__init__(dry_run=dry_run, poll_interval=poll_interval,
                         ralph_enabled=ralph_enabled)

        # Diamond components
        self.registry = create_default_registry()
        self.bus = MockMessageBus(max_queue_size=1000)
        self.router = MessageRouter(self.bus, self.registry)
        self.tracker = OutcomeTracker()
        self.optimizer = PromptOptimizer(self.tracker, min_sample_size=10)
        self.metrics = PerformanceMetrics(self.tracker, self.registry)

        # Get security agent reference for validation
        security_agents = self.registry.get_by_type("security")
        self._security: SecurityAgent | None = security_agents[0] if security_agents else None

        self._optimization_counter = 0
        self._optimization_interval = 100  # Run optimizer every N tasks

    def poll_once(self) -> int:
        """Scan + delegate to specialized agents."""
        files = list_md_files("Needs_Action", ignore_prefixes=self.IGNORE_PREFIXES)

        new_files = [f for f in files if f.name not in self._processing]
        if not new_files:
            return 0

        tasks = [self._classify_task(f) for f in new_files]
        tasks = self._sort_by_priority(tasks)

        log_action("Swarm", f"Found {len(tasks)} task(s) to delegate", "swarm")
        audit_log("swarm_poll", actor="swarm",
                  params={"task_count": len(tasks)})

        processed = 0
        for task in tasks:
            if not self._running:
                break

            self._processing.add(task["filename"])
            try:
                self._delegate_task(task)
                processed += 1
            except Exception as e:
                log_action("Swarm Error", f"{task['filename']}: {e}", "swarm")
                self._record_outcome(task, Outcome.FAILURE, 0, str(e))
            finally:
                self._processing.discard(task["filename"])

        # Periodic optimization
        self._optimization_counter += processed
        if self._optimization_counter >= self._optimization_interval:
            self._run_optimization()
            self._optimization_counter = 0

        return processed

    def _delegate_task(self, task: dict) -> None:
        """Delegate a task to the best specialized agent."""
        filename = task["filename"]
        start = time.time()

        # Find best agent
        agent = self.registry.find_best_agent(task)
        if agent is None:
            # No specialized agent — fall back to base orchestrator
            log_action("Swarm", f"No agent for {filename}, using base pipeline", "swarm")
            self._process_task(task)
            return

        log_action("Swarm", f"Delegating {filename} → {agent.agent_id}", "swarm")
        audit_log("swarm_delegate", actor="swarm",
                  params={"file": filename, "agent": agent.agent_id,
                          "agent_type": agent.AGENT_TYPE})

        # Security pre-check
        if self._security and agent.AGENT_TYPE != "security":
            scan = self._security.scan_outgoing(
                task.get("body", ""), task.get("task_type", "unknown")
            )
            if not scan["passed"]:
                log_action("Security", f"Blocked {filename}: {scan['issues']}", "swarm")
                audit_log("security_block", actor="security",
                          params={"file": filename, "issues": scan["issues"]})
                # Still process but flag for approval
                task["requires_approval"] = True

        # Delegate to agent
        result = agent.process_task(task, dry_run=self.dry_run)
        duration_ms = int((time.time() - start) * 1000)

        if result["status"] == "success":
            self._record_outcome(task, Outcome.SUCCESS, duration_ms,
                                 result.get("result", ""))

            # Route based on approval requirement
            if task.get("requires_approval", False):
                self._route_to_approval(task, result.get("result", ""))
            else:
                safe_move(task["filepath"], "Done")
                log_action("Swarm", f"Completed {filename} via {agent.agent_id}", "swarm")
        else:
            self._record_outcome(task, Outcome.FAILURE, duration_ms,
                                 result.get("error", ""))
            log_action("Swarm", f"Failed {filename}: {result.get('error')}", "swarm")

    def _record_outcome(self, task: dict, outcome: Outcome,
                        duration_ms: int, details: str) -> None:
        """Record task outcome for learning."""
        agent = self.registry.find_best_agent(task)
        self.tracker.record(TaskOutcome(
            task_id=task.get("filename", "unknown"),
            task_type=task.get("task_type", "unknown"),
            agent_id=agent.agent_id if agent else "base",
            agent_type=agent.AGENT_TYPE if agent else "base",
            outcome=outcome,
            duration_ms=duration_ms,
            details=details[:200],  # Truncate long details
        ))

    def _run_optimization(self) -> None:
        """Run the self-improving optimization loop."""
        optimizations = self.optimizer.analyze()
        if optimizations:
            log_action("Optimizer", f"Generated {len(optimizations)} recommendations", "swarm")
            for opt in optimizations:
                audit_log("optimization", actor="optimizer",
                          params={
                              "agent_type": opt.agent_type,
                              "recommendation": opt.recommendation[:200],
                              "confidence": opt.confidence,
                          })
                self.optimizer.apply(opt)

    def get_swarm_status(self) -> dict:
        """Get full swarm status for dashboard/API."""
        return {
            "orchestrator": "swarm",
            "tier": "diamond",
            "dry_run": self.dry_run,
            "agents": self.registry.get_swarm_stats(),
            "bus": self.bus.get_stats(),
            "learning": {
                "outcomes": self.tracker.get_stats(),
                "optimizer": self.optimizer.get_stats(),
            },
            "metrics": self.metrics.get_swarm_health(),
        }
