Re-run the AST scanner to refresh all cached indexes.
Use this when:
- New code was added to the repo
- Existing code was modified
- A new repo was added to the repo/ folder

Steps:

1. Run the AST scanner:
   python3 tools/ast-scanner.py

2. Confirm java-ast.json was updated:
   Check that ast-output/java-ast.json modification
   timestamp is within the last 60 seconds.

3. Confirm sql-ast.json was updated:
   Check that ast-output/sql-ast.json modification
   timestamp is within the last 60 seconds.

4. Confirm attribute-index.json was rebuilt:
   Read ast-output/attribute-index.json and count
   the number of top-level keys (one per attribute).

5. Clear stale lineage cache:
   List all folders in lineage-results/.
   Delete any folder whose timestamp (parsed from
   the folder name <attribute>_YYYYMMDD_HHMMSS) is
   older than the current AST scan time.
   Report how many folders were removed.

6. Report the final status exactly as:

   ==========================================
   AST CACHE REFRESHED
   ==========================================
   java-ast.json       ✓ updated
   sql-ast.json        ✓ updated
   plpgsql-ast.json    ✓ updated
   mapper-ast.json     ✓ updated
   attribute-index.json ✓ rebuilt — X attributes indexed

   Stale lineage cache cleared: N folder(s) removed
   Lineage cache kept: M folder(s) still valid

   Ready. Run /lineage to trace any attribute.
   ==========================================
