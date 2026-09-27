#!/usr/bin/env python3
"""
ADK Skill Script: graph_traversal.py
Enables autonomous agents inside the sandbox to traverse AST dependency graphs via CLI or import.
"""

import sys
import json
import argparse
import networkx as nx


def load_graph(graph_file: str) -> nx.MultiDiGraph:
    with open(graph_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    g = nx.MultiDiGraph()
    for node in data.get("nodes", []):
        g.add_node(node["id"], name=node.get("name", node["id"]), text=node.get("text", ""))
    for edge in data.get("edges", []):
        g.add_edge(edge["source"], edge["target"], type=edge.get("type", "calls"))
    return g


def main():
    parser = argparse.ArgumentParser(description="Traverse code multigraph.")
    parser.add_argument("--graph", required=True, help="Path to graph.json")
    parser.add_argument("--symbol", required=True, help="Symbol to inspect")
    parser.add_argument("--direction", choices=["in", "out", "both"], default="both")
    args = parser.parse_args()

    g = load_graph(args.graph)
    if args.symbol not in g:
        print(json.dumps({"error": f"Symbol '{args.symbol}' not found in graph."}))
        sys.exit(1)

    callers = [u for u, v, d in g.in_edges(args.symbol, data=True)]
    callees = [v for u, v, d in g.out_edges(args.symbol, data=True)]

    result = {
        "symbol": args.symbol,
        "callers": callers,
        "callees": callees
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
