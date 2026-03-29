You are running the Data Lineage pipeline.
Repository: repo/spring-petclinic/
User query: $ARGUMENTS

STEP 0 — Apply cache-checker skill FIRST
  Check if this attribute was already traced.
  If [CACHE HIT]  → show cached result, ask user
                    if they want fresh analysis.
  If [INDEX HIT]  → use attribute-index.json for
                    fast lookup, skip full AST scan.
  If [CACHE MISS] → proceed to full pipeline below.

Only run Steps 1-7 if cache-checker returns
[CACHE MISS] or user explicitly requests fresh run.

STEP 1 — Apply query-agent skill
  Understand intent, extract attribute name and variants

STEP 2 — Apply db-agent skill
  DB specialist: calls db-scanner + sql-scanner +
  plpgsql-scanner skills internally

STEP 3 — Apply app-agent skill
  App specialist: calls java-scanner + api-scanner +
  mapper-scanner skills internally

  Note: Steps 2 and 3 are independent — run both
  before moving to Step 4

STEP 4 — Apply transform-agent skill
  Calls tracer + collector skills internally
  Builds complete transformation chain

STEP 5 — Apply graph-output skill
STEP 6 — Apply json-output skill
STEP 7 — Apply report-output skill
  Save lineage-report.md, lineage-graph.txt,
  lineage.json, lineage-summary.txt to lineage-results/ folder

STEP 8 — Apply csv-output skill  (run after Step 7)
  Produces lineage-matrix.csv — one row per hop
  Columns: source_system, source_component, source_attribute,
           target_system, target_component, target_attribute,
           transformation, sensitive
  Saves to same lineage-results/<attribute>_<timestamp>/ folder

STEP 9 — Apply openlineage-output skill  (run after Step 7)
  Produces openlineage.json — OpenLineage 1.0 spec format
  Compatible with DataHub, Marquez, Atlan, Apache Atlas
  Saves to same lineage-results/<attribute>_<timestamp>/ folder

  Note: Steps 8 and 9 are independent — run both in parallel.

Show progress as each agent and skill activates.
