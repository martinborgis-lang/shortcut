from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="ShortCut Mock API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004", "http://localhost:3005", "http://localhost:3006", "http://localhost:3007", "http://localhost:3008", "http://localhost:3009", "http://localhost:3010", "http://localhost:3011"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "shortcut-api", "version": "1.0.0", "mock_mode": True}

@app.get("/api/users/me")
async def get_current_user():
    return {
        "id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "plan": "free",
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    return {
        "totalProjects": 5,
        "totalClips": 15,
        "monthlyMinutesUsed": 45,
        "monthlyMinutesLimit": 100
    }

@app.get("/api/projects")
async def get_projects():
    # Liste des projets par défaut
    default_projects = [
        {
            "id": "proj_1",
            "userId": "user_123",
            "name": "Mon Premier Projet",
            "description": "Premier projet de test",
            "originalVideoUrl": "https://youtube.com/watch?v=example1",
            "originalVideoFilename": "example1.mp4",
            "originalVideoSize": 1024000,
            "status": "completed",
            "processingProgress": 100,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        },
        {
            "id": "proj_2",
            "userId": "user_123",
            "name": "Projet Démo",
            "description": "Projet de démonstration",
            "originalVideoUrl": "https://youtube.com/watch?v=example2",
            "originalVideoFilename": "example2.mp4",
            "originalVideoSize": 2048000,
            "status": "processing",
            "processingProgress": 45,
            "createdAt": "2024-01-02T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z"
        }
    ]

    # Ajouter les projets créés dynamiquement
    all_projects = default_projects.copy()
    if hasattr(app, "projects_db"):
        for project_id, project in app.projects_db.items():
            all_projects.append(project)

    # Trier par date de création (plus récents d'abord)
    all_projects.sort(key=lambda p: p.get("createdAt", "2024-01-01T00:00:00Z"), reverse=True)

    return all_projects

@app.post("/api/projects")
async def create_project(data: dict):
    import time
    import asyncio

    # Handle both URL-based project creation and traditional project creation
    if data.get("url"):
        # URL-based project creation (for video processing)
        url = data.get("url")
        max_clips = data.get("max_clips", 5)

        # Extract video title from URL (mock implementation)
        video_title = "Video from " + url.split("/")[-1] if "/" in url else "New Video Project"

        # Detect platform
        platform = "youtube" if "youtube" in url or "youtu.be" in url else "twitch" if "twitch.tv" in url else "unknown"

        # Simulate video metadata extraction
        mock_metadata = {
            "duration": 300.0,  # 5 minutes
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "title": f"Viral Video Content - {platform.title()}"
        }

        project_id = f"proj_{int(time.time())}"

        # Start with pending status
        project = {
            "id": project_id,
            "userId": "user_123",
            "name": mock_metadata["title"],
            "description": f"Traitement automatique de video {platform.title()}: transcription, detection des moments viraux, generation de {max_clips} clips courts avec sous-titres",
            "originalVideoUrl": url,
            "originalVideoFilename": f"{mock_metadata['title']}.mp4",
            "originalVideoSize": 1024000,
            "originalVideoDuration": mock_metadata["duration"],
            "videoMetadata": mock_metadata,
            "status": "pending",
            "processingProgress": 0,
            "currentStep": "Initialisation du pipeline de traitement...",
            "maxClipsRequested": max_clips,
            "platform": platform,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }

        # Store project in memory for status updates
        if not hasattr(app, "projects_db"):
            app.projects_db = {}
        app.projects_db[project_id] = project

        # Start background processing simulation
        asyncio.create_task(simulate_video_processing(project_id, max_clips))

        return project
    else:
        # Traditional project creation
        return {
            "id": "proj_new",
            "userId": "user_123",
            "name": data.get("name", "Nouveau Projet"),
            "description": data.get("description", ""),
            "originalVideoUrl": data.get("originalVideoUrl", ""),
            "originalVideoFilename": "new_project.mp4",
            "originalVideoSize": 1024000,
            "status": "pending",
            "processingProgress": 0,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    # Check if project exists in memory
    if hasattr(app, "projects_db") and project_id in app.projects_db:
        return app.projects_db[project_id]

    # Return mock project if not found
    return {
        "id": project_id,
        "userId": "user_123",
        "name": "Project Not Found",
        "status": "failed",
        "processingProgress": 0,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
    }

@app.get("/api/projects/{project_id}/status")
async def get_project_status(project_id: str):
    # Check if project exists in memory
    if hasattr(app, "projects_db") and project_id in app.projects_db:
        project = app.projects_db[project_id]
        return {
            "id": project_id,
            "status": project["status"],
            "processingProgress": project["processingProgress"],
            "currentStep": project.get("currentStep", ""),
            "updatedAt": project["updatedAt"]
        }

    # Return not found
    return {
        "id": project_id,
        "status": "not_found",
        "processingProgress": 0,
        "currentStep": "Project not found",
        "updatedAt": "2024-01-01T00:00:00Z"
    }

@app.get("/api/projects/{project_id}/clips")
async def get_project_clips(project_id: str):
    # Check if project exists and is completed
    if hasattr(app, "projects_db") and project_id in app.projects_db:
        project = app.projects_db[project_id]
        if project["status"] == "completed" and "clips" in project:
            return project["clips"]

    # Return empty clips if not completed
    return []

async def simulate_video_processing(project_id: str, max_clips: int):
    """Simulate the video processing pipeline with realistic timing and steps"""
    import asyncio

    if not hasattr(app, "projects_db") or project_id not in app.projects_db:
        return

    try:
        # Pipeline stages with realistic timing
        stages = [
            (10, "downloading", "Telechargement de la video depuis YouTube/Twitch..."),
            (25, "transcribing", "Extraction audio et transcription avec Deepgram..."),
            (45, "analyzing", "Analyse IA pour detecter les moments viraux..."),
            (70, "processing", f"Generation de {max_clips} clips courts avec recadrage 9:16..."),
            (90, "subtitles", "Ajout des sous-titres avec style Hormozi..."),
            (100, "completed", "Traitement termine! Clips prets au telechargement.")
        ]

        for progress, status, step in stages:
            await asyncio.sleep(3)  # 3 seconds between each step

            project = app.projects_db[project_id]
            project["processingProgress"] = progress
            project["status"] = status
            project["currentStep"] = step
            project["updatedAt"] = "2024-01-01T00:00:00Z"

        # Generate mock clips when completed
        project = app.projects_db[project_id]
        project["clips"] = []

        # Create viral segments mock data
        viral_segments = [
            {
                "title": "Le secret du succes en entrepreneuriat",
                "start_time": 15.0,
                "end_time": 47.0,
                "virality_score": 95,
                "hook": "Personne ne vous dira cette verite...",
                "reason": "Revelation choc avec emotion forte"
            },
            {
                "title": "La strategie que les millionnaires cachent",
                "start_time": 127.5,
                "end_time": 159.3,
                "virality_score": 88,
                "hook": "Voici ce que font vraiment les riches...",
                "reason": "Conseil actionnable exclusif"
            },
            {
                "title": "L'erreur qui coute des millions",
                "start_time": 203.2,
                "end_time": 234.8,
                "virality_score": 82,
                "hook": "Cette erreur a ruine ma vie...",
                "reason": "Storytelling avec tension dramatique"
            }
        ]

        # Create clips for each segment
        for i, segment in enumerate(viral_segments[:max_clips], 1):
            clip = {
                "id": f"clip_{project_id}_{i}",
                "projectId": project_id,
                "title": segment["title"],
                "description": f"Clip viral genere automatiquement - Score: {segment['virality_score']}/100",
                "startTime": segment["start_time"],
                "endTime": segment["end_time"],
                "duration": segment["end_time"] - segment["start_time"],
                "videoUrl": f"https://mock-cdn.shortcut.com/clips/{project_id}_{i}.mp4",
                "thumbnailUrl": f"https://mock-cdn.shortcut.com/thumbs/{project_id}_{i}.jpg",
                "previewGifUrl": f"https://mock-cdn.shortcut.com/previews/{project_id}_{i}.gif",
                "viralScore": segment["virality_score"],
                "hookStrength": 85 + (i * 5),
                "contentQuality": 90,
                "subtitleStyle": "hormozi",
                "status": "ready",
                "processingProgress": 100,
                "isFavorite": False,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
                "generatedAt": "2024-01-01T00:00:00Z",
                "metadata": {
                    "hook": segment["hook"],
                    "reason": segment["reason"],
                    "format": "9:16 vertical",
                    "resolution": "1080x1920",
                    "duration_formatted": f"{segment['end_time'] - segment['start_time']:.1f}s"
                }
            }
            project["clips"].append(clip)

        # Final update
        project["clipsGenerated"] = len(project["clips"])
        project["completedAt"] = "2024-01-01T00:00:00Z"

    except Exception as e:
        # Handle errors
        if project_id in app.projects_db:
            project = app.projects_db[project_id]
            project["status"] = "failed"
            project["currentStep"] = f"Erreur: {str(e)}"
            project["updatedAt"] = "2024-01-01T00:00:00Z"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)