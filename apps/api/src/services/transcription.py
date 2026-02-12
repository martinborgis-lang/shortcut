import os
import tempfile
import subprocess
import structlog
import httpx
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import asyncio

from ..config import settings

logger = structlog.get_logger()


class TranscriptionService:
    """
    Service for transcribing audio using Deepgram API.

    Critères PRD F4-05: Envoie l'audio à Deepgram API, récupère la transcription avec timestamps word-level, stocke en JSONB
    """

    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.api_url = "https://api.deepgram.com/v1/listen"

    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode for development"""
        return os.getenv("MOCK_MODE", "false").lower() == "true"

    async def transcribe(self, video_path: str) -> Dict[str, Any]:
        """
        Transcribe video audio with word-level timestamps.

        Args:
            video_path: Path to the video file (local or S3 URL)

        Returns:
            Deepgram transcription response with word-level timestamps
        """
        logger.info("Starting transcription", video_path=video_path, mock_mode=self._is_mock_mode())

        if self._is_mock_mode():
            return self._mock_transcribe()

        try:
            # Extract audio from video
            audio_path = self._extract_audio(video_path)

            # Send to Deepgram
            transcript = await self._send_to_deepgram(audio_path)

            # Cleanup temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)

            logger.info("Transcription completed", video_path=video_path)
            return transcript

        except Exception as e:
            logger.error("Transcription failed", video_path=video_path, error=str(e))
            raise Exception(f"Transcription error: {str(e)}")

    def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video using ffmpeg"""
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_path = audio_file.name

            # Extract audio using ffmpeg
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
                "-ar", "16000",  # 16kHz sample rate (optimal for speech)
                "-ac", "1",  # Mono channel
                "-y",  # Overwrite output file
                audio_path
            ]

            logger.info("Extracting audio", cmd=" ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)

            logger.info("Audio extraction completed", audio_path=audio_path)
            return audio_path

        except subprocess.CalledProcessError as e:
            logger.error("Audio extraction failed", error=str(e), stderr=e.stderr)
            raise Exception(f"Failed to extract audio: {str(e)}")

    async def _send_to_deepgram(self, audio_path: str) -> Dict[str, Any]:
        """Send audio to Deepgram API for transcription"""
        if not self.api_key:
            raise Exception("Deepgram API key not configured")

        try:
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "audio/wav"
            }

            # Deepgram parameters for optimal transcription
            params = {
                "model": "nova-2",  # Latest model
                "detect_language": "true",  # Auto-detect language
                "smart_format": "true",  # Smart formatting (punctuation, capitalization)
                "punctuate": "true",  # Add punctuation
                "paragraphs": "true",  # Paragraph detection
                "utterances": "true",  # Utterance detection
                "timestamps": "true",  # Word-level timestamps
                "diarize": "true",  # Speaker diarization
                "numerals": "true",  # Convert numbers to numerals
                "profanity_filter": "false",  # Keep original content
                "redact": "false"  # Don't redact content
            }

            # Read audio file
            with open(audio_path, "rb") as audio_file:
                audio_data = audio_file.read()

            logger.info("Sending to Deepgram API", size_bytes=len(audio_data))

            # Send request to Deepgram
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes timeout
                response = await client.post(
                    self.api_url,
                    params=params,
                    headers=headers,
                    content=audio_data
                )

            response.raise_for_status()
            result = response.json()

            logger.info("Deepgram API response received", confidence=self._get_average_confidence(result))
            return result

        except httpx.RequestError as e:
            logger.error("Deepgram API request failed", error=str(e))
            raise Exception(f"Failed to connect to Deepgram API: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error("Deepgram API error", status_code=e.response.status_code, response=e.response.text)
            raise Exception(f"Deepgram API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            logger.error("Unexpected Deepgram error", error=str(e))
            raise Exception(f"Deepgram processing error: {str(e)}")

    def _get_average_confidence(self, transcript: Dict[str, Any]) -> float:
        """Calculate average confidence score from transcript"""
        try:
            results = transcript.get("results", {})
            channels = results.get("channels", [])

            if not channels:
                return 0.0

            total_confidence = 0.0
            word_count = 0

            for channel in channels:
                for alternative in channel.get("alternatives", []):
                    for word in alternative.get("words", []):
                        if "confidence" in word:
                            total_confidence += word["confidence"]
                            word_count += 1

            return total_confidence / word_count if word_count > 0 else 0.0

        except Exception:
            return 0.0

    def _mock_transcribe(self) -> Dict[str, Any]:
        """Mock transcription for development"""
        logger.info("Using mock transcription")

        # Return mock Deepgram response format
        return {
            "metadata": {
                "transaction_key": "mock-transaction-key",
                "request_id": "mock-request-id",
                "sha256": "mock-sha256",
                "created": "2024-02-06T10:00:00.000Z",
                "duration": 300.0,
                "channels": 1,
                "models": ["nova-2"]
            },
            "results": {
                "channels": [
                    {
                        "alternatives": [
                            {
                                "transcript": "Welcome to this amazing video! Today we're going to talk about creating viral content. This is absolutely incredible and you won't believe what happens next. The secret to viral content is understanding your audience and creating something that resonates with them emotionally. But here's the thing that most people don't realize - timing is everything. You need to hook your viewers in the first three seconds or they'll scroll away. Let me share with you the three most important principles that changed my life and business forever.",
                                "confidence": 0.95,
                                "words": [
                                    {"word": "welcome", "start": 0.0, "end": 0.5, "confidence": 0.98, "punctuated_word": "Welcome"},
                                    {"word": "to", "start": 0.5, "end": 0.65, "confidence": 0.99, "punctuated_word": "to"},
                                    {"word": "this", "start": 0.65, "end": 0.85, "confidence": 0.97, "punctuated_word": "this"},
                                    {"word": "amazing", "start": 0.85, "end": 1.3, "confidence": 0.96, "punctuated_word": "amazing"},
                                    {"word": "video", "start": 1.3, "end": 1.8, "confidence": 0.98, "punctuated_word": "video!"},
                                    {"word": "today", "start": 2.0, "end": 2.4, "confidence": 0.97, "punctuated_word": "Today"},
                                    {"word": "we're", "start": 2.4, "end": 2.7, "confidence": 0.95, "punctuated_word": "we're"},
                                    {"word": "going", "start": 2.7, "end": 3.0, "confidence": 0.98, "punctuated_word": "going"},
                                    {"word": "to", "start": 3.0, "end": 3.1, "confidence": 0.99, "punctuated_word": "to"},
                                    {"word": "talk", "start": 3.1, "end": 3.4, "confidence": 0.97, "punctuated_word": "talk"},
                                    {"word": "about", "start": 3.4, "end": 3.7, "confidence": 0.96, "punctuated_word": "about"},
                                    {"word": "creating", "start": 3.7, "end": 4.2, "confidence": 0.95, "punctuated_word": "creating"},
                                    {"word": "viral", "start": 4.2, "end": 4.6, "confidence": 0.98, "punctuated_word": "viral"},
                                    {"word": "content", "start": 4.6, "end": 5.1, "confidence": 0.97, "punctuated_word": "content."},

                                    # Continue with more words to simulate realistic transcript
                                    {"word": "this", "start": 15.0, "end": 15.2, "confidence": 0.96, "punctuated_word": "This"},
                                    {"word": "is", "start": 15.2, "end": 15.4, "confidence": 0.99, "punctuated_word": "is"},
                                    {"word": "absolutely", "start": 15.4, "end": 16.0, "confidence": 0.94, "punctuated_word": "absolutely"},
                                    {"word": "incredible", "start": 16.0, "end": 16.8, "confidence": 0.95, "punctuated_word": "incredible"},

                                    {"word": "you", "start": 30.0, "end": 30.2, "confidence": 0.98, "punctuated_word": "you"},
                                    {"word": "won't", "start": 30.2, "end": 30.5, "confidence": 0.96, "punctuated_word": "won't"},
                                    {"word": "believe", "start": 30.5, "end": 31.0, "confidence": 0.97, "punctuated_word": "believe"},
                                    {"word": "what", "start": 31.0, "end": 31.2, "confidence": 0.98, "punctuated_word": "what"},
                                    {"word": "happens", "start": 31.2, "end": 31.7, "confidence": 0.95, "punctuated_word": "happens"},
                                    {"word": "next", "start": 31.7, "end": 32.1, "confidence": 0.97, "punctuated_word": "next."},

                                    {"word": "the", "start": 45.0, "end": 45.2, "confidence": 0.99, "punctuated_word": "The"},
                                    {"word": "secret", "start": 45.2, "end": 45.7, "confidence": 0.96, "punctuated_word": "secret"},
                                    {"word": "to", "start": 45.7, "end": 45.9, "confidence": 0.98, "punctuated_word": "to"},
                                    {"word": "viral", "start": 45.9, "end": 46.4, "confidence": 0.97, "punctuated_word": "viral"},
                                    {"word": "content", "start": 46.4, "end": 46.9, "confidence": 0.95, "punctuated_word": "content"},

                                    # Continue pattern for full mock transcript...
                                    {"word": "timing", "start": 80.0, "end": 80.5, "confidence": 0.97, "punctuated_word": "timing"},
                                    {"word": "is", "start": 80.5, "end": 80.7, "confidence": 0.99, "punctuated_word": "is"},
                                    {"word": "everything", "start": 80.7, "end": 81.5, "confidence": 0.96, "punctuated_word": "everything."}
                                ]
                            }
                        ]
                    }
                ]
            }
        }

    def extract_text_segments(self, transcript: Dict[str, Any], segment_duration: float = 30.0) -> List[Dict[str, Any]]:
        """
        Extract text segments from transcript for easier processing.

        Args:
            transcript: Deepgram transcript response
            segment_duration: Duration of each text segment in seconds

        Returns:
            List of text segments with timestamps
        """
        try:
            segments = []
            results = transcript.get("results", {})
            channels = results.get("channels", [])

            if not channels:
                return segments

            words = []
            for channel in channels:
                for alternative in channel.get("alternatives", []):
                    words.extend(alternative.get("words", []))

            if not words:
                return segments

            # Group words into segments
            current_segment = {
                "start_time": words[0]["start"],
                "words": [],
                "text": ""
            }

            for word in words:
                word_start = word["start"]

                # If we've exceeded segment duration, start new segment
                if word_start - current_segment["start_time"] >= segment_duration:
                    if current_segment["words"]:
                        current_segment["end_time"] = current_segment["words"][-1]["end"]
                        current_segment["text"] = " ".join([w["punctuated_word"] for w in current_segment["words"]])
                        segments.append(current_segment)

                    current_segment = {
                        "start_time": word_start,
                        "words": [],
                        "text": ""
                    }

                current_segment["words"].append(word)

            # Add final segment
            if current_segment["words"]:
                current_segment["end_time"] = current_segment["words"][-1]["end"]
                current_segment["text"] = " ".join([w["punctuated_word"] for w in current_segment["words"]])
                segments.append(current_segment)

            logger.info("Text segments extracted", segment_count=len(segments))
            return segments

        except Exception as e:
            logger.error("Failed to extract text segments", error=str(e))
            return []