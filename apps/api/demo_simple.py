"""
Demonstration simple du pipeline video ShortCut
"""

import os
import asyncio

# Configuration
os.environ["MOCK_MODE"] = "true"

from src.services.video_downloader import VideoDownloaderService
from src.services.transcription import TranscriptionService
from src.services.viral_detection import ViralDetectionService
from src.services.video_processor import VideoProcessorService
from src.services.subtitle_generator import SubtitleGeneratorService

async def demo_shortcut():
    print("SHORTCUT PIPELINE DEMONSTRATION")
    print("=" * 50)
    print("Mode MOCK: simulation complete du workflow")

    # URL de test
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # 1. TELECHARGEMENT
    print("\n1. TELECHARGEMENT YOUTUBE")
    downloader = VideoDownloaderService()
    s3_key, metadata = downloader.download(test_url)

    print(f"Video telechargee: {metadata['filename']}")
    print(f"Duree: {metadata['duration']/60:.1f} minutes")
    print(f"Resolution: {metadata['width']}x{metadata['height']}")

    # 2. TRANSCRIPTION
    print("\n2. TRANSCRIPTION AUDIO")
    transcription = TranscriptionService()
    transcript = await transcription.transcribe("/fake/video.mp4")

    words_count = len(transcript.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("words", []))
    print(f"Transcription: {words_count} mots detectes")

    # 3. DETECTION VIRALE
    print("\n3. DETECTION MOMENTS VIRAUX")
    viral_detection = ViralDetectionService()
    segments = viral_detection.detect_viral_segments(transcript, metadata['duration'], 3)

    print(f"{len(segments)} segments viraux detectes:")
    for i, seg in enumerate(segments, 1):
        print(f"  Segment {i}: {seg['start_time']:.1f}s-{seg['end_time']:.1f}s")
        print(f"    Score: {seg['virality_score']}/100")
        print(f"    Titre: {seg['title']}")
        print(f"    Raison: {seg['reason']}")

    # 4. TRAITEMENT VIDEO
    print("\n4. TRAITEMENT VIDEO")
    video_processor = VideoProcessorService()
    segment = segments[0]

    cut_path = video_processor.cut_clip("/fake/source.mp4", segment["start_time"], segment["end_time"])
    print(f"Decoupage termine: {cut_path}")

    cropped_path = video_processor.crop_to_portrait(cut_path)
    print(f"Recadrage 9:16 termine: {cropped_path}")

    # 5. SOUS-TITRES
    print("\n5. GENERATION SOUS-TITRES")
    subtitle_generator = SubtitleGeneratorService()
    styles = subtitle_generator.get_available_styles()

    print("Styles disponibles:")
    for name, info in styles.items():
        print(f"  {name}: {info['description']}")

    subtitle_path = subtitle_generator.generate_subtitles(transcript, segment, "hormozi")
    print(f"Sous-titres generes: {subtitle_path}")

    final_path = subtitle_generator.burn_subtitles(cropped_path, subtitle_path)
    print(f"Incrustation terminee: {final_path}")

    # RESUME
    print("\nRESUME:")
    print(f"Video source: {metadata['duration']/60:.1f}min")
    print(f"Segments detectes: {len(segments)}")
    print(f"Clips generes: 1 (style Hormozi)")
    print(f"Format: 9:16 vertical optimise")

    print("\nFONCTIONNALITES:")
    print("- Import YouTube/Twitch automatique")
    print("- Transcription precise avec timestamps")
    print("- Detection IA des moments viraux")
    print("- Decoupage automatique intelligent")
    print("- Recadrage portrait avec detection faciale")
    print("- 5 styles de sous-titres professionnels")
    print("- Export MP4 optimise pour reseaux sociaux")

    print("\nComme OpusClip mais en mieux!")

if __name__ == "__main__":
    asyncio.run(demo_shortcut())