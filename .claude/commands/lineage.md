You are running the Data Lineage pipeline.
Repository: repo/spring-petclinic/
User query: $ARGUMENTS

STEP 1 — Apply query-agent skill
  Understand intent, extract attribute name and variants

STEP 2 — Apply cache-checker skill
  Check for existing saved results and attribute-index.json
  If [CACHE HIT]:  show cached result, ask user: cached or fresh?
  If [INDEX HIT]:  use attribute-index.json locations, skip Steps 3-4
  If [CACHE MISS]: proceed to Steps 3-4 (full AST scan)

STEP 3 — Apply db-agent skill
  DB specialist: calls db-scanner + sql-scanner +
  plpgsql-scanner skills internally

STEP 4 — Apply app-agent skill
  App specialist: calls java-scanner + api-scanner +
  mapper-scanner skills internally

  Note: Steps 3 and 4 are independent — run both
  before moving to Step 5

STEP 5 — Apply transform-agent skill
  Calls tracer + collector skills internally
  Builds complete transformation chain

STEP 6 — Apply graph-output skill
STEP 7 — Apply json-output skill
STEP 8 — Apply report-output skill
  Save all outputs to lineage-results/ folder

Show progress as each agent and skill activates.
