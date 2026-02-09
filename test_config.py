#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration de ShortCut
"""
import os
import sys
sys.path.append('./apps/api')

# Test 1: Variables d'environnement
print("=" * 50)
print("TEST 1: Variables d'environnement")
print("=" * 50)

env_vars = [
    'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
    'CLERK_SECRET_KEY',
    'MOCK_MODE',
    'DATABASE_URL',
    'REDIS_URL'
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        # Masquer les clés sensibles
        if 'KEY' in var or 'SECRET' in var:
            masked = value[:10] + "..." + value[-4:] if len(value) > 14 else value[:6] + "..."
            print(f"✓ {var}: {masked}")
        else:
            print(f"✓ {var}: {value}")
    else:
        print(f"✗ {var}: NON TROUVÉ")

print("\n" + "=" * 50)
print("TEST 2: Import de la configuration")
print("=" * 50)

try:
    from src.config import settings
    print("✓ Configuration importée avec succès")
    print(f"✓ Mode MOCK: {settings.MOCK_MODE}")
    print(f"✓ Debug: {settings.DEBUG}")

    if settings.CLERK_SECRET_KEY:
        print(f"✓ Clerk configuré: {settings.CLERK_SECRET_KEY[:10]}...")
    else:
        print("✗ Clerk Secret Key non trouvé")

except Exception as e:
    print(f"✗ Erreur import config: {e}")

print("\n" + "=" * 50)
print("TEST 3: Base de données")
print("=" * 50)

try:
    from src.database import engine
    print("✓ Connexion DB configurée")

    # Test de connexion (sans créer de tables)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1 as test")
        print("✓ Connexion DB réussie")
except Exception as e:
    print(f"✗ Erreur DB: {e}")
    print("  Assure-toi que PostgreSQL est démarré et que la DB 'shortcut' existe")

print("\n" + "=" * 50)
print("RÉSUMÉ DU TEST")
print("=" * 50)
print("Si tous les tests sont ✓, tu peux lancer l'application !")
print("Sinon, vérifie les erreurs ci-dessus.")