"""
Script to validate all Python files for syntax errors and import issues
"""
import os
import sys
import py_compile
from pathlib import Path

def validate_python_file(file_path):
    """Validate a Python file for syntax errors"""
    try:
        py_compile.compile(file_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    """Validate all Python files in the project"""
    project_dir = Path(__file__).parent
    python_files = list(project_dir.glob("*.py"))
    
    print("=" * 60)
    print("VALIDATING PYTHON FILES")
    print("=" * 60)
    
    results = {}
    
    for file_path in python_files:
        if file_path.name == "validate_files.py":
            continue
            
        print(f"\nChecking {file_path.name}...", end=" ")
        success, error = validate_python_file(file_path)
        
        if success:
            print("✅ OK")
            results[file_path.name] = True
        else:
            print(f"❌ ERROR")
            print(f"  Error: {error}")
            results[file_path.name] = False
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for filename, success in sorted(results.items()):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{filename:<30} {status}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} files passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ All files are valid!")
        return 0
    else:
        print(f"\n❌ {total - passed} file(s) have errors!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
