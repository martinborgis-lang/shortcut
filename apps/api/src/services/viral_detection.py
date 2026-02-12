import os
import json
import structlog
import re
import ast
from typing import Dict, Any, List
import google.generativeai as genai

from ..config import settings

logger = structlog.get_logger()


class ViralDetectionService:
    """
    Service for detecting viral moments using Google Gemini Flash.

    Critères PRD F4-06: Envoie la transcription à Gemini Flash avec un prompt spécifique, parse la réponse JSON, retourne les segments avec scores
    """

    def __init__(self):
        self.model = None
        if not self._is_mock_mode() and settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash')

    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode for development"""
        return os.getenv("MOCK_MODE", "false").lower() == "true"

    def detect_viral_segments(
        self,
        transcript: Dict[str, Any],
        duration: float,
        max_clips: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detect viral segments from transcript using Google Gemini Flash.

        Args:
            transcript: Deepgram transcript with word-level timestamps
            duration: Total video duration in seconds
            max_clips: Maximum number of clips to detect

        Returns:
            List of viral segments with scores and metadata
        """
        logger.info(
            "Starting viral detection",
            duration=duration,
            max_clips=max_clips,
            mock_mode=self._is_mock_mode()
        )

        if self._is_mock_mode():
            return self._mock_detect_viral_segments(max_clips)

        try:
            # Prepare transcript for Gemini
            transcript_text = self._format_transcript_for_ai(transcript)

            # Generate prompt
            prompt = self._build_viral_detection_prompt(transcript_text, duration, max_clips)

            # Send to Gemini Flash
            response = self._send_to_gemini(prompt)

            # Parse and validate response
            segments = self._parse_gemini_response(response, duration)

            # Filter and sort by virality score
            segments = self._filter_and_rank_segments(segments, max_clips)

            logger.info(
                "Viral detection completed",
                segments_found=len(segments),
                max_clips=max_clips
            )

            return segments

        except Exception as e:
            logger.error("Viral detection failed", error=str(e))
            raise Exception(f"Viral detection error: {str(e)}")

    def _format_transcript_for_ai(self, transcript: Dict[str, Any]) -> str:
        """Format Deepgram transcript for Gemini analysis"""
        try:
            results = transcript.get("results", {})
            channels = results.get("channels", [])

            if not channels:
                return ""

            formatted_text = ""

            for channel in channels:
                for alternative in channel.get("alternatives", []):
                    words = alternative.get("words", [])

                    if not words:
                        continue

                    # Group words by approximate sentences/phrases for better readability
                    current_line = []
                    current_start = None

                    for word in words:
                        if current_start is None:
                            current_start = word["start"]

                        current_line.append(word["punctuated_word"])

                        # End line at punctuation or after reasonable length
                        word_text = word["punctuated_word"]
                        if (
                            word_text.endswith(('.', '!', '?', ':')) or
                            len(current_line) >= 15  # Max words per line
                        ):
                            timestamp = f"[{current_start:.1f}s]"
                            line_text = " ".join(current_line)
                            formatted_text += f"{timestamp} {line_text}\n"

                            current_line = []
                            current_start = None

                    # Add any remaining words
                    if current_line and current_start is not None:
                        timestamp = f"[{current_start:.1f}s]"
                        line_text = " ".join(current_line)
                        formatted_text += f"{timestamp} {line_text}\n"

            return formatted_text.strip()

        except Exception as e:
            logger.error("Failed to format transcript", error=str(e))
            return ""

    def _build_viral_detection_prompt(
        self,
        transcript_text: str,
        duration: float,
        max_clips: int
    ) -> str:
        """Build the viral detection prompt according to PRD specifications"""

        return f"""System: Tu es un expert en contenu viral sur TikTok et les réseaux sociaux. Tu analyses des transcriptions de vidéos pour identifier les meilleurs segments à découper en shorts viraux.

User: Voici la transcription d'une vidéo avec timestamps word-level :

{transcript_text}

Durée totale : {duration} secondes

Identifie les {max_clips} meilleurs segments pour des TikTok shorts viraux (30-90 secondes chacun).

Pour chaque segment, retourne UNIQUEMENT un JSON array :
[
  {{
    "start_time": float,
    "end_time": float,
    "title": "Titre accrocheur pour TikTok (max 60 chars)",
    "virality_score": int (0-100),
    "reason": "Pourquoi ce moment est viral (max 100 chars)",
    "hook": "Première phrase d'accroche suggérée"
  }}
]

Critères de viralité (par ordre d'importance) :
1. Punchline / révélation inattendue
2. Émotion forte (rire, choc, inspiration)
3. Conseil actionnable et concret
4. Polémique / opinion tranchée
5. Storytelling avec tension narrative
6. Moment de réaction intense

IMPORTANT : Les segments ne doivent PAS se chevaucher. Chaque segment doit être auto-suffisant (compréhensible sans contexte).
Retourne UNIQUEMENT le JSON, aucun texte avant ou après."""

    def _send_to_gemini(self, prompt: str) -> str:
        """Send prompt to Gemini Flash and get response"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                )
            )

            response_text = response.text.strip()
            logger.info(
                "Gemini response received",
                response_length=len(response_text),
                model="gemini-1.5-flash"
            )

            return response_text

        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            raise Exception(f"Gemini API error: {str(e)}")

    def _parse_gemini_response(self, response: str, duration: float) -> List[Dict[str, Any]]:
        """Parse and validate Gemini's JSON response"""
        try:
            # Extract JSON from response (in case Gemini adds extra text)
            response = response.strip()

            # Find JSON array in response
            start_idx = response.find('[')
            end_idx = response.rfind(']')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON array found in Gemini response")

            json_text = response[start_idx:end_idx + 1]

            # Try to parse JSON normally first
            try:
                segments = json.loads(json_text)
            except json.JSONDecodeError:
                # Fallback: try to repair JSON
                try:
                    # Fix common JSON issues: unescaped quotes in strings
                    repaired_json = self._repair_json(json_text)
                    segments = json.loads(repaired_json)
                except json.JSONDecodeError:
                    # Last resort: try ast.literal_eval or manual extraction
                    try:
                        segments = ast.literal_eval(json_text)
                    except (ValueError, SyntaxError):
                        segments = self._extract_segments_manually(json_text)
                        if not segments:
                            raise ValueError("Failed to parse JSON with all fallback methods")

            # Validate and sanitize each segment
            validated_segments = []

            for segment in segments:
                try:
                    # Required fields validation
                    if not all(key in segment for key in ["start_time", "end_time", "title", "virality_score", "reason", "hook"]):
                        logger.warning("Segment missing required fields", segment=segment)
                        continue

                    # Data type validation
                    start_time = float(segment["start_time"])
                    end_time = float(segment["end_time"])
                    virality_score = int(segment["virality_score"])

                    # Logical validation
                    if start_time < 0 or end_time > duration or start_time >= end_time:
                        logger.warning("Invalid segment timing", segment=segment, duration=duration)
                        continue

                    if not (30 <= end_time - start_time <= 90):
                        logger.warning("Segment duration outside 30-90s range", segment=segment)
                        # Continue anyway, we can adjust duration later

                    if not (0 <= virality_score <= 100):
                        logger.warning("Invalid virality score", segment=segment)
                        virality_score = max(0, min(100, virality_score))

                    # String length validation
                    title = str(segment["title"])[:60]  # Truncate if too long
                    reason = str(segment["reason"])[:100]  # Truncate if too long
                    hook = str(segment["hook"])

                    validated_segment = {
                        "start_time": start_time,
                        "end_time": end_time,
                        "title": title,
                        "virality_score": virality_score,
                        "reason": reason,
                        "hook": hook
                    }

                    validated_segments.append(validated_segment)

                except (ValueError, KeyError) as e:
                    logger.warning("Invalid segment data", segment=segment, error=str(e))
                    continue

            if not validated_segments:
                raise ValueError("No valid segments found in Gemini response")

            logger.info("Gemini response parsed", segments_found=len(validated_segments))
            return validated_segments

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini JSON response", error=str(e), response=response[:500])
            raise ValueError(f"Invalid JSON in Gemini response: {str(e)}")
        except Exception as e:
            logger.error("Failed to parse Gemini response", error=str(e))
            raise ValueError(f"Failed to parse Gemini response: {str(e)}")

    def _filter_and_rank_segments(self, segments: List[Dict[str, Any]], max_clips: int) -> List[Dict[str, Any]]:
        """Filter overlapping segments and rank by virality score"""
        if not segments:
            return []

        # Sort by virality score (descending)
        segments = sorted(segments, key=lambda x: x["virality_score"], reverse=True)

        # Remove overlapping segments (keep higher scoring ones)
        filtered_segments = []

        for segment in segments:
            is_overlapping = False

            for existing in filtered_segments:
                # Check if segments overlap
                if not (
                    segment["end_time"] <= existing["start_time"] or
                    segment["start_time"] >= existing["end_time"]
                ):
                    is_overlapping = True
                    break

            if not is_overlapping:
                filtered_segments.append(segment)

                # Stop when we have enough clips
                if len(filtered_segments) >= max_clips:
                    break

        logger.info(
            "Segments filtered and ranked",
            original_count=len(segments),
            filtered_count=len(filtered_segments)
        )

        return filtered_segments

    def _mock_detect_viral_segments(self, max_clips: int) -> List[Dict[str, Any]]:
        """Mock viral detection for development"""
        logger.info("Using mock viral detection", max_clips=max_clips)

        # Return mock viral segments
        mock_segments = [
            {
                "start_time": 15.0,
                "end_time": 47.0,
                "title": "🔥 This Incredible Moment Will Blow Your Mind",
                "virality_score": 95,
                "reason": "Revelation inattendue + émotion forte",
                "hook": "You won't believe what happens next..."
            },
            {
                "start_time": 60.0,
                "end_time": 95.0,
                "title": "💡 The Secret Everyone Should Know",
                "virality_score": 88,
                "reason": "Conseil actionnable concret",
                "hook": "Here's the secret that changed everything..."
            },
            {
                "start_time": 120.0,
                "end_time": 155.0,
                "title": "🚀 Game-Changing Life Advice",
                "virality_score": 82,
                "reason": "Inspiration forte + storytelling",
                "hook": "This one principle transformed my life..."
            },
            {
                "start_time": 180.0,
                "end_time": 210.0,
                "title": "⚡ Mind-Blowing Reaction",
                "virality_score": 79,
                "reason": "Moment de réaction intense",
                "hook": "Watch what happens when..."
            },
            {
                "start_time": 240.0,
                "end_time": 270.0,
                "title": "💯 This Changes Everything",
                "virality_score": 75,
                "reason": "Opinion tranchée + polémique légère",
                "hook": "Most people get this completely wrong..."
            }
        ]

        # Return only requested number of clips
        return mock_segments[:max_clips]

    def _repair_json(self, json_text: str) -> str:
        """Attempt to repair malformed JSON"""
        try:
            # Fix unescaped quotes in string values
            # This regex finds strings and escapes any unescaped quotes inside them
            def fix_quotes(match):
                string_content = match.group(1)
                # Escape any unescaped quotes
                fixed_content = re.sub(r'(?<!\\)"', r'\\"', string_content)
                return f'"{fixed_content}"'

            # Pattern to match string values (between quotes)
            pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
            repaired = re.sub(pattern, fix_quotes, json_text)

            return repaired
        except Exception:
            return json_text

    def _extract_segments_manually(self, text: str) -> List[Dict[str, Any]]:
        """Extract segments manually when JSON parsing fails"""
        try:
            segments = []

            # Look for start_time patterns
            start_times = re.findall(r'"start_time":\s*([0-9.]+)', text)
            end_times = re.findall(r'"end_time":\s*([0-9.]+)', text)
            titles = re.findall(r'"title":\s*"([^"]*)"', text)
            scores = re.findall(r'"virality_score":\s*([0-9]+)', text)
            reasons = re.findall(r'"reason":\s*"([^"]*)"', text)
            hooks = re.findall(r'"hook":\s*"([^"]*)"', text)

            # Create segments from extracted data
            min_length = min(len(start_times), len(end_times), len(titles), len(scores), len(reasons), len(hooks))

            for i in range(min_length):
                segment = {
                    "start_time": float(start_times[i]),
                    "end_time": float(end_times[i]),
                    "title": titles[i],
                    "virality_score": int(scores[i]),
                    "reason": reasons[i],
                    "hook": hooks[i]
                }
                segments.append(segment)

            return segments

        except Exception:
            return []