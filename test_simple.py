#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()

print("=== TEST CONFIGURATION SHORTCUT ===")
print()

print("1. Variables d'environnement:")
env_vars = [
    'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
    'CLERK_SECRET_KEY',
    'MOCK_MODE',
    'DATABASE_URL'
]

all_found = True
for var in env_vars:
    value = os.getenv(var)
    if value:
        if 'KEY' in var:
            print(f"[OK] {var}: {value[:10]}...")
        else:
            print(f"[OK] {var}: {value}")
    else:
        print(f"[ERROR] {var}: NON TROUVE")
        all_found = False

print()
print("2. Test import configuration:")
try:
    import sys
    sys.path.append('./apps/api')
    from src.config import settings
    print("[OK] Configuration importee")
    print(f"[OK] Mock mode: {settings.MOCK_MODE}")
except Exception as e:
    print(f"[ERROR] Import config: {e}")
    all_found = False

print()
print("3. Resultat:")
if all_found:
    print("[OK] Configuration prete! Tu peux lancer l'app.")
else:
    print("[ERROR] Il y a des problemes de configuration.")