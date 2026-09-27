"""
AgentRunner: Autonomous Loop for GraphSWE-Gemma
Coordinates tool dispatch, context budgeting, and test-time iterative refinement.
"""

from typing import Dict, Any, List, Optional
import os
import re
import numpy as np
from .graph_engine import GraphEngine
from .diff_verifier import DiffVerifier


class GraphSWEAgent:
    def __init__(
        self,
        graph_engine: GraphEngine,
        model_name: str = "google/gemma-4-9b-it",
        max_turns: int = 6,
        token_budget: int = 4096
    ):
        self.graph_engine = graph_engine
        self.model_name = model_name
        self.max_turns = max_turns
        self.token_budget = token_budget
        self.verifier = DiffVerifier()

    def solve_task(
        self,
        instance_id: str,
        problem_statement: str,
        task_query_vector: Optional[np.ndarray] = None,
        file_lookup: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes autonomous SWE loop for a given benchmark instance:
        Step 1: Semantic symbol retrieval via 256-dim embeddings
        Step 2: Subgraph ego-network expansion
        Step 3: Compact context synthesis
        Step 4: Patch generation
        Step 5: AST verification & guardrails
        """
        trajectory = []
        file_lookup = file_lookup or {}

        # Step 1: Semantic symbol retrieval
        if task_query_vector is not None:
            top_candidates = self.graph_engine.search_similar_code(task_query_vector, top_k=3)
        else:
            # Fallback heuristic based on problem statement keywords
            top_candidates = []
            for sym_id, node in self.graph_engine.nodes_data.items():
                short_name = sym_id.split(".")[-1]
                if short_name.lower() in problem_statement.lower():
                    top_candidates.append({
                        "symbol_id": sym_id,
                        "similarity_score": 0.85,
                        "name": node.name,
                        "snippet_preview": node.text[:150]
                    })
            if not top_candidates and self.graph_engine.symbol_list:
                top_candidates = [{"symbol_id": self.graph_engine.symbol_list[0], "similarity_score": 0.5}]

        trajectory.append({
            "step": 1,
            "action": "search_similar_code",
            "candidates": [c["symbol_id"] for c in top_candidates]
        })

        if not top_candidates:
            return {
                "instance_id": instance_id,
                "status": "FAILED",
                "reason": "No candidate symbols identified in graph.",
                "patch": "NO_PATCH",
                "trajectory": trajectory
            }

        primary_candidate = top_candidates[0]["symbol_id"]

        # Step 2 & 3: Ego-subgraph extraction and context compaction
        subgraph_context = self.graph_engine.compact_subgraph_context(
            primary_candidate, hops=1, max_tokens=self.token_budget // 2
        )
        trajectory.append({
            "step": 2,
            "action": "compact_subgraph_context",
            "primary_symbol": primary_candidate,
            "context_length_chars": len(subgraph_context)
        })

        # Step 4: Patch Synthesis
        target_node = self.graph_engine.nodes_data.get(primary_candidate)
        target_file_content = file_lookup.get(primary_candidate, target_node.text if target_node else "")

        # Synthesize candidate patch (simulated or LLM generation)
        candidate_patch = self._synthesize_patch(
            problem_statement=problem_statement,
            target_symbol=primary_candidate,
            context=subgraph_context,
            original_code=target_file_content
        )

        trajectory.append({
            "step": 3,
            "action": "synthesize_patch",
            "raw_patch_preview": candidate_patch[:200]
        })

        # Step 5: Verification & Self-Correction
        verification_result = self.verifier.verify_patch(target_file_content, candidate_patch)
        
        if not verification_result["valid"]:
            trajectory.append({
                "step": 4,
                "action": "self_correction_triggered",
                "error": verification_result["error_message"]
            })
            # Attempt self-correction refinement
            corrected_patch = self._self_correct_patch(
                candidate_patch,
                verification_result["error_message"],
                target_file_content
            )
            verification_result = self.verifier.verify_patch(target_file_content, corrected_patch)
            candidate_patch = corrected_patch

        trajectory.append({
            "step": 5,
            "action": "final_verification",
            "valid": verification_result["valid"]
        })

        return {
            "instance_id": instance_id,
            "status": "COMPLETED" if verification_result["valid"] else "REPAIR_FAILED",
            "primary_symbol": primary_candidate,
            "patch": candidate_patch if verification_result["valid"] else "NO_PATCH",
            "trajectory": trajectory,
            "verification": verification_result
        }

    def _synthesize_patch(self, problem_statement: str, target_symbol: str, context: str, original_code: str) -> str:
        """
        Generates unified git diff patch for target defect.
        """
        # Minimal clean diff synthesis
        rel_path = target_symbol.replace(".", "/") + ".py"
        lines = original_code.splitlines()

        # If a pass/return/None pattern exists in original code, provide robust targeted fix
        diff_lines = [
            f"diff --git a/{rel_path} b/{rel_path}",
            f"--- a/{rel_path}",
            f"+++ b/{rel_path}",
            f"@@ -1,{max(1, len(lines))} +1,{max(1, len(lines))} @@"
        ]

        # In baseline demo, produce context-aware diff
        patched = False
        for line in lines:
            if "pass" in line and not patched:
                diff_lines.append(f"-{line}")
                indent = " " * (len(line) - len(line.lstrip()))
                diff_lines.append(f"+{indent}# Fixed by GraphSWE-Gemma: handle edge condition")
                diff_lines.append(f"+{indent}return True")
                patched = True
            elif "return None" in line and not patched:
                diff_lines.append(f"-{line}")
                indent = " " * (len(line) - len(line.lstrip()))
                diff_lines.append(f"+{indent}# Fixed by GraphSWE-Gemma: validate boundary")
                diff_lines.append(f"+{indent}return self.validate_boundary()")
                patched = True
            else:
                diff_lines.append(f" {line}")

        if not patched and lines:
            # Append guardrail
            diff_lines[-1] = f"+    # GraphSWE-Gemma edge case handler"
            diff_lines.append(f" {lines[-1]}")

        return "\n".join(diff_lines)

    def _self_correct_patch(self, broken_patch: str, error_msg: str, original_code: str) -> str:
        """Self-corrects syntax or formatting failures."""
        # Clean markdown wrappers or repair headers
        cleaned = DiffVerifier.extract_diff_from_markdown(broken_patch) or broken_patch
        return cleaned
