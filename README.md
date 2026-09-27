# GraphSWE-Gemma: Developer Agent & Paper Track Project

This repository contains the complete implementation, Google ADK submission package, benchmark harness, and formal research paper for the **Google - The Gemma 4 Developer Agent Paper Track** (and companion code agent competition).

---

## 🌟 Key Innovations
- **AST Multigraph Navigation:** Navigates NetworkX directed multigraphs with 256-dimensional symbol embeddings instead of dumping raw repository files into prompt windows.
- **Context Compaction:** Achieves **93.1% token compression** by extracting ego-induced caller/callee subgraphs around defect sites.
- **AST Verification Guardrails:** Deterministic in-memory diff application and Python AST validation to prevent syntax and indentation errors.
- **Google ADK 2.0 Compliance:** Fully structured with declarative YAML configs (`agent.yaml`, `sampling.yaml`, `prompts/`, `sub_agents/`, `skills/`).

---

## 📁 Repository Structure
```
gemma_developer_agent/
├── adk_agent/                 # Google ADK Submission directory
│   ├── agent.yaml             # Root ADK Agent configuration
│   ├── configs/sampling.yaml  # Sampling parameters (temperature, top_p)
│   ├── prompts/               # Prompt templates (system, localizer, patcher)
│   ├── sub_agents/            # Specialized sub-agents (localizer, verifier)
│   └── skills/                # ADK Skills (repo_graph_navigation)
│
├── src/                       # Core Python Framework
│   ├── graph_engine.py        # NetworkX multigraph & cosine embedding matcher
│   ├── diff_verifier.py       # In-memory patch applicator & AST syntax parser
│   ├── agent_runner.py        # Autonomous agent loop & tool dispatcher
│   └── evaluator.py           # Benchmark evaluator & metrics calculator
│
├── demo/                      # Demonstration & Benchmark Data
│   ├── mock_graph.json        # NetworkX AST multigraph matching competition schema
│   └── mock_tasks.jsonl       # Multi-task benchmark instances (FastAPI, Rich, Requests)
│
├── paper/                     # Research Paper & Kaggle Writeup
│   ├── KAGGLE_WRITEUP.md      # Ready-to-publish Kaggle writeup (<= 3,000 words)
│   ├── paper.tex              # Formal arXiv / NeurIPS LaTeX manuscript
│   └── references.bib         # Academic bibliography
│
├── run_demo.py                # 1-Click test & verification script
├── package_submission.py      # Creates submission.zip for Kaggle
└── requirements.txt           # Python dependencies
```

---

## 🚀 Quickstart

### 1. Run the Demo & Benchmark Harness
Verify the end-to-end graph navigation and AST verification pipeline:
```bash
python run_demo.py
```

### 2. Generate the Kaggle ADK `submission.zip`
Package the `adk_agent/` directory into a competition-ready zip archive:
```bash
python package_submission.py
```
This produces `submission.zip` containing `agent.yaml` at its root.
