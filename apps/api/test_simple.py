#!/usr/bin/env python3
"""
Simple test to verify the structure and imports are working
"""

def test_imports():
    """Test that basic imports work"""
    try:
        from src.config import settings
        from src.models.user import User, PlanType
        from src.utils.logging import mask_sensitive_data, mask_email, safe_log_user_data
        print("All imports successful")
        return True
    except Exception as e:
        print(f"Import failed: {e}")
        return False

def test_utilities():
    """Test utility functions"""
    from src.utils.logging import mask_sensitive_data, mask_email
    from src.config import settings

    # Test masking functions
    test_clerk_id = "user_1234567890abcdef"
    test_email = "test.user@example.com"

    masked_id = mask_sensitive_data(test_clerk_id, 8)
    masked_email = mask_email(test_email)

    print(f"Original clerk_id: {test_clerk_id}")
    print(f"Masked clerk_id: {masked_id}")
    print(f"Original email: {test_email}")
    print(f"Masked email: {masked_email}")

    if settings.DEBUG:
        assert masked_id == test_clerk_id, "Should not mask in DEBUG mode"
        assert masked_email == test_email, "Should not mask in DEBUG mode"
    else:
        assert "***" in masked_id, "Should mask in production mode"
        assert "***" in masked_email, "Should mask in production mode"

    print("Utility functions work correctly")
    return True

if __name__ == "__main__":
    print("Testing basic functionality...")

    if test_imports():
        print("Imports test passed")
    else:
        print("Imports test failed")
        exit(1)

    if test_utilities():
        print("Utilities test passed")
    else:
        print("Utilities test failed")
        exit(1)

    print("\nAll tests passed!")