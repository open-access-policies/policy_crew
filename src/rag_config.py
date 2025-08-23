"""Configuration loader for RAG tools with YAML support, validation, and environment overrides."""

import os
import yaml
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path

# Define the expected configuration structure for validation
REQUIRED_CONFIG_KEYS = {
    "paths": ["kb_dir", "index_dir", "results_dir"],
    "loader": ["globs", "exclude", "max_files"],
    "splitter": ["chunk_size", "chunk_overlap"],
    "embedder": ["backend", "model", "base_url", "use_gpu", "batch_size", "cosine_floor"],
    "vector_store": ["type", "persist"],
    "retriever": ["strategy", "k", "mmr_lambda"],
    "reranker": ["model", "device", "max_length", "batch_size"],
    "gating": ["tau", "delta", "ratio", "min_overlap", "keep_within", "top_k_return"],
    "preflight": ["force_cpu_embeddings", "force_cpu_reranker", "skip_ollama"]
}

def _load_config_from_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def _load_config_from_env() -> Optional[str]:
    """Check if RAG_CONFIG environment variable is set."""
    return os.getenv("RAG_CONFIG")

def _validate_config(config: Dict[str, Any]) -> None:
    """Validate that all required keys are present in config."""
    for section, keys in REQUIRED_CONFIG_KEYS.items():
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
        
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing required configuration key: {section}.{key}")

def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to config."""
    # Map env vars to config keys
    env_to_config_map = {
        "RAG_EMBEDDINGS_BACKEND": "embedder.backend",
        "RAG_EMBEDDINGS_MODEL": "embedder.model",
        "RAG_EMBEDDINGS_BASE_URL": "embedder.base_url",
        "RAG_EMBEDDINGS_GPU": "embedder.use_gpu",
        "RAG_EMBEDDINGS_BATCH_SIZE": "embedder.batch_size",
        "RAG_EMBEDDINGS_COSINE_FLOOR": "embedder.cosine_floor",
        "RAG_VECTOR_STORE_TYPE": "vector_store.type",
        "RAG_VECTOR_STORE_PERSIST": "vector_store.persist",
        "RAG_RETRIEVER_STRATEGY": "retriever.strategy",
        "RAG_RETRIEVER_K": "retriever.k",
        "RAG_RETRIEVER_MMR_LAMBDA": "retriever.mmr_lambda",
        "RAG_RERANKER_MODEL": "reranker.model",
        "RAG_RERANKER_DEVICE": "reranker.device",
        "RAG_RERANKER_MAX_LENGTH": "reranker.max_length",
        "RAG_RERANKER_BATCH_SIZE": "reranker.batch_size",
        "RAG_TAU": "gating.tau",
        "RAG_DELTA": "gating.delta",
        "RAG_RATIO": "gating.ratio",
        "RAG_MIN_OVERLAP": "gating.min_overlap",
        "RAG_KEEP_WITHIN": "gating.keep_within",
        "RAG_TOP_K_RETURN": "gating.top_k_return",
        "RAG_FORCE_CPU_EMBEDDINGS": "preflight.force_cpu_embeddings",
        "RAG_FORCE_CPU_RERANKER": "preflight.force_cpu_reranker",
        "RAG_SKIP_OLLAMA": "preflight.skip_ollama"
    }
    
    # Apply overrides
    for env_var, config_path in env_to_config_map.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            
            # Convert string values to appropriate types
            if config_path.endswith(".use_gpu") or config_path.endswith(".force_cpu_embeddings") or config_path.endswith(".force_cpu_reranker") or config_path.endswith(".skip_ollama"):
                # Boolean values
                if value.lower() in ("true", "1", "yes", "on"):
                    value = True
                elif value.lower() in ("false", "0", "no", "off"):
                    value = False
                else:
                    raise ValueError(f"Invalid boolean value for {env_var}: {value}")
            elif config_path.endswith(".chunk_size") or config_path.endswith(".chunk_overlap") or config_path.endswith(".batch_size") or config_path.endswith(".k") or config_path.endswith(".mmr_lambda") or config_path.endswith(".max_length") or config_path.endswith(".top_k_return"):
                # Numeric values
                try:
                    value = float(value) if '.' in value else int(value)
                except ValueError:
                    raise ValueError(f"Invalid numeric value for {env_var}: {value}")
            elif config_path.endswith(".cosine_floor") or config_path.endswith(".tau") or config_path.endswith(".delta") or config_path.endswith(".ratio") or config_path.endswith(".min_overlap") or config_path.endswith(".keep_within"):
                # Float values
                try:
                    value = float(value)
                except ValueError:
                    raise ValueError(f"Invalid numeric value for {env_var}: {value}")
            
            # Set the config value
            keys = config_path.split(".")
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
    
    return config

def _compute_config_sha(config: Dict[str, Any]) -> str:
    """Compute SHA256 hash of the config."""
    # Convert to JSON string and compute SHA256
    json_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

# Cache the loaded configuration
_config_cache = None
_config_sha_cache = None

def get_config() -> Dict[str, Any]:
    """Get the canonical configuration with environment overrides applied."""
    global _config_cache, _config_sha_cache
    
    if _config_cache is not None:
        return _config_cache
    
    # Determine config file path
    env_config_path = _load_config_from_env()
    if env_config_path:
        config_path = env_config_path
    else:
        config_path = "config/rag_config.yaml"
    
    # Validate that config file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load the config
    config = _load_config_from_file(config_path)
    
    # Validate the config
    _validate_config(config)
    
    # Apply environment overrides
    config = _apply_env_overrides(config)
    
    # Compute SHA256 of the effective config
    _config_sha_cache = _compute_config_sha(config)
    
    # Cache and return the config
    _config_cache = config
    return config

def get_config_sha() -> str:
    """Get the SHA256 hash of the effective configuration."""
    get_config()  # Ensure config is loaded and cached
    return _config_sha_cache

# Validate config at import time - this will now fail if any required keys are missing
try:
    get_config()
except Exception as e:
    raise ValueError(f"Configuration validation failed at import: {e}")