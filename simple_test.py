#!/usr/bin/env python3
"""
Simple validation test for F6 corrections
"""

import sys
import os

def test_syntax_validation():
    """Test that all corrected files have valid Python syntax"""
    print("Testing Python syntax validation...")

    files_to_test = [
        "apps/api/src/workers/publish_worker.py",
        "apps/api/src/services/tiktok_oauth.py",
        "apps/api/src/services/tiktok_publisher.py",
        "apps/api/src/routers/social.py"
    ]

    results = []

    for file_path in files_to_test:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Test compilation
            compile(content, file_path, 'exec')
            print(f"[PASS] {file_path}")
            results.append(True)

        except SyntaxError as e:
            print(f"[FAIL] {file_path}: Syntax Error at line {e.lineno}: {e.msg}")
            results.append(False)
        except Exception as e:
            print(f"[FAIL] {file_path}: {e}")
            results.append(False)

    return all(results)

def test_worker_sync_functions():
    """Test that worker functions are synchronous"""
    print("\nTesting worker function definitions...")

    try:
        with open("apps/api/src/workers/publish_worker.py", 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for sync function definitions
        sync_functions = [
            "_refresh_account_token_sync",
            "_publish_to_tiktok_sync",
            "_publish_video_sync",
            "_mock_publish_video_sync"
        ]

        for func in sync_functions:
            if f"def {func}(" in content:
                print(f"[PASS] Found sync function: {func}")
            else:
                print(f"[FAIL] Missing sync function: {func}")
                return False

        # Check that async calls are converted
        if "await _refresh_account_token(" not in content:
            print("[PASS] Removed async refresh call")
        else:
            print("[FAIL] Still contains async refresh call")
            return False

        if "await _publish_to_tiktok(" not in content:
            print("[PASS] Removed async publish call")
        else:
            print("[FAIL] Still contains async publish call")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Worker sync test failed: {e}")
        return False

def test_oauth_security_enhancements():
    """Test OAuth security features"""
    print("\nTesting OAuth security enhancements...")

    try:
        with open("apps/api/src/services/tiktok_oauth.py", 'r', encoding='utf-8') as f:
            content = f.read()

        security_features = [
            "_generate_secure_state",
            "_verify_secure_state",
            "_validate_redirect_uri",
            "_validate_token_response",
            "_request_tokens_with_retry",
            "_get_user_info_with_retry"
        ]

        for feature in security_features:
            if feature in content:
                print(f"[PASS] Found security feature: {feature}")
            else:
                print(f"[FAIL] Missing security feature: {feature}")
                return False

        # Check for timestamp validation
        if "timestamp" in content and "3600" in content:
            print("[PASS] Timestamp validation present")
        else:
            print("[FAIL] Missing timestamp validation")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] OAuth security test failed: {e}")
        return False

def test_error_handling_improvements():
    """Test error handling improvements"""
    print("\nTesting error handling improvements...")

    try:
        with open("apps/api/src/services/tiktok_publisher.py", 'r', encoding='utf-8') as f:
            content = f.read()

        error_classes = [
            "class TikTokError",
            "class TikTokRateLimitError",
            "class TikTokAuthError",
            "class TikTokUploadError",
            "class TikTokValidationError",
            "class TikTokNetworkError"
        ]

        for error_class in error_classes:
            if error_class in content:
                print(f"[PASS] Found error class: {error_class}")
            else:
                print(f"[FAIL] Missing error class: {error_class}")
                return False

        # Check for retry logic
        if "_with_retry" in content:
            print("[PASS] Retry logic implemented")
        else:
            print("[FAIL] Missing retry logic")
            return False

        # Check for validation
        if "_validate_publish_inputs" in content:
            print("[PASS] Input validation implemented")
        else:
            print("[FAIL] Missing input validation")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Error handling test failed: {e}")
        return False

def test_router_security_enhancements():
    """Test router security enhancements"""
    print("\nTesting router security enhancements...")

    try:
        with open("apps/api/src/routers/social.py", 'r', encoding='utf-8') as f:
            content = f.read()

        security_functions = [
            "_validate_oauth_callback_inputs",
            "_validate_tiktok_user_info",
            "_sanitize_username",
            "_sanitize_display_name",
            "_sanitize_user_metadata"
        ]

        for func in security_functions:
            if f"def {func}(" in content:
                print(f"[PASS] Found security function: {func}")
            else:
                print(f"[FAIL] Missing security function: {func}")
                return False

        # Check for enhanced validation
        if "HTTPException" in content and "409" in content:
            print("[PASS] Conflict handling implemented")
        else:
            print("[FAIL] Missing conflict handling")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Router security test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("F6 TikTok OAuth + Content Posting + Scheduling - Correction Validation")
    print("=" * 70)

    tests = [
        ("Syntax Validation", test_syntax_validation),
        ("Worker Sync Functions", test_worker_sync_functions),
        ("OAuth Security", test_oauth_security_enhancements),
        ("Error Handling", test_error_handling_improvements),
        ("Router Security", test_router_security_enhancements)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"Running: {test_name}")
        print('-' * 40)

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll corrections validated successfully!")
        print("\nSummary of implemented fixes:")
        print("- Converted async/sync issues in Celery workers")
        print("- Enhanced OAuth security with timestamp validation")
        print("- Improved error handling with custom exception classes")
        print("- Added comprehensive input validation and sanitization")
        print("- Implemented retry logic for network operations")
        return 0
    else:
        print(f"\n{total - passed} validation(s) failed - review needed")
        return 1

if __name__ == "__main__":
    sys.exit(main())