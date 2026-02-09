import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID

from src.services.thumbnail_generator import ThumbnailGeneratorService, get_thumbnail_generator_service
from src.models.clip import Clip
from src.models.project import Project


class TestThumbnailGeneratorService:
    """Test cases for ThumbnailGeneratorService"""

    def setup_method(self):
        """Setup test environment"""
        self.service = ThumbnailGeneratorService()
        self.mock_clip = Mock(spec=Clip)
        self.mock_clip.id = UUID('12345678-1234-5678-1234-123456789012')
        self.mock_clip.s3_key = 'test_clip.mp4'
        self.mock_clip.duration = 30.0

    def test_service_initialization(self):
        """Test service initializes with required dependencies"""
        assert self.service.s3_service is not None
        assert self.service.ffmpeg_service is not None

    @patch('src.services.thumbnail_generator.get_s3_service')
    @patch('src.services.thumbnail_generator.get_ffmpeg_service')
    def test_generate_thumbnail_from_video_success(self, mock_ffmpeg_service, mock_s3_service):
        """Test successful thumbnail generation from video"""
        # Mock services
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg_service.return_value = mock_ffmpeg_instance
        mock_ffmpeg_instance.get_video_duration.return_value = 60.0
        mock_ffmpeg_instance.extract_thumbnail.return_value = '/tmp/thumbnail.jpg'

        # Test
        result = self.service.generate_thumbnail_from_video('/path/to/video.mp4')

        # Assertions
        assert result == '/tmp/thumbnail.jpg'
        mock_ffmpeg_instance.get_video_duration.assert_called_once_with('/path/to/video.mp4')
        mock_ffmpeg_instance.extract_thumbnail.assert_called_once_with(
            video_path='/path/to/video.mp4',
            timestamp=18.0,  # 30% of 60 seconds
            width=480,
            height=854
        )

    @patch('src.services.thumbnail_generator.get_s3_service')
    @patch('src.services.thumbnail_generator.get_ffmpeg_service')
    def test_generate_thumbnail_from_video_with_custom_timestamp(self, mock_ffmpeg_service, mock_s3_service):
        """Test thumbnail generation with custom timestamp"""
        # Mock services
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg_service.return_value = mock_ffmpeg_instance
        mock_ffmpeg_instance.extract_thumbnail.return_value = '/tmp/thumbnail.jpg'

        # Test with custom timestamp
        result = self.service.generate_thumbnail_from_video('/path/to/video.mp4', timestamp=15.5)

        # Assertions
        assert result == '/tmp/thumbnail.jpg'
        mock_ffmpeg_instance.extract_thumbnail.assert_called_once_with(
            video_path='/path/to/video.mp4',
            timestamp=15.5,
            width=480,
            height=854
        )

    @patch('src.services.thumbnail_generator.get_s3_service')
    @patch('src.services.thumbnail_generator.get_ffmpeg_service')
    def test_generate_thumbnail_from_video_ffmpeg_failure(self, mock_ffmpeg_service, mock_s3_service):
        """Test handling FFmpeg failure"""
        # Mock services
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg_service.return_value = mock_ffmpeg_instance
        mock_ffmpeg_instance.extract_thumbnail.return_value = None

        # Test
        result = self.service.generate_thumbnail_from_video('/path/to/video.mp4')

        # Assertions
        assert result is None

    @patch('tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.unlink')
    def test_generate_thumbnail_for_clip_success(self, mock_unlink, mock_exists, mock_temp_file):
        """Test successful thumbnail generation for clip"""
        # Mock temporary file
        mock_temp = Mock()
        mock_temp.name = '/tmp/video.mp4'
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        mock_temp_file.return_value.__exit__.return_value = None

        # Mock file system
        mock_exists.return_value = True

        # Mock services
        self.service.s3_service._is_mock_mode = Mock(return_value=True)
        self.service.s3_service.generate_signed_url = Mock(return_value='http://example.com/video.mp4')
        self.service.ffmpeg_service.extract_thumbnail = Mock(return_value='/tmp/thumbnail.jpg')

        # Test
        result = self.service.generate_thumbnail_for_clip(self.mock_clip)

        # Assertions
        expected_s3_key = f'clips/{self.mock_clip.id}/thumbnail.jpg'
        assert result == expected_s3_key

        self.service.s3_service.generate_signed_url.assert_called_once_with(
            self.mock_clip.s3_key,
            expiration=3600
        )

        # Verify thumbnail extraction called
        self.service.ffmpeg_service.extract_thumbnail.assert_called_once()

        # Verify cleanup
        assert mock_unlink.call_count >= 1  # At least video file cleanup

    def test_generate_thumbnail_for_clip_no_s3_key(self):
        """Test thumbnail generation when clip has no S3 key"""
        self.mock_clip.s3_key = None

        result = self.service.generate_thumbnail_for_clip(self.mock_clip)

        assert result is None

    @patch('tempfile.NamedTemporaryFile')
    def test_generate_animated_thumbnail_success(self, mock_temp_file):
        """Test successful animated thumbnail generation"""
        # Mock temporary file
        mock_temp = Mock()
        mock_temp.name = '/tmp/video.mp4'
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        mock_temp_file.return_value.__exit__.return_value = None

        # Mock services
        self.service.s3_service._is_mock_mode = Mock(return_value=True)
        self.service.ffmpeg_service.create_preview_gif = Mock(return_value='/tmp/preview.gif')

        # Test
        result = self.service.generate_animated_thumbnail(self.mock_clip, duration=2.0)

        # Assertions
        expected_s3_key = f'clips/{self.mock_clip.id}/animated_thumbnail.gif'
        assert result == expected_s3_key

        self.service.ffmpeg_service.create_preview_gif.assert_called_once_with(
            video_path=mock_temp.name,
            start_time=0,
            duration=2.0,
            width=240,
            height=427,
            fps=10
        )

    def test_generate_animated_thumbnail_no_s3_key(self):
        """Test animated thumbnail generation when clip has no S3 key"""
        self.mock_clip.s3_key = None

        result = self.service.generate_animated_thumbnail(self.mock_clip)

        assert result is None

    @patch('src.services.thumbnail_generator.get_db')
    def test_batch_generate_thumbnails_success(self, mock_get_db):
        """Test successful batch thumbnail generation"""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db)

        # Mock clip query
        mock_clip_1 = Mock(spec=Clip)
        mock_clip_1.id = UUID('12345678-1234-5678-1234-123456789012')
        mock_clip_1.s3_key = 'clip1.mp4'

        mock_clip_2 = Mock(spec=Clip)
        mock_clip_2.id = UUID('12345678-1234-5678-1234-123456789013')
        mock_clip_2.s3_key = 'clip2.mp4'

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_clip_1, mock_clip_2]

        # Mock thumbnail generation
        with patch.object(self.service, 'generate_thumbnail_for_clip') as mock_generate:
            mock_generate.side_effect = ['thumbnail1.jpg', 'thumbnail2.jpg']

            # Test
            clip_ids = [str(mock_clip_1.id), str(mock_clip_2.id)]
            result = self.service.batch_generate_thumbnails(clip_ids)

            # Assertions
            assert result['total'] == 2
            assert result['successful'] == 2
            assert result['failed'] == 0
            assert len(result['results']) == 2
            assert result['results'][str(mock_clip_1.id)]['success'] is True
            assert result['results'][str(mock_clip_2.id)]['success'] is True

    def test_download_video_temp_mock_mode(self):
        """Test temporary video download in mock mode"""
        self.service.s3_service._is_mock_mode = Mock(return_value=True)

        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp = Mock()
            mock_temp.name = '/tmp/video.mp4'
            mock_temp_file.return_value = mock_temp

            with patch('builtins.open', mock=Mock()) as mock_open:
                result = self.service._download_video_temp('test_key.mp4')

                assert result == '/tmp/video.mp4'
                mock_open.assert_called_once_with('/tmp/video.mp4', 'wb')

    def test_upload_thumbnail_to_s3_mock_mode(self):
        """Test thumbnail upload in mock mode"""
        self.service.s3_service._is_mock_mode = Mock(return_value=True)

        result = self.service._upload_thumbnail_to_s3('/path/thumbnail.jpg', 'test_key.jpg')

        assert result is True

    def test_upload_thumbnail_to_s3_real_mode(self):
        """Test thumbnail upload in real mode"""
        self.service.s3_service._is_mock_mode = Mock(return_value=False)
        self.service.s3_service.upload_file = Mock(return_value=True)

        result = self.service._upload_thumbnail_to_s3('/path/thumbnail.jpg', 'test_key.jpg')

        assert result is True
        self.service.s3_service.upload_file.assert_called_once_with(
            file_path='/path/thumbnail.jpg',
            s3_key='test_key.jpg',
            content_type='image/jpeg'
        )

    def test_select_best_thumbnail_timestamp(self):
        """Test best timestamp selection"""
        candidates = [10.0, 20.0, 30.0]

        result = self.service._select_best_thumbnail_timestamp('/path/video.mp4', candidates)

        # Should return middle candidate
        assert result == 20.0

    def test_clean_up_orphaned_thumbnails(self):
        """Test orphaned thumbnails cleanup"""
        result = self.service.clean_up_orphaned_thumbnails()

        # In mock mode, should return success
        assert result['scanned'] >= 0
        assert result['orphaned'] >= 0
        assert result['deleted'] >= 0
        assert result['errors'] >= 0


def test_get_thumbnail_generator_service():
    """Test service factory function"""
    service = get_thumbnail_generator_service()
    assert isinstance(service, ThumbnailGeneratorService)