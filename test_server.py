#!/usr/bin/env python3
"""
Serveur de test minimal pour ShortCut avec API complète
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ShortCut API Test", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ShortCut API is running!", "status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "shortcut-api",
        "version": "1.0.0",
        "mock_mode": True
    }

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
    return [
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

@app.post("/api/projects")
async def create_project(data: dict):
    # Handle both URL-based project creation and traditional project creation
    if data.get("url"):
        # URL-based project creation (for video processing)
        url = data.get("url")
        max_clips = data.get("max_clips", 5)

        # Extract video title from URL (mock implementation)
        video_title = "Video from " + url.split("/")[-1] if "/" in url else "New Video Project"

        return {
            "id": f"proj_{len(url)}",
            "userId": "user_123",
            "name": video_title,
            "description": f"Processing video from {url}",
            "originalVideoUrl": url,
            "originalVideoFilename": f"{url.split('/')[-1]}.mp4",
            "originalVideoSize": 1024000,
            "status": "processing",
            "processingProgress": 0,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }
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
            "status": "processing",
            "processingProgress": 0,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }

if __name__ == "__main__":
    print(">> Lancement ShortCut API Test...")
    print(">> URL: http://localhost:8000")
    print(">> Health: http://localhost:8000/health")
    print(">> Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)