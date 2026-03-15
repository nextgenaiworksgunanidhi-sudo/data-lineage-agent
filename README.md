# Data Lineage Agent System

A conversational data lineage tool built entirely with
Claude Code skills and agents — no backend server,
no separate API key needed beyond Claude Pro.

Ask in plain English — get full data lineage traced
from database sink back to source application.

---

## What it does

Traces any data attribute (firstName, telephone, email
etc.) through a Java Spring + PL/SQL + PostgreSQL stack:

  REST API → Spring Controller → Spring Service
  → Spring Repository → JPA Entity → Database Column

Shows every transformation, rename, type conversion
and SQL function applied along the way.

---

## How it works

Built on Claude Code's skill and agent system:
- Skills = atomic workers (db-scanner, java-scanner etc.)
- Agents = orchestrators that call skills in combination
- Commands = entry points (/lineage, /impact, /transforms)
- AST scanner = pre-indexes the codebase once

---

## Setup

### 1. Clone this repo
```bash
git clone https://github.com/YOUR-USERNAME/data-lineage-agent.git
cd data-lineage-agent
```

### 2. Clone a repo to analyse
```bash
git clone https://github.com/spring-petclinic/spring-petclinic repo/spring-petclinic
```

### 3. Install Python dependencies
```bash
pip install javalang sqlglot
```

### 4. Run the AST scanner (do this once)
```bash
python tools/ast-scanner.py
```

### 5. Launch Claude Code
```bash
claude
```

---

## Available commands

| Command | Description |
|---------|-------------|
| `/inventory` | List all traceable attributes |
| `/lineage "query"` | Trace an attribute — output in terminal |
| `/lineage-save "query"` | Trace + save results to lineage-results/ |
| `/transforms "query"` | Show only transformation chain |
| `/impact "query"` | Impact analysis — what breaks if field changes |
| `/lineage-history` | List all saved lineage results |
| `/lineage-batch "f1, f2"` | Trace multiple attributes at once |
| `/refresh-ast` | Refresh AST cache after code changes |

---

## Example queries

```
/inventory
/lineage "trace firstName from database to source"
/lineage-save "trace telephone from REST API to database"
/transforms "trace lastName"
/impact "if I rename firstName in owners table"
/lineage-batch "firstName, lastName, telephone"
```

---

## Project structure

```
data-lineage/
  CLAUDE.md                    ← project memory
  README.md                    ← this file
  tools/
    ast-scanner.py             ← pre-indexes codebase
  ast-output/
    java-ast.json              ← pre-parsed Java structure
    sql-ast.json               ← pre-parsed SQL structure
    attribute-index.json       ← fast attribute lookup
  .claude/
    commands/
      lineage.md               ← /lineage entry point
      lineage-save.md          ← /lineage-save with file output
      lineage-history.md       ← /lineage-history
      lineage-batch.md         ← /lineage-batch
      transforms.md            ← /transforms
      impact.md                ← /impact
      inventory.md             ← /inventory
      refresh-ast.md           ← /refresh-ast
    skills/
      ── scanner skills ──
      orchestrator/SKILL.md
      db-scanner/SKILL.md
      sql-scanner/SKILL.md
      java-scanner/SKILL.md
      api-scanner/SKILL.md
      ── agent skills ──
      query-agent/SKILL.md
      db-agent/SKILL.md
      app-agent/SKILL.md
      transform-agent/SKILL.md
      impact-agent/SKILL.md
      cache-checker/SKILL.md
      ── output skills ──
      tracer/SKILL.md
      collector/SKILL.md
      graph-output/SKILL.md
      json-output/SKILL.md
      report-output/SKILL.md
```

---

## When to refresh the AST cache

Run `python tools/ast-scanner.py` when:
- New code added to the repo
- Existing code modified
- New repository added to `repo/` folder
- Or just run `/refresh-ast` inside Claude Code

---

## Tech stack

- Claude Code skills + agents (.md files only)
- Python 3.x — javalang, sqlglot
- Sample repo: Spring PetClinic (Spring Boot + MySQL)
- Designed for: Java + Spring + PL/SQL + PostgreSQL
