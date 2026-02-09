#!/usr/bin/env python3
"""
Test script to verify the corrections made to the codebase
"""
import os
import sys

def test_rate_limiting_correction():
    """Test that rate limiting has been moved from middleware to dependencies"""
    print("Testing rate limiting correction...")

    # Check main.py doesn't have rate limiting middleware
    with open('src/main.py', 'r') as f:
        main_content = f.read()

    # Rate limiting should be removed from middleware
    assert 'from .middleware.rate_limiting' not in main_content, "Rate limiting middleware still imported in main.py"
    print("[OK] Rate limiting middleware removed from main.py")

    # Check that rate_limiting.py has dependency functions
    with open('src/middleware/rate_limiting.py', 'r') as f:
        rl_content = f.read()

    assert 'check_rate_limit' in rl_content, "check_rate_limit function missing"
    assert 'get_current_user' in rl_content, "Rate limiting doesn't depend on auth"
    print("[OK] Rate limiting converted to dependency functions")

    return True

def test_auth_session_correction():
    """Test that auth middleware properly handles DB sessions"""
    print("Testing auth session management...")

    with open('src/middleware/auth.py', 'r') as f:
        auth_content = f.read()

    # Check proper session management
    assert 'db_generator = get_db()' in auth_content, "DB generator not used properly"
    assert 'next(db_generator)' in auth_content, "DB session not closed properly"
    assert 'try:' in auth_content and 'finally:' in auth_content, "No proper exception handling"
    print("[OK] Auth middleware has proper DB session management")

    return True

def test_jwt_security_correction():
    """Test that JWT verification uses environment variable"""
    print("Testing JWT security configuration...")

    with open('src/config.py', 'r') as f:
        config_content = f.read()

    assert 'CLERK_JWT_VERIFY_SIGNATURE' in config_content, "JWT verification config missing"
    print("[OK] JWT verification uses environment variable")

    with open('src/middleware/auth.py', 'r') as f:
        auth_content = f.read()

    assert 'settings.CLERK_JWT_VERIFY_SIGNATURE' in auth_content, "JWT verification setting not used"
    print("[OK] Auth middleware uses JWT verification setting")

    return True

def test_logging_security_correction():
    """Test that logging utilities mask sensitive data"""
    print("Testing logging security...")

    with open('src/utils/logging.py', 'r') as f:
        logging_content = f.read()

    assert 'mask_sensitive_data' in logging_content, "Sensitive data masking function missing"
    assert 'mask_email' in logging_content, "Email masking function missing"
    assert 'safe_log_user_data' in logging_content, "Safe logging function missing"
    assert 'settings.DEBUG' in logging_content, "DEBUG mode check missing"
    print("[OK] Logging utilities have data masking functions")

    return True

def test_dependencies_added():
    """Test that required dependencies were added"""
    print("Testing dependencies...")

    with open('requirements.txt', 'r') as f:
        req_content = f.read()

    assert 'pyjwt' in req_content, "PyJWT dependency missing"
    assert 'aiosqlite' in req_content, "SQLite dependency for tests missing"
    print("[OK] Required dependencies added to requirements.txt")

    return True

def test_router_uses_dependencies():
    """Test that routers use rate limiting dependencies"""
    print("Testing router dependencies...")

    with open('src/routers/users.py', 'r') as f:
        users_content = f.read()

    assert 'check_rate_limit' in users_content, "User router doesn't use rate limiting dependency"
    assert 'Depends(check_rate_limit)' in users_content, "Rate limiting not used as dependency"
    print("[OK] User router uses rate limiting dependencies")

    return True

def main():
    print("Verifying corrections made by Agent Executor...\n")

    # Change to API directory
    os.chdir('C:/Users/marti/shortcut/apps/api')

    tests = [
        test_rate_limiting_correction,
        test_auth_session_correction,
        test_jwt_security_correction,
        test_logging_security_correction,
        test_dependencies_added,
        test_router_uses_dependencies
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

    print(f"\nTest Results: {passed}/{total} tests passed")

    if passed == total:
        print("All corrections verified!")
        return True
    else:
        print("Some corrections need attention")
        return False

if __name__ == "__main__":
    main()