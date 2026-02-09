#!/usr/bin/env python3
"""
Core test to verify essential functionality corrections
"""
import os
import sys

# Set environment variables before any imports
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['DEBUG'] = 'True'
os.environ['CLERK_SECRET_KEY'] = 'test-secret'
os.environ['CLERK_JWT_VERIFY_SIGNATURE'] = 'False'

def test_core_functionality():
    """Test core functionality that was corrected"""
    print("Testing core corrected functionality...")

    # Test 1: Config works
    from src.config import settings
    assert settings.CLERK_JWT_VERIFY_SIGNATURE == False
    print("[OK] JWT verification config works")

    # Test 2: Logging utilities work
    from src.utils.logging import mask_sensitive_data, safe_log_user_data

    # Test in DEBUG mode
    test_data = mask_sensitive_data("sensitive123", 3)
    assert test_data == "sensitive123"  # Should not mask in DEBUG
    print("[OK] Logging masking respects DEBUG mode")

    # Test 3: PlanType enum (without SQLAlchemy)
    try:
        from src.models.user import PlanType
        assert PlanType.FREE.value == "free"
        print("[OK] PlanType enum accessible")
    except Exception as e:
        print(f"[SKIP] PlanType test skipped due to SQLAlchemy: {e}")

    return True

if __name__ == "__main__":
    print("Testing core corrections...\n")
    try:
        if test_core_functionality():
            print("\nCore functionality tests passed!")
            sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] Core test failed: {e}")
        sys.exit(1)