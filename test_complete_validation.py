#!/usr/bin/env python3
"""
Complete validation test that runs all deep merge tests and generates a comprehensive report.
"""

import subprocess
import sys
import time
import os

def run_test_suite(test_file):
    """Run a test suite and return results"""
    print(f"🧪 Running {test_file}...")
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=30)
        end_time = time.time()
        
        return {
            "file": test_file,
            "success": result.returncode == 0,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "file": test_file,
            "success": False,
            "duration": 30.0,
            "stdout": "",
            "stderr": "Test timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "file": test_file,
            "success": False,
            "duration": 0.0,
            "stdout": "",
            "stderr": str(e)
        }

def main():
    """Run complete validation suite"""
    print("🚀 COMPLETE DEEP MERGE VALIDATION SUITE")
    print("=" * 80)
    print("This suite validates that the deep merge functionality is robust")
    print("across all scenarios and fixes the original Elen character bug.")
    print("=" * 80)
    
    # Test files to run
    test_files = [
        "test_deep_merge.py",
        "test_deep_merge_stress.py", 
        "test_elen_bug_reproduction.py"
    ]
    
    results = []
    total_start = time.time()
    
    # Run each test suite
    for test_file in test_files:
        if os.path.exists(test_file):
            result = run_test_suite(test_file)
            results.append(result)
            
            if result["success"]:
                print(f"✅ {test_file} - PASSED ({result['duration']:.3f}s)")
            else:
                print(f"❌ {test_file} - FAILED ({result['duration']:.3f}s)")
                if result["stderr"]:
                    print(f"   Error: {result['stderr'][:200]}...")
        else:
            print(f"⚠️  {test_file} - FILE NOT FOUND")
            results.append({
                "file": test_file,
                "success": False,
                "duration": 0.0,
                "stdout": "",
                "stderr": "File not found"
            })
    
    total_end = time.time()
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE VALIDATION REPORT")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    total_duration = total_end - total_start
    
    print(f"📈 OVERALL RESULTS:")
    print(f"   ✅ Test Suites Passed: {passed}/{len(results)}")
    print(f"   ❌ Test Suites Failed: {failed}/{len(results)}")
    print(f"   ⏱️  Total Execution Time: {total_duration:.3f} seconds")
    print(f"   📈 Success Rate: {(passed / len(results)) * 100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status} | {result['file']:<25} | {result['duration']:.3f}s")
    
    # Extract test statistics from outputs
    total_individual_tests = 0
    total_individual_passed = 0
    
    for result in results:
        if result["success"] and "Tests Passed:" in result["stdout"]:
            # Extract numbers from output
            lines = result["stdout"].split('\n')
            for line in lines:
                if "Tests Passed:" in line and "Tests Failed:" in line:
                    try:
                        parts = line.split()
                        passed_idx = parts.index("Passed:") + 1
                        failed_idx = parts.index("Failed:") + 1
                        individual_passed = int(parts[passed_idx])
                        individual_failed = int(parts[failed_idx])
                        total_individual_tests += individual_passed + individual_failed
                        total_individual_passed += individual_passed
                    except (ValueError, IndexError):
                        pass
    
    if total_individual_tests > 0:
        print(f"\n🎯 INDIVIDUAL TEST STATISTICS:")
        print(f"   • Total Individual Tests: {total_individual_tests}")
        print(f"   • Individual Tests Passed: {total_individual_passed}")
        print(f"   • Individual Tests Failed: {total_individual_tests - total_individual_passed}")
        print(f"   • Individual Success Rate: {(total_individual_passed / total_individual_tests) * 100:.1f}%")
    
    print(f"\n🔍 VALIDATION CONCLUSIONS:")
    
    if failed == 0:
        print("   🎉 ALL VALIDATION TESTS PASSED!")
        print("   ✅ Deep merge functionality is robust and correct")
        print("   ✅ Original Elen character bug is completely fixed")
        print("   ✅ System prevents future spell data corruption")
        print("   ✅ Performance is excellent even with large datasets")
        print("   ✅ Edge cases and stress scenarios are handled properly")
        print("   ✅ Critical field validation prevents data loss")
        print("\n   🏆 The implementation is production-ready!")
    else:
        print(f"   ⚠️  {failed} validation suite(s) failed")
        print("   🔧 Review failed tests and address issues before deployment")
        
        if any("test_elen_bug_reproduction.py" in r["file"] and not r["success"] for r in results):
            print("   🚨 CRITICAL: Elen bug reproduction test failed!")
            print("   🚨 The original bug may not be fully fixed!")
    
    print("\n" + "=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)