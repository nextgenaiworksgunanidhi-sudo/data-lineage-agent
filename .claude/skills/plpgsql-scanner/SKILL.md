---
name: plpgsql-scanner
description: Scans ast-output/plpgsql-ast.json to find where an attribute
             flows through PL/pgSQL functions and procedures. Identifies
             reads, writes, and transformations inside function bodies.
             Use when tracing attribute through the PostgreSQL stored function layer.
---

When scanning PL/pgSQL functions for an attribute:

PRIORITY: Read ast-output/plpgsql-ast.json first.

1. Read ast-output/plpgsql-ast.json and check meta.total_functions.
   If total_functions is 0, skip to step 4 (no functions found).

2. Search all entries in functions[*] for the attribute and its variants:

   a) parameters[*].name
      — attribute is passed directly into the function as an argument
      — if found: record function name, param name, param type → INBOUND

   b) reads[*]
      — attribute's table is SELECTed inside the function body
      — if found: the function reads rows that contain the attribute

   c) writes[*].table
      — attribute's table is INSERTed, UPDATEd, or DELETEd inside the body
      — if found: the function writes to a table containing the attribute
      — record the operation type (INSERT / UPDATE / DELETE)

3. For each matching function also check for TRANSFORMATIONS:
   - RENAMED:      first_name AS fname, telephone AS phone
   - COMPUTED:     UPPER(first_name), CONCAT(first_name, ' ', last_name)
   - CONDITIONAL:  CASE WHEN first_name IS NULL THEN 'Unknown' END
   - FORMATTED:    TO_CHAR(...), TRIM(...), COALESCE(first_name, '')
   Note: transformations must be inferred from the raw SQL body text
   since the AST only stores table-level read/write info.

4. If no PL/pgSQL functions found in repo, state clearly:
   "No PL/pgSQL functions found in repo.
    Application uses JPA/ORM for all DB operations."
   Do NOT fall back to scanning raw .sql files.

5. Output exactly as:

   ==========================================
   PLPGSQL SCAN RESULT
   ==========================================
   FILES SCANNED:   <number>
   FUNCTIONS FOUND: <number>

   (if none found)
   No PL/pgSQL functions found in repo.
   Application uses JPA/ORM for all DB operations.
   ==========================================

   (if functions found — repeat block per function)
   ------------------------------------------
   FUNCTION: <name>
   KIND:     FUNCTION | PROCEDURE
   PARAMS:   <name type, name type, ...>
   RETURNS:  <return type>
   READS:    <comma-separated table list, or none>
   WRITES:   <INSERT table, UPDATE table, DELETE table — or none>
   ATTR IN:  PARAMETER | READ | WRITTEN | NOT FOUND
   TRANSFORM: none | <description of any transformation detected>
   ------------------------------------------
   ==========================================
