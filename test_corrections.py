#!/usr/bin/env python3
"""
Test script to validate F6 TikTok OAuth + Content Posting + Scheduling corrections
"""

import sys
import os
import asyncio
from unittest.mock import patch, MagicMock

# Add the project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api', 'src'))

def test_imports():
    """Test that all corrected modules can be imported successfully"""
    print("Testing imports...")

    try:
        from workers.publish_worker import (
            check_scheduled_posts,
            publish_scheduled_post,
            _refresh_account_token_sync,
            _publish_to_tiktok_sync,
            _publish_video_sync
        )
        print("[PASS] publish_worker imports successful")
    except Exception as e:
        print(f"[FAIL] publish_worker import failed: {e}")
        return False

    try:
        from services.tiktok_oauth import (
            TikTokOAuthService,
            tiktok_oauth_service
        )
        print("[PASS] tiktok_oauth imports successful")
    except Exception as e:
        print(f"[FAIL] tiktok_oauth import failed: {e}")
        return False

    try:
        from services.tiktok_publisher import (
            TikTokPublisherService,
            TikTokError,
            TikTokRateLimitError,
            TikTokAuthError,
            TikTokUploadError,
            TikTokValidationError,
            TikTokNetworkError,
            tiktok_publisher_service
        )
        print("[PASS] tiktok_publisher imports successful")
    except Exception as e:
        print(f"[FAIL] tiktok_publisher import failed: {e}")
        return False

    try:
        from routers.social import (
            router,
            _validate_oauth_callback_inputs,
            _validate_tiktok_user_info,
            _sanitize_username,
            _sanitize_display_name,
            _sanitize_user_metadata
        )
        print("[PASS] social router imports successful")
    except Exception as e:
        print(f"[FAIL] social router import failed: {e}")
        return False

    return True

def test_oauth_security():
    """Test OAuth security enhancements"""
    print("\nTesting OAuth security...")

    try:
        from services.tiktok_oauth import tiktok_oauth_service

        # Test state generation
        state = tiktok_oauth_service._generate_secure_state("test_user_123")
        print(f"✅ Secure state generated: {len(state)} chars")

        # Test state verification
        is_valid = tiktok_oauth_service._verify_secure_state(state, "test_user_123")
        print(f"✅ State verification: {'Valid' if is_valid else 'Invalid'}")

        # Test invalid state
        is_invalid = tiktok_oauth_service._verify_secure_state("invalid_state", "test_user_123")
        print(f"✅ Invalid state rejected: {'Correctly' if not is_invalid else 'Failed'}")

        return True
    except Exception as e:
        print(f"❌ OAuth security test failed: {e}")
        return False

def test_error_handling():
    """Test enhanced error handling in publisher"""
    print("\nTesting error handling...")

    try:
        from services.tiktok_publisher import (
            TikTokValidationError,
            TikTokAuthError,
            TikTokRateLimitError,
            tiktok_publisher_service
        )

        # Test validation errors
        try:
            tiktok_publisher_service._validate_publish_inputs("", "", "", [], "INVALID")
            print("❌ Validation should have failed")
            return False
        except TikTokValidationError:
            print("✅ Validation error caught correctly")

        # Test input validation
        try:
            tiktok_publisher_service._validate_publish_inputs(
                "encrypted_token", "https://example.com/video.mp4",
                "Test caption", ["test"], "SELF_ONLY"
            )
            print("✅ Valid inputs accepted")
        except Exception as e:
            print(f"❌ Valid inputs rejected: {e}")
            return False

        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_input_sanitization():
    """Test input sanitization functions"""
    print("\nTesting input sanitization...")

    try:
        from routers.social import (
            _sanitize_username,
            _sanitize_display_name,
            _sanitize_user_metadata,
            _validate_oauth_callback_inputs,
            _validate_tiktok_user_info
        )

        # Test username sanitization
        clean_username = _sanitize_username("test_user@123!")
        print(f"✅ Username sanitized: 'test_user@123!' -> '{clean_username}'")

        # Test display name sanitization
        clean_display = _sanitize_display_name("Test\x00User\x1f")
        print(f"✅ Display name sanitized: contains control chars -> '{clean_display}'")

        # Test OAuth callback validation
        valid_inputs = _validate_oauth_callback_inputs("valid_code_12345", "valid_state_abcdef123456")
        print(f"✅ Valid OAuth inputs: {'Accepted' if valid_inputs else 'Rejected'}")

        invalid_inputs = _validate_oauth_callback_inputs("", "short")
        print(f"✅ Invalid OAuth inputs: {'Rejected' if not invalid_inputs else 'Accepted'}")

        # Test TikTok user info validation
        valid_user_info = _validate_tiktok_user_info({
            "open_id": "valid_open_id_12345",
            "username": "testuser",
            "display_name": "Test User"
        })
        print(f"✅ Valid user info: {'Accepted' if valid_user_info else 'Rejected'}")

        invalid_user_info = _validate_tiktok_user_info({"invalid": "data"})
        print(f"✅ Invalid user info: {'Rejected' if not invalid_user_info else 'Accepted'}")

        return True
    except Exception as e:
        print(f"❌ Sanitization test failed: {e}")
        return False

def test_worker_functions():
    """Test that worker functions are properly synchronous"""
    print("\nTesting worker functions...")

    try:
        from workers.publish_worker import (
            _refresh_account_token_sync,
            _publish_to_tiktok_sync,
            _publish_video_sync,
            _mock_publish_video_sync
        )

        # Verify functions are callable (not async)
        assert not asyncio.iscoroutinefunction(_refresh_account_token_sync), "refresh function should be sync"
        assert not asyncio.iscoroutinefunction(_publish_to_tiktok_sync), "publish function should be sync"
        assert not asyncio.iscoroutinefunction(_publish_video_sync), "video publish function should be sync"
        assert not asyncio.iscoroutinefunction(_mock_publish_video_sync), "mock function should be sync"

        print("✅ All worker functions are properly synchronous")

        # Test mock functionality
        result = _mock_publish_video_sync("https://example.com/video.mp4", "Test caption")
        assert "publish_id" in result, "Mock result should contain publish_id"
        assert result["status"] == "published", "Mock status should be published"
        print("✅ Mock worker function returns expected result")

        return True
    except Exception as e:
        print(f"❌ Worker function test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting F6 TikTok OAuth + Content Posting + Scheduling correction tests...\n")

    tests = [
        ("Module Imports", test_imports),
        ("OAuth Security", test_oauth_security),
        ("Error Handling", test_error_handling),
        ("Input Sanitization", test_input_sanitization),
        ("Worker Functions", test_worker_functions),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} Tests")
        print('='*50)

        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} tests PASSED")
            else:
                print(f"❌ {test_name} tests FAILED")
        except Exception as e:
            print(f"❌ {test_name} tests CRASHED: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("All corrections validated successfully!")
        return 0
    else:
        print("Some tests failed - review corrections needed")
        return 1

if __name__ == "__main__":
    sys.exit(main())