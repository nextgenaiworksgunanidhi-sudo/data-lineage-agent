List all previous lineage query results saved in the
lineage-results/ folder.

Steps:

1. Check if the lineage-results/ folder exists and contains any subfolders.
   Run: ls lineage-results/ 2>/dev/null

   If the folder does not exist or is empty, output exactly:

   No lineage results saved yet.
   Run /lineage-save "your query" to generate and save results.

   Then stop.

2. For each subfolder found in lineage-results/:

   a) Parse the subfolder name to extract attribute and timestamp.
      Folder format: <attribute>_<YYYYMMDD_HHMMSS>
      Example: telephone_20260315_143022
        → attribute = telephone
        → timestamp = 20260315_143022
        → formatted date = 2026-03-15 14:30:22

   b) Read lineage-results/<subfolder>/lineage-summary.txt
      Extract these fields:
        Total hops:   → HOPS column
        Primary path: → SUMMARY column (truncate to 50 chars if longer)

   c) Count the number of files in the subfolder → FILES column

3. Sort rows by timestamp descending (most recent first).

4. Output exactly as:

   ==========================================
   LINEAGE HISTORY
   ==========================================
   Results found: <count>

   ATTRIBUTE    | DATE              | HOPS | FILES | SUMMARY
   -------------|-------------------|------|-------|--------------------------------------------------
   <attribute>  | <YYYY-MM-DD HH:MM>|  <n> |   4   | <primary path, max 50 chars>
   ...

   Run /lineage-save "<attribute>" to trace a new attribute and save results.
   Run /lineage-save "<attribute>" again to add a new timestamped entry.
   ==========================================
