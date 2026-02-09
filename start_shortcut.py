#!/usr/bin/env python3
"""
Script de lancement rapide pour ShortCut
Lance le backend, vérifie que tout fonctionne
"""
import subprocess
import sys
import os
import time
import requests
from dotenv import load_dotenv

def test_service(name, url, timeout=5):
    """Test si un service est accessible"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"[OK] {name}: {url}")
            return True
        else:
            print(f"[ERROR] {name}: Status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {name}: {e}")
        return False

def main():
    print("=== LANCEMENT SHORTCUT ===")
    print()

    # 1. Charger la config
    print("1. Chargement configuration...")
    load_dotenv('./apps/api/.env')
    os.chdir('./apps/api')

    try:
        sys.path.append('./apps/api')
        from src.config import settings
        print(f"   - Mode MOCK: {settings.MOCK_MODE}")
        print(f"   - Base URL: http://localhost:8000")
    except Exception as e:
        print(f"   [ERROR] Configuration: {e}")
        return False

    # 2. Test des dépendances
    print("\n2. Test des services requis...")

    # Test PostgreSQL (optionnel en mode mock)
    if settings.MOCK_MODE:
        print("   - PostgreSQL: Optionnel en mode MOCK")
    else:
        print("   - PostgreSQL: A tester manuellement")

    # Test Redis (optionnel en mode mock)
    if settings.MOCK_MODE:
        print("   - Redis: Optionnel en mode MOCK")
    else:
        print("   - Redis: A tester manuellement")

    print("\n3. Lancement API backend...")
    print("   Commande: uvicorn src.main:app --reload --port 8000")
    print("   Pour lancer manuellement:")
    print("   > cd apps/api")
    print("   > uvicorn src.main:app --reload --port 8000")
    print()
    print("4. Lancement Frontend (dans un autre terminal):")
    print("   > cd apps/web")
    print("   > npm run dev")
    print()
    print("5. URLs de test:")
    print("   - API Health: http://localhost:8000/health")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Frontend: http://localhost:3000")
    print()
    print("6. Test d'authentification:")
    print("   - Va sur http://localhost:3000")
    print("   - Clique 'Get Started'")
    print("   - Cree un compte avec ton email")
    print("   - Tu devrais etre redirige vers /dashboard")
    print()

    # 7. Test API
    print("7. Test de l'API backend...")
    try:
        # Lance l'API en arrière-plan pour test
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8000"
        ], cwd="apps/api", stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Attend que l'API démarre
        time.sleep(3)

        # Test health check
        if test_service("API Health", "http://localhost:8000/health"):
            print("   [OK] Backend prêt !")
        else:
            print("   [ERROR] Backend non accessible")

        # Arrête le process de test
        api_process.terminate()

    except Exception as e:
        print(f"   [ERROR] Impossible de tester l'API: {e}")

    print("\n=== CONFIGURATION COMPLETE ===")
    print("Tu peux maintenant:")
    print("1. Lancer le backend: cd apps/api && uvicorn src.main:app --reload --port 8000")
    print("2. Lancer le frontend: cd apps/web && npm run dev")
    print("3. Aller sur http://localhost:3000")

if __name__ == "__main__":
    main()