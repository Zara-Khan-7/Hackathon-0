"""Cloud Manager — mock multi-cloud scaling.

Simulates managing cloud instances across providers.
Production would use cloud provider SDKs (boto3, google-cloud, azure-mgmt).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CloudProvider(str, Enum):
    ORACLE = "oracle"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    MOCK = "mock"


class InstanceStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    TERMINATING = "terminating"


@dataclass
class CloudInstance:
    """A cloud VM instance."""
    instance_id: str
    provider: CloudProvider
    role: str  # cloud | local | worker
    status: InstanceStatus = InstanceStatus.STOPPED
    created_at: float = field(default_factory=time.time)
    ip_address: str = "127.0.0.1"
    specs: str = "mock-1vcpu-1gb"


class CloudManager:
    """Mock cloud instance manager for Diamond tier.

    Simulates spinning up/down cloud workers for horizontal scaling.
    """

    def __init__(self, max_instances: int = 3, provider: str = "mock"):
        self._max_instances = max_instances
        self._provider = CloudProvider(provider)
        self._instances: dict[str, CloudInstance] = {}
        self._next_id = 1

    def launch_instance(self, role: str = "worker") -> CloudInstance:
        """Launch a new cloud instance."""
        if len(self._instances) >= self._max_instances:
            raise RuntimeError(
                f"Max instances ({self._max_instances}) reached. "
                f"Cannot launch more."
            )

        instance_id = f"{self._provider.value}-{self._next_id:03d}"
        self._next_id += 1

        instance = CloudInstance(
            instance_id=instance_id,
            provider=self._provider,
            role=role,
            status=InstanceStatus.RUNNING,
            ip_address=f"10.0.0.{self._next_id}",
        )
        self._instances[instance_id] = instance
        return instance

    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate a cloud instance."""
        instance = self._instances.get(instance_id)
        if instance is None:
            return False
        instance.status = InstanceStatus.TERMINATING
        del self._instances[instance_id]
        return True

    def stop_instance(self, instance_id: str) -> bool:
        """Stop (but don't terminate) an instance."""
        instance = self._instances.get(instance_id)
        if instance is None:
            return False
        instance.status = InstanceStatus.STOPPED
        return True

    def start_instance(self, instance_id: str) -> bool:
        """Start a stopped instance."""
        instance = self._instances.get(instance_id)
        if instance is None:
            return False
        instance.status = InstanceStatus.RUNNING
        return True

    def list_instances(self, status: str | None = None) -> list[dict]:
        """List all managed instances."""
        results = []
        for inst in self._instances.values():
            if status and inst.status.value != status:
                continue
            results.append({
                "instance_id": inst.instance_id,
                "provider": inst.provider.value,
                "role": inst.role,
                "status": inst.status.value,
                "ip_address": inst.ip_address,
                "specs": inst.specs,
            })
        return results

    def get_instance(self, instance_id: str) -> dict | None:
        """Get details for a specific instance."""
        inst = self._instances.get(instance_id)
        if inst is None:
            return None
        return {
            "instance_id": inst.instance_id,
            "provider": inst.provider.value,
            "role": inst.role,
            "status": inst.status.value,
            "ip_address": inst.ip_address,
            "specs": inst.specs,
            "created_at": inst.created_at,
        }

    @property
    def running_count(self) -> int:
        return sum(
            1 for i in self._instances.values()
            if i.status == InstanceStatus.RUNNING
        )

    def scale_to(self, target_count: int, role: str = "worker") -> list[CloudInstance]:
        """Scale running instances to target count."""
        running = [
            i for i in self._instances.values()
            if i.status == InstanceStatus.RUNNING and i.role == role
        ]

        launched = []
        if len(running) < target_count:
            # Scale up
            for _ in range(target_count - len(running)):
                try:
                    inst = self.launch_instance(role)
                    launched.append(inst)
                except RuntimeError:
                    break
        elif len(running) > target_count:
            # Scale down
            to_remove = running[target_count:]
            for inst in to_remove:
                self.terminate_instance(inst.instance_id)

        return launched

    def get_stats(self) -> dict:
        return {
            "provider": self._provider.value,
            "max_instances": self._max_instances,
            "total_instances": len(self._instances),
            "running": self.running_count,
            "mock": True,
        }
