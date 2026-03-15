---
name: plpgsql-scanner
description: Scans ast-output/plpgsql-ast.json to find where an attribute
             flows through PL/pgSQL functions and procedures. Identifies
             reads, writes, and structured transformations inside function bodies.
             Use when tracing attribute through the PostgreSQL stored function layer.
---

When scanning PL/pgSQL functions for an attribute:

PRIORITY: Read ast-output/plpgsql-ast.json first.

1. Read ast-output/plpgsql-ast.json and check meta.total_functions.
   If total_functions is 0, skip to step 5 (no functions found).

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

3. For each matching function check transformations[*]:
   Search transformations[*].field against attribute variants.
   For each match report the full transformation entry:

   Transform types and what they mean:
   - CASE_TRANSFORM  UPPER() / LOWER() / TRIM() applied — value case or whitespace changed
   - TRUNCATE        SUBSTR() / SUBSTRING() — value is partially extracted
   - TYPE_CONVERT    TO_DATE() / TO_CHAR() / TO_TIMESTAMP() / TO_NUMBER() — type is changed
   - NULL_HANDLE     COALESCE() / NULLIF() — null substitution or null-producing logic applied
   - CONDITIONAL     CASE WHEN field — value is conditionally replaced or branched
   - MERGE           CONCAT() / || operator — field is combined with another value
   - REPLACE         REPLACE() / REGEXP_REPLACE() — substring substitution applied

   For each transformation found:
   - State which SQL function is applied (e.g. UPPER, COALESCE)
   - State the transform type
   - Note the lineage implication (e.g. TRUNCATE means downstream value may be shorter)

4. Determine ATTR IN status for each function:
   - PARAMETER  — attribute name matches a function parameter
   - READ       — attribute's table appears in reads[] only
   - WRITTEN    — attribute's table appears in writes[]
   - BOTH       — attribute's table appears in both reads[] and writes[]
   - NOT FOUND  — attribute not referenced in this function

5. If no PL/pgSQL functions found in repo, state clearly:
   "No PL/pgSQL functions found in repo.
    Application uses JPA/ORM for all DB operations."
   Do NOT fall back to scanning raw .sql files.

6. Output exactly as:

   ==========================================
   PLPGSQL SCAN RESULT
   ==========================================
   FILES SCANNED:   <number>
   FUNCTIONS FOUND: <number>

   (if none found)
   No PL/pgSQL functions found in repo.
   Application uses JPA/ORM for all DB operations.
   ==========================================

   (if functions found — repeat block per matching function)
   ------------------------------------------
   FUNCTION: <name>
   KIND:     FUNCTION | PROCEDURE
   PARAMS:   <name type, name type, ...>
   RETURNS:  <return type>
   READS:    <comma-separated table list, or none>
   WRITES:   <INSERT table / UPDATE table / DELETE table — or none>
   ATTR IN:  PARAMETER | READ | WRITTEN | BOTH | NOT FOUND
   TRANSFORMATIONS:
     • <function>(<field>) → <TRANSFORM_TYPE>
       <one-line lineage implication>
     (repeat per transformation, or "none" if transformations[] is empty)
   ------------------------------------------

   Example (for a function that applies UPPER and COALESCE to telephone):
   ------------------------------------------
   FUNCTION: validate_customer
   KIND:     FUNCTION
   PARAMS:   p_telephone VARCHAR
   RETURNS:  void
   READS:    customers
   WRITES:   UPDATE customers
   ATTR IN:  BOTH
   TRANSFORMATIONS:
     • UPPER(telephone) → CASE_TRANSFORM
       Value is uppercased before storage — downstream comparisons must account for case
     • COALESCE(telephone, default) → NULL_HANDLE
       Null telephone replaced with a default value before write
   ------------------------------------------
   ==========================================
