#!/usr/bin/env python3
"""Test script to verify config integration works correctly."""

import os
import sys

# Add src directory to path
sys.path.insert(0, '/Users/seantodd/Projects/policy_crew/src')

def test_imports():
    """Test that imports work without errors."""
    print("Testing imports...")
    
    try:
        from src.retrieval_tool import RetrievalTool
        from src.reranking_tool import ReRankingTool
        print("✅ Imports successful")
        
        # Test that config is loaded and SHA is computed
        from src.rag_config import get_config_sha
        sha = get_config_sha()
        print(f"✅ Config SHA computed: {sha[:16]}...")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_config_values():
    """Test that config values are correctly loaded."""
    print("Testing config values...")
    
    try:
        from src.rag_config import get_config
        
        config = get_config()
        
        # Test some key values
        assert config['embedder']['model'] == 'nomic-embed-text'
        assert config['embedder']['use_gpu'] == False
        assert config['retriever']['k'] == 20
        assert config['gating']['tau'] == 0.50
        
        print("✅ Config values are correct")
        return True
    except Exception as e:
        print(f"❌ Config value test failed: {e}")
        return False

def test_env_override():
    """Test that environment overrides work."""
    print("Testing env overrides...")
    
    try:
        # Set an environment variable
        os.environ['RAG_TAU'] = '0.30'
        
        from src.rag_config import get_config
        config = get_config()
        
        # Check that the override was applied
        assert config['gating']['tau'] == 0.30
        
        # Clean up
        del os.environ['RAG_TAU']
        
        print("✅ Environment override works")
        return True
    except Exception as e:
        print(f"❌ Environment override test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Running config integration tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_values,
        test_env_override
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("🔥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())