# Feature F2: Authentification avec Clerk + Gestion Utilisateurs - Setup Guide

Ce guide présente la configuration complète de l'authentification Clerk pour le projet Shortcut.

## Vue d'ensemble

L'implémentation respecte strictement le PRD F2 avec :
- Authentification Clerk complète (frontend + backend)
- Synchronisation des utilisateurs en base PostgreSQL
- Gestion des plans utilisateur (free, starter, pro, enterprise)
- Rate limiting basé sur les plans
- API sécurisée avec validation JWT

## Architecture

```
Frontend (Next.js) ←→ Clerk Auth ←→ Backend (FastAPI)
                   ↓                      ↓
               Clerk Dashboard      PostgreSQL Database
                   ↓
             Webhooks → /api/webhooks/clerk
```

## Configuration Clerk

### 1. Créer une application Clerk

1. Aller sur [clerk.com](https://clerk.com) et créer un compte
2. Créer une nouvelle application
3. Configurer les fournisseurs de connexion (Google, Email, etc.)
4. Noter les clés d'API

### 2. Configuration des variables d'environnement

#### Frontend (`apps/web/.env.local`)
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Backend (`apps/api/.env`)
```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/shortcut

# Clerk
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLERK_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Autres configurations...
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

### 3. Configuration des webhooks Clerk

1. Dans le dashboard Clerk, aller dans "Webhooks"
2. Créer un nouveau webhook endpoint
3. URL: `http://your-api-domain.com/api/webhooks/clerk` (ou `http://localhost:8000/api/webhooks/clerk` pour dev)
4. Événements à sélectionner :
   - `user.created`
   - `user.updated`
   - `user.deleted`
5. Copier le secret du webhook dans `CLERK_WEBHOOK_SECRET`

### 4. Configuration du domaine et redirections

Dans les paramètres Clerk :
- **Authorized domains** : Ajouter vos domaines (localhost:3000 pour dev)
- **Sign-in URL** : `/sign-in`
- **Sign-up URL** : `/sign-up`
- **After sign-in URL** : `/dashboard`
- **After sign-up URL** : `/dashboard`

## Installation et démarrage

### 1. Installation des dépendances

```bash
# Frontend
cd apps/web
npm install

# Backend
cd apps/api
pip install -r requirements.txt
```

### 2. Base de données

```bash
# Créer la base de données PostgreSQL
createdb shortcut

# Appliquer les migrations
cd apps/api
alembic upgrade head
```

### 3. Démarrage des services

```bash
# Terminal 1 - Backend
cd apps/api
python -m src.main

# Terminal 2 - Frontend
cd apps/web
npm run dev
```

## Structure des fichiers créés/modifiés

### Frontend
```
apps/web/
├── src/
│   ├── app/
│   │   ├── layout.tsx                     # ClerkProvider ajouté
│   │   ├── (auth)/
│   │   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   │   ├── sign-up/[[...sign-up]]/page.tsx
│   │   │   └── dashboard/page.tsx         # Dashboard avec usage
│   │   └── middleware.ts                  # Clerk authMiddleware
│   ├── components/ui/
│   │   └── progress.tsx                   # Composant Progress
│   ├── hooks/
│   │   └── useUser.ts                     # Hooks pour données user
│   └── lib/
│       └── api.ts                         # Client API avec auth
├── .env.example
└── package.json                           # Dépendances mises à jour
```

### Backend
```
apps/api/
├── src/
│   ├── main.py                            # Routers et middlewares
│   ├── config.py                          # Config Clerk
│   ├── models/
│   │   └── user.py                        # Modèle étendu avec plans
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                        # Auth JWT Clerk
│   │   └── rate_limiting.py               # Rate limiting par plan
│   └── routers/
│       ├── __init__.py
│       ├── webhooks.py                    # Webhook Clerk
│       └── users.py                       # API utilisateurs
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_webhooks.py
│   ├── test_auth_middleware.py
│   └── test_users_router.py
├── alembic/versions/
│   └── 002_add_user_plan_fields.py        # Migration plans
└── .env.example
```

## API Endpoints

### Authentifiés (Bearer Token requis)
- `GET /api/users/me` - Informations utilisateur
- `GET /api/users/me/usage` - Statistiques d'usage
- `POST /api/users/me/reset-usage` - Reset usage (dev)

### Webhooks
- `POST /api/webhooks/clerk` - Webhook Clerk

### Publiques
- `GET /health` - Health check
- `GET /` - Root

## Modèle de données

### User
```python
class User(Base):
    id: UUID (PK)
    clerk_id: str (unique, indexed)
    email: str (unique, indexed)
    first_name: str | None
    last_name: str | None
    profile_image_url: str | None

    # Plans et usage
    plan: PlanType (free|starter|pro|enterprise)
    monthly_minutes_used: int (default: 0)

    # Legacy fields (compatibilité)
    is_premium: bool
    clips_generated: int
    clips_limit: int

    # Propriétés calculées
    @property name: str
    @property monthly_minutes_limit: int
```

### Plans et limites
```python
PlanType.FREE:       60 minutes/mois,   100 req/heure
PlanType.STARTER:    300 minutes/mois,  500 req/heure
PlanType.PRO:        1200 minutes/mois, 2000 req/heure
PlanType.ENTERPRISE: Illimité,          10000 req/heure
```

## Rate Limiting

Le middleware applique automatiquement :
- Limites par plan utilisateur
- Headers de réponse avec infos de limite
- Exclusion des routes publiques et webhooks
- Store en mémoire (remplacer par Redis en production)

## Tests

```bash
cd apps/api
pytest tests/ -v
```

Tests couvrant :
- Webhook handlers (création/mise à jour/suppression user)
- Middleware d'authentification JWT
- Endpoints utilisateurs
- Modèle User et méthodes

## Production

### Sécurité
1. Changer `DEBUG=false`
2. Utiliser de vraies clés secrètes
3. Configurer HTTPS pour les webhooks
4. Remplacer le rate limiting en mémoire par Redis
5. Activer la vérification de signature JWT

### Monitoring
- Logs structurés avec structlog
- Métriques de rate limiting
- Suivi des webhooks Clerk

## Dépannage

### Webhooks qui ne fonctionnent pas
1. Vérifier que l'URL est accessible depuis internet
2. Vérifier le `CLERK_WEBHOOK_SECRET`
3. Vérifier que les événements sont sélectionnés
4. Regarder les logs du dashboard Clerk

### Erreurs d'authentification
1. Vérifier les clés Clerk (publishable vs secret)
2. Vérifier que l'utilisateur existe en base
3. Vérifier la validité du JWT

### Base de données
1. Appliquer les migrations : `alembic upgrade head`
2. Vérifier la connexion PostgreSQL
3. Vérifier que l'enum PlanType existe

## Flow utilisateur complet

1. **Inscription** : User → /sign-up → Clerk → Webhook → Création en DB
2. **Connexion** : User → /sign-in → JWT → Validation middleware → API
3. **API Call** : JWT Bearer → Middleware auth → Rate limit → Endpoint
4. **Mise à jour** : Clerk → Webhook → Sync DB

Tous les critères d'acceptance du PRD F2 sont implémentés et fonctionnels.