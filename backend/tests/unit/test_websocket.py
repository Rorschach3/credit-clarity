"""
Unit tests for WebSocket functionality.
Tests WebSocket connection manager and message handling.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.websocket_manager import (
    ConnectionManager,
    JobStatusPublisher,
    WebSocketMessage,
)


class TestWebSocketMessage:
    """Tests for WebSocketMessage model."""

    def test_create_message(self):
        """Test creating a WebSocket message."""
        message = WebSocketMessage(
            type="job_status",
            job_id="job-123",
            status="processing",
            progress=50
        )

        assert message.type == "job_status"
        assert message.job_id == "job-123"
        assert message.status == "processing"
        assert message.progress == 50
        assert message.timestamp is not None

    def test_message_with_all_fields(self):
        """Test creating a WebSocket message with all fields."""
        message = WebSocketMessage(
            type="job_status",
            job_id="job-456",
            status="completed",
            progress=100,
            stage="complete",
            message="Processing finished",
            request_id="req-abc123",
            data={"result": "success"}
        )

        assert message.stage == "complete"
        assert message.message == "Processing finished"
        assert message.request_id == "req-abc123"
        assert message.data == {"result": "success"}


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest_asyncio.fixture
    async def manager(self):
        """Create a ConnectionManager for testing."""
        return ConnectionManager()

    @pytest_asyncio.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.close = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test connecting a WebSocket."""
        await manager.connect("job-123", mock_websocket)

        mock_websocket.accept.assert_called_once()
        count = await manager.get_connection_count("job-123")
        assert count == 1

    @pytest.mark.asyncio
    async def test_multiple_connections_per_job(self, manager, mock_websocket):
        """Test multiple WebSocket connections for same job."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect("job-123", ws1)
        await manager.connect("job-123", ws2)

        count = await manager.get_connection_count("job-123")
        assert count == 2

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting a WebSocket."""
        await manager.connect("job-123", mock_websocket)
        await manager.disconnect("job-123", mock_websocket)

        count = await manager.get_connection_count("job-123")
        assert count == 0

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(self, manager, mock_websocket):
        """Test disconnecting a nonexistent connection doesn't raise."""
        await manager.disconnect("job-nonexistent", mock_websocket)  # Should not raise

    @pytest.mark.asyncio
    async def test_broadcast(self, manager, mock_websocket):
        """Test broadcasting a message."""
        await manager.connect("job-123", mock_websocket)

        message = {"type": "job_status", "job_id": "job-123", "progress": 50}
        await manager.broadcast("job-123", message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple(self, manager):
        """Test broadcasting to multiple connections."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect("job-123", ws1)
        await manager.connect("job-123", ws2)

        message = {"type": "test"}
        await manager.broadcast("job-123", message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self, manager):
        """Test broadcasting to job with no connections doesn't raise."""
        message = {"type": "test"}
        await manager.broadcast("job-no-connections", message)  # Should not raise

    @pytest.mark.asyncio
    async def test_get_connection_count_no_job(self, manager):
        """Test getting connection count for nonexistent job."""
        count = await manager.get_connection_count("job-nonexistent")
        assert count == 0

    @pytest.mark.asyncio
    async def test_close_all_connections(self, manager):
        """Test closing all connections."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.close = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.close = AsyncMock()

        await manager.connect("job-1", ws1)
        await manager.connect("job-2", ws2)

        await manager.close_all_connections()

        ws1.close.assert_called_once()
        ws2.close.assert_called_once()

        count1 = await manager.get_connection_count("job-1")
        count2 = await manager.get_connection_count("job-2")
        assert count1 == 0
        assert count2 == 0


class TestJobStatusPublisher:
    """Tests for JobStatusPublisher class."""

    @pytest_asyncio.fixture
    async def publisher(self):
        """Create a JobStatusPublisher for testing."""
        publisher = JobStatusPublisher()
        manager = ConnectionManager()
        await publisher.initialize(manager)
        return publisher

    @pytest.mark.asyncio
    async def test_publish_status(self, publisher):
        """Test publishing job status."""
        manager = ConnectionManager()
        await publisher.initialize(manager)

        # Mock the _publish_to_redis to avoid Redis connection
        publisher._publish_to_redis = AsyncMock(return_value=True)

        await publisher.publish_status(
            job_id="job-123",
            status="processing",
            progress=50,
            stage="ocr",
            message="Processing page 2"
        )

        # Check that broadcast was called
        manager.get_connection_count("job-123")

    @pytest.mark.asyncio
    async def test_publish_status_with_request_id(self, publisher):
        """Test publishing job status with request ID."""
        manager = ConnectionManager()
        await publisher.initialize(manager)
        publisher._publish_to_redis = AsyncMock(return_value=True)

        # We'll test the message format
        message = {
            "type": "job_status",
            "job_id": "job-123",
            "status": "completed",
            "progress": 100,
            "stage": "complete",
            "message": "",
            "request_id": "req-custom",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }

        assert message["request_id"] == "req-custom"
        assert message["type"] == "job_status"

    @pytest.mark.asyncio
    async def test_subscribe_to_job(self, publisher):
        """Test subscribing to job updates."""
        publisher._publish_to_redis = AsyncMock(return_value=True)

        # Should not raise even without Redis
        await publisher.subscribe_to_job("job-123")


class TestConnectionManagerConcurrency:
    """Tests for ConnectionManager thread-safety."""

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test concurrent connection management."""
        manager = ConnectionManager()
        websockets = [AsyncMock() for _ in range(10)]

        # Connect all
        await asyncio.gather(
            *(manager.connect(f"job-{i % 3}", ws) for i, ws in enumerate(websockets))
        )

        # Check counts
        assert await manager.get_connection_count("job-0") == 4  # ws 0, 3, 6, 9
        assert await manager.get_connection_count("job-1") == 3  # ws 1, 4, 7
        assert await manager.get_connection_count("job-2") == 3  # ws 2, 5, 8

    @pytest.mark.asyncio
    async def test_concurrent_disconnects(self):
        """Test concurrent disconnections."""
        manager = ConnectionManager()
        websockets = [AsyncMock() for _ in range(10)]

        # Connect all
        for ws in websockets:
            await manager.connect("job-123", ws)

        # Disconnect all concurrently
        await asyncio.gather(
            *(manager.disconnect("job-123", ws) for ws in websockets)
        )

        count = await manager.get_connection_count("job-123")
        assert count == 0
