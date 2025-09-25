#!/usr/bin/env python3
"""
SLGS OBU Voting System - Deployment Test Script
Tests the application in production-like environment
"""

import os
import sys
from app import create_app, db

def test_database_connection():
    """Test database connectivity"""
    print("Testing database connection...")
    try:
        app = create_app()
        with app.app_context():
            db.create_all()
            print("Database connection successful")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def test_admin_access():
    """Test admin dashboard access"""
    print("Testing admin access...")
    try:
        app = create_app()
        with app.test_client() as client:
            # Test with debug mode
            response = client.get('/admin?debug=true')
            if response.status_code == 200:
                print("Admin dashboard accessible")
                return True
            else:
                print(f"Admin dashboard failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"Admin access test failed: {e}")
        return False

def test_voting_system():
    """Test voting functionality"""
    print("Testing voting system...")
    try:
        app = create_app()
        with app.test_client() as client:
            # Test voting page
            response = client.get('/vote')
            if response.status_code == 200:
                print("Voting page accessible")
                return True
            else:
                print(f"Voting page failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"Voting system test failed: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("Testing environment configuration...")

    required_vars = ['SECRET_KEY', 'ADMIN_TOKEN', 'DATABASE_URL']
    missing_vars = []

    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Using default values for testing")
    else:
        print("All environment variables configured")

    return len(missing_vars) == 0

def main():
    """Run all deployment tests"""
    print("SLGS OBU Voting System - Deployment Test")
    print("=" * 50)

    tests = [
        ("Environment Configuration", test_environment),
        ("Database Connection", test_database_connection),
        ("Admin Dashboard", test_admin_access),
        ("Voting System", test_voting_system),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! Ready for deployment!")
        print("\nProduction URLs:")
        print("   Admin: https://your-domain.com/admin")
        print("   Voting: https://your-domain.com/vote")
        return True
    else:
        print("Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)