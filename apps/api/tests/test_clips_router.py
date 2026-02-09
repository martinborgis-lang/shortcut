import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app
from src.models.clip import Clip
from src.models.project import Project
from src.models.user import User


class TestClipsRouter:
    """Test cases for clips router endpoints"""

    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.mock_user = Mock(spec=User)
        self.mock_user.id = uuid.uuid4()
        self.mock_user.plan = "pro"

        self.mock_clip = Mock(spec=Clip)
        self.mock_clip.id = uuid.uuid4()
        self.mock_clip.title = "Test Clip"
        self.mock_clip.start_time = 10.0
        self.mock_clip.end_time = 40.0
        self.mock_clip.duration = 30.0
        self.mock_clip.subtitle_style = "hormozi"
        self.mock_clip.status = "ready"
        self.mock_clip.s3_key = "clips/test.mp4"
        self.mock_clip.thumbnail_url = "thumbnails/test.jpg"
        self.mock_clip.created_at = datetime.utcnow()
        self.mock_clip.updated_at = datetime.utcnow()

        # Mock project
        self.mock_project = Mock(spec=Project)
        self.mock_project.id = uuid.uuid4()
        self.mock_project.user_id = self.mock_user.id
        self.mock_project.source_duration = 300.0

        self.mock_clip.project = self.mock_project
        self.mock_clip.project_id = self.mock_project.id

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    @patch('src.routers.clips.get_s3_service')
    def test_get_clip_success(self, mock_s3_service, mock_db, mock_get_user):
        """Test successful clip retrieval with signed URLs"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.generate_signed_url.return_value = "https://s3.example.com/signed-url"
        mock_s3_instance.generate_download_url.return_value = "https://s3.example.com/download-url"

        # Test
        response = self.client.get(f"/api/clips/{self.mock_clip.id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == str(self.mock_clip.id)
        assert data['title'] == self.mock_clip.title
        assert 'signed_video_url' in data
        assert 'download_url' in data

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    def test_get_clip_not_found(self, mock_db, mock_get_user):
        """Test clip retrieval when clip doesn't exist"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Test
        response = self.client.get(f"/api/clips/{uuid.uuid4()}")

        # Assertions
        assert response.status_code == 404
        assert "Clip not found" in response.json()['detail']

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    @patch('src.routers.clips.get_clip_editor_service')
    def test_update_clip_success(self, mock_editor_service, mock_db, mock_get_user):
        """Test successful clip update"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        mock_editor_instance = Mock()
        mock_editor_service.return_value = mock_editor_instance
        mock_editor_instance.update_clip_timing.return_value = {
            "success": True,
            "requires_regeneration": False
        }

        # Test data
        update_data = {
            "title": "Updated Title",
            "start_time": 15.0,
            "end_time": 45.0
        }

        # Test
        response = self.client.patch(f"/api/clips/{self.mock_clip.id}", json=update_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == "Updated Title"

        # Verify clip was updated
        assert self.mock_clip.title == "Updated Title"
        mock_db_session.commit.assert_called_once()

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    @patch('src.routers.clips.get_clip_editor_service')
    def test_update_clip_invalid_timing(self, mock_editor_service, mock_db, mock_get_user):
        """Test clip update with invalid timing"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        mock_editor_instance = Mock()
        mock_editor_service.return_value = mock_editor_instance
        mock_editor_instance.update_clip_timing.return_value = {
            "success": False,
            "error": "Duration must be at least 10 seconds",
            "requires_regeneration": False
        }

        # Test data - invalid timing (too short)
        update_data = {
            "start_time": 10.0,
            "end_time": 15.0  # Only 5 seconds duration
        }

        # Test
        response = self.client.patch(f"/api/clips/{self.mock_clip.id}", json=update_data)

        # Assertions
        assert response.status_code == 400
        assert "Duration must be at least 10 seconds" in response.json()['detail']

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    @patch('src.routers.clips.get_clip_editor_service')
    @patch('src.routers.clips.regenerate_clip_task')
    def test_regenerate_clip_success(self, mock_task, mock_editor_service, mock_db, mock_get_user):
        """Test successful clip regeneration"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        mock_editor_instance = Mock()
        mock_editor_service.return_value = mock_editor_instance
        mock_editor_instance.regenerate_clip.return_value = {
            "success": True,
            "message": "Clip regeneration started",
            "clip_id": str(self.mock_clip.id),
            "status": "processing"
        }
        mock_editor_instance.estimate_regeneration_time.return_value = 60

        # Test
        response = self.client.post(f"/api/clips/{self.mock_clip.id}/regenerate")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == "Clip regeneration started"
        assert data['estimated_duration_seconds'] == 60

        # Verify background task was started
        mock_task.delay.assert_called_once_with(str(self.mock_clip.id))

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    def test_regenerate_clip_already_processing(self, mock_db, mock_get_user):
        """Test regeneration when clip is already processing"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Set clip status to processing
        self.mock_clip.status = "processing"
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        # Test
        response = self.client.post(f"/api/clips/{self.mock_clip.id}/regenerate")

        # Assertions
        assert response.status_code == 409
        assert "already being processed" in response.json()['detail']

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    @patch('src.routers.clips.get_s3_service')
    def test_get_download_url_success(self, mock_s3_service, mock_db, mock_get_user):
        """Test successful download URL generation"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.generate_download_url.return_value = "https://s3.example.com/download"
        mock_s3_instance.get_object_info.return_value = {"size": 1024000}  # 1MB

        # Test
        response = self.client.get(f"/api/clips/{self.mock_clip.id}/download")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['download_url'] == "https://s3.example.com/download"
        assert data['file_size'] == 1024000
        assert 'expires_at' in data
        assert 'filename' in data

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    def test_get_download_url_not_ready(self, mock_db, mock_get_user):
        """Test download URL when clip is not ready"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Set clip status to processing
        self.mock_clip.status = "processing"
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        # Test
        response = self.client.get(f"/api/clips/{self.mock_clip.id}/download")

        # Assertions
        assert response.status_code == 409
        assert "not ready" in response.json()['detail']

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    @patch('src.routers.clips.get_s3_service')
    def test_delete_clip_success(self, mock_s3_service, mock_db, mock_get_user):
        """Test successful clip deletion"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = self.mock_clip

        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance

        # Test
        response = self.client.delete(f"/api/clips/{self.mock_clip.id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == "Clip deleted successfully"

        # Verify S3 cleanup was attempted
        assert mock_s3_instance.delete_object.call_count >= 1

        # Verify database deletion
        mock_db_session.delete.assert_called_once_with(self.mock_clip)
        mock_db_session.commit.assert_called_once()

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    def test_list_clips_success(self, mock_db, mock_get_user):
        """Test successful clips listing"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock query chain
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_clip, self.mock_clip]

        # Test
        response = self.client.get("/api/clips/")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['clips']) == 2
        assert data['page'] == 1
        assert data['size'] == 20

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    def test_list_clips_with_filters(self, mock_db, mock_get_user):
        """Test clips listing with filters"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock query chain
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_clip]

        # Test with filters
        response = self.client.get("/api/clips/?status=ready&min_viral_score=0.8&sort_by=viral_score&sort_order=desc")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    @patch('src.routers.clips.get_s3_service')
    def test_bulk_download_clips_success(self, mock_s3_service, mock_db, mock_get_user):
        """Test successful bulk download"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock clip queries
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [self.mock_clip]

        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance._is_mock_mode.return_value = True
        mock_s3_instance.get_object_info.return_value = {"exists": True, "size": 1024000}
        mock_s3_instance.generate_download_url.return_value = "https://s3.example.com/download.zip"

        # Test data
        request_data = {
            "clip_ids": [str(self.mock_clip.id)],
            "project_id": str(self.mock_project.id)
        }

        # Test
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            with patch('zipfile.ZipFile') as mock_zip:
                mock_temp = Mock()
                mock_temp.name = '/tmp/test.zip'
                mock_temp_file.return_value = mock_temp

                response = self.client.post("/api/clips/bulk-download", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['download_url'] == "https://s3.example.com/download.zip"
        assert data['clips_count'] == 1

    @patch('src.routers.clips.get_current_user')
    @patch('src.routers.clips.get_db')
    def test_bulk_download_no_clips(self, mock_db, mock_get_user):
        """Test bulk download with no clips found"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock empty query result
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        # Test data
        request_data = {
            "clip_ids": [str(uuid.uuid4())],
            "project_id": str(self.mock_project.id)
        }

        # Test
        response = self.client.post("/api/clips/bulk-download", json=request_data)

        # Assertions
        assert response.status_code == 404
        assert "No clips found" in response.json()['detail']

    def test_list_clips_invalid_sort_field(self):
        """Test clips listing with invalid sort field"""
        with patch('src.routers.clips.get_current_user') as mock_get_user:
            with patch('src.routers.clips.get_db') as mock_db:
                mock_get_user.return_value = self.mock_user
                mock_db_session = Mock()
                mock_db.return_value = mock_db_session

                # Mock query chain
                mock_query = Mock()
                mock_db_session.query.return_value = mock_query
                mock_query.filter.return_value = mock_query

                # Test with invalid sort field
                response = self.client.get("/api/clips/?sort_by=invalid_field")

                # Assertions
                assert response.status_code == 400
                assert "Invalid sort field" in response.json()['detail']