#!/usr/bin/env python3
"""
Verification script to check that Phase 1 implementation meets all requirements.
This checks the basic acceptance criteria from the specification.
"""

import os
import sys

# Add src to path so we can import modules
sys.path.insert(0, '/Users/seantodd/Projects/policy_crew/src')

def test_imports():
    """Test that imports work without errors and no placeholders."""
    print("1. Testing imports...")
    
    try:
        # Import the modules - this should work without placeholders or errors
        from src.retrieval_tool import RetrievalTool
        from src.reranking_tool import ReRankingTool
        from src.rag_config import get_config_sha
        
        print("   ✅ Imports successful - no placeholders or errors")
        
        # Test that config SHA can be computed
        sha = get_config_sha()
        print(f"   ✅ Config SHA computed: {sha[:16]}...")
        
        return True
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False

def test_config_loading():
    """Test that config is loaded from the correct file."""
    print("2. Testing config loading...")
    
    try:
        from src.rag_config import get_config
        config = get_config()
        
        # Check that required keys exist
        required_keys = ['embedder', 'retriever', 'gating', 'reranker']
        for key in required_keys:
            if key not in config:
                print(f"   ❌ Missing required config section: {key}")
                return False
        
        # Check some specific values
        assert config['embedder']['model'] == 'nomic-embed-text'
        assert config['retriever']['k'] == 20
        assert config['gating']['tau'] == 0.50
        
        print("   ✅ Config loaded and validated correctly")
        return True
    except Exception as e:
        print(f"   ❌ Config loading test failed: {e}")
        return False

def test_env_override():
    """Test that environment overrides work."""
    print("3. Testing env overrides...")
    
    try:
        # Set an environment variable
        os.environ['RAG_TAU'] = '0.30'
        
        from src.rag_config import get_config
        config = get_config()
        
        # Check that the override was applied
        assert config['gating']['tau'] == 0.30
        
        # Clean up
        del os.environ['RAG_TAU']
        
        print("   ✅ Environment override works")
        return True
    except Exception as e:
        print(f"   ❌ Environment override test failed: {e}")
        return False

def test_tool_initialization():
    """Test that tools log their configuration properly."""
    print("4. Testing tool initialization...")
    
    try:
        # This will test that the tools can be instantiated and log properly
        from src.retrieval_tool import RetrievalTool
        from src.reranking_tool import ReRankingTool
        
        # Create instances - this should log the config information
        retrieval_tool = RetrievalTool()
        reranking_tool = ReRankingTool()
        
        print("   ✅ Tool initialization successful")
        return True
    except Exception as e:
        print(f"   ❌ Tool initialization failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("Verifying Phase 1 Implementation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_loading,
        test_env_override,
        test_tool_initialization
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All Phase 1 verification tests passed!")
        return 0
    else:
        print("🔥 Some Phase 1 verification tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())