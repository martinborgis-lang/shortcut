"""
Démonstration détaillée du pipeline vidéo ShortCut
Montre les fonctionnalités comme OpusClip
"""

import os
import asyncio
import structlog
from datetime import datetime

# Configuration pour la démo
os.environ["MOCK_MODE"] = "true"

# Import des services
from src.services.video_downloader import VideoDownloaderService
from src.services.transcription import TranscriptionService
from src.services.viral_detection import ViralDetectionService
from src.services.video_processor import VideoProcessorService
from src.services.subtitle_generator import SubtitleGeneratorService

# Configuration des logs
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def print_header(title):
    """Print a nice header for demo sections"""
    print("\n" + "="*60)
    print(f"🎬 {title}")
    print("="*60)

def print_feature(emoji, feature_name, description):
    """Print feature details"""
    print(f"\n{emoji} {feature_name}")
    print(f"   {description}")

async def demo_shortcut_pipeline():
    """Démonstration complète du pipeline ShortCut"""

    print_header("SHORTCUT - Pipeline de Traitement Vidéo comme OpusClip")
    print("🚀 Mode MOCK activé - Simulation du workflow complet")

    # URL de test
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    try:
        # ========== ÉTAPE 1: TÉLÉCHARGEMENT ==========
        print_header("1. TÉLÉCHARGEMENT YOUTUBE")
        print_feature("🔽", "Video Downloader Service",
                     "Télécharge vidéos YouTube/Twitch avec yt-dlp, max 1080p")

        downloader = VideoDownloaderService()
        s3_key, metadata = downloader.download(test_url)

        print(f"✅ Vidéo téléchargée: {metadata['filename']}")
        print(f"📹 Durée: {metadata['duration']/60:.1f} minutes")
        print(f"📐 Résolution: {metadata['width']}x{metadata['height']}")
        print(f"💾 Taille: {metadata['size']/(1024*1024):.1f} MB")
        print(f"☁️  S3 Key: {s3_key}")

        # ========== ÉTAPE 2: TRANSCRIPTION ==========
        print_header("2. TRANSCRIPTION AUDIO")
        print_feature("🎤", "Transcription Service",
                     "Extrait l'audio et transcrit avec Deepgram Nova-2 (timestamps précis)")

        transcription = TranscriptionService()
        transcript = await transcription.transcribe("/fake/video/path.mp4")

        # Afficher les détails de transcription
        words_count = len(transcript.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("words", []))
        print(f"✅ Transcription terminée: {words_count} mots détectés")
        print(f"🎯 Timestamps précis au niveau des mots")
        print(f"🗣️  Exemple: \"The future of content creation...\"")

        # ========== ÉTAPE 3: DÉTECTION VIRALE ==========
        print_header("3. DÉTECTION DE MOMENTS VIRAUX")
        print_feature("🤖", "Viral Detection Service",
                     "Analyse par IA Claude Haiku pour détecter les segments les plus engageants")

        viral_detection = ViralDetectionService()
        viral_segments = viral_detection.detect_viral_segments(
            transcript,
            metadata['duration'],
            max_clips=3
        )

        print(f"✅ {len(viral_segments)} segments viraux détectés:")
        for i, segment in enumerate(viral_segments, 1):
            start_min = segment['start_time'] // 60
            start_sec = segment['start_time'] % 60
            end_min = segment['end_time'] // 60
            end_sec = segment['end_time'] % 60
            duration = segment['end_time'] - segment['start_time']

            print(f"\n   🎯 Segment {i}: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} ({duration:.1f}s)")
            print(f"      🔥 Score viral: {segment['virality_score']}/100")
            print(f"      📖 Titre: \"{segment['title']}\"")
            print(f"      💡 Raison: {segment['reason']}")
            print(f"      🎣 Hook: \"{segment['hook']}\"")

        # ========== ÉTAPE 4: TRAITEMENT VIDÉO ==========
        print_header("4. TRAITEMENT VIDÉO")
        print_feature("✂️", "Video Processor Service",
                     "Découpage précis, recadrage 9:16 avec détection faciale MediaPipe")

        video_processor = VideoProcessorService()

        # Traitement du premier segment pour la démo
        segment = viral_segments[0]
        print(f"🎬 Traitement du segment: \"{segment['title']}\"")

        # Découpage
        cut_path = video_processor.cut_clip(
            "/fake/source.mp4",
            segment["start_time"],
            segment["end_time"]
        )
        print(f"✅ Découpage terminé: {cut_path}")

        # Recadrage portrait
        cropped_path = video_processor.crop_to_portrait(cut_path)
        print(f"✅ Recadrage 9:16 terminé avec détection faciale: {cropped_path}")

        # ========== ÉTAPE 5: GÉNÉRATION DE SOUS-TITRES ==========
        print_header("5. GÉNÉRATION DE SOUS-TITRES")
        print_feature("📝", "Subtitle Generator Service",
                     "5 styles disponibles: Hormozi, Clean, Neon, Karaoke, Minimal")

        subtitle_generator = SubtitleGeneratorService()

        # Afficher les styles disponibles
        styles = subtitle_generator.get_available_styles()
        print("🎨 Styles disponibles:")
        for style_name, style_info in styles.items():
            print(f"   • {style_info['name']}: {style_info['description']}")

        # Générer sous-titres avec style Hormozi (comme OpusClip)
        subtitle_path = subtitle_generator.generate_subtitles(
            transcript,
            segment,
            style="hormozi"
        )
        print(f"\n✅ Sous-titres générés (style Hormozi): {subtitle_path}")

        # Incrustation des sous-titres
        final_path = subtitle_generator.burn_subtitles(cropped_path, subtitle_path)
        print(f"✅ Incrustation terminée: {final_path}")

        # ========== RÉSUMÉ FINAL ==========
        print_header("🎉 PIPELINE TERMINÉ")
        print("📊 Résumé de traitement:")
        print(f"   📹 Vidéo source: {metadata['filename']} ({metadata['duration']/60:.1f}min)")
        print(f"   🎯 Segments détectés: {len(viral_segments)}")
        print(f"   📝 Mots transcrits: {words_count}")
        print(f"   🎬 Clips générés: 1 (style Hormozi)")
        print(f"   ⚡ Format optimisé: 9:16 vertical pour TikTok/Instagram/YouTube Shorts")

        print("\n🔥 FONCTIONNALITÉS DISPONIBLES:")
        print("   • Import YouTube/Twitch automatique")
        print("   • Transcription précise avec timestamps")
        print("   • Détection IA des moments viraux")
        print("   • Découpage automatique intelligent")
        print("   • Recadrage portrait avec détection faciale")
        print("   • 5 styles de sous-titres professionnels")
        print("   • Export MP4 optimisé pour les réseaux sociaux")

        print("\n✨ Comme OpusClip mais en mieux ! ✨")

        return {
            "status": "success",
            "segments_generated": len(viral_segments),
            "styles_available": len(styles),
            "total_duration": metadata['duration']
        }

    except Exception as e:
        logger.error("Erreur dans le pipeline", error=str(e))
        raise

if __name__ == "__main__":
    print("DEMONSTRATION SHORTCUT PIPELINE")
    print("=" * 60)

    # Lancer la démo
    result = asyncio.run(demo_shortcut_pipeline())

    print("\n" + "="*60)
    print("✅ Démonstration terminée avec succès!")
    print(f"📈 Résultat: {result}")