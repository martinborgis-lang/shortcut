#!/usr/bin/env python3
"""
Minimal test to verify basic functionality without database dependencies
"""
import os
import sys

# Set environment variables before any imports
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['DEBUG'] = 'True'
os.environ['CLERK_SECRET_KEY'] = 'test-secret'
os.environ['CLERK_JWT_VERIFY_SIGNATURE'] = 'False'

def test_config_loading():
    """Test configuration loading"""
    print("Testing config loading...")
    from src.config import settings
    assert settings.DEBUG == True
    assert settings.CLERK_SECRET_KEY == 'test-secret'
    assert settings.CLERK_JWT_VERIFY_SIGNATURE == False
    print("[OK] Configuration loaded correctly")
    return True

def test_logging_utils():
    """Test logging utilities work correctly"""
    print("Testing logging utilities...")
    from src.utils.logging import mask_sensitive_data, mask_email, safe_log_user_data

    # Test masking in DEBUG mode (should not mask)
    test_id = "user_1234567890"
    test_email = "test@example.com"

    masked_id = mask_sensitive_data(test_id, 8)
    masked_email = mask_email(test_email)

    # In DEBUG mode, should not mask
    assert masked_id == test_id
    assert masked_email == test_email
    print("[OK] Logging utilities work in DEBUG mode")

    # Test safe logging function
    log_data = safe_log_user_data("123", clerk_id="user_abc", email="test@example.com")
    assert 'user_id' in log_data
    assert 'clerk_id' in log_data
    assert 'email' in log_data
    print("[OK] Safe logging function works")

    return True

def test_user_model():
    """Test User model definition"""
    print("Testing User model...")
    from src.models.user import User, PlanType

    # Test enum values
    assert PlanType.FREE.value == "free"
    assert PlanType.STARTER.value == "starter"
    assert PlanType.PRO.value == "pro"
    assert PlanType.ENTERPRISE.value == "enterprise"
    print("[OK] User model and PlanType enum work")

    return True

def test_rate_limiting_structure():
    """Test rate limiting dependencies structure"""
    print("Testing rate limiting structure...")
    from src.middleware.rate_limiting import check_rate_limit, check_minute_usage

    # Functions should exist
    assert callable(check_rate_limit)
    assert callable(check_minute_usage)
    print("[OK] Rate limiting dependency functions exist")

    return True

def main():
    print("Running minimal tests...\n")

    tests = [
        test_config_loading,
        test_logging_utils,
        test_user_model,
        test_rate_limiting_structure
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"[FAIL] Test failed: {e}\n")

    print(f"\nMinimal Test Results: {passed}/{total} tests passed")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)