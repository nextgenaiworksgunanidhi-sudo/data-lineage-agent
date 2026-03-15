---
name: cache-checker
description: Checks if lineage for an attribute was
             already computed and saved. Use at the
             very start of every /lineage pipeline
             BEFORE running any other agent or skill.
             Prevents redundant full scans.
---

When checking the cache:

1. Get the attribute name from query-agent output

2. Check lineage-results/ folder for existing results:
   Look for any folder matching: <attribute>_*/
   Example: firstName_20260315_143022/

3. If cached result found:
   - Read lineage-summary.txt from that folder
   - Report:
     [CACHE HIT]
     Attribute: firstName
     Cached on: 2026-03-15 14:30
     Summary: <one line from lineage-summary.txt>

   - Ask user:
     "Cached lineage found from <date>.
      Use cached result or run fresh analysis?
      Type 'cached' to use saved result.
      Type 'fresh' to re-run the full pipeline."

4. If no cached result found:
   - Check ast-output/attribute-index.json
   - If attribute exists in index:
     [INDEX HIT]
     Found in attribute-index.json
     Locations: <list from index>
     Proceeding with fast lookup — no full scan needed.

   - If attribute NOT in index:
     [CACHE MISS]
     Not found in attribute-index.json
     Falling back to AST file scan.
     Note: if still not found in AST files,
     will fall back to raw file scanning.

5. Always output one of:
   [CACHE HIT]   → use saved lineage
   [INDEX HIT]   → use attribute-index.json
   [CACHE MISS]  → proceed to full AST scan
