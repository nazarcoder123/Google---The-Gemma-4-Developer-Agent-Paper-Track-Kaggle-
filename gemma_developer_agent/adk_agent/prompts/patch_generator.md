### Patch Synthesis Directive

You are provided with:
1. The problem statement.
2. The localized target symbol definition and its context subgraph.
3. Reproduction trace or unit test specifications.

Requirements for Unified Diff Generation:
- Output MUST be valid unified diff format (`diff --git a/... b/...`).
- Only modify lines directly responsible for the defect.
- Maintain identical indentation and code style.
- Do NOT rewrite or reformat unmodified methods.
- Ensure all variable references and imports are valid.
- Wrap the diff cleanly within ````diff ... ```` markdown blocks.
