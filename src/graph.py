"""
graph.py

FalkorDB schema and operations for concept graphs.

Two named graphs are supported:
  - "ncert"  : NCERT school curriculum concepts
  - "dharma" : Buddhist/dharma terminology across traditions

Node labels:
  - Concept  : a single concept/term
  - Subject  : Physics, Mathematics, Dharma, etc.

Edge types:
  - PREREQUISITE_OF : source must be learned before target
  - RELATED_TO      : loosely related, no strict ordering
  - TRANSLATION_OF  : same concept in a different language/tradition

Properties on Concept nodes:
  name_en      : canonical English name
  name_hi      : Hindi (optional)
  name_ta      : Tamil (optional)
  name_te      : Telugu (optional)
  name_bn      : Bengali (optional)
  name_sa      : Sanskrit (optional, dharma graph)
  name_bo      : Tibetan (optional, dharma graph)
  name_pi      : Pali (optional, dharma graph)
  name_zh      : Chinese (optional, dharma graph)
  subject      : subject/domain string
  grade        : school grade (ncert only, int)
  chapter      : chapter number (ncert only, int)
  tradition    : Buddhist tradition (dharma only, e.g. "Theravada", "Tibetan")
"""

import os
from falkordb import FalkorDB
from dotenv import load_dotenv

load_dotenv()

FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", 6379))


def get_db() -> FalkorDB:
    return FalkorDB(host=FALKORDB_HOST, port=FALKORDB_PORT)


def get_graph(graph_name: str = "ncert"):
    db = get_db()
    return db.select_graph(graph_name)


# ---------------------------------------------------------------------------
# Schema initialisation (idempotent)
# ---------------------------------------------------------------------------

def init_schema(graph_name: str = "ncert"):
    """Create indexes. Safe to call multiple times."""
    g = get_graph(graph_name)
    try:
        g.query("CREATE INDEX FOR (c:Concept) ON (c.name_en)")
    except Exception:
        pass  # index already exists


# ---------------------------------------------------------------------------
# Node operations
# ---------------------------------------------------------------------------

def upsert_concept(graph_name: str, props: dict) -> None:
    """
    Insert or update a Concept node. props must include 'name_en'.
    All other language fields are optional.
    """
    g = get_graph(graph_name)
    name_en = props["name_en"]

    # Build SET clause dynamically from provided props
    set_parts = []
    params = {"name_en": name_en}
    for key, val in props.items():
        set_parts.append(f"c.{key} = ${key}")
        params[key] = val

    set_clause = ", ".join(set_parts)
    query = (
        "MERGE (c:Concept {name_en: $name_en}) "
        f"SET {set_clause}"
    )
    g.query(query, params)


def upsert_edge(graph_name: str, src_en: str, tgt_en: str, rel: str = "PREREQUISITE_OF", props: dict = None) -> None:
    """
    Create a directed edge between two Concept nodes by their English names.
    rel: PREREQUISITE_OF | RELATED_TO | TRANSLATION_OF
    """
    g = get_graph(graph_name)
    params = {"src": src_en, "tgt": tgt_en}

    prop_str = ""
    if props:
        prop_items = ", ".join(f"{k}: ${k}" for k in props)
        prop_str = f" {{{prop_items}}}"
        params.update(props)

    query = (
        f"MATCH (a:Concept {{name_en: $src}}), (b:Concept {{name_en: $tgt}}) "
        f"MERGE (a)-[r:{rel}{prop_str}]->(b)"
    )
    g.query(query, params)


# ---------------------------------------------------------------------------
# Query operations
# ---------------------------------------------------------------------------

def get_prerequisites(graph_name: str, name_en: str, depth: int = 3) -> list[dict]:
    """
    Return all concepts that are prerequisites of name_en, up to given depth.
    Returns list of dicts with concept properties.
    """
    g = get_graph(graph_name)
    query = (
        f"MATCH (prereq:Concept)-[:PREREQUISITE_OF*1..{depth}]->(c:Concept {{name_en: $name}}) "
        "RETURN DISTINCT prereq"
    )
    result = g.query(query, {"name": name_en})
    return [row[0].properties for row in result.result_set]


def get_dependents(graph_name: str, name_en: str, depth: int = 3) -> list[dict]:
    """
    Return concepts that require name_en as a prerequisite (i.e. what you can
    learn AFTER mastering this concept).
    """
    g = get_graph(graph_name)
    query = (
        f"MATCH (c:Concept {{name_en: $name}})-[:PREREQUISITE_OF*1..{depth}]->(dep:Concept) "
        "RETURN DISTINCT dep"
    )
    result = g.query(query, {"name": name_en})
    return [row[0].properties for row in result.result_set]


def get_learning_path(graph_name: str, from_en: str, to_en: str) -> list[dict]:
    """
    Shortest prerequisite path via Python-side BFS.
    FalkorDB shortestPath has limitations so we BFS manually.
    """
    g = get_graph(graph_name)

    frontier = [[from_en]]
    visited = {from_en}

    while frontier:
        next_frontier = []
        for path in frontier:
            current = path[-1]
            result = g.query(
                "MATCH (a:Concept)-[:PREREQUISITE_OF]->(b:Concept) "
                "WHERE a.name_en = $name "
                "RETURN b.name_en, b",
                {"name": current}
            )
            for row in result.result_set:
                neighbor_name = row[0]
                if neighbor_name in visited:
                    continue
                new_path = path + [neighbor_name]
                if neighbor_name == to_en:
                    props_path = []
                    for n in new_path:
                        r = g.query(
                            "MATCH (c:Concept) WHERE c.name_en = $n RETURN c",
                            {"n": n}
                        )
                        if r.result_set:
                            props_path.append(r.result_set[0][0].properties)
                    return props_path
                visited.add(neighbor_name)
                next_frontier.append(new_path)
        frontier = next_frontier
        if not frontier or len(frontier[0]) > 10:
            break
    return []


def fuzzy_match(graph_name: str, term: str, lang_field: str = "name_en") -> list[dict]:
    """
    Search across all language fields and aliases.
    First tries the specified lang_field, then falls back to all fields.
    This handles cases like 'Great Perfection' matching 'Dzogchen' via name_en_alt.
    """
    g = get_graph(graph_name)

    # Primary: match on requested field
    query = (
        f"MATCH (c:Concept) "
        f"WHERE toLower(c.{lang_field}) CONTAINS toLower($term) "
        "RETURN c LIMIT 5"
    )
    result = g.query(query, {"term": term})
    if result.result_set:
        return [row[0].properties for row in result.result_set]

    # Fallback: search all language fields at once
    all_fields = ["name_en", "name_en_alt", "name_sa", "name_pi",
                  "name_bo", "name_zh", "name_ta", "name_hi",
                  "name_te", "name_bn"]
    conditions = " OR ".join(
        f"toLower(c.{f}) CONTAINS toLower($term)" for f in all_fields
    )
    query = f"MATCH (c:Concept) WHERE {conditions} RETURN c LIMIT 5"
    result = g.query(query, {"term": term})
    return [row[0].properties for row in result.result_set]


def list_concepts(graph_name: str, subject: str = None) -> list[dict]:
    """List all concepts, optionally filtered by subject."""
    g = get_graph(graph_name)
    if subject:
        query = "MATCH (c:Concept {subject: $subject}) RETURN c"
        result = g.query(query, {"subject": subject})
    else:
        query = "MATCH (c:Concept) RETURN c"
        result = g.query(query)
    return [row[0].properties for row in result.result_set]
