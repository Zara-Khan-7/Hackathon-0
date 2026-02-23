"""REST API Server — exposes AI Employee status and controls via HTTP.

Mock implementation using Flask. Provides endpoints for:
- Dashboard status
- Agent health
- Task management
- CRM data
- Swarm metrics

In DRY_RUN / mock mode, no actual server is started — just the route handlers.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

# Flask is optional — API can work without it in mock mode
try:
    from flask import Flask, jsonify, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


class APIServer:
    """REST API for the Diamond tier AI Employee.

    Can run as a real Flask server or in mock mode (returns dicts).
    """

    def __init__(self, project_root: Path, mock: bool = True):
        self._root = project_root
        self._mock = mock
        self._app = None
        self._registry = None
        self._tracker = None
        self._crm = None
        self._vault = None

        if HAS_FLASK and not mock:
            self._app = Flask("ai-employee-api")
            self._setup_routes()

    def set_components(self, registry=None, tracker=None, crm=None, vault=None):
        """Inject Diamond components for the API to expose."""
        self._registry = registry
        self._tracker = tracker
        self._crm = crm
        self._vault = vault

    # --- Route handlers (work in both Flask and mock mode) ---

    def get_status(self) -> dict:
        """GET /api/status — overall system status."""
        return {
            "status": "running",
            "tier": "diamond",
            "timestamp": time.time(),
            "mock_mode": self._mock,
            "components": {
                "agents": self._registry is not None,
                "tracker": self._tracker is not None,
                "crm": self._crm is not None,
                "vault": self._vault is not None,
            },
        }

    def get_agents(self) -> dict:
        """GET /api/agents — list all agents and their stats."""
        if self._registry is None:
            return {"agents": [], "error": "Registry not initialized"}
        return self._registry.get_swarm_stats()

    def get_tasks(self, folder: str = "Needs_Action") -> dict:
        """GET /api/tasks — list tasks in a folder."""
        folder_path = self._root / folder
        if not folder_path.exists():
            return {"tasks": [], "folder": folder}

        tasks = []
        for f in sorted(folder_path.glob("*.md")):
            tasks.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime,
            })
        return {"tasks": tasks, "folder": folder, "count": len(tasks)}

    def get_metrics(self) -> dict:
        """GET /api/metrics — performance metrics."""
        if self._tracker is None:
            return {"metrics": {}, "error": "Tracker not initialized"}
        return self._tracker.get_stats()

    def get_crm_summary(self) -> dict:
        """GET /api/crm — CRM summary."""
        if self._crm is None:
            return {"crm": {}, "error": "CRM not initialized"}
        return self._crm.get_stats()

    def get_health(self) -> dict:
        """GET /api/health — system health check."""
        return {
            "healthy": True,
            "timestamp": time.time(),
            "checks": {
                "api": "ok",
                "agents": "ok" if self._registry else "not_initialized",
                "crm": "ok" if self._crm else "not_initialized",
            },
        }

    def get_folders(self) -> dict:
        """GET /api/folders — count files in each folder."""
        folder_names = [
            "Inbox", "Needs_Action", "In_Progress", "Pending_Approval",
            "Approved", "Rejected", "Done", "Errors", "Logs",
            "Accounting", "Briefings",
        ]
        counts = {}
        for name in folder_names:
            folder = self._root / name
            if folder.exists():
                counts[name] = len(list(folder.glob("*.md")))
            else:
                counts[name] = 0
        return {"folders": counts}

    # --- Flask integration ---

    def _setup_routes(self):
        """Register Flask routes (only when Flask is available)."""
        if not self._app:
            return

        @self._app.route("/api/status")
        def status():
            return jsonify(self.get_status())

        @self._app.route("/api/agents")
        def agents():
            return jsonify(self.get_agents())

        @self._app.route("/api/tasks")
        def tasks():
            folder = request.args.get("folder", "Needs_Action")
            return jsonify(self.get_tasks(folder))

        @self._app.route("/api/metrics")
        def metrics():
            return jsonify(self.get_metrics())

        @self._app.route("/api/crm")
        def crm():
            return jsonify(self.get_crm_summary())

        @self._app.route("/api/health")
        def health():
            return jsonify(self.get_health())

        @self._app.route("/api/folders")
        def folders():
            return jsonify(self.get_folders())

    def run(self, host: str = "127.0.0.1", port: int = 8080):
        """Start the Flask server (non-mock mode only)."""
        if self._mock:
            return {"mock": True, "message": "API running in mock mode"}
        if not self._app:
            return {"error": "Flask not available"}
        self._app.run(host=host, port=port, debug=False)

    def get_stats(self) -> dict:
        return {
            "mock_mode": self._mock,
            "flask_available": HAS_FLASK,
            "endpoints": 7,
        }
