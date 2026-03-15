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
  Save all outputs to lineage-results/ folder

Show progress as each agent and skill activates.
