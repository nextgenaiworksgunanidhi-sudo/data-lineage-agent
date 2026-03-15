You are running the Data Lineage pipeline.
Repository: repo/spring-petclinic/
User query: $ARGUMENTS

STEP 1 — Apply query-agent skill
  Understand intent, route to correct agents

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
