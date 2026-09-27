"""
DiffVerifier: AST Syntax & Unified Patch Validator
Ensures generated git patches are syntactically sound and cleanly applicable before running sandbox execution.
"""

from typing import Dict, Any, Tuple, Optional
import ast
import re


class DiffVerifier:
    @staticmethod
    def extract_diff_from_markdown(text: str) -> Optional[str]:
        """Extracts diff block from markdown triple backticks if present."""
        match = re.search(r"```(?:diff)?\s*\n(diff --git[\s\S]*?)```", text)
        if match:
            return match.group(1).strip()
        
        # Check without diff --git header
        match_simple = re.search(r"```(?:diff)?\s*\n(--- [\s\S]*?)```", text)
        if match_simple:
            return match_simple.group(1).strip()

        # If already raw diff
        if text.strip().startswith("diff --git") or text.strip().startswith("---"):
            return text.strip()

        return None

    @staticmethod
    def validate_python_syntax(code_string: str) -> Tuple[bool, Optional[str]]:
        """Parses Python source using AST to ensure zero syntax or indentation errors."""
        try:
            ast.parse(code_string)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"
        except Exception as e:
            return False, f"ParsingError: {str(e)}"

    @staticmethod
    def apply_unified_diff(original_text: str, patch_text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Applies a unified patch to original text in-memory.
        Returns: (success, resulting_text, error_message)
        """
        lines = original_text.splitlines()
        patch_lines = patch_text.splitlines()

        hunk_header_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
        
        result_lines = list(lines)
        offset = 0
        i = 0

        while i < len(patch_lines):
            line = patch_lines[i]
            match = hunk_header_re.match(line)
            if not match:
                i += 1
                continue

            orig_start = int(match.group(1)) - 1  # 0-indexed
            orig_count = int(match.group(2)) if match.group(2) else 1

            i += 1
            hunk_orig = []
            hunk_new = []

            while i < len(patch_lines) and not patch_lines[i].startswith("@@"):
                pline = patch_lines[i]
                if pline.startswith(" "):
                    hunk_orig.append(pline[1:])
                    hunk_new.append(pline[1:])
                elif pline.startswith("-"):
                    hunk_orig.append(pline[1:])
                elif pline.startswith("+"):
                    hunk_new.append(pline[1:])
                i += 1

            adj_start = orig_start + offset
            
            # Verify slice
            target_slice = result_lines[adj_start : adj_start + len(hunk_orig)]
            if target_slice != hunk_orig:
                # Fuzzy matching or line drift
                # Attempt to find hunk_orig nearby
                found_idx = -1
                search_radius = 5
                low = max(0, adj_start - search_radius)
                high = min(len(result_lines) - len(hunk_orig) + 1, adj_start + search_radius)
                for test_idx in range(low, high):
                    if result_lines[test_idx : test_idx + len(hunk_orig)] == hunk_orig:
                        found_idx = test_idx
                        break

                if found_idx == -1:
                    return False, original_text, f"Hunk at line {orig_start+1} failed to match target text."
                adj_start = found_idx

            # Replace slice
            result_lines[adj_start : adj_start + len(hunk_orig)] = hunk_new
            offset += (len(hunk_new) - len(hunk_orig))

        modified_code = "\n".join(result_lines)
        return True, modified_code, None

    @classmethod
    def verify_patch(cls, original_file_content: str, patch_str: str) -> Dict[str, Any]:
        """
        End-to-end verification pipeline:
        1. Formats patch
        2. Applies patch in memory
        3. AST parses patched result
        """
        extracted = cls.extract_diff_from_markdown(patch_str) or patch_str
        applied_ok, new_code, apply_err = cls.apply_unified_diff(original_file_content, extracted)
        if not applied_ok:
            return {
                "valid": False,
                "error_stage": "patch_application",
                "error_message": apply_err,
                "patch": extracted
            }

        ast_ok, ast_err = cls.validate_python_syntax(new_code)
        if not ast_ok:
            return {
                "valid": False,
                "error_stage": "ast_validation",
                "error_message": ast_err,
                "patch": extracted
            }

        return {
            "valid": True,
            "error_stage": None,
            "error_message": None,
            "patched_content": new_code,
            "patch": extracted
        }
