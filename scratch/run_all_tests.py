import os
import sys
import subprocess

def run_all_tests():
    # Find all test files matching test_*.py in the root directory
    test_files = [f for f in os.listdir(".") if f.startswith("test_") and f.endswith(".py")]
    test_files.sort()
    
    print("==================================================")
    print("START: ScholarSwarm Test Verification Suite")
    print(f"Found {len(test_files)} test files to execute.")
    print("==================================================")
    
    passed_tests = []
    failed_tests = []
    
    # Configure environment key if missing (mock key for offline router testing if necessary)
    if "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = "mock_key_for_test_purposes"
        
    for idx, test_file in enumerate(test_files, 1):
        print(f"\n[{idx}/{len(test_files)}] Running {test_file}...")
        try:
            # Run the test python script synchronously
            # Use 120 seconds timeout for full multi-agent swarm flows
            result = subprocess.run(
                [sys.executable, test_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"PASS: {test_file}")
                passed_tests.append(test_file)
            else:
                print(f"FAIL: {test_file} (Return code {result.returncode})")
                print("--- Output Snippet ---")
                print(result.stdout[-800:] if result.stdout else "")
                print(result.stderr[-800:] if result.stderr else "")
                failed_tests.append((test_file, result.stderr))
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT: {test_file} after 30 seconds.")
            failed_tests.append((test_file, "TimeoutExpired"))
        except Exception as e:
            print(f"ERROR: {test_file} - {str(e)}")
            failed_tests.append((test_file, str(e)))
            
    print("\n==================================================")
    print("Test Results Summary")
    print(f"Passed: {len(passed_tests)} / {len(test_files)}")
    print(f"Failed: {len(failed_tests)} / {len(test_files)}")
    print("==================================================")
    
    if failed_tests:
        print("\nFailed Tests:")
        for name, err in failed_tests:
            print(f" - {name}")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
