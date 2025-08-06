#!/usr/bin/env python3
"""
Comprehensive Test Runner for Cafe Pentagon Chatbot
Runs all tests with coverage reporting and performance monitoring
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Exit Code: {result.returncode}")
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} FAILED")
        return False
    else:
        print(f"✅ {description} PASSED")
        return True

def main():
    """Main test runner"""
    print("🚀 Cafe Pentagon Chatbot - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create tests directory if it doesn't exist
    Path("tests").mkdir(exist_ok=True)
    Path("tests/test_data").mkdir(exist_ok=True)
    
    # Test results tracking
    test_results = []
    
    # 1. Run unit tests
    print("\n📋 Phase 1: Unit Tests")
    unit_success = run_command(
        "python -m pytest tests/ -m unit -v --tb=short",
        "Unit Tests"
    )
    test_results.append(("Unit Tests", unit_success))
    
    # 2. Run integration tests
    print("\n📋 Phase 2: Integration Tests")
    integration_success = run_command(
        "python -m pytest tests/ -m integration -v --tb=short",
        "Integration Tests"
    )
    test_results.append(("Integration Tests", integration_success))
    
    # 3. Run async tests
    print("\n📋 Phase 3: Async Tests")
    async_success = run_command(
        "python -m pytest tests/ -m asyncio -v --tb=short",
        "Async Tests"
    )
    test_results.append(("Async Tests", async_success))
    
    # 4. Run performance tests
    print("\n📋 Phase 4: Performance Tests")
    performance_success = run_command(
        "python -m pytest tests/ -m performance -v --tb=short",
        "Performance Tests"
    )
    test_results.append(("Performance Tests", performance_success))
    
    # 5. Run all tests with coverage
    print("\n📋 Phase 5: Full Test Suite with Coverage")
    coverage_success = run_command(
        "python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=80",
        "Full Test Suite with Coverage"
    )
    test_results.append(("Full Test Suite", coverage_success))
    
    # 6. Run linting
    print("\n📋 Phase 6: Code Quality Checks")
    lint_success = run_command(
        "python -m flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503",
        "Code Linting"
    )
    test_results.append(("Code Linting", lint_success))
    
    # 7. Run type checking
    print("\n📋 Phase 7: Type Checking")
    type_success = run_command(
        "python -m mypy src/ --ignore-missing-imports --no-strict-optional",
        "Type Checking"
    )
    test_results.append(("Type Checking", type_success))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! The codebase is ready for production.")
        print("\n📁 Coverage report available at: htmlcov/index.html")
        return 0
    else:
        print(f"\n⚠️  {failed} test phase(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 