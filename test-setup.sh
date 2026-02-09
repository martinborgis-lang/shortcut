#!/bin/bash

# Shortcut Application Setup Test Script
# This script tests the basic setup and configuration

echo "🧪 Testing Shortcut Application Setup..."
echo "========================================"

# Test 1: Check if all required files exist
echo "✅ Checking required files..."
required_files=(
    ".env.example"
    "README.md"
    "docker-compose.dev.yml"
    "apps/web/package.json"
    "apps/web/tsconfig.json"
    "apps/api/requirements.txt"
    "apps/api/alembic.ini"
    "apps/api/src/main.py"
    "apps/api/src/config.py"
    "apps/api/src/database.py"
    "apps/api/src/models/__init__.py"
    "apps/api/src/workers/celery_app.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
        exit 1
    fi
done

# Test 2: Check Python syntax in backend files
echo -e "\n✅ Checking Python syntax..."
find apps/api/src -name "*.py" -exec python -m py_compile {} \; 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✓ All Python files have valid syntax"
else
    echo "  ✗ Python syntax errors found"
    exit 1
fi

# Test 3: Check if Docker Compose file is valid
echo -e "\n✅ Checking Docker Compose configuration..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.dev.yml config >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ Docker Compose configuration is valid"
    else
        echo "  ✗ Docker Compose configuration has errors"
        exit 1
    fi
else
    echo "  ⚠ Docker Compose not installed, skipping validation"
fi

# Test 4: Check if package.json is valid
echo -e "\n✅ Checking Frontend configuration..."
if command -v node &> /dev/null; then
    cd apps/web && npm install --dry-run >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ Frontend package.json is valid"
    else
        echo "  ✗ Frontend package.json has issues"
        exit 1
    fi
    cd ../..
else
    echo "  ⚠ Node.js not installed, skipping validation"
fi

# Test 5: Check directory structure
echo -e "\n✅ Checking directory structure..."
expected_dirs=(
    "apps/web/src/app"
    "apps/web/src/components/ui"
    "apps/web/src/lib"
    "apps/api/src/models"
    "apps/api/src/workers"
    "apps/api/alembic"
    "packages/shared"
)

for dir in "${expected_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ✗ $dir missing"
        exit 1
    fi
done

echo -e "\n🎉 All setup tests passed!"
echo "========================================"
echo "Your Shortcut application is properly configured!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Run: docker-compose -f docker-compose.dev.yml up -d"
echo "3. Run: docker exec shortcut_api alembic upgrade head"
echo "4. Visit: http://localhost:3000"
echo ""
echo "Happy coding! 🚀"