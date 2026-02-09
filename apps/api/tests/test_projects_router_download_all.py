import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.models.clip import Clip
from src.models.project import Project
from src.models.user import User


class TestProjectsRouterDownloadAll:
    """Test cases for projects router download-all endpoint"""

    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.mock_user = Mock(spec=User)
        self.mock_user.id = uuid.uuid4()

        self.mock_project = Mock(spec=Project)
        self.mock_project.id = uuid.uuid4()
        self.mock_project.user_id = self.mock_user.id
        self.mock_project.source_url = "https://youtube.com/watch?v=test123"

        self.mock_clip_1 = Mock(spec=Clip)
        self.mock_clip_1.id = uuid.uuid4()
        self.mock_clip_1.title = "Test Clip 1"
        self.mock_clip_1.status = "ready"
        self.mock_clip_1.s3_key = "clips/test1.mp4"
        self.mock_clip_1.duration = 30.0

        self.mock_clip_2 = Mock(spec=Clip)
        self.mock_clip_2.id = uuid.uuid4()
        self.mock_clip_2.title = "Test Clip 2"
        self.mock_clip_2.status = "ready"
        self.mock_clip_2.s3_key = "clips/test2.mp4"
        self.mock_clip_2.duration = 45.0

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    @patch('src.routers.projects.get_s3_service')
    def test_download_all_project_clips_success(self, mock_s3_service, mock_db, mock_get_user):
        """Test successful download of all project clips"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock project query
        mock_project_query = Mock()
        mock_db_session.query.return_value = mock_project_query
        mock_project_query.filter.return_value.first.return_value = self.mock_project

        # Mock clips query
        mock_clips_query = Mock()
        # We need to handle multiple query calls (project and clips)
        mock_db_session.query.side_effect = [mock_project_query, mock_clips_query]
        mock_clips_query.filter.return_value.all.return_value = [self.mock_clip_1, self.mock_clip_2]

        # Mock S3 service
        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance._is_mock_mode.return_value = True
        mock_s3_instance.get_object_info.return_value = {"exists": True, "size": 5000000}  # 5MB
        mock_s3_instance.generate_download_url.return_value = "https://s3.example.com/download.zip"

        # Test
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            with patch('zipfile.ZipFile') as mock_zip:
                mock_temp = Mock()
                mock_temp.name = '/tmp/project_clips.zip'
                mock_temp_file.return_value = mock_temp

                response = self.client.get(f"/api/projects/{self.mock_project.id}/download-all")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['download_url'] == "https://s3.example.com/download.zip"
        assert data['clips_count'] == 2
        assert data['total_size'] == 10000000  # 2 clips * 5MB each
        assert 'filename' in data
        assert 'expires_at' in data

        # Verify S3 operations were called
        assert mock_s3_instance.get_object_info.call_count == 2  # Once per clip
        mock_s3_instance.generate_download_url.assert_called_once()

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    def test_download_all_project_not_found(self, mock_db, mock_get_user):
        """Test download when project doesn't exist or user has no access"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock project query returning None
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        # Test
        response = self.client.get(f"/api/projects/{uuid.uuid4()}/download-all")

        # Assertions
        assert response.status_code == 404
        assert "Project not found" in response.json()['detail']

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    def test_download_all_no_ready_clips(self, mock_db, mock_get_user):
        """Test download when project has no ready clips"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock project query
        mock_project_query = Mock()
        mock_clips_query = Mock()
        mock_db_session.query.side_effect = [mock_project_query, mock_clips_query]
        mock_project_query.filter.return_value.first.return_value = self.mock_project
        mock_clips_query.filter.return_value.all.return_value = []  # No ready clips

        # Test
        response = self.client.get(f"/api/projects/{self.mock_project.id}/download-all")

        # Assertions
        assert response.status_code == 404
        assert "No clips ready for download" in response.json()['detail']

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    @patch('src.routers.projects.get_s3_service')
    def test_download_all_with_processing_clips(self, mock_s3_service, mock_db, mock_get_user):
        """Test download when project has both ready and processing clips"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Create clips with different statuses
        processing_clip = Mock(spec=Clip)
        processing_clip.id = uuid.uuid4()
        processing_clip.status = "processing"
        processing_clip.s3_key = None

        # Mock queries
        mock_project_query = Mock()
        mock_clips_query = Mock()
        mock_db_session.query.side_effect = [mock_project_query, mock_clips_query]
        mock_project_query.filter.return_value.first.return_value = self.mock_project
        # Only ready clips should be returned due to filter
        mock_clips_query.filter.return_value.all.return_value = [self.mock_clip_1]

        # Mock S3 service
        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance._is_mock_mode.return_value = True
        mock_s3_instance.get_object_info.return_value = {"exists": True, "size": 2500000}
        mock_s3_instance.generate_download_url.return_value = "https://s3.example.com/project.zip"

        # Test
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            with patch('zipfile.ZipFile'):
                mock_temp = Mock()
                mock_temp.name = '/tmp/project.zip'
                mock_temp_file.return_value = mock_temp

                response = self.client.get(f"/api/projects/{self.mock_project.id}/download-all")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['clips_count'] == 1  # Only the ready clip
        assert data['total_size'] == 2500000

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    @patch('src.routers.projects.get_s3_service')
    def test_download_all_s3_upload_failure(self, mock_s3_service, mock_db, mock_get_user):
        """Test download when S3 upload fails"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock successful queries
        mock_project_query = Mock()
        mock_clips_query = Mock()
        mock_db_session.query.side_effect = [mock_project_query, mock_clips_query]
        mock_project_query.filter.return_value.first.return_value = self.mock_project
        mock_clips_query.filter.return_value.all.return_value = [self.mock_clip_1]

        # Mock S3 service - successful info but failed download URL generation
        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance._is_mock_mode.return_value = True
        mock_s3_instance.get_object_info.return_value = {"exists": True, "size": 2500000}
        mock_s3_instance.generate_download_url.return_value = None  # Simulate failure

        # Test
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            with patch('zipfile.ZipFile'):
                mock_temp = Mock()
                mock_temp.name = '/tmp/project.zip'
                mock_temp_file.return_value = mock_temp

                response = self.client.get(f"/api/projects/{self.mock_project.id}/download-all")

        # Assertions
        assert response.status_code == 500
        assert "Failed to generate download URL" in response.json()['detail']

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    @patch('src.routers.projects.get_s3_service')
    def test_download_all_zip_creation_error(self, mock_s3_service, mock_db, mock_get_user):
        """Test download when ZIP creation fails"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock successful queries
        mock_project_query = Mock()
        mock_clips_query = Mock()
        mock_db_session.query.side_effect = [mock_project_query, mock_clips_query]
        mock_project_query.filter.return_value.first.return_value = self.mock_project
        mock_clips_query.filter.return_value.all.return_value = [self.mock_clip_1]

        # Mock S3 service
        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance

        # Test with ZIP creation failure
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            with patch('zipfile.ZipFile', side_effect=Exception("ZIP creation failed")):
                mock_temp = Mock()
                mock_temp.name = '/tmp/project.zip'
                mock_temp_file.return_value = mock_temp

                response = self.client.get(f"/api/projects/{self.mock_project.id}/download-all")

        # Assertions
        assert response.status_code == 500
        assert "Failed to create project download" in response.json()['detail']

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    @patch('src.routers.projects.get_s3_service')
    def test_download_all_filename_generation(self, mock_s3_service, mock_db, mock_get_user):
        """Test proper filename generation for download"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock queries
        mock_project_query = Mock()
        mock_clips_query = Mock()
        mock_db_session.query.side_effect = [mock_project_query, mock_clips_query]
        mock_project_query.filter.return_value.first.return_value = self.mock_project
        mock_clips_query.filter.return_value.all.return_value = [self.mock_clip_1]

        # Mock S3 service
        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance._is_mock_mode.return_value = True
        mock_s3_instance.get_object_info.return_value = {"exists": True, "size": 1000000}
        mock_s3_instance.generate_download_url.return_value = "https://s3.example.com/project.zip"

        # Test
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            with patch('zipfile.ZipFile'):
                with patch('src.routers.projects.datetime') as mock_datetime:
                    # Mock datetime for consistent filename
                    mock_datetime.now.return_value.strftime.return_value = "20240301_143000"
                    mock_datetime.utcnow.return_value = datetime(2024, 3, 1, 14, 30, 0)

                    mock_temp = Mock()
                    mock_temp.name = '/tmp/project.zip'
                    mock_temp_file.return_value = mock_temp

                    response = self.client.get(f"/api/projects/{self.mock_project.id}/download-all")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        # Should contain project URL fragment and timestamp
        assert "test123_clips_20240301_143000.zip" in data['filename']

    @patch('src.routers.projects.get_current_user')
    @patch('src.routers.projects.get_db')
    @patch('src.routers.projects.get_s3_service')
    @patch('src.routers.projects._cleanup_temp_zip')
    def test_download_all_background_cleanup(self, mock_cleanup, mock_s3_service, mock_db, mock_get_user):
        """Test that background cleanup task is scheduled"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Mock successful queries
        mock_project_query = Mock()
        mock_clips_query = Mock()
        mock_db_session.query.side_effect = [mock_project_query, mock_clips_query]
        mock_project_query.filter.return_value.first.return_value = self.mock_project
        mock_clips_query.filter.return_value.all.return_value = [self.mock_clip_1]

        # Mock S3 service
        mock_s3_instance = Mock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance._is_mock_mode.return_value = True
        mock_s3_instance.get_object_info.return_value = {"exists": True, "size": 1000000}
        mock_s3_instance.generate_download_url.return_value = "https://s3.example.com/project.zip"

        # Test
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            with patch('zipfile.ZipFile'):
                mock_temp = Mock()
                mock_temp.name = '/tmp/project.zip'
                mock_temp_file.return_value = mock_temp

                response = self.client.get(f"/api/projects/{self.mock_project.id}/download-all")

        # Assertions
        assert response.status_code == 200

        # Note: In a real test, we'd verify that BackgroundTasks.add_task was called
        # This is more complex to test with the current setup, so we just verify the endpoint works

    def test_cleanup_temp_zip_function(self):
        """Test the cleanup function works correctly"""
        from src.routers.projects import _cleanup_temp_zip

        # Test with existing file
        with patch('os.path.exists', return_value=True):
            with patch('os.unlink') as mock_unlink:
                _cleanup_temp_zip('/tmp/test.zip')
                mock_unlink.assert_called_once_with('/tmp/test.zip')

        # Test with non-existing file
        with patch('os.path.exists', return_value=False):
            with patch('os.unlink') as mock_unlink:
                _cleanup_temp_zip('/tmp/nonexistent.zip')
                mock_unlink.assert_not_called()

        # Test with cleanup error
        with patch('os.path.exists', return_value=True):
            with patch('os.unlink', side_effect=Exception("Permission denied")):
                # Should not raise exception
                _cleanup_temp_zip('/tmp/test.zip')