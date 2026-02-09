#!/bin/bash

# Installation and testing script for the API
echo "🚀 Starting API installation and testing..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Run basic import test
echo "🧪 Running import tests..."
python -c "
try:
    from src.utils.logging import mask_sensitive_data, mask_email, safe_log_user_data
    print('✅ Logging utilities imported successfully')

    # Test masking functions
    test_id = 'user_1234567890abcdef'
    test_email = 'test@example.com'

    masked_id = mask_sensitive_data(test_id, 8)
    masked_email = mask_email(test_email)

    print(f'🔒 Masked ID: {masked_id}')
    print(f'🔒 Masked Email: {masked_email}')

    print('✅ All utility functions work correctly')

except Exception as e:
    print(f'❌ Import test failed: {e}')
    exit(1)
"

echo "🏁 Installation and basic tests completed successfully!"
echo ""
echo "To run the API:"
echo "  1. Activate virtual environment: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
echo "  2. Set environment variables (copy .env.example to .env and configure)"
echo "  3. Run: uvicorn src.main:app --reload"
echo ""
echo "To run tests:"
echo "  pytest tests/ -v"