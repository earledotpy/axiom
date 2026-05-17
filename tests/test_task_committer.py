import pytest

from axiom.core.task_committer import TaskCommitError, TaskCommitter
from axiom.persistence.repositories import create_session, create_task, get_task

TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"


def test_task_committer_commits_pending_to_running_with_heartbeats():
    session_id = create_session(operator_id="committer-running")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-committer-running",
        task_class="system_maintenance",
        task_type="committer_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    result = TaskCommitter().commit_status(task_id, "running")

    task = get_task(task_id)

    assert result.task_id == task_id
    assert result.previous_status == "pending"
    assert result.next_status == "running"
    assert result.heartbeat_before_id > 0
    assert result.heartbeat_after_id > result.heartbeat_before_id
    assert task["status"] == "running"


def test_task_committer_commits_running_to_completed():
    session_id = create_session(operator_id="committer-completed")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-committer-completed",
        task_class="system_maintenance",
        task_type="committer_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    committer = TaskCommitter()
    committer.commit_status(task_id, "running")
    result = committer.commit_status(task_id, "completed", result_text="done")

    task = get_task(task_id)

    assert result.previous_status == "running"
    assert result.next_status == "completed"
    assert task["status"] == "completed"
    assert task["result_text"] == "done"
    assert task["completed_at"] is not None


def test_task_committer_rejects_invalid_transition():
    session_id = create_session(operator_id="committer-invalid")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-committer-invalid",
        task_class="system_maintenance",
        task_type="committer_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    committer = TaskCommitter()
    committer.commit_status(task_id, "running")
    committer.commit_status(task_id, "completed")

    with pytest.raises(Exception):
        committer.commit_status(task_id, "running")


def test_task_committer_rejects_unknown_task():
    with pytest.raises(TaskCommitError):
        TaskCommitter().commit_status(999999999, "running")


def test_task_committer_rejects_second_running_task_in_same_session():
    session_id = create_session(operator_id="committer-one-running")

    task_id_1 = create_task(
        session_id=session_id,
        chain_id="chain-one-running",
        task_class="system_maintenance",
        task_type="committer_test_1",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    task_id_2 = create_task(
        session_id=session_id,
        chain_id="chain-one-running",
        task_class="system_maintenance",
        task_type="committer_test_2",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    committer = TaskCommitter()
    committer.commit_status(task_id_1, "running")

    with pytest.raises(TaskCommitError):
        committer.commit_status(task_id_2, "running")


def test_task_committer_rejects_running_without_manifest_id():
    session_id = create_session(operator_id="committer-missing-manifest")
    task_id = create_task(
        session_id=session_id,
        chain_id="chain-missing-manifest",
        task_class="system_maintenance",
        task_type="committer_missing_manifest_test",
    )

    with pytest.raises(TaskCommitError) as exc:
        TaskCommitter().commit_status(task_id, "running")

    assert "manifest_id is required" in str(exc.value)
