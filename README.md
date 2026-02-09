# Shortcut - AI Video Clip Creator

Transform long-form videos into viral TikTok clips with AI-powered analysis and automated publishing.

## 🚀 Quick Start (5 Commands)

```bash
# 1. Clone and setup environment
git clone <your-repo> && cd shortcut && cp .env.example .env

# 2. Start development environment
docker-compose -f docker-compose.dev.yml up -d

# 3. Run database migrations
docker exec shortcut_api alembic upgrade head

# 4. Install frontend dependencies
cd apps/web && npm install

# 5. Access the application
echo "🎉 Frontend: http://localhost:3000 | Backend: http://localhost:8000/docs"
```

## 📁 Project Structure

```
shortcut/
├── apps/
│   ├── web/                    # Next.js 14 Frontend
│   │   ├── src/
│   │   │   ├── app/           # App Router pages
│   │   │   ├── components/    # React components
│   │   │   ├── lib/           # Utilities & API client
│   │   │   ├── hooks/         # Custom React hooks
│   │   │   ├── stores/        # Zustand state stores
│   │   │   └── types/         # TypeScript types
│   │   └── package.json
│   │
│   └── api/                    # FastAPI Backend
│       ├── src/
│       │   ├── models/        # SQLAlchemy models
│       │   ├── schemas/       # Pydantic schemas
│       │   ├── routers/       # API endpoints
│       │   ├── services/      # Business logic
│       │   ├── workers/       # Celery workers
│       │   └── utils/         # Helper functions
│       ├── alembic/           # Database migrations
│       └── requirements.txt
│
├── infra/                      # Infrastructure configs
├── packages/                   # Shared packages
├── docker-compose.dev.yml      # Development environment
└── .env.example               # Environment variables template
```

## 🛠 Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack React Query v5
- **Authentication**: Clerk

### Backend
- **Framework**: FastAPI 0.110+
- **Database**: PostgreSQL 16 + SQLAlchemy 2.x
- **Cache/Queue**: Redis 7.x + Celery
- **Migrations**: Alembic

### AI & Media Processing
- **Transcription**: Deepgram SDK
- **AI Analysis**: Anthropic SDK (Claude Haiku)
- **Video Processing**: FFmpeg + yt-dlp
- **Face Detection**: MediaPipe

### Infrastructure
- **Storage**: AWS S3 (boto3)
- **Payments**: Stripe
- **Containerization**: Docker + Docker Compose

## ⚙️ Environment Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Configuration

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Required Environment Variables**:
   ```env
   # Database
   DATABASE_URL=postgresql://postgres:password@localhost:5432/shortcut

   # Authentication (Get from Clerk)
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...

   # AI Services
   DEEPGRAM_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key

   # AWS Storage
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_key
   S3_BUCKET_NAME=shortcut-storage
   ```

## 🚀 Development

### Start Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Database Operations

```bash
# Create migration
docker exec shortcut_api alembic revision --autogenerate -m "description"

# Apply migrations
docker exec shortcut_api alembic upgrade head

# Downgrade migration
docker exec shortcut_api alembic downgrade -1
```

### Frontend Development

```bash
cd apps/web
npm install
npm run dev
# Visit: http://localhost:3000
```

### Backend Development

```bash
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload
# API Docs: http://localhost:8000/docs
```

### Celery Workers

```bash
# Start worker
celery -A src.workers.celery_app worker --loglevel=info

# Start beat scheduler
celery -A src.workers.celery_app beat --loglevel=info

# Monitor with Flower
celery -A src.workers.celery_app flower
# Visit: http://localhost:5555
```

## 📊 Available Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| Backend API | http://localhost:8000 | FastAPI + docs |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5432 | PostgreSQL |
| Redis | localhost:6379 | Cache & message broker |
| Flower | http://localhost:5555 | Celery monitoring |

## 🧪 Testing

### Backend Tests
```bash
cd apps/api
pytest
```

### Frontend Tests
```bash
cd apps/web
npm test
```

## 📈 Database Schema

### Core Tables
- **users**: User accounts and subscription info
- **projects**: Video upload projects
- **clips**: Generated video clips
- **scheduled_posts**: Social media publishing queue
- **social_accounts**: Connected social media accounts

## 🔧 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### Authentication
All protected endpoints require Clerk authentication header.

### Key Endpoints
- `POST /projects` - Create new project
- `GET /projects/{id}/clips` - Get project clips
- `POST /upload/video` - Upload video file
- `POST /schedule/post` - Schedule social media post

## 🐳 Docker Services

### Development Stack
- **postgres**: PostgreSQL database
- **redis**: Cache and message broker
- **api**: FastAPI backend
- **web**: Next.js frontend
- **celery_worker**: Background task processor
- **celery_beat**: Task scheduler
- **flower**: Task monitoring

## 🔍 Monitoring

### Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f api
```

### Health Checks
- Backend: http://localhost:8000/health
- Database: `docker exec shortcut_postgres pg_isready`
- Redis: `docker exec shortcut_redis redis-cli ping`

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   ```bash
   docker-compose -f docker-compose.dev.yml restart postgres
   ```

2. **Redis Connection Error**:
   ```bash
   docker-compose -f docker-compose.dev.yml restart redis
   ```

3. **Frontend Build Issues**:
   ```bash
   cd apps/web && rm -rf .next node_modules && npm install
   ```

4. **Backend Module Errors**:
   ```bash
   docker-compose -f docker-compose.dev.yml build api --no-cache
   ```

### Reset Development Environment
```bash
# Stop and remove all containers + volumes
docker-compose -f docker-compose.dev.yml down -v

# Rebuild and restart
docker-compose -f docker-compose.dev.yml up -d --build
```

## 📝 License

This project is proprietary. All rights reserved.

---

**Built with ❤️ for creating viral content**