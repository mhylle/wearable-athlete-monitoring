"""Tests for sync_all_athletes_task."""

import uuid
from unittest.mock import MagicMock, patch

from app.tasks.sync_tasks import sync_all_athletes_task


class TestSyncAllAthletesTask:
    """Test the sync_all_athletes_task Celery task."""

    @patch("app.tasks.sync_tasks.sync_athlete_data_task")
    @patch("app.tasks.sync_tasks.asyncio.run")
    def test_dispatches_tasks_for_connected_athletes(
        self,
        mock_asyncio_run: MagicMock,
        mock_sync_task: MagicMock,
    ) -> None:
        athlete_ids = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
        mock_asyncio_run.return_value = athlete_ids

        result = sync_all_athletes_task()

        assert result["dispatched"] == 3
        assert result["athlete_ids"] == athlete_ids
        assert mock_sync_task.delay.call_count == 3
        for aid in athlete_ids:
            mock_sync_task.delay.assert_any_call(aid)

    @patch("app.tasks.sync_tasks.sync_athlete_data_task")
    @patch("app.tasks.sync_tasks.asyncio.run")
    def test_no_athletes_dispatches_nothing(
        self,
        mock_asyncio_run: MagicMock,
        mock_sync_task: MagicMock,
    ) -> None:
        mock_asyncio_run.return_value = []

        result = sync_all_athletes_task()

        assert result["dispatched"] == 0
        mock_sync_task.delay.assert_not_called()

    def test_task_is_registered(self) -> None:
        assert sync_all_athletes_task.name == "app.tasks.sync_tasks.sync_all_athletes_task"
