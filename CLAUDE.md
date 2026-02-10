# CLAUDE.md — ShortCut

## Projet

ShortCut est un SaaS B2C de clipping vidéo IA (concurrent d'Opus Clip). L'utilisateur colle un lien YouTube/Twitch, l'IA découpe la vidéo en shorts viraux au format 9:16 avec sous-titres, et permet la publication automatique sur TikTok via l'API Content Posting.

## Architecture

```
shortcut/
├── apps/web/                         # Frontend Next.js (déployé sur Vercel)
│   ├── src/app/(marketing)/          # Landing page publique
│   ├── src/app/(auth)/               # Pages protégées (dashboard, projects, clips, schedule, settings)
│   ├── src/app/sign-in/              # Auth Clerk
│   ├── src/app/sign-up/              # Auth Clerk
│   ├── src/components/
│   │   ├── landing/                  # Composants landing (Navbar, Hero, FeatureTabs, Pricing, etc.)
│   │   ├── dashboard/                # Stats, recent projects/clips
│   │   ├── clips/                    # Clip card, editor, preview, subtitles
│   │   ├── schedule/                 # Calendrier, scheduling modal
│   │   ├── billing/                  # Plans, usage, invoices
│   │   ├── layout/                   # Sidebar, notifications
│   │   ├── ui/                       # Composants shadcn/ui
│   │   ├── modals/                   # New project, video player
│   │   ├── shared/                   # Empty state, error boundary, loading
│   │   └── pricing/                  # Plan cards, upgrade modal
│   ├── src/hooks/                    # useProjects, useClips, useSchedule, useBilling, etc.
│   ├── src/lib/                      # api.ts, auth.ts, utils.ts, query-provider.tsx
│   └── src/stores/                   # Zustand (projectStore, uiStore, userStore)
│
├── apps/api/                         # Backend FastAPI Python
│   ├── src/
│   │   ├── main.py                   # Entry point FastAPI
│   │   ├── config.py                 # Settings & env vars
│   │   ├── database.py               # SQLAlchemy setup
│   │   ├── models/                   # User, Project, Clip, ScheduledPost, SocialAccount
│   │   ├── schemas/                  # Pydantic schemas
│   │   ├── routers/                  # projects, clips, schedule, social, stripe, users, webhooks
│   │   ├── services/                 # video_downloader, transcription, viral_detection,
│   │   │                             #   video_processor, subtitle_generator, clip_editor,
│   │   │                             #   tiktok_oauth, tiktok_publisher, stripe_service, etc.
│   │   ├── workers/                  # Celery: video_pipeline, publish_worker, billing_worker
│   │   └── utils/                    # ffmpeg, s3, logging
│   ├── alembic/                      # DB migrations
│   └── tests/
```

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Frontend | Next.js 14 (App Router) + Tailwind CSS v4 |
| UI | shadcn/ui + Framer Motion |
| State | Zustand + TanStack React Query v5 |
| Auth | Clerk |
| Backend | FastAPI (Python) |
| ORM | SQLAlchemy 2.x + Alembic |
| Queue | Celery + Redis |
| BDD | PostgreSQL 16 |
| Storage | AWS S3 / Cloudflare R2 |
| Paiement | Stripe |
| Video | FFmpeg + yt-dlp |
| Transcription | Deepgram SDK |
| IA/LLM | Anthropic SDK (Claude Haiku) |
| Face detection | MediaPipe |
| Déploiement | Vercel (frontend) |

## Design System

### Thème : Dark mode exclusif

```
Backgrounds:  zinc-950 (#09090b), zinc-900, zinc-800
Borders:      white/10, white/5, white/20 (hover)
Text:         white (principal), gray-300 (secondaire), gray-400, gray-500 (muted)
Accent:       gradient from-purple-600 to-cyan-500
Glow:         purple-500/25
```

### Patterns UI récurrents

**Card :**
```tsx
<div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all duration-300">
```

**Bouton CTA :**
```tsx
<button className="px-6 py-3 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 text-white font-medium hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-200">
```

**Bouton secondaire :**
```tsx
<button className="px-6 py-3 rounded-full border border-white/10 text-gray-300 hover:bg-white/5 transition-all duration-200">
```

**Input :**
```tsx
<input className="w-full px-4 py-3 bg-zinc-800 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/25 transition-all" />
```

**Glassmorphism (navbar, modales) :**
```tsx
<div className="backdrop-blur-md bg-zinc-950/80 border-b border-white/10">
```

## Conventions de code

### Frontend (TypeScript/React)
- Composants fonctionnels avec hooks
- Un composant par fichier, nommé en PascalCase
- Hooks custom préfixés `use` dans `src/hooks/`
- Imports absolus via `@/` alias
- Pas de `any` — typer explicitement
- Utiliser les composants shadcn/ui existants dans `src/components/ui/`
- Animations avec Framer Motion (`motion.div`, `AnimatePresence`)
- État global : Zustand. État serveur : TanStack Query
- Les textes de l'interface sont en **français**

### Backend (Python)
- FastAPI avec Pydantic v2 pour la validation
- SQLAlchemy 2.x (async)
- Alembic pour les migrations
- Workers Celery pour les tâches longues (video processing)
- Tests avec pytest

### Git
- Commits en anglais, descriptifs
- Branch `main` = production
- Pas de fichiers .env dans le repo (utiliser .env.example)

## Points d'attention critiques

### Tailwind v4 — Cascade Layers
Tailwind v4 utilise des CSS cascade layers. Si des styles ne s'appliquent pas :
- Vérifier que `globals.css` ne contient PAS de reset CSS hors `@layer`
- Ne PAS mettre de classes CSS custom qui override les utilities Tailwind
- Privilégier les classes Tailwind pures plutôt que du CSS custom
- Si un style ne marche pas, c'est probablement un conflit de layer

### Landing page
- Les composants sont dans `src/components/landing/`
- NE PAS modifier le contenu textuel (textes, prix, features sont validés)
- Les animations Framer Motion doivent rester fluides
- Le scroll vers les sections utilise des ancres (#features, #pricing, #faq)

### Auth (Clerk)
- Routes sign-in : `/sign-in/[[...sign-in]]/page.tsx`
- Routes sign-up : `/sign-up/[[...sign-up]]/page.tsx`
- Middleware dans `src/middleware.ts`
- Ne pas casser les routes catch-all Clerk

### Pipeline vidéo (feature principale)
Le flux complet :
1. URL YouTube/Twitch → `video_downloader.py` (yt-dlp)
2. Audio → `transcription.py` (Deepgram)
3. Transcription → `viral_detection.py` (Claude Haiku) → moments viraux identifiés
4. Découpe → `video_processor.py` (FFmpeg) → clips 9:16 avec face tracking
5. Sous-titres → `subtitle_generator.py` (ASS/SRT via FFmpeg)
6. Export → S3/R2 storage → CDN → preview utilisateur

### TikTok Integration (à venir)
- Content Posting API avec OAuth 2.0
- Scopes : user.info.basic, video.publish, video.upload
- UX obligatoire : sélection privacy level (pas de défaut), toggles Comment/Duet/Stitch, déclaration contenu commercial
- App non-auditée = vidéos en mode privé uniquement, max 5 users/24h

## Commandes utiles

```bash
# Frontend
cd apps/web
npm run dev          # Dev server (localhost:3000)
npm run build        # Build production — DOIT passer sans erreur
npm run lint         # Linter

# Backend
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload    # Dev server
pytest                            # Tests
alembic upgrade head              # Migrations
```

## Objectifs en cours

1. ✅ Landing page terminée et mergée
2. 🔄 Mise à jour UI globale (design system dark theme)
3. ⬜ Valider le pipeline vidéo end-to-end
4. ⬜ Connecter front ↔ back sans erreur de build
5. ⬜ Déployer sur Vercel
6. ⬜ Acheter le domaine
7. ⬜ Préparer la demande TikTok Developer (Privacy Policy, ToS, démo)
8. ⬜ Plans gratuit/payant avec Stripe
