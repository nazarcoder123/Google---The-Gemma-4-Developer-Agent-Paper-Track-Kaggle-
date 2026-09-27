---
name: repo_graph_navigation
description: Navigates AST call and dependency multigraphs to localize code defects and compact context for small local models.
version: 1.0.0
---

# Repository Graph Navigation Skill

This skill equips autonomous SWE agents with tools and heuristics to explore large codebases through precomputed AST dependency multigraphs and dense symbol embeddings.

## Key Capabilities
- **Semantic Anchor Querying**: Query dense 256-dim embeddings to locate initial candidate symbols.
- **Topological Traversal**: Traverse caller/callee edges without opening entire files.
- **Context Compactor**: Slice target function definitions into a token-budgeted prompt context.
