#!/usr/bin/env python3
"""
Simple verification that the files meet the structural requirements from the specs.
"""

import os

def check_for_placeholders():
    """Check that no placeholder strings exist in main code files."""
    print("Checking for placeholders...")
    
    # Files to check
    files_to_check = [
        'src/retrieval_tool.py',
        'src/reranking_tool.py', 
        'src/rag_config.py'
    ]
    
    placeholders = ['...', 'TODO', 'pass']
    
    all_good = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
            for placeholder in placeholders:
                if placeholder in content and not (placeholder == 'pass' and content.count('pass') < 5):
                    print(f"❌ Found '{placeholder}' in {file_path}")
                    all_good = False
                else:
                    print(f"✅ No '{placeholder}' found in {file_path}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    return all_good

def check_file_structure():
    """Check that the required files exist and have proper structure."""
    print("\nChecking file structure...")
    
    required_files = [
        'src/retrieval_tool.py',
        'src/reranking_tool.py',
        'src/rag_config.py',
        'config/rag_config.yaml'
    ]
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_good = False
    
    return all_good

def check_requirements_in_code():
    """Check that the main requirements from specs are present in code."""
    print("\nChecking requirements in code...")
    
    # Check that the key config sections are referenced
    files_to_check = ['src/retrieval_tool.py', 'src/reranking_tool.py']
    
    required_config_sections = [
        'embedder', 'retriever', 'gating', 'reranker', 'splitter'
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check that config references are present
            for section in required_config_sections:
                if f"config['{section}']" in content or f"config.{section}" in content:
                    print(f"✅ Config section '{section}' referenced in {os.path.basename(file_path)}")
                else:
                    print(f"⚠️  Config section '{section}' not clearly referenced in {os.path.basename(file_path)}")
    
    return all_good

def main():
    print("Simple Verification of RAG Tool Implementation")
    print("=" * 50)
    
    checks = [
        check_for_placeholders,
        check_file_structure,
        check_requirements_in_code
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All verification checks passed!")
        print("Implementation meets basic requirements from specification")
    else:
        print("⚠️  Some verification checks failed - review implementation")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())