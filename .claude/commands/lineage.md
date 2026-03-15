You are running the Data Lineage pipeline.
The repository under analysis is in repo/spring-petclinic/

The user query is: $ARGUMENTS

Follow these steps in order. Show a progress message 
before starting each step.

Step 1 - Apply orchestrator skill
  Parse the query. Extract attribute name, variants, 
  direction and which scanners are needed.

Step 2 - Apply db-scanner skill
  Scan repo/ for DB schema, JPA entities, SQL scripts.
  Find the attribute at the database layer.

Step 3 - Apply sql-scanner skill
  Scan repo/ for SQL files, stored procedures, triggers.
  Find the attribute in SQL logic layer.

Step 4 - Apply java-scanner skill
  Scan repo/ Java source for services, repositories,
  batch jobs that use the attribute.

Step 5 - Apply api-scanner skill
  Scan repo/ for REST controllers and forms that
  expose or receive the attribute.

Step 6 - Apply tracer skill
  Connect all findings into one lineage chain
  from sink to source or source to sink.

Step 7 - Apply collector skill
  Merge all paths. Remove duplicates.
  Structure the final lineage.

Step 8 - Apply graph-output skill
  Draw the visual ASCII lineage diagram.

Step 9 - Apply json-output skill
  Output the structured JSON lineage.

Step 10 - Apply report-output skill
  Write the full human-readable markdown report.

Label every output clearly. Do not skip any step.