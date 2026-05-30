"""
load_dharma_seed.py

Loads Buddhist/dharma terminology into FalkorDB.
Run once to bootstrap the dharma graph.

    python -m src.load_dharma_seed

Concepts span Sanskrit, Tibetan, Pali, Chinese, Tamil.
The seed data is in data/seed/dharma_concepts.json and
data/seed/dharma_edges.json.
"""

import json
import os
from src.graph import init_schema, upsert_concept, upsert_edge

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "seed")


def load_dharma():
    init_schema("dharma")

    concepts_path = os.path.join(SEED_DIR, "dharma_concepts.json")
    edges_path = os.path.join(SEED_DIR, "dharma_edges.json")

    with open(concepts_path, encoding="utf-8") as f:
        concepts = json.load(f)

    with open(edges_path, encoding="utf-8") as f:
        edges = json.load(f)

    print(f"Loading {len(concepts)} dharma concepts...")
    for c in concepts:
        upsert_concept("dharma", c)

    print(f"Loading {len(edges)} edges...")
    for e in edges:
        upsert_edge("dharma", e["source"], e["target"], rel=e.get("rel", "PREREQUISITE_OF"))

    print("Dharma seed loaded.")


if __name__ == "__main__":
    load_dharma()
