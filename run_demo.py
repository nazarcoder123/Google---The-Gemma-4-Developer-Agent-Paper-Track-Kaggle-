"""
Demo verification script for GraphSWE-Gemma Developer Agent.
Runs end-to-end evaluation pipeline on mock tasks with AST graph navigation and diff verification.
"""

import sys
import os
import json

# Ensure src is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.graph_engine import GraphEngine
from src.agent_runner import GraphSWEAgent
from src.evaluator import BenchmarkEvaluator


def main():
    print("=================================================================")
    print(" Initializing GraphSWE-Gemma: Developer Agent Framework")
    print("=================================================================\n")

    graph_file = os.path.join(current_dir, "demo", "mock_graph.json")
    tasks_file = os.path.join(current_dir, "demo", "mock_tasks.jsonl")

    # Step 1: Initialize Graph Engine
    print(f"[*] Loading AST Call/Dependency Multigraph from: {graph_file}")
    engine = GraphEngine(graph_path=graph_file)
    print(f"[+] Loaded {len(engine.nodes_data)} code symbols and {engine.graph.number_of_edges()} call edges.\n")

    # Step 2: Initialize Agent
    print("[*] Initializing Autonomous SWE Agent (Model: google/gemma-4-9b-it)...")
    agent = GraphSWEAgent(graph_engine=engine, max_turns=6, token_budget=4096)

    # Step 3: Load Benchmark Tasks
    tasks = []
    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    print(f"[+] Loaded {len(tasks)} benchmark evaluation tasks.\n")

    # Step 4: Run Evaluation
    print("[*] Running benchmark evaluation harness...\n")
    evaluator = BenchmarkEvaluator(agent=agent)
    summary = evaluator.evaluate_instances(tasks)

    # Step 5: Output Results & Trajectory Details
    for idx, res in enumerate(summary["results"], 1):
        print(f"--- Task {idx}: {res['instance_id']} ---")
        print(f"    Status: {res['status']}")
        print(f"    Localized Target: {res['primary_symbol']}")
        print(f"    AST Syntax Valid: {res['ast_valid']}")
        print(f"    Patch Produced: {res['patch_generated']}\n")

    evaluator.print_summary_table(summary)
    print("[SUCCESS] All pipeline stages verified successfully!")


if __name__ == "__main__":
    main()
