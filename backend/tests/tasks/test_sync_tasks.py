"""Tests for sync_athlete_data_task."""

import json
import uuid
from unittest.mock import MagicMock, patch

from app.tasks.sync_tasks import (
    _set_sync_status,
    get_all_sync_statuses,
    get_sync_status,
    sync_athlete_data_task,
)


class TestSyncStatusTracking:
    """Test Redis sync status storage."""

    @patch("app.tasks.sync_tasks._get_redis")
    def test_set_sync_status(self, mock_get_redis: MagicMock) -> None:
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        _set_sync_status("athlete-123", "completed")

        mock_redis.set.assert_called_once()
        key, value = mock_redis.set.call_args[0][:2]
        assert key == "sync:status:athlete-123"
        data = json.loads(value)
        assert data["status"] == "completed"
        assert data["athlete_id"] == "athlete-123"

    @patch("app.tasks.sync_tasks._get_redis")
    def test_set_sync_status_with_error(self, mock_get_redis: MagicMock) -> None:
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        _set_sync_status("athlete-123", "error", "Connection failed")

        key, value = mock_redis.set.call_args[0][:2]
        data = json.loads(value)
        assert data["status"] == "error"
        assert data["error"] == "Connection failed"

    @patch("app.tasks.sync_tasks._get_redis")
    def test_get_sync_status_found(self, mock_get_redis: MagicMock) -> None:
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({"status": "completed", "athlete_id": "a1"})
        mock_get_redis.return_value = mock_redis

        result = get_sync_status("a1")

        assert result is not None
        assert result["status"] == "completed"

    @patch("app.tasks.sync_tasks._get_redis")
    def test_get_sync_status_not_found(self, mock_get_redis: MagicMock) -> None:
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_get_redis.return_value = mock_redis

        result = get_sync_status("nonexistent")

        assert result is None

    @patch("app.tasks.sync_tasks._get_redis")
    def test_get_all_sync_statuses(self, mock_get_redis: MagicMock) -> None:
        mock_redis = MagicMock()
        mock_redis.keys.return_value = ["sync:status:a1", "sync:status:a2"]
        mock_redis.get.side_effect = [
            json.dumps({"status": "completed", "athlete_id": "a1"}),
            json.dumps({"status": "error", "athlete_id": "a2"}),
        ]
        mock_get_redis.return_value = mock_redis

        statuses = get_all_sync_statuses()

        assert len(statuses) == 2
        assert statuses[0]["athlete_id"] == "a1"
        assert statuses[1]["status"] == "error"


class TestSyncAthleteDataTask:
    """Test the sync_athlete_data_task Celery task."""

    @patch("app.tasks.sync_tasks._set_sync_status")
    @patch("app.tasks.sync_tasks._run_athlete_sync")
    @patch("app.tasks.sync_tasks.asyncio.run")
    def test_successful_sync(
        self,
        mock_asyncio_run: MagicMock,
        mock_run_sync: MagicMock,
        mock_set_status: MagicMock,
    ) -> None:
        mock_asyncio_run.return_value = {
            "records_synced": 10,
            "records_skipped": 2,
            "errors": [],
        }
        athlete_id = str(uuid.uuid4())

        result = sync_athlete_data_task(athlete_id)

        assert result["records_synced"] == 10
        assert result["records_skipped"] == 2
        # Should be called twice: in_progress then completed
        assert mock_set_status.call_count == 2
        mock_set_status.assert_any_call(athlete_id, "in_progress")
        mock_set_status.assert_any_call(athlete_id, "completed")

    @patch("app.tasks.sync_tasks._set_sync_status")
    @patch("app.tasks.sync_tasks._run_athlete_sync")
    @patch("app.tasks.sync_tasks.asyncio.run")
    def test_partial_sync_with_errors(
        self,
        mock_asyncio_run: MagicMock,
        mock_run_sync: MagicMock,
        mock_set_status: MagicMock,
    ) -> None:
        mock_asyncio_run.return_value = {
            "records_synced": 5,
            "records_skipped": 0,
            "errors": ["Failed to fetch sleep"],
        }
        athlete_id = str(uuid.uuid4())

        result = sync_athlete_data_task(athlete_id)

        assert result["records_synced"] == 5
        mock_set_status.assert_any_call(athlete_id, "partial", "Failed to fetch sleep")

    def test_task_is_registered(self) -> None:
        assert sync_athlete_data_task.name == "app.tasks.sync_tasks.sync_athlete_data_task"

    def test_task_has_retries_configured(self) -> None:
        assert sync_athlete_data_task.max_retries == 3
