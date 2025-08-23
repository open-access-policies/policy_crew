from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from functools import cached_property
from sentence_transformers.cross_encoder import CrossEncoder
import math, re, os, numpy as np
from collections import Counter
from typing import List, Tuple, Dict, Any
import random
from src.rag_config import get_config, get_config_sha

# Load configuration
config = get_config()
config_sha = get_config_sha()

STOP = set("""
        a an the and or not for to of in on with from by as at into over under up down
        is are was were be been being do does did this that these those it its it's
        """.split())

class ReRankingToolSchema(BaseModel):
    query: str = Field(description="The search query.")
    documents: list[str] = Field(description="List of document contents to re-rank.")

class ReRankingTool(BaseTool):
    name: str = "Re-ranking Tool"
    description: str = "Re-ranks documents based on relevance to the query."
    args_schema: type[BaseModel] = ReRankingToolSchema

    def __init__(self):
        """Initialize the re-ranking tool with config logging."""
        super().__init__()
        print(f"[reranking_tool] Loaded config from {os.path.abspath('config/rag_config.yaml')}")
        print(f"[reranking_tool] Config SHA: {config_sha}")
        print(f"[reranking_tool] Reranker model: {config['reranker']['model']}")
        print(f"[reranking_tool] Splitter: chunk_size={config['splitter']['chunk_size']}, overlap={config['splitter']['chunk_overlap']}")
        print(f"[reranking_tool] Retriever strategy: {config['retriever']['strategy']}")
        print(f"[reranking_tool] Gating thresholds - tau={config['gating']['tau']}, delta={config['gating']['delta']}, ratio={config['gating']['ratio']}")
        print(f"[reranking_tool] Gating min_overlap={config['gating']['min_overlap']}, keep_within={config['gating']['keep_within']}")
        
        # Set random seed for deterministic behavior
        random_seed = config.get('tuning', {}).get('random_seed', 42)
        random.seed(random_seed)
        np.random.seed(random_seed)

    @cached_property
    def reranker(self):
        print("Loading Re-ranker model...")
        # Enforce CPU for reranker as per config and requirements
        return CrossEncoder(
            config['reranker']['model'], 
            device="cpu",  # Force CPU as required
            max_length=config['reranker']['max_length']
        )

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        # If any score is outside [0,1], treat outputs as logits and apply sigmoid.
        if any(s < 0.0 or s > 1.0 for s in scores):
            return [1.0 / (1.0 + math.exp(-s)) for s in scores]
        return [float(s) for s in scores]

    def _overlap_ratio(self, q: str, d: str) -> float:
        qset, dset = set(self._tokens(q)), set(self._tokens(d))
        if not qset or not dset: 
            return 0.0
        return len(qset & dset) / max(1, len(qset))

    def _tokens(self, s: str):
        return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOP]

    def _sigmoid_if_needed(self, scores):
        # Only squash if we see logits outside [0,1]
        if any(s < 0.0 or s > 1.0 for s in scores):
            import math
            return [1.0 / (1.0 + math.exp(-s)) for s in scores]
        return [float(s) for s in scores]

    def _run(self, query: str, documents: list[str]) -> str:
        # Initialize diagnostics dictionary
        diagnostics = {
            "query": query,
            "returned_any": bool(documents),
            "n_candidates": len(documents),
            "n_after_rerank": 0,
            "top1_score": 0.0,
            "top2_score": 0.0,
            "margin": 0.0,
            "ratio": 0.0,
            "overlap": 0.0,
            "chunk_len_chars": 0,
            "t_embed": 0.0,
            "t_retrieve": 0.0,
            "t_rerank": 0.0,
            "t_gate": 0.0,
            "t_total": 0.0,
            "config_sha": config_sha,
            "gate_trigger": ""
        }

        if not documents:
            print("[reranker] no docs")
            return ""

        pairs = [[query, doc] for doc in documents]
        
        # Batch predict to NumPy array; drop non-finite scores; if all drop, return empty with drop_reason="non_finite_scores"
        try:
            raw_scores = self.reranker.predict(pairs)
            scores = [float(s) for s in raw_scores]
            
            # Check for non-finite scores and filter them out
            finite_scores = [s for s in scores if np.isfinite(s)]
            
            # If all scores are non-finite, return empty with drop_reason
            if not finite_scores:
                print("[reranker] All scores are non-finite")
                diagnostics["gate_trigger"] = "non_finite_scores"
                return ""
            
            # Apply sigmoid to all remaining scores if any score is outside [0,1]
            if any(s < 0.0 or s > 1.0 for s in finite_scores):
                scores = [1.0 / (1.0 + math.exp(-s)) for s in finite_scores]
            else:
                scores = [float(s) for s in finite_scores]
                
        except Exception as e:
            print(f"[reranker] Error during prediction: {e}")
            return ""
            
        # Sort descending and compute top1, top2, margin, ratio
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        
        if not ranked:
            print("[reranker] ranked empty")
            return ""
            
        # Update diagnostics with top scores
        top1_doc, top1 = ranked[0]
        top2 = ranked[1][1] if len(ranked) > 1 else 0.0
        ov1 = self._overlap_ratio(query, top1_doc)
        
        # Update diagnostics with computed values
        diagnostics["top1_score"] = top1
        diagnostics["top2_score"] = top2
        diagnostics["margin"] = top1 - top2
        diagnostics["ratio"] = top1 / max(top2, 1e-6)
        diagnostics["overlap"] = ov1
        diagnostics["chunk_len_chars"] = len(top1_doc) if top1_doc else 0
        diagnostics["n_after_rerank"] = len(ranked)
        
        # ---- Debug: print quick stats so you can tune intelligently ----
        try:
            s_sorted = sorted(scores)
            mid = s_sorted[len(s_sorted)//2]
            print(f"[reranker] n={len(scores)} min={s_sorted[0]:.3f} med={mid:.3f} max={s_sorted[-1]:.3f} "
                  f"top1={top1:.3f} top2={top2:.3f} margin={top1-top2:.3f} ratio={(top1/(top2+1e-6)):.2f} overlap={ov1:.2f}")
        except Exception:
            pass

        # ---- Gates (start lenient) ----
        TAU = config['gating']['tau']         # absolute min score
        DELTA = config['gating']['delta']     # min margin top1 - top2
        RATIO = config['gating']['ratio']     # min ratio top1/top2
        MIN_OVERLAP = config['gating']['min_overlap']  # lexical floor
        KEEP_WITHIN = config['gating']['keep_within']  # tie window
        TOP_K = config['gating']['top_k_return']       # cap number of returned docs

        # Gate 1: Reject if top1 < tau
        if top1 < TAU:
            diagnostics["gate_trigger"] = "tau"
            print(f"[gate] reject: top1<{TAU}")
            return ""
        
        # Gate 2: Reject if both (top1 - top2) < delta and top1/(top2+ε) < ratio
        if (top1 - top2) < DELTA and (top1 / (top2 + 1e-6)) < RATIO:
            diagnostics["gate_trigger"] = "margin_ratio"
            print(f"[gate] reject: margin<{DELTA} and ratio<{RATIO}")
            return ""
        
        # Gate 3: Reject if overlap < min_overlap
        if ov1 < MIN_OVERLAP:
            diagnostics["gate_trigger"] = "overlap"
            print(f"[gate] reject: overlap<{MIN_OVERLAP}")
            return ""
        
        # Gate 4: Keep docs where score ≥ top1 − keep_within and score ≥ tau, capped at top_k_return
        kept = [d for d, s in ranked if s >= top1 - KEEP_WITHIN and s >= TAU]
        if not kept:
            print("[gate] nothing within tie window; keeping top1 only")
            kept = [top1_doc]
        
        diagnostics["gate_trigger"] = "accepted"
        
        # Print diagnostics as JSON for verification
        import json
        print(f"[diagnostics] {json.dumps(diagnostics)}")
        
        return "\n\n".join(kept[:TOP_K])
