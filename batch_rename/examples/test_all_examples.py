#!/usr/bin/env python3
"""
Test all examples in one command to verify they work correctly.

This script runs all examples in preview mode to validate the 
batch rename tool works properly with all configurations.
"""

# run this from within the batch_rename folder

import subprocess
import sys
from pathlib import Path


def test_all_examples():
    """Test all examples to ensure they work properly."""
    
    print("🧪 Testing all batch rename tool examples...")
    print("=" * 60)
    
    # Test configurations for each example
    tests = [
        {
            'name': '01_basic_corporate',
            'description': 'Basic corporate document standardization',
            'cmd': [
                'python', 'main.py',
                '--input-folder', 'examples/01_basic_corporate/sample_files',
                '--extractor', 'split,[ _-],dept,doc_type,extra1,extra2,extra3',
                '--converter', 'case,dept,upper',
                '--converter', 'case,doc_type,upper', 
                '--converter', 'case,extra1,upper',
                '--converter', 'case,extra2,upper',
                '--converter', 'case,extra3,upper',
                '--template', 'join,dept,doc_type,extra1,extra2,extra3,separator=-',
                '--preview'
            ]
        },
        {
            'name': '02_project_organization',
            'description': 'Project file organization with date handling',
            'cmd': [
                'python', 'main.py',
                '--input-folder', 'examples/02_project_organization/sample_files',
                '--extractor', 'split,[_-],project,phase,date,version_or_extra',
                '--converter', 'strip_prefix,project,project',
                '--converter', 'case,phase,title',
                '--template', 'join,project,phase,date,version_or_extra,separator=/',
                '--preview'
            ]
        },
        {
            'name': '05_custom_functions',
            'description': 'Custom business functions',
            'cmd': [
                'python', 'main.py',
                '--input-folder', 'examples/05_custom_functions/sample_files',
                '--extractor', 'examples/05_custom_functions/business_extractors.py,department_extractor,"HR,ACCT,SALES"',
                '--converter', 'examples/05_custom_functions/business_converters.py,normalize_version,format',
                '--template', 'examples/05_custom_functions/business_templates.py,business_format',
                '--preview'
            ]
        }
    ]
    
    results = []
    
    print(f"Running {len(tests)} test scenarios...\n")
    
    for i, test in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] {test['description']}...")
        
        try:
            result = subprocess.run(test['cmd'], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ PASSED")
                
                # Extract some basic info from output 
                files_found = None
                files_to_rename = None
                
                for line in result.stdout.split('\n'):
                    if 'Files found:' in line:
                        files_found = line.split(':')[1].strip()
                    elif 'Files to rename:' in line:
                        files_to_rename = line.split(':')[1].strip()
                
                if files_found:
                    print(f"   Files found: {files_found}")
                if files_to_rename:
                    print(f"   Files to rename: {files_to_rename}")
                
                results.append({'test': test['name'], 'status': 'PASS', 'output': result.stdout})
                
            else:
                print("❌ FAILED")
                print(f"   Error code: {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}...")
                results.append({'test': test['name'], 'status': 'FAIL', 'error': result.stderr})
                
        except subprocess.TimeoutExpired:
            print("❌ TIMEOUT (30 seconds)")
            results.append({'test': test['name'], 'status': 'TIMEOUT', 'error': 'Command timed out'})
            
        except FileNotFoundError:
            print("❌ COMMAND NOT FOUND")
            print("   Make sure 'python main.py' works from the current directory")
            results.append({'test': test['name'], 'status': 'NOT_FOUND', 'error': 'Command not found'})
            
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
            results.append({'test': test['name'], 'status': 'ERROR', 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = len([r for r in results if r['status'] == 'PASS'])
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your batch rename tool examples are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        print("\nFailed tests:")
        for result in results:
            if result['status'] != 'PASS':
                print(f"  - {result['test']}: {result['status']}")
                if 'error' in result:
                    print(f"    Error: {result['error'][:100]}...")
    
    print("\n" + "=" * 60)
    
    # Use assert instead of return for pytest compatibility
    assert passed == total, f"Only {passed}/{total} tests passed"


def check_prerequisites():
    """Check if examples are set up and main.py exists."""
    
    # Check if main.py exists
    if not Path('main.py').exists():
        print("❌ Error: main.py not found in current directory")
        print("   Run this script from the batch rename tool root directory")
        return False
    
    # Check if examples directory exists
    examples_dir = Path('examples')
    if not examples_dir.exists():
        print("❌ Error: examples directory not found")
        print("   Run 'python examples/setup_examples.py' first to create examples")
        return False
    
    # Check if basic example files exist
    basic_files = examples_dir / '01_basic_corporate' / 'sample_files'
    if not basic_files.exists() or len(list(basic_files.glob('*.txt'))) == 0:
        print("❌ Error: Example files not found")
        print("   Run 'python examples/setup_examples.py' first to create examples")
        return False
    
    return True


def quick_test():
    """Run just one quick test to verify basic functionality."""
    
    print("🚀 Running quick test...")
    
    cmd = [
        'python', 'main.py',
        'examples/01_basic_corporate/sample_files',  # positional argument
        '--extractor', 'split,[ _-],dept,doc_type,extra1',
        '--converter', 'case,dept,upper',
        '--template', 'join,dept,doc_type,extra1,separator=-',
        '--preview'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ Quick test passed!")
            print("   Run with --full for comprehensive testing")
            return True
        else:
            print("❌ Quick test failed")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test all batch rename tool examples")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    
    args = parser.parse_args()
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Run tests
    if args.quick:
        success = quick_test()
    else:
        success = test_all_examples()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)