# indic-concept-graph

Multilingual concept prerequisite lookup across Indian school curriculum (NCERT) and Buddhist dharma terminology.

Given a concept name in **any Indian language** — or in Sanskrit, Tibetan, Pali, or Chinese — returns its prerequisites and related concepts from a FalkorDB knowledge graph.

```bash
# What do I need to know before Newton's Second Law? (in Hindi)
python -m src.lookup --query "न्यूटन का दूसरा नियम" --graph ncert

# What must I understand before Dzogchen? (in Tibetan)
python -m src.lookup --query "rdzogs pa chen po" --lang tibetan --graph dharma

# What concepts open up after understanding Emptiness?
python -m src.lookup --query "śūnyatā" --lang sanskrit --graph dharma --mode dependents
```

## Architecture

```
User query (any language)
    │
    ▼
Language detection / normalisation
    │
    ├─ Indic scripts (Hindi, Tamil, Telugu, Bengali, ...)
    │      └─ IndicTrans2 (AI4Bharat) → English
    │
    └─ Classical langs (Sanskrit, Tibetan, Pali, Chinese)
           └─ Ollama LLM (qwen2.5) → English
    │
    ▼
FalkorDB fuzzy concept match
    │
    ▼
Cypher query: prerequisites / dependents / learning path
    │
    ▼
Translate results back to source language
    │
    ▼
Formatted output
```

## Two Graphs

### `ncert` — Indian School Curriculum
Concepts from NCERT textbooks, Grades 6-10, across Physics, Chemistry, Mathematics, Biology. All concept names stored in English, Hindi, Tamil, Telugu, Bengali.

### `dharma` — Buddhist Terminology
Core Buddhist concepts with cross-traditional multilingual names: Sanskrit, Tibetan (Wylie), Pali, Chinese (Traditional), Tamil, Hindi. Covers Theravada, Mahayana, Madhyamaka, Dzogchen, Tantra, Pure Land, Jodo Shinshu.

Prerequisite edges reflect doctrinal learning sequences — e.g. the Tibetan Ngöndro progression, the Theravada path stages, the Mahayana Bodhisattva path.

## Supported Languages

**Indic (via IndicTrans2, AI4Bharat):**
Hindi (`hin_Deva`), Bengali (`ben_Beng`), Tamil (`tam_Taml`), Telugu (`tel_Telu`), Kannada (`kan_Knda`), Malayalam (`mal_Mlym`), Marathi (`mar_Deva`), Gujarati (`guj_Gujr`), Punjabi (`pan_Guru`), Odia (`ory_Orya`), Assamese (`asm_Beng`), Urdu (`urd_Arab`)

**Classical (via Ollama LLM):**
Sanskrit, Tibetan (Wylie romanization), Pali, Chinese

## Setup

```bash
# 1. Start FalkorDB
docker-compose up -d

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install IndicTransToolkit (required for IndicTrans2)
pip install git+https://github.com/AI4Bharat/IndicTransToolkit.git

# 4. Pull Ollama model (for Sanskrit/Tibetan/Pali/Chinese queries)
ollama pull qwen2.5:7b

# 5. Copy and edit environment config
cp .env.example .env

# 6. Load seed data
python -m src.load_ncert_seed
python -m src.load_dharma_seed
```

## Usage

### CLI

```bash
# NCERT: prerequisites for a concept in Hindi
python -m src.lookup --query "त्रिकोणमिति" --graph ncert

# NCERT: what can I learn after mastering Integers?
python -m src.lookup --query "Integers" --graph ncert --mode dependents

# NCERT: learning path from Fractions to Quadratic Equations
python -m src.lookup --query "Fractions" --graph ncert --mode path --to "Quadratic Equations"

# Dharma: prerequisites for Dzogchen in Tibetan
python -m src.lookup --query "rdzogs pa chen po" --lang tibetan --graph dharma

# Dharma: prerequisites for Emptiness in Sanskrit
python -m src.lookup --query "śūnyatā" --lang sanskrit --graph dharma

# Dharma: prerequisites for 菩提心 (Bodhicitta) in Chinese
python -m src.lookup --query "菩提心" --lang chinese --graph dharma

# Output as JSON
python -m src.lookup --query "न्यूटन का पहला नियम" --graph ncert --json
```

### Python API

```python
from src.lookup import lookup

# NCERT lookup in Tamil
result = lookup("த்ரிகோணமிதி", graph_name="ncert")
for concept in result["results"]:
    print(concept["name_translated"], "→", concept["name_en"])

# Dharma lookup
result = lookup("rigpa", graph_name="dharma", src_lang="tibetan")
print(result["matched_concept"])
print(result["results"])
```

### Adding Concepts

Edit `data/seed/ncert_concepts.json` or `data/seed/dharma_concepts.json` and rerun the loader. The `upsert_concept` and `upsert_edge` functions in `src/graph.py` are also callable directly.

## Acknowledgements

- [AI4Bharat / IndicTrans2](https://github.com/AI4Bharat/IndicTrans2) — translation models for 22 Indian languages
- [FalkorDB](https://www.falkordb.com/) — graph database
- NCERT textbooks (freely available at ncert.nic.in) — curriculum source
- Dharma seed data informed by Nyingma, Theravada, Mahayana, and Pure Land canonical sources

## Citation

If you use this in research:

```bibtex
@software{indic_concept_graph_2026,
  author = {Bose, Joy},
  title  = {indic-concept-graph: Multilingual Concept Prerequisite Lookup for NCERT Curriculum and Buddhist Dharma Terminology},
  year   = {2026},
  url    = {https://github.com/joyboseroy/indic-concept-graph}
}
```

## License

MIT

