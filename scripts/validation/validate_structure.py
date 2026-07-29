#!/usr/bin/env python3
"""
Automated Project Structure & Anti-Pattern Validator
Verifies directory layout compliance and blocks generic/helper dump files.
"""
import os
import sys
import glob

# Generic file name patterns that lead to unorganized/messy structures.
# We encourage creating focused, cohesive modules instead of dump files.
FORBIDDEN_PATTERNS = [
    "utils.py", "helpers.py", "common.py", "misc.py",
    "temp_*.py", "new_*.py"
]

# Excluded directories from scanning
EXCLUDED_DIRS = [
    'venv/', '.git/', '__pycache__/', 'node_modules/', 
    '.pytest_cache/', '.specify/', '.claude/', 'temp/'
]

def check_forbidden_files():
    """
    Scans the workspace for generic anti-pattern file names.
    Returns True if no violations are found, False otherwise.
    """
    violations = []
    
    for pattern in FORBIDDEN_PATTERNS:
        matches = glob.glob(f"**/{pattern}", recursive=True)
        # Filter out matches inside excluded directories
        for match in matches:
            is_excluded = False
            for excl in EXCLUDED_DIRS:
                if match.startswith(excl) or f'/{excl}' in match:
                    is_excluded = True
                    break
            if not is_excluded:
                violations.append(match)
                
    if violations:
        print("\033[0;31m❌ ERROR: Anti-Pattern file names detected!\033[0m")
        print("   The following files violate project modularity rules:")
        for file in violations:
            print(f"      - {file}")
        print("\n💡 Tip: Avoid generic names like 'utils.py' or 'helpers.py'.")
        print("   Instead, create focused modules (e.g. 'date_formatter.py', 'security_service.py').")
        return False
        
    return True

def check_required_directories():
    """
    Ensures that key project directories exist.
    """
    required = ["src", "tests", "specs", "temp"]
    missing = []
    
    for directory in required:
        if not os.path.exists(directory):
            missing.append(directory)
            
    if missing:
        print("\033[0;31m❌ ERROR: Required project directories are missing:\033[0m")
        for directory in missing:
            print(f"      - {directory}/")
        print("\n💡 Please initialize them or run 'make init-harness' to restore.")
        return False
        
    return True

def main():
    print("🔍 Validating project architecture & layout...")
    
    success = True
    
    print("   [1/2] Verifying core directories...")
    if not check_required_directories():
        success = False
        
    print("   [2/2] Scanning for forbidden generic file patterns...")
    if not check_forbidden_files():
        success = False
        
    if success:
        print("\033[0;32m✅ VALIDATION SUCCESSFUL: Project structure is clean and compliant!\033[0m")
        return 0
    else:
        print("\n\033[0;31m❌ VALIDATION FAILED: Structure corrections required.\033[0m")
        return 1

if __name__ == "__main__":
    sys.exit(main())
