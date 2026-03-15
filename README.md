# Data Lineage Agent System

A Claude Code-powered AI agent system that traces data attributes (e.g. `email`, `firstName`, `telephone`, `petName`) from database tables all the way back to the source application — REST APIs, Spring controllers, Thymeleaf forms, and JPA entities.

The repository under analysis is **spring-petclinic** — a Spring Boot + MySQL application with JPA, Thymeleaf, and REST controllers.

---

## How It Works

You ask a natural language question. The pipeline does the rest.

```
/lineage "trace firstName from database to source application"
```

The system runs a 10-step automated pipeline:

```
orchestrator
    │
    ├── db-scanner      ← finds attribute in DB schema + JPA entities
    ├── sql-scanner     ← finds attribute in SQL files, triggers, views
    ├── java-scanner    ← finds attribute in services, repos, controllers
    └── api-scanner     ← finds attribute in REST endpoints + forms
            │
          tracer        ← connects all findings into one lineage chain
            │
         collector      ← merges paths, removes duplicates
            │
    ├── graph-output    ← ASCII visual diagram
    ├── json-output     ← structured JSON lineage
    └── report-output   ← full markdown report
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
│   ├── java-ast.json                # Pre-parsed Java AST (entities, repos, controllers)
│   └── sql-ast.json                 # Pre-parsed SQL AST (tables, columns, inserts)
│
├── tools/
│   └── ast-scanner.py               # Python script that generates the AST JSON files
│
└── .claude/
    ├── commands/
    │   ├── lineage.md               # /lineage slash command definition
    │   └── inventory.md             # /inventory slash command definition
    └── skills/
        ├── orchestrator/            # Parses query, selects scanners
        ├── db-scanner/              # Scans DB schema + JPA entities
        ├── sql-scanner/             # Scans SQL files
        ├── java-scanner/            # Scans Java application layer
        ├── api-scanner/             # Scans REST + form endpoints
        ├── tracer/                  # Builds the lineage chain
        ├── collector/               # Merges and deduplicates paths
        ├── graph-output/            # Renders ASCII diagram
        ├── json-output/             # Produces JSON lineage
        └── report-output/           # Produces markdown report
```

---

## Prerequisites

### 1. Claude Code CLI

Install Claude Code if you haven't already:

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
python tools/ast-scanner.py
```

This will overwrite `ast-output/java-ast.json` and `ast-output/sql-ast.json`.

### Step 3 — Open Claude Code in this directory

```bash
cd data-lineage
claude
```

---

## Usage

### `/lineage` — Trace any attribute

```
/lineage "your natural language query"
```

**Example queries:**

```
/lineage "trace firstName from database to source application"
/lineage "trace owner email from database to source"
/lineage "where does pet name originate?"
/lineage "what writes to the owners table?"
/lineage "trace telephone from REST API to database"
/lineage "trace lastName sink to source"
```

**Trace directions:**
- `"from database"` / `"from DB"` → traces **sink-to-source** (DB → API)
- `"to database"` / `"to DB"` → traces **source-to-sink** (API → DB)
- `"where does X originate"` → sink-to-source
- `"what writes to X"` → source-to-sink
- Not specified → both directions

**What you get back:**
- Orchestrator output (attribute name, variants, direction, scanners)
- DB Scan Result
- SQL Scan Result
- Java Scan Result
- API Scan Result
- Full Lineage Chain (all hops connected)
- Collected Lineage (nodes + edges)
- ASCII Lineage Graph
- Structured JSON Lineage
- Complete Markdown Report

---

### `/inventory` — Discover what's traceable

At the start of a session, run this to get an overview of all traceable attributes:

```
/inventory
```

This reads both AST files and outputs:
- A table of every entity field mapped to its DB column and type
- 5 ready-to-run `/lineage` example queries based on what actually exists

---

## Outputs Explained

| Output | Description |
|--------|-------------|
| **Lineage Chain** | Every hop from DB column to API endpoint (or reverse), with layer labels and actions |
| **ASCII Graph** | Visual box-and-arrow diagram of the full flow |
| **JSON Lineage** | Machine-readable structured lineage with nodes, edges, paths, gaps |
| **Markdown Report** | Human-readable report combining all findings — suitable for sharing |

---

## How the AST Files Are Used

Instead of parsing raw Java and SQL source on every query, the system pre-parses them once into structured JSON:

| File | Contains |
|------|----------|
| `ast-output/java-ast.json` | All JPA entities, repositories, services, controllers, fields, annotations, method signatures |
| `ast-output/sql-ast.json` | All table definitions, column names/types/constraints, INSERT statements, column index |

All scanner skills read these files first — making traces fast and consistent.

---

## Adding a New Repository to Analyze

1. Place the new repo inside `repo/`:
   ```
   repo/my-new-app/
   ```

2. Update `CLAUDE.md` to point to the new repo path and describe its stack.

3. Regenerate AST files:
   ```bash
   python tools/ast-scanner.py
   ```

4. Start tracing:
   ```
   /lineage "trace email from database to API"
   ```

---

## Agent Skills Reference

| Skill | Triggered by | Purpose |
|-------|-------------|---------|
| `orchestrator` | `/lineage` start | Parses query, extracts attribute + variants + direction |
| `db-scanner` | Always | Finds attribute in DB schema and JPA entities |
| `sql-scanner` | When SQL files exist | Finds attribute in SQL scripts, procedures, triggers |
| `java-scanner` | Always | Finds attribute in services, repos, controllers |
| `api-scanner` | Always | Finds attribute in REST endpoints and Thymeleaf forms |
| `tracer` | After all scanners | Connects findings into one lineage chain |
| `collector` | After tracer | Merges paths, builds node/edge list |
| `graph-output` | After collector | Renders ASCII lineage diagram |
| `json-output` | After collector | Outputs structured JSON |
| `report-output` | Final step | Produces full markdown report |
