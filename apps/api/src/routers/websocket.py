"""
WebSocket Router for Real-time Project Updates

Provides WebSocket endpoints for receiving real-time updates about project processing
according to PRD F4-16.

Endpoint: /ws/projects/{project_id}
Sends JSON updates with status and progression.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog
import uuid
import json
from typing import Dict, Set
from datetime import datetime

from ..database import get_db
from ..models.project import Project
from ..models.user import User
from ..middleware.auth import get_current_user_from_token

logger = structlog.get_logger()

router = APIRouter()


class WebSocketManager:
    """Manages WebSocket connections for real-time project updates."""

    def __init__(self):
        # Store active connections: {project_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.connection_counter = 0

    async def connect(self, websocket: WebSocket, project_id: str, user_id: str) -> str:
        """Accept a WebSocket connection and register it for a project."""
        await websocket.accept()

        # Generate unique connection ID
        self.connection_counter += 1
        connection_id = f"{user_id}_{self.connection_counter}"

        # Initialize project connections if not exists
        if project_id not in self.active_connections:
            self.active_connections[project_id] = {}

        # Register connection
        self.active_connections[project_id][connection_id] = websocket

        logger.info(
            "WebSocket connected",
            project_id=project_id,
            user_id=user_id,
            connection_id=connection_id,
            total_connections=len(self.active_connections[project_id])
        )

        return connection_id

    def disconnect(self, project_id: str, connection_id: str):
        """Disconnect a WebSocket and remove it from active connections."""
        if project_id in self.active_connections:
            if connection_id in self.active_connections[project_id]:
                del self.active_connections[project_id][connection_id]

                # Clean up empty project entries
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]

                logger.info(
                    "WebSocket disconnected",
                    project_id=project_id,
                    connection_id=connection_id
                )

    async def send_project_update(self, project_id: str, message: dict):
        """Send update message to all connections for a specific project."""
        if project_id not in self.active_connections:
            return

        # Create update message
        update_data = {
            "type": "project_update",
            "timestamp": datetime.utcnow().isoformat(),
            "project_id": project_id,
            **message
        }

        # Send to all connections for this project
        connections_to_remove = []
        for connection_id, websocket in self.active_connections[project_id].items():
            try:
                await websocket.send_text(json.dumps(update_data))
            except Exception as e:
                logger.warning(
                    "Failed to send WebSocket message",
                    project_id=project_id,
                    connection_id=connection_id,
                    error=str(e)
                )
                connections_to_remove.append(connection_id)

        # Remove failed connections
        for connection_id in connections_to_remove:
            self.disconnect(project_id, connection_id)

        logger.debug(
            "Sent project update",
            project_id=project_id,
            message_type=message.get('status', 'unknown'),
            connections_count=len(self.active_connections.get(project_id, {}))
        )

    async def send_error_message(self, websocket: WebSocket, error: str):
        """Send error message to a specific WebSocket connection."""
        try:
            error_data = {
                "type": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": error
            }
            await websocket.send_text(json.dumps(error_data))
        except Exception as e:
            logger.error("Failed to send error message", error=str(e))


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def get_current_user_from_websocket_token(token: str, db: Session) -> User:
    """Get current user from WebSocket token parameter."""
    try:
        # Reuse existing auth logic
        return await get_current_user_from_token(token, db)
    except Exception as e:
        logger.warning("WebSocket authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


@router.websocket("/projects/{project_id}")
async def websocket_project_updates(
    websocket: WebSocket,
    project_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time project updates.

    PRD F4-16: Provides real-time updates for project processing status and progress.

    Query parameters:
    - token: JWT authentication token

    Message format:
    {
        "type": "project_update",
        "timestamp": "2024-01-01T00:00:00",
        "project_id": "uuid",
        "status": "downloading|transcribing|analyzing|processing|done|failed",
        "progress": 0-100,
        "current_step": "string",
        "step_details": {...},
        "error_message": "string|null"
    }
    """
    connection_id = None
    try:
        # Validate project ID format
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            await websocket_manager.send_error_message(websocket, "Invalid project ID format")
            return

        # Authenticate user
        try:
            current_user = await get_current_user_from_websocket_token(token, db)
        except Exception:
            await websocket_manager.send_error_message(websocket, "Authentication failed")
            return

        # Verify project exists and belongs to user
        project = db.query(Project).filter(
            Project.id == project_uuid,
            Project.user_id == current_user.id
        ).first()

        if not project:
            await websocket_manager.send_error_message(websocket, "Project not found or access denied")
            return

        # Connect WebSocket
        connection_id = await websocket_manager.connect(websocket, project_id, str(current_user.id))

        # Send initial project status
        await websocket_manager.send_project_update(project_id, {
            "status": project.status,
            "progress": project.processing_progress,
            "current_step": project.current_step,
            "error_message": project.error_message,
            "step_details": _get_step_details(project)
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (though we don't expect any from client)
                data = await websocket.receive_text()
                logger.debug("Received WebSocket message", project_id=project_id, data=data)

                # Parse and handle client messages if needed
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received from WebSocket client", project_id=project_id)

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected", project_id=project_id)
                break

    except Exception as e:
        logger.error(
            "WebSocket error",
            project_id=project_id,
            error=str(e),
            connection_id=connection_id
        )
    finally:
        # Ensure cleanup
        if connection_id:
            websocket_manager.disconnect(project_id, connection_id)


def _get_step_details(project: Project) -> dict:
    """Generate step details based on project status."""
    if project.status == "downloading":
        return {
            "message": "Downloading video from source",
            "current_operation": "Video download in progress"
        }
    elif project.status == "transcribing":
        return {
            "message": "Extracting audio and generating transcript",
            "current_operation": "Sending audio to Deepgram API"
        }
    elif project.status == "analyzing":
        return {
            "message": "Analyzing content for viral moments",
            "current_operation": "AI analysis with Claude Haiku"
        }
    elif project.status == "processing":
        return {
            "message": "Processing video clips",
            "current_operation": "Cutting, cropping and adding subtitles"
        }
    elif project.status == "done":
        return {
            "message": "Processing complete!",
            "current_operation": "Ready for download"
        }
    elif project.status == "failed":
        return {
            "message": "Processing failed",
            "current_operation": "Error occurred during processing",
            "error": project.error_message
        }
    else:
        return {
            "message": "Preparing to process",
            "current_operation": "Initializing pipeline"
        }


# Function to be used by Celery workers to send updates
async def send_project_update(project_id: str, status: str, progress: int, current_step: str = None, error_message: str = None):
    """
    Send project update to all connected WebSocket clients.

    This function should be called by Celery workers to push real-time updates.
    """
    message = {
        "status": status,
        "progress": progress,
        "current_step": current_step,
        "error_message": error_message
    }

    await websocket_manager.send_project_update(project_id, message)


# Export the manager for use in other modules
__all__ = ["router", "websocket_manager", "send_project_update"]