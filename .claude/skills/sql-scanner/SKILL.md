---
name: sql-scanner
description: Scans repo/ for SQL files, stored procedures,
             triggers and views that read or write the
             attribute. Use when tracing through the SQL
             and database logic layer.
---

When scanning SQL files for an attribute:

1. Search repo/ for:
   - All .sql files
   - Files with stored procedure or function definitions
   - Files with CREATE TRIGGER statements
   - Files with CREATE VIEW statements

2. Search for all attribute variants from orchestrator

3. For each match note:
   - SQL object type: TABLE / PROCEDURE / TRIGGER / VIEW
   - Object name
   - Action: DEFINES / READS / WRITES / TRANSFORMS
   - Source table (where data comes from)
   - Target table (where data goes to)

4. If no stored procedures or triggers found:
   State clearly:
   "No stored procedures/triggers found in repo.
    Application uses JPA/ORM for all DB operations."
   Then list what SQL files DO exist and what they contain.

5. Output exactly as:

   ==========================================
   SQL SCAN RESULT
   ==========================================
   FILES FOUND: <list of .sql files>
   
   OBJECT: <object name>
   TYPE:   TABLE | PROCEDURE | TRIGGER | VIEW
   ACTION: DEFINES | READS | WRITES | TRANSFORMS
   SOURCE: <source table/input>
   TARGET: <target table/output>
   NOTE:   <any important detail>
   ==========================================