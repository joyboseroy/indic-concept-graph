# indic-concept-graph

A multilingual concept prerequisite graph for two domains:

- **NCERT** — Indian school curriculum (Grades 6-10), Physics, Chemistry, Mathematics, Biology
- **Dharma** — Buddhist terminology across Sanskrit, Tibetan, Pali, Chinese, Tamil, Hindi

Given a concept name in any Indian language — or in Sanskrit, Tibetan, Wylie romanization, Pali, or Chinese — returns its prerequisites, dependents, or shortest learning path from a FalkorDB knowledge graph.

Built on [IndicTrans2 (AI4Bharat)](https://github.com/AI4Bharat/IndicTrans2) for 22 Indian languages and Ollama for classical languages.

---

## Examples

### NCERT — English

```
$ python3 -m src.lookup --query "Trigonometry" --graph ncert

Query      : Trigonometry
Matched    : Trigonometry (en: Trigonometry)
Mode       : prerequisites
Language   : eng_Latn

Prerequisites (2):
   1. Pythagoras Theorem  [Mathematics | Grade 9]
   2. Basic Arithmetic    [Mathematics | Grade 6]
```

### NCERT — Hindi (Devanagari)

```
$ python3 -m src.lookup --query "त्रिकोणमिति" --graph ncert

Query      : त्रिकोणमिति
Matched    : त्रिकोणमिति (en: Trigonometry)
Mode       : prerequisites
Language   : hin_Deva

Prerequisites (2):
   1. पाइथागोरस प्रमेय  [Mathematics | Grade 9]
   2. बुनियादी अंकगणित  [Mathematics | Grade 6]
```

### NCERT — What does mastering Integers unlock?

```
$ python3 -m src.lookup --query "Integers" --graph ncert --mode dependents

Query      : Integers
Matched    : Integers (en: Integers)
Mode       : dependents
Language   : eng_Latn

Dependents (1):
   1. Algebra Basics  [Mathematics | Grade 7]
```

### NCERT — Learning path

```
$ python3 -m src.lookup --query "Fractions" --graph ncert --mode path --to "Quadratic Equations"

Query      : Fractions
Matched    : Fractions (en: Fractions)
Mode       : path
Language   : eng_Latn

Path (4):
   1. Fractions
   2. Ratio and Proportion
   3. ... (via Algebra Basics, Linear Equations)
   4. Quadratic Equations
```

---

### Dharma — Prerequisites for Dzogchen

```
$ python3 -m src.lookup --query "Dzogchen" --graph dharma

Query      : Dzogchen
Matched    : Dzogchen (en: Dzogchen)
Mode       : prerequisites
Language   : eng_Latn

Prerequisites (9):
   1. Refuge          [Dharma | All]
   2. Bodhicitta      [Dharma | Mahayana/Vajrayana]
   3. Ngondro         [Tantra | Vajrayana]
   4. Guru Yoga       [Tantra | Vajrayana]
   5. Tantra          [Tantra | Vajrayana]
   6. Buddha Nature   [Dharma | Mahayana/Vajrayana]
   7. Emptiness       [Madhyamaka | Mahayana/Vajrayana]
   8. Prajna          [Dharma | All]
   9. Rigpa           [Dzogchen | Nyingma/Vajrayana]
```

### Dharma — Path from Refuge to Rigpa (Nyingma sequence)

```
$ python3 -m src.lookup --query "Refuge" --graph dharma --mode path --to "Rigpa"

Query      : Refuge
Matched    : Refuge (en: Refuge)
Mode       : path
Language   : eng_Latn

Path (4):
   1. Refuge     [Dharma | All]
   2. Ngondro    [Tantra | Vajrayana]
   3. Guru Yoga  [Tantra | Vajrayana]
   4. Rigpa      [Dzogchen | Nyingma/Vajrayana]
```

### Dharma — What does understanding Emptiness unlock?

```
$ python3 -m src.lookup --query "Emptiness" --graph dharma --mode dependents

Query      : Emptiness
Matched    : Emptiness (en: Emptiness)
Mode       : dependents
Language   : eng_Latn

Dependents (5):
   1. Buddha Nature  [Dharma | Mahayana/Vajrayana]
   2. Rigpa          [Dzogchen | Nyingma/Vajrayana]
   3. Dzogchen       [Dzogchen | Nyingma]
   4. Mahamudra      [Tantra | Kagyu/Vajrayana]
   5. Two Truths     [Madhyamaka | Mahayana]
```

### Dharma — Prerequisites for Nirvana (Theravada path)

```
$ python3 -m src.lookup --query "Nirvana" --graph dharma

Query      : Nirvana
Matched    : Nirvana (en: Nirvana)
Mode       : prerequisites
Language   : eng_Latn

Prerequisites (10):
   1. Impermanence           [Dharma | All]
   2. Suffering              [Dharma | All]
   3. Non-self               [Dharma | All]
   4. Three Marks of Existence [Dharma | All]
   5. Dependent Origination  [Dharma | All]
   6. Karma                  [Dharma | All]
   7. Rebirth                [Dharma | All]
   8. Four Noble Truths      [Dharma | All]
   9. Noble Eightfold Path   [Dharma | All]
  10. Refuge                 [Dharma | All]
```

### Dharma — Tibetan Wylie romanization query (via Ollama)

```
$ python3 -m src.lookup --query "rdzogs pa chen po" --lang tibetan --graph dharma

Query      : rdzogs pa chen po
Matched    : Dzogchen (en: Dzogchen)
Mode       : prerequisites
Language   : tibetan

Prerequisites (9):
   [prerequisites returned translated to Tibetan via Ollama]
```

### Dharma — Sanskrit query

```
$ python3 -m src.lookup --query "śūnyatā" --lang sanskrit --graph dharma

Query      : śūnyatā
Matched    : Emptiness (en: Emptiness)
Mode       : prerequisites
Language   : sanskrit
```

### Dharma — Chinese query

```
$ python3 -m src.lookup --query "菩提心" --lang chinese --graph dharma

Query      : 菩提心
Matched    : Bodhicitta (en: Bodhicitta)
Mode       : prerequisites
Language   : chinese
```

---

## Architecture

```
User query (any language/script)
        │
        ├─ Indic scripts (Hindi, Tamil, Telugu, Bengali ...)
        │       └─ IndicTrans2 (AI4Bharat) → English
        │
        └─ Classical (Sanskrit, Tibetan, Pali, Chinese)
                └─ Ollama LLM (qwen2.5) → English
        │
        ▼
FalkorDB: fuzzy match on all language fields
        │
        ▼
Cypher query: prerequisites / dependents / BFS path
        │
        ▼
Translate results back to source language
        │
        ▼
Formatted output
```

---

## Multilingual concept storage

Every concept node stores names across languages. Example for Emptiness:

| Field      | Value                        |
|------------|------------------------------|
| name_en    | Emptiness                    |
| name_sa    | śūnyatā                      |
| name_pi    | suññatā                      |
| name_bo    | stong pa nyid                |
| name_zh    | 空                            |
| name_ta    | சூன்யதா                      |
| name_hi    | शून्यता                      |

Queries in any of these languages or scripts match the same node.

---

## Supported languages

**Indic (via IndicTrans2, AI4Bharat):**
Hindi (`hin_Deva`), Bengali (`ben_Beng`), Tamil (`tam_Taml`), Telugu (`tel_Telu`),
Kannada (`kan_Knda`), Malayalam (`mal_Mlym`), Marathi (`mar_Deva`), Gujarati (`guj_Gujr`),
Punjabi (`pan_Guru`), Odia (`ory_Orya`), Assamese (`asm_Beng`), Urdu (`urd_Arab`)

**Classical (via Ollama LLM):**
Sanskrit, Tibetan (Wylie romanization), Pali, Chinese (Traditional/Simplified)

---

## Setup

```bash
# 1. Start FalkorDB
docker-compose up -d

# 2. Install dependencies
pip install -r requirements.txt --break-system-packages

# 3. Copy environment config
cp .env.example .env

# 4. Load seed data
python3 -m src.load_ncert_seed
python3 -m src.load_dharma_seed

# 5. Pull Ollama model (for Sanskrit/Tibetan/Pali/Chinese queries)
ollama pull qwen2.5:7b
```

IndicTrans2 models download automatically on first use (~900MB, one-time).

---

## CLI reference

```bash
python3 -m src.lookup --query QUERY
                      --graph {ncert,dharma}
                      --lang  LANG           # FLORES code or classical name
                      --mode  {prerequisites,dependents,path}
                      --to    TARGET_CONCEPT  # for path mode
                      --depth N              # traversal depth (default 3)
                      --json                 # raw JSON output
```

---

## Extending the seed data

Add concepts to `data/seed/dharma_concepts.json` or `data/seed/ncert_concepts.json`
and edges to the corresponding `*_edges.json`. Then reload:

```bash
python3 -m src.load_dharma_seed
```

The loader uses `MERGE` so existing nodes are updated, not duplicated.

Planned additions to the dharma graph:
- Sixteen insight knowledges (Theravada vipassana sequence)
- Four Ngondro practices individually with sequence edges
- Longchenpa's four visions (thögal progression)
- Five Buddha families
- Bardo stages

---

## Acknowledgements

- [AI4Bharat / IndicTrans2](https://github.com/AI4Bharat/IndicTrans2) — translation models for 22 Indian languages
- [FalkorDB](https://www.falkordb.com/) — graph database
- NCERT textbooks (freely available at ncert.nic.in)
- Dharma seed data informed by Nyingma, Theravada, Mahayana, Madhyamaka, and Pure Land canonical sources

## Citation

```bibtex
@software{indic_concept_graph_2026,
  author = {Bose, Joy},
  title  = {indic-concept-graph: Multilingual Concept Prerequisite Graph for NCERT Curriculum and Buddhist Dharma Terminology},
  year   = {2026},
  url    = {https://github.com/joyboseroy/indic-concept-graph}
}
```

## License

MIT
