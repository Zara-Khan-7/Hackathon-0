"""Tests for cloud manager (mock scaling)."""

import pytest
from src.scaling.cloud_manager import CloudManager, CloudProvider, InstanceStatus


class TestCloudManager:
    def test_launch_instance(self):
        cm = CloudManager(max_instances=3)
        inst = cm.launch_instance("worker")
        assert inst.status == InstanceStatus.RUNNING
        assert inst.role == "worker"

    def test_max_instances_limit(self):
        cm = CloudManager(max_instances=2)
        cm.launch_instance()
        cm.launch_instance()
        with pytest.raises(RuntimeError, match="Max instances"):
            cm.launch_instance()

    def test_terminate_instance(self):
        cm = CloudManager()
        inst = cm.launch_instance()
        assert cm.terminate_instance(inst.instance_id) is True
        assert cm.running_count == 0

    def test_terminate_nonexistent(self):
        cm = CloudManager()
        assert cm.terminate_instance("fake-id") is False

    def test_stop_and_start(self):
        cm = CloudManager()
        inst = cm.launch_instance()
        assert cm.stop_instance(inst.instance_id) is True
        assert inst.status == InstanceStatus.STOPPED
        assert cm.start_instance(inst.instance_id) is True
        assert inst.status == InstanceStatus.RUNNING

    def test_list_instances(self):
        cm = CloudManager()
        cm.launch_instance("cloud")
        cm.launch_instance("worker")
        instances = cm.list_instances()
        assert len(instances) == 2

    def test_list_instances_by_status(self):
        cm = CloudManager()
        inst1 = cm.launch_instance()
        cm.launch_instance()
        cm.stop_instance(inst1.instance_id)
        running = cm.list_instances(status="running")
        assert len(running) == 1

    def test_get_instance(self):
        cm = CloudManager()
        inst = cm.launch_instance()
        details = cm.get_instance(inst.instance_id)
        assert details is not None
        assert details["status"] == "running"

    def test_scale_up(self):
        cm = CloudManager(max_instances=5)
        launched = cm.scale_to(3, role="worker")
        assert len(launched) == 3
        assert cm.running_count == 3

    def test_scale_down(self):
        cm = CloudManager(max_instances=5)
        cm.scale_to(3, role="worker")
        cm.scale_to(1, role="worker")
        assert cm.running_count == 1

    def test_scale_up_respects_max(self):
        cm = CloudManager(max_instances=2)
        launched = cm.scale_to(5, role="worker")
        assert len(launched) == 2
        assert cm.running_count == 2

    def test_stats(self):
        cm = CloudManager()
        cm.launch_instance()
        stats = cm.get_stats()
        assert stats["total_instances"] == 1
        assert stats["running"] == 1
        assert stats["mock"] is True

    def test_provider(self):
        cm = CloudManager(provider="mock")
        inst = cm.launch_instance()
        assert "mock" in inst.instance_id
