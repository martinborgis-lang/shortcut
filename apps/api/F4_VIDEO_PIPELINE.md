# Feature F4: Pipeline de Traitement Vidéo

## Vue d'ensemble

La Feature F4 implémente le pipeline complet de traitement vidéo selon les spécifications du PRD. Elle permet de télécharger une vidéo depuis YouTube/Twitch, la transcrire, détecter les moments viraux avec l'IA, et générer des clips courts automatiquement avec sous-titres.

## Architecture

### Endpoints API

| Endpoint | Méthode | Description | Critères PRD |
|----------|---------|-------------|---------------|
| `POST /api/projects` | POST | Créer un projet depuis une URL | F4-01 |
| `GET /api/projects/{id}` | GET | Récupérer un projet avec ses clips | F4-02 |
| `GET /api/projects/{id}/status` | GET | Statut détaillé en temps réel | F4-03 |

### Services Implémentés

| Service | Description | Critères PRD |
|---------|-------------|---------------|
| `VideoDownloaderService` | Téléchargement YouTube/Twitch avec yt-dlp | F4-04 |
| `TranscriptionService` | Transcription audio via Deepgram API | F4-05 |
| `ViralDetectionService` | Détection de segments viraux avec Claude Haiku | F4-06 |
| `VideoProcessorService` | Découpage et recadrage 9:16 avec MediaPipe | F4-07 |
| `SubtitleGeneratorService` | Génération sous-titres ASS et incrustation | F4-08 |

### Worker Celery

Le worker `video_pipeline.process_video` orchestre l'ensemble du pipeline:

1. **Téléchargement** - Récupère la vidéo et l'upload sur S3
2. **Transcription** - Extrait l'audio et génère la transcription
3. **Analyse IA** - Détecte les segments viraux avec Claude
4. **Traitement** - Découpe, recadre et ajoute les sous-titres
5. **Finalisation** - Upload des clips finaux et nettoyage

## Configuration

### Variables d'environnement

```bash
# Mode développement
MOCK_MODE=true  # Active les mocks pour développement

# APIs externes
DEEPGRAM_API_KEY=your_deepgram_key
ANTHROPIC_API_KEY=your_anthropic_key

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=shortcut-storage

# Base de données
DATABASE_URL=postgresql://user:pass@localhost:5432/shortcut

# Redis pour Celery
REDIS_URL=redis://localhost:6379/0
```

### Mode MOCK

Pour le développement, utilisez `MOCK_MODE=true` pour simuler tous les services externes:

- **VideoDownloader**: Retourne des métadonnées de test
- **Transcription**: Retourne une transcription pré-définie
- **ViralDetection**: Retourne des segments viraux de test
- **VideoProcessor**: Crée des fichiers vides pour les tests
- **SubtitleGenerator**: Génère des fichiers ASS simplifiés

## Styles de sous-titres

| Style | Description | Usage |
|-------|-------------|-------|
| `hormozi` | Gros texte centré, mot actif en jaune (défaut) | Contenu motivationnel |
| `clean` | Texte blanc propre en bas | Contenu professionnel |
| `neon` | Texte avec glow coloré | Contenu gaming |
| `karaoke` | Mots qui apparaissent un par un | Contenu musical |
| `minimal` | Petits sous-titres discrets | Contenu éducatif |

## Limitations par plan utilisateur

| Plan | Durée max vidéo | Projets simultanés |
|------|----------------|-------------------|
| Basic | 10 minutes | 1 |
| Pro | 60 minutes | 5 |

## Pipeline détaillé

### 1. Téléchargement (F4-04)
- Support YouTube (youtu.be, youtube.com/watch, youtube.com/shorts)
- Support Twitch (twitch.tv/videos/)
- Qualité max 1080p, format MP4
- Upload automatique vers S3

### 2. Transcription (F4-05)
- Extraction audio avec FFmpeg
- Transcription via Deepgram Nova-2
- Timestamps au niveau des mots
- Format JSON JSONB stocké

### 3. Détection virale (F4-06)
- Analyse avec Claude Haiku
- Prompt optimisé pour détecter:
  - Punchlines / révélations inattendues
  - Émotions fortes
  - Conseils actionnables
  - Opinions tranchées
  - Storytelling avec tension
- Segments de 30-90 secondes sans chevauchement

### 4. Traitement vidéo (F4-07)
- Découpage précis avec FFmpeg
- Détection faciale avec MediaPipe
- Recadrage intelligent 9:16
- Optimisé pour format mobile

### 5. Sous-titres (F4-08)
- Génération fichiers ASS
- 5 styles pré-configurés
- Incrustation avec FFmpeg
- Timing précis mot par mot

## Retry et gestion d'erreurs

### Retry logic (F4-10)
- 3 tentatives par étape
- Backoff exponentiel (60s, 120s, 240s)
- Retry automatique avec jitter

### Status updates (F4-11)
- Mise à jour temps réel en BDD
- Progression 0-100% par étape
- Détails spécifiques par étape

### Cleanup (F4-13)
- Suppression fichiers temporaires
- Nettoyage automatique après upload S3
- Task de cleanup périodique

## Test du pipeline

```bash
# Test en mode mock
cd apps/api
export MOCK_MODE=true
python test_pipeline.py

# Test avec vrais services
export MOCK_MODE=false
export DEEPGRAM_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
python test_pipeline.py
```

## Déploiement

### Worker Celery

```bash
# Démarrer le worker vidéo
celery -A src.workers.celery_app worker -Q video_processing -l info

# Démarrer le scheduler pour tâches périodiques
celery -A src.workers.celery_app beat -l info

# Monitoring
celery -A src.workers.celery_app flower
```

### Migration BDD

```bash
# Appliquer la migration F4
alembic upgrade head
```

## Monitoring

### Métriques importantes
- Temps de traitement par projet
- Taux de succès par étape
- Utilisation stockage S3
- Performance des APIs externes

### Logs structurés
Tous les logs utilisent structlog avec format JSON pour faciliter le monitoring.

## Sécurité

- URLs signées S3 avec expiration 24h
- Validation stricte des URLs source
- Rate limiting sur tous les endpoints
- Validation des plans utilisateur

## Performance

- Processing parallèle des clips
- Réutilisation connexions S3
- Cache intelligent Deepgram
- Optimisation FFmpeg pour vitesse