# Data Lineage Agent System

A Claude Code-powered AI agent system that traces data attributes (e.g. `email`, `firstName`, `telephone`, `petName`) from database tables all the way back to the source application — REST APIs, Spring controllers, Thymeleaf forms, and JPA entities.

The repository under analysis is **spring-petclinic** — a Spring Boot application (MySQL / H2 / PostgreSQL) with JPA, Thymeleaf, and REST controllers.

---

## How It Works

You ask a natural language question. The pipeline does the rest.

```
/lineage "trace firstName from database to source application"
```

The system runs an 11-step automated pipeline:

```
orchestrator
    │
    ├── db-scanner        ← finds attribute in DB schema + JPA entities
    ├── sql-scanner       ← finds attribute in SQL files, triggers, views
    ├── plpgsql-scanner   ← finds attribute in PL/pgSQL functions + procedures
    ├── java-scanner      ← finds attribute in services, repos, controllers, batch jobs
    ├── mapper-scanner    ← finds attribute in MapStruct / ModelMapper mappings
    └── api-scanner       ← finds attribute in REST endpoints + forms
            │
          tracer          ← connects all findings into one labelled lineage chain
            │
         collector        ← merges paths, removes duplicates
            │
    ├── graph-output      ← ASCII visual diagram
    ├── json-output       ← structured JSON lineage
    └── report-output     ← full markdown report + saves 4 files to lineage-results/
```

---

## Project Structure

```
data-lineage/
├── CLAUDE.md                        # Project instructions for Claude
├── README.md                        # This file
│
├── repo/
│   └── spring-petclinic/            # Repository under analysis
│       ├── src/main/java/           # Java Spring source code
│       └── src/main/resources/      # SQL scripts, templates, config
│
├── ast-output/
│   ├── java-ast.json                # Pre-parsed Java AST (entities, repos, controllers, batch)
│   ├── sql-ast.json                 # Pre-parsed SQL AST (tables, columns, inserts)
│   ├── plpgsql-ast.json             # Pre-parsed PL/pgSQL AST (functions, procedures, transforms)
│   └── mapper-ast.json              # Pre-parsed mapper AST (MapStruct interfaces, ModelMapper calls)
│
├── tools/
│   └── ast-scanner.py               # Python script that generates all 4 AST JSON files
│
├── lineage-results/                 # Saved lineage outputs (created by /lineage-save)
│   └── <attribute>_<timestamp>/
│       ├── lineage-report.md
│       ├── lineage-graph.txt
│       ├── lineage.json
│       └── lineage-summary.txt
│
└── .claude/
    ├── commands/
    │   ├── lineage.md               # /lineage — full pipeline, output to screen
    │   ├── lineage-save.md          # /lineage-save — full pipeline + save to files
    │   ├── lineage-batch.md         # /lineage-batch — run /lineage-save for multiple attributes
    │   ├── lineage-history.md       # /lineage-history — list all saved results
    │   └── inventory.md             # /inventory — discover all traceable attributes
    └── skills/
        ├── orchestrator/            # Parses query, selects scanners
        ├── db-scanner/              # Scans DB schema + JPA entities
        ├── sql-scanner/             # Scans SQL files
        ├── plpgsql-scanner/         # Scans PL/pgSQL functions and procedures
        ├── java-scanner/            # Scans Java layer incl. Spring Batch components
        ├── mapper-scanner/          # Scans MapStruct @Mapper interfaces + ModelMapper calls
        ├── api-scanner/             # Scans REST + form endpoints
        ├── tracer/                  # Builds the lineage chain with labelled edges
        ├── collector/               # Merges and deduplicates paths
        ├── graph-output/            # Renders ASCII diagram
        ├── json-output/             # Produces JSON lineage
        └── report-output/           # Produces markdown report + saves files
```

---

## Prerequisites

### 1. Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Python dependencies (for AST scanner)

```bash
pip install javalang sqlglot
```

---

## Setup

### Step 1 — Clone this repository

```bash
git clone <this-repo-url>
cd data-lineage
```

### Step 2 — (Optional) Regenerate the AST files

The `ast-output/` folder already contains pre-built AST JSON files for spring-petclinic.
If you modify the repo under analysis or want a fresh scan, regenerate them:

```bash
python3 tools/ast-scanner.py
```

This overwrites all four AST files:
- `ast-output/java-ast.json` — entities, repos, controllers, Spring Batch components
- `ast-output/sql-ast.json` — tables, columns, inserts (postgres dialect)
- `ast-output/plpgsql-ast.json` — PL/pgSQL functions and procedures with transformations
- `ast-output/mapper-ast.json` — MapStruct interfaces and ModelMapper call sites

### Step 3 — Open Claude Code in this directory

```bash
cd data-lineage
claude
```

---

## Usage

### `/lineage` — Trace any attribute (output to screen)

```
/lineage "your natural language query"
```

Runs the full 11-step pipeline and prints all results in the conversation.

**Example queries:**

```
/lineage "trace firstName from database to source application"
/lineage "trace owner email from database to source"
/lineage "where does pet name originate?"
/lineage "what writes to the owners table?"
/lineage "trace telephone from REST API to database"
/lineage "trace lastName sink to source"
```

---

### `/lineage-save` — Trace and save to files

```
/lineage-save "your natural language query"
```

Runs the same full pipeline as `/lineage`, then saves 4 output files to a timestamped folder:

```
lineage-results/<attribute>_<YYYYMMDD_HHMMSS>/
├── lineage-report.md      ← full markdown report
├── lineage-graph.txt      ← ASCII lineage diagram
├── lineage.json           ← structured JSON lineage
└── lineage-summary.txt    ← key facts (hops, layers, path, transformations)
```

---

### `/lineage-batch` — Trace multiple attributes at once

```
/lineage-batch "firstName, lastName, telephone, email"
```

Splits the arguments by comma and runs `/lineage-save` for each attribute one by one. After all are done, displays a consolidated summary table of all results.

---

### `/lineage-history` — View saved results

```
/lineage-history
```

Lists all previously saved lineage results from the `lineage-results/` folder as a formatted table:

```
==========================================
LINEAGE HISTORY
==========================================
Results found: 3

ATTRIBUTE    | DATE              | HOPS | FILES | SUMMARY
-------------|-------------------|------|-------|--------------------------------------------------
telephone    | 2026-03-15 14:30  |    5 |     4 | owners.telephone → Owner.java → OwnerController
firstName    | 2026-03-15 13:10  |    4 |     4 | owners.first_name → Owner.java → OwnerController
==========================================
```

---

### `/inventory` — Discover what's traceable

```
/inventory
```

Reads both AST files and outputs:
- A table of every entity field mapped to its DB column and type
- 5 ready-to-run `/lineage` example queries based on what actually exists in the repo

---

## Trace Directions

| Query phrasing | Direction | Flow |
|----------------|-----------|------|
| `"from database"` / `"from DB"` | sink-to-source | DB → API |
| `"to database"` / `"to DB"` | source-to-sink | API → DB |
| `"where does X originate"` | sink-to-source | DB → API |
| `"what writes to X"` | source-to-sink | API → DB |
| Not specified | both | both directions |

---

## Outputs Explained

| Output | Description |
|--------|-------------|
| **Lineage Chain** | Every hop from DB column to API endpoint (or reverse), with layer labels and transformation labels on each arrow |
| **ASCII Graph** | Visual box-and-arrow diagram of the full flow |
| **JSON Lineage** | Machine-readable structured lineage with nodes, edges, paths, and gaps |
| **Markdown Report** | Human-readable report combining all findings — suitable for sharing |

### Transformation Labels on Edges

The `tracer` skill labels every edge in the chain where a transformation is detected:

| Label | Source | Meaning |
|-------|--------|---------|
| `RENAME: fieldA → fieldB` | MapStruct `@Mapping` | Field is renamed between DTO and entity |
| `CONVERT: qualifiedByName` | MapStruct `qualifiedByName` | Custom converter method applied |
| `EXPRESSION: <expr>` | MapStruct `expression` | SpEL expression transforms the value |
| `UPPER(field) applied` | PL/pgSQL `UPPER()` | Value is uppercased |
| `LOWER(field) applied` | PL/pgSQL `LOWER()` | Value is lowercased |
| `SUBSTR(field) — value truncated` | PL/pgSQL `SUBSTR()` | Value is partially extracted |
| `CONVERT: TO_CHAR / TO_DATE / ...` | PL/pgSQL type cast | Type conversion applied |
| `COALESCE(field, default)` | PL/pgSQL `COALESCE()` | Null substitution applied |
| `CASE WHEN field — conditional branch` | PL/pgSQL `CASE` | Value is conditionally replaced |
| `CONCAT / \|\| — merged with other value` | PL/pgSQL concat | Field is merged with another value |
| `REPLACE(field, ...) applied` | PL/pgSQL `REPLACE()` | Substring substitution applied |
| `CONVERT: TypeA → TypeB` | Java type cast | Type conversion in Java layer |

---

## How the AST Files Are Used

Instead of parsing raw Java and SQL source on every query, the system pre-parses them once into structured JSON:

| File | Contains |
|------|----------|
| `ast-output/java-ast.json` | JPA entities, repositories, services, controllers, Spring Batch readers/processors/writers, `@Bean` Step/Job definitions |
| `ast-output/sql-ast.json` | Table definitions, column names/types/constraints, INSERT/UPDATE/SELECT statements, column index (postgres dialect) |
| `ast-output/plpgsql-ast.json` | PL/pgSQL FUNCTION and PROCEDURE definitions — parameters, return type, tables read/written, structured transformations (UPPER, COALESCE, CASE, SUBSTR, etc.) |
| `ast-output/mapper-ast.json` | MapStruct `@Mapper` interfaces with field-level `@Mapping` entries (source/target field, transform type); ModelMapper `.map()` and `.addMapping()` call sites |

All scanner skills read these files first — making traces fast and consistent.

### SQL Dialect
The scanner uses **postgres** as the canonical SQL dialect for all files (MySQL, H2, and Postgres schemas alike). `SERIAL`/`BIGSERIAL` types, `RETURNING` clauses, and `$1`/`$2` parameter placeholders are all handled natively.

### Spring Batch Detection
`java-ast.json` includes a `batch_components` array in its summary. Classes implementing `ItemReader`, `ItemProcessor`, or `ItemWriter` are classified by role. `@Bean` methods returning `Step`, `Job`, or `Tasklet` are captured as batch config entries so the full reader → processor → writer chain can be traced.

### MapStruct / ModelMapper Detection
`mapper-ast.json` captures two types of mappings:
- **MapStruct**: `@Mapper` interfaces with `@Mapping(source=, target=)` annotations — detects DIRECT (same name), RENAME (different names), CONVERT (`qualifiedByName`), and EXPRESSION transforms
- **ModelMapper**: `.map()`, `.typeMap()`, and `.addMapping()` call sites in Java source — detected via regex scan

---

## Adding a New Repository to Analyze

1. Place the new repo inside `repo/`:
   ```
   repo/my-new-app/
   ```

2. Update `CLAUDE.md` to point to the new repo path and describe its stack.

3. Regenerate AST files:
   ```bash
   python3 tools/ast-scanner.py
   ```

4. Start tracing:
   ```
   /lineage "trace email from database to API"
   ```

---

## Agent Skills Reference

| Skill | Step | Purpose |
|-------|------|---------|
| `orchestrator` | 1 | Parses query, extracts attribute + variants + direction |
| `db-scanner` | 2 | Finds attribute in DB schema and JPA entities |
| `sql-scanner` | 3 | Finds attribute in SQL scripts, procedures, triggers |
| `plpgsql-scanner` | 3b | Finds attribute in PL/pgSQL functions/procedures; detects UPPER, COALESCE, CASE, SUBSTR and other transforms |
| `java-scanner` | 4 | Finds attribute in services, repos, controllers; traces Spring Batch reader → processor → writer chain |
| `mapper-scanner` | 4b | Finds field renames and conversions in MapStruct `@Mapper` interfaces and ModelMapper call sites |
| `api-scanner` | 5 | Finds attribute in REST endpoints and Thymeleaf forms |
| `tracer` | 6 | Connects all findings into one lineage chain; labels every edge with RENAME/CONVERT/CASE_TRANSFORM etc. |
| `collector` | 7 | Merges paths, builds clean node/edge list |
| `graph-output` | 8 | Renders ASCII lineage diagram |
| `json-output` | 9 | Outputs structured JSON |
| `report-output` | 10 | Produces full markdown report and saves 4 files to `lineage-results/` |

## Slash Commands Reference

| Command | Usage | Description |
|---------|-------|-------------|
| `/lineage` | `/lineage "query"` | Full pipeline, results printed to screen |
| `/lineage-save` | `/lineage-save "query"` | Full pipeline + saves 4 files to `lineage-results/` |
| `/lineage-batch` | `/lineage-batch "attr1, attr2, attr3"` | Runs `/lineage-save` for each comma-separated attribute |
| `/lineage-history` | `/lineage-history` | Lists all saved results as a formatted table |
| `/inventory` | `/inventory` | Discovers all traceable attributes in the repo |
