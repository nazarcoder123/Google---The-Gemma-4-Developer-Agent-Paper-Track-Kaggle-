"""
GraphEngine: High-Performance AST Call/Dependency Multigraph & Embedding Navigation
Powers semantic fault localization and context compaction for local Gemma developer agents.
"""

from typing import Dict, List, Optional, Any, Tuple
import json
import os
import numpy as np
import networkx as nx


class CodeNode:
    def __init__(self, node_id: str, name: str, text: str, node_type: str = "function"):
        self.id = node_id
        self.name = name
        self.text = text
        self.node_type = node_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "text": self.text,
            "node_type": self.node_type,
        }


class GraphEngine:
    def __init__(self, graph_path: Optional[str] = None, embeddings_path: Optional[str] = None):
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.nodes_data: Dict[str, CodeNode] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        self.symbol_list: List[str] = []
        self.embedding_matrix: Optional[np.ndarray] = None

        if graph_path and os.path.exists(graph_path):
            self.load_graph(graph_path)
        if embeddings_path and os.path.exists(embeddings_path):
            self.load_embeddings(embeddings_path)

    def load_graph(self, graph_path: str):
        """Loads NetworkX graph from Kaggle JSON multigraph schema."""
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.graph = nx.MultiDiGraph()
        self.nodes_data.clear()

        # Parse nodes
        for node in data.get("nodes", []):
            node_id = node.get("id")
            name = node.get("name", node_id)
            text = node.get("text", "")
            node_type = node.get("type", "symbol")
            code_node = CodeNode(node_id, name, text, node_type)
            self.nodes_data[node_id] = code_node
            self.graph.add_node(node_id, name=name, type=node_type)

        # Parse edges
        for edge in data.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            edge_type = edge.get("type", "calls")
            key = edge.get("key", 0)
            self.graph.add_edge(source, target, key=key, type=edge_type)

    def load_embeddings(self, embeddings_path: str):
        """Loads precomputed 256-dim symbol embeddings from .npz or .npy archive."""
        if embeddings_path.endswith(".npz"):
            npz_data = np.load(embeddings_path)
            self.symbol_list = []
            vectors = []
            for k in npz_data.files:
                vec = npz_data[k].astype(np.float32)
                # Normalize vector for fast cosine similarity
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                self.embeddings[k] = vec
                self.symbol_list.append(k)
                vectors.append(vec)
            if vectors:
                self.embedding_matrix = np.stack(vectors)
        elif embeddings_path.endswith(".json"):
            # Fallback for synthetic/mock data
            with open(embeddings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.symbol_list = []
            vectors = []
            for k, v in data.items():
                vec = np.array(v, dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                self.embeddings[k] = vec
                self.symbol_list.append(k)
                vectors.append(vec)
            if vectors:
                self.embedding_matrix = np.stack(vectors)

    def search_similar_code(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """Finds top-k most semantically similar code nodes using cosine distance."""
        if self.embedding_matrix is None or len(self.symbol_list) == 0:
            return []

        q_vec = query_vector.astype(np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self.embedding_matrix, q_vec)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            sym_id = self.symbol_list[idx]
            results.append({
                "symbol_id": sym_id,
                "similarity_score": float(scores[idx]),
                "name": self.nodes_data.get(sym_id).name if sym_id in self.nodes_data else sym_id,
                "snippet_preview": self.nodes_data[sym_id].text[:200] if sym_id in self.nodes_data else "",
            })
        return results

    def get_code_neighbors(self, symbol_id: str) -> Dict[str, List[Dict[str, str]]]:
        """Retrieves inbound callers and outbound referenced symbols."""
        if symbol_id not in self.graph:
            return {"callers": [], "callees": []}

        callers = []
        for src, _, edge_data in self.graph.in_edges(symbol_id, data=True):
            callers.append({"symbol": src, "relation": edge_data.get("type", "calls")})

        callees = []
        for _, tgt, edge_data in self.graph.out_edges(symbol_id, data=True):
            callees.append({"symbol": tgt, "relation": edge_data.get("type", "calls")})

        return {"callers": callers, "callees": callees}

    def get_code_subgraph(self, center_symbols: List[str], hops: int = 1, max_nodes: int = 15) -> nx.MultiDiGraph:
        """Extracts an ego-induced subgraph up to k hops centered around target nodes."""
        nodes_to_include = set(center_symbols)
        current_frontier = set(center_symbols)

        for _ in range(hops):
            next_frontier = set()
            for node in current_frontier:
                if node in self.graph:
                    next_frontier.update(self.graph.predecessors(node))
                    next_frontier.update(self.graph.successors(node))
            nodes_to_include.update(next_frontier)
            current_frontier = next_frontier
            if len(nodes_to_include) >= max_nodes:
                break

        # Trim if exceeds max_nodes
        nodes_list = list(nodes_to_include)[:max_nodes]
        return self.graph.subgraph(nodes_list).copy()

    def compact_subgraph_context(self, center_symbol: str, hops: int = 1, max_tokens: int = 2500) -> str:
        """
        Synthesizes a minimal, budget-aware context representation for Gemma.
        Places center target function first, followed by caller signatures and callee interfaces.
        """
        if center_symbol not in self.nodes_data:
            return f"# Symbol '{center_symbol}' not found in graph."

        center_node = self.nodes_data[center_symbol]
        output_blocks = [
            f"# === PRIMARY FOCUS SYMBOL: {center_symbol} ===",
            center_node.text.strip(),
            "\n# === CONNECTED GRAPH CONTEXT ==="
        ]

        neighbors = self.get_code_neighbors(center_symbol)
        
        # Add callee summaries
        output_blocks.append("# Called Dependencies:")
        for callee in neighbors["callees"][:5]:
            tgt_id = callee["symbol"]
            if tgt_id in self.nodes_data:
                # Add first 10 lines of callee definition for signature/type info
                snippet_lines = self.nodes_data[tgt_id].text.strip().splitlines()[:8]
                output_blocks.append(f"## {tgt_id} ({callee['relation']}):\n" + "\n".join(snippet_lines))

        # Add caller summaries
        output_blocks.append("\n# Upstream Callers:")
        for caller in neighbors["callers"][:3]:
            src_id = caller["symbol"]
            if src_id in self.nodes_data:
                snippet_lines = self.nodes_data[src_id].text.strip().splitlines()[:5]
                output_blocks.append(f"## {src_id} ({caller['relation']}):\n" + "\n".join(snippet_lines))

        context_str = "\n".join(output_blocks)
        return context_str
