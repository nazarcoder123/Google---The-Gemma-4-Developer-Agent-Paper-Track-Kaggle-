#!/usr/bin/env python3
"""
ADK Skill Script: context_compactor.py
Compact multi-file repo context into a tight token budget for Gemma.
"""

import sys
import json
import argparse


def main():
    parser = argparse.ArgumentParser(description="Compact context around target symbol.")
    parser.add_argument("--graph", required=True, help="Path to graph.json")
    parser.add_argument("--symbol", required=True, help="Target symbol")
    parser.add_argument("--max-lines", type=int, default=100)
    args = parser.parse_args()

    with open(args.graph, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = {n["id"]: n for n in data.get("nodes", [])}
    if args.symbol not in nodes:
        print(f"# Symbol '{args.symbol}' not found.")
        return

    target = nodes[args.symbol]
    print(f"# Target: {args.symbol}")
    print(target.get("text", "")[: args.max_lines * 80])


if __name__ == "__main__":
    main()
