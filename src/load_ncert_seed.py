"""
load_ncert_seed.py

Loads a seed set of NCERT concepts into FalkorDB.
Run once to bootstrap the ncert graph.

    python -m src.load_ncert_seed

The seed data lives in data/seed/ncert_concepts.json and
data/seed/ncert_edges.json. You can extend those files and rerun.
"""

import json
import os
from src.graph import init_schema, upsert_concept, upsert_edge

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "seed")


def load_ncert():
    init_schema("ncert")

    concepts_path = os.path.join(SEED_DIR, "ncert_concepts.json")
    edges_path = os.path.join(SEED_DIR, "ncert_edges.json")

    with open(concepts_path, encoding="utf-8") as f:
        concepts = json.load(f)

    with open(edges_path, encoding="utf-8") as f:
        edges = json.load(f)

    print(f"Loading {len(concepts)} concepts...")
    for c in concepts:
        upsert_concept("ncert", c)

    print(f"Loading {len(edges)} prerequisite edges...")
    for e in edges:
        upsert_edge("ncert", e["source"], e["target"], rel=e.get("rel", "PREREQUISITE_OF"))

    print("NCERT seed loaded.")


if __name__ == "__main__":
    load_ncert()
