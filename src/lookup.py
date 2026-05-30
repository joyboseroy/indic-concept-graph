"""
lookup.py

The main entry point for multilingual concept lookup.

Given a query in any supported language:
1. Detect or accept the source language
2. Translate to English (via IndicTrans2 or LLM)
3. Fuzzy-match against the FalkorDB concept graph
4. Retrieve prerequisites / learning path
5. Translate results back to the query language

Usage (CLI):
    python -m src.lookup --query "न्यूटन का पहला नियम" --graph ncert
    python -m src.lookup --query "śūnyatā" --lang sanskrit --graph dharma
    python -m src.lookup --query "rigpa" --lang tibetan --graph dharma --dependents

Usage (Python):
    from src.lookup import lookup
    results = lookup("প্রতীত্যসমুৎপাদ", graph="dharma")
"""

import argparse
import json
from src.translate import Translator, INDIC_LANG_CODES, CLASSICAL_LANGS
from src import graph as G


def lookup(
    query: str,
    graph_name: str = "ncert",
    src_lang: str = None,
    mode: str = "prerequisites",   # prerequisites | dependents | path
    to_concept: str = None,        # used when mode=path
    depth: int = 3,
    translate_results: bool = True,
) -> dict:
    """
    Full multilingual lookup pipeline.

    Returns:
        {
          "query": original query,
          "matched_concept": {...concept properties...},
          "results": [...list of concept dicts...],
          "result_lang": the language results are returned in,
        }
    """
    t = Translator()

    # 1. Determine source language
    resolved_lang = src_lang
    if resolved_lang is None:
        detected = t.detect_lang(query)
        resolved_lang = detected  # may still be None for romanized input

    # 2. Translate to English
    if resolved_lang and resolved_lang != "eng_Latn" and resolved_lang != "english":
        english_query = t.to_english(query, src_lang=resolved_lang)
    else:
        english_query = query

    # 3. Exact then fuzzy match in graph
    exact = G.fuzzy_match(graph_name, english_query, lang_field="name_en")
    if not exact:
        # Try the original query text in case it was already English
        exact = G.fuzzy_match(graph_name, query, lang_field="name_en")

    if not exact:
        return {
            "query": query,
            "matched_concept": None,
            "results": [],
            "error": f"No concept found matching '{english_query}' in graph '{graph_name}'",
        }

    matched = exact[0]
    matched_en = matched["name_en"]

    # 4. Retrieve related concepts
    if mode == "prerequisites":
        results = G.get_prerequisites(graph_name, matched_en, depth=depth)
    elif mode == "dependents":
        results = G.get_dependents(graph_name, matched_en, depth=depth)
    elif mode == "path" and to_concept:
        # to_concept assumed English for path mode
        results = G.get_learning_path(graph_name, matched_en, to_concept)
    else:
        results = G.get_prerequisites(graph_name, matched_en, depth=depth)

    # 5. Translate results back to source language if requested
    result_lang = resolved_lang or "eng_Latn"
    if translate_results and resolved_lang and resolved_lang not in ("eng_Latn", "english"):
        # map FLORES code to stored field name
        lang_field_map = {
            "hin_Deva": "name_hi", "ben_Beng": "name_bn",
            "tam_Taml": "name_ta", "tel_Telu": "name_te",
            "kan_Knda": "name_kn", "mal_Mlym": "name_ml",
        }
        native_field = lang_field_map.get(resolved_lang)

        for concept in results:
            # use stored native name if available, else translate
            if native_field and concept.get(native_field):
                concept["name_translated"] = concept[native_field]
            else:
                en_name = concept.get("name_en", "")
                if en_name:
                    try:
                        concept["name_translated"] = t.from_english(en_name, tgt_lang=resolved_lang)
                    except Exception:
                        concept["name_translated"] = en_name

        if matched.get("name_en"):
            if native_field and matched.get(native_field):
                matched["name_translated"] = matched[native_field]
            else:
                try:
                    matched["name_translated"] = t.from_english(matched["name_en"], tgt_lang=resolved_lang)
                except Exception:
                    pass
                
    return {
        "query": query,
        "english_query": english_query,
        "matched_concept": matched,
        "results": results,
        "result_lang": result_lang,
        "mode": mode,
    }


def pretty_print(result: dict):
    if result.get("error"):
        print(f"\nError: {result['error']}")
        return

    matched = result["matched_concept"]
    name_display = matched.get("name_translated") or matched.get("name_en", "?")
    print(f"\nQuery      : {result['query']}")
    print(f"Matched    : {name_display} (en: {matched.get('name_en', '?')})")
    print(f"Mode       : {result['mode']}")
    print(f"Language   : {result['result_lang']}")

    results = result["results"]
    if not results:
        print("No related concepts found.")
        return

    print(f"\n{result['mode'].capitalize()} ({len(results)}):")
    for i, c in enumerate(results, 1):
        name = c.get("name_translated") or c.get("name_en", "?")
        subject = c.get("subject", "")
        grade = c.get("grade", "")
        tradition = c.get("tradition", "")
        meta = " | ".join(filter(None, [subject, f"Grade {grade}" if grade else "", tradition]))
        print(f"  {i:2}. {name}  [{meta}]  (en: {c.get('name_en', '?')})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Multilingual concept prerequisite lookup using FalkorDB + IndicTrans2"
    )
    parser.add_argument("--query", "-q", required=True, help="Concept name in any language")
    parser.add_argument("--graph", "-g", default="ncert", choices=["ncert", "dharma"],
                        help="Which graph to query (default: ncert)")
    parser.add_argument("--lang", "-l", default=None,
                        help="Source language: FLORES code (hin_Deva) or classical name (tibetan, sanskrit, pali, chinese)")
    parser.add_argument("--mode", "-m", default="prerequisites",
                        choices=["prerequisites", "dependents", "path"],
                        help="What to return (default: prerequisites)")
    parser.add_argument("--to", default=None,
                        help="Target concept for path mode (English)")
    parser.add_argument("--depth", "-d", type=int, default=3,
                        help="Traversal depth (default: 3)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON instead of formatted text")
    args = parser.parse_args()

    result = lookup(
        query=args.query,
        graph_name=args.graph,
        src_lang=args.lang,
        mode=args.mode,
        to_concept=args.to,
        depth=args.depth,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        pretty_print(result)


if __name__ == "__main__":
    main()
