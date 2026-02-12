import os
import tempfile
import subprocess
import structlog
from typing import Dict, Any, List, Optional
from pathlib import Path
import math

logger = structlog.get_logger()


class SubtitleGeneratorService:
    """
    Service for generating and burning subtitles with different styles.

    Critères PRD F4-08: Génère un fichier ASS avec le style sélectionné, incrustation via FFmpeg
    """

    def __init__(self):
        # Define subtitle styles according to PRD specifications
        self.styles = {
            "hormozi": {
                "name": "Hormozi Style",
                "description": "Gros texte centré, mot actif en jaune, ombre portée",
                "fontsize": 24,
                "primary_colour": "&HFFFFFF",  # White
                "secondary_colour": "&H00FFFF",  # Yellow for active word
                "outline": 2,
                "shadow": 3,
                "alignment": 2,  # Bottom center
                "margin_v": 50
            },
            "clean": {
                "name": "Clean Style",
                "description": "Texte blanc propre en bas, pas de highlight",
                "fontsize": 18,
                "primary_colour": "&HFFFFFF",  # White
                "secondary_colour": "&HFFFFFF",  # No highlight
                "outline": 1,
                "shadow": 0,
                "alignment": 2,  # Bottom center
                "margin_v": 30
            },
            "neon": {
                "name": "Neon Style",
                "description": "Texte avec glow coloré, style gaming",
                "fontsize": 22,
                "primary_colour": "&H00FFFF",  # Cyan
                "secondary_colour": "&HFF00FF",  # Magenta
                "outline": 3,
                "shadow": 0,
                "borderstyle": 3,  # Glow effect
                "alignment": 2,
                "margin_v": 40
            },
            "karaoke": {
                "name": "Karaoke Style",
                "description": "Mots qui apparaissent un par un avec effet karaoké",
                "fontsize": 20,
                "primary_colour": "&HFFFFFF",  # White
                "secondary_colour": "&H00FFFF",  # Yellow for karaoke
                "outline": 2,
                "shadow": 1,
                "alignment": 2,
                "margin_v": 40,
                "karaoke": True
            },
            "minimal": {
                "name": "Minimal Style",
                "description": "Petits sous-titres discrets en bas",
                "fontsize": 14,
                "primary_colour": "&HCCCCCC",  # Light gray
                "secondary_colour": "&HCCCCCC",
                "outline": 1,
                "shadow": 0,
                "alignment": 2,
                "margin_v": 20
            }
        }

    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode for development"""
        return os.getenv("MOCK_MODE", "false").lower() == "true"

    def generate_subtitles(
        self,
        transcript: Dict[str, Any],
        segment: Dict[str, Any],
        style: str = "hormozi",
        output_path: str = None
    ) -> str:
        """
        Generate ASS subtitle file for a video segment.

        Args:
            transcript: Deepgram transcript with word-level timestamps
            segment: Viral segment with start/end times
            style: Subtitle style name
            output_path: Optional output path

        Returns:
            Path to generated ASS file
        """
        if self._is_mock_mode():
            return self._mock_generate_subtitles(segment, style, output_path)

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".ass", delete=False).name

        if style not in self.styles:
            style = "hormozi"  # Default fallback

        try:
            # Extract words for the segment
            segment_words = self._extract_segment_words(transcript, segment)

            if not segment_words:
                raise Exception("No words found for segment")

            # Generate ASS content
            ass_content = self._generate_ass_content(segment_words, style, segment)

            # Write ASS file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)

            logger.info(
                "Subtitles generated",
                style=style,
                word_count=len(segment_words),
                output_path=output_path
            )

            return output_path

        except Exception as e:
            logger.error("Subtitle generation failed", error=str(e), style=style)
            raise Exception(f"Failed to generate subtitles: {str(e)}")

    def burn_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str = None
    ) -> str:
        """
        Burn subtitles into video using FFmpeg.

        Args:
            video_path: Path to input video
            subtitle_path: Path to ASS subtitle file
            output_path: Optional output path

        Returns:
            Path to video with burned subtitles
        """
        if self._is_mock_mode():
            return self._mock_burn_subtitles(video_path, subtitle_path, output_path)

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix="_subtitled.mp4", delete=False).name

        try:
            # Escape ASS path for FFmpeg filter on Windows
            ass_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')

            # FFmpeg command to burn subtitles
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"ass={ass_path_escaped}",
                "-c:a", "copy",  # Copy audio without re-encoding
                "-y",
                output_path
            ]

            logger.info(
                "Burning subtitles",
                video_path=video_path,
                subtitle_path=subtitle_path,
                cmd=" ".join(cmd)
            )

            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)

            logger.info("Subtitles burned successfully", output_path=output_path)
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error("Subtitle burning failed", error=str(e), stderr=e.stderr)
            raise Exception(f"Failed to burn subtitles: {str(e)}")

    def _extract_segment_words(
        self,
        transcript: Dict[str, Any],
        segment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract words from transcript that fall within the segment timeframe"""
        try:
            segment_words = []
            start_time = segment["start_time"]
            end_time = segment["end_time"]

            results = transcript.get("results", {})
            channels = results.get("channels", [])

            for channel in channels:
                for alternative in channel.get("alternatives", []):
                    words = alternative.get("words", [])

                    for word in words:
                        word_start = word.get("start", 0)
                        word_end = word.get("end", 0)

                        # Include word if it falls within segment
                        if word_start >= start_time and word_end <= end_time:
                            # Adjust timestamps relative to segment start
                            segment_word = {
                                "word": word.get("word", ""),
                                "punctuated_word": word.get("punctuated_word", word.get("word", "")),
                                "start": word_start - start_time,
                                "end": word_end - start_time,
                                "confidence": word.get("confidence", 0.0)
                            }
                            segment_words.append(segment_word)

            logger.info(
                "Extracted segment words",
                segment_duration=end_time - start_time,
                word_count=len(segment_words)
            )

            return segment_words

        except Exception as e:
            logger.error("Failed to extract segment words", error=str(e))
            return []

    def _generate_ass_content(
        self,
        words: List[Dict[str, Any]],
        style: str,
        segment: Dict[str, Any]
    ) -> str:
        """Generate ASS subtitle file content"""
        style_config = self.styles[style]

        # ASS file header
        header = f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{style_config['fontsize']},{style_config['primary_colour']},{style_config['secondary_colour']},&H00000000,&H00000000,1,0,0,0,100,100,0,0,{style_config.get('borderstyle', 1)},{style_config['outline']},{style_config['shadow']},{style_config['alignment']},10,10,{style_config['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # Generate subtitle events
        events = []

        if style_config.get("karaoke"):
            # Karaoke style - word by word
            events.extend(self._generate_karaoke_events(words, style_config))
        else:
            # Regular style - grouped by phrases
            events.extend(self._generate_phrase_events(words, style_config))

        return header + "\n".join(events)

    def _generate_phrase_events(self, words: List[Dict[str, Any]], style_config: Dict[str, Any]) -> List[str]:
        """Generate subtitle events grouped by phrases"""
        events = []

        if not words:
            return events

        # Group words into phrases (max 8 words or 3 seconds per phrase)
        phrases = []
        current_phrase = []
        phrase_start = words[0]["start"]

        for word in words:
            current_phrase.append(word)

            # End phrase if too long or too many words
            phrase_duration = word["end"] - phrase_start
            should_end_phrase = (
                len(current_phrase) >= 8 or
                phrase_duration >= 3.0 or
                word["punctuated_word"].endswith(('.', '!', '?', ':'))
            )

            if should_end_phrase:
                phrases.append({
                    "words": current_phrase,
                    "start": phrase_start,
                    "end": word["end"],
                    "text": " ".join([w["punctuated_word"] for w in current_phrase])
                })

                current_phrase = []
                if word != words[-1]:  # Not last word
                    phrase_start = words[words.index(word) + 1]["start"]

        # Add remaining words as final phrase
        if current_phrase:
            phrases.append({
                "words": current_phrase,
                "start": phrase_start,
                "end": current_phrase[-1]["end"],
                "text": " ".join([w["punctuated_word"] for w in current_phrase])
            })

        # Generate ASS events for each phrase
        for phrase in phrases:
            start_time = self._format_ass_time(phrase["start"])
            end_time = self._format_ass_time(phrase["end"])
            text = phrase["text"]

            # Apply style-specific formatting
            if style_config.get("name") == "Hormozi Style":
                # Add highlight effect for key words
                text = self._add_hormozi_effects(text)

            event = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
            events.append(event)

        return events

    def _generate_karaoke_events(self, words: List[Dict[str, Any]], style_config: Dict[str, Any]) -> List[str]:
        """Generate karaoke-style events with word timing"""
        events = []

        # Group words into phrases for karaoke
        phrases = []
        current_phrase = []
        phrase_start = words[0]["start"] if words else 0

        for word in words:
            current_phrase.append(word)

            # End phrase at punctuation or after 6 words
            should_end_phrase = (
                len(current_phrase) >= 6 or
                word["punctuated_word"].endswith(('.', '!', '?'))
            )

            if should_end_phrase:
                phrases.append({
                    "words": current_phrase,
                    "start": phrase_start,
                    "end": word["end"]
                })

                current_phrase = []
                if word != words[-1]:  # Not last word
                    phrase_start = words[words.index(word) + 1]["start"]

        # Add remaining words
        if current_phrase:
            phrases.append({
                "words": current_phrase,
                "start": phrase_start,
                "end": current_phrase[-1]["end"]
            })

        # Generate karaoke events
        for phrase in phrases:
            start_time = self._format_ass_time(phrase["start"])
            end_time = self._format_ass_time(phrase["end"])

            # Build karaoke text with timing
            karaoke_text = ""
            for word in phrase["words"]:
                word_duration = (word["end"] - word["start"]) * 100  # Centiseconds
                karaoke_text += f"{{\\k{int(word_duration)}}}{word['punctuated_word']} "

            event = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text.strip()}"
            events.append(event)

        return events

    def _add_hormozi_effects(self, text: str) -> str:
        """Add Hormozi-style emphasis to key words"""
        # Simple logic to emphasize certain words
        emphasis_words = [
            "incredible", "amazing", "secret", "never", "always", "everything",
            "nothing", "everyone", "nobody", "best", "worst", "first", "last",
            "only", "must", "should", "will", "won't", "can't", "don't"
        ]

        words = text.split()
        emphasized_text = []

        for word in words:
            word_lower = word.lower().strip(".,!?:")
            if word_lower in emphasis_words:
                # Add yellow color and bold for emphasis
                emphasized_text.append(f"{{\\c&H00FFFF&\\b1}}{word}{{\\c&HFFFFFF&\\b0}}")
            else:
                emphasized_text.append(word)

        return " ".join(emphasized_text)

    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS subtitle format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def _mock_generate_subtitles(self, segment: Dict[str, Any], style: str, output_path: str = None) -> str:
        """Mock subtitle generation for development"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".ass", delete=False).name

        logger.info("Mock generating subtitles", style=style, output_path=output_path)

        # Create simple mock ASS file
        mock_content = f"""[Script Info]
Title: Mock Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&HFFFFFF,&H00FFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,1,2,10,10,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,Welcome to this amazing video!
Dialogue: 0,0:00:03.00,0:00:06.00,Default,,0,0,0,,This is absolutely incredible.
Dialogue: 0,0:00:06.00,0:00:10.00,Default,,0,0,0,,You won't believe what happens next.
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mock_content)

        return output_path

    def _mock_burn_subtitles(self, video_path: str, subtitle_path: str, output_path: str = None) -> str:
        """Mock subtitle burning for development"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix="_subtitled.mp4", delete=False).name

        logger.info(
            "Mock burning subtitles",
            video_path=video_path,
            subtitle_path=subtitle_path,
            output_path=output_path
        )

        # In mock mode, just create an empty file
        Path(output_path).touch()
        return output_path

    def get_available_styles(self) -> Dict[str, Dict[str, Any]]:
        """Get all available subtitle styles"""
        return {
            style_name: {
                "name": config["name"],
                "description": config["description"]
            }
            for style_name, config in self.styles.items()
        }