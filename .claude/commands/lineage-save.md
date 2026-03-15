You are running the Data Lineage pipeline with file output.
The repository under analysis is in repo/spring-petclinic/

The user query is: $ARGUMENTS

Follow these steps in order. Show a progress message
before starting each step.

Step 1 - Apply orchestrator skill
  Parse the query. Extract attribute name, variants,
  direction and which scanners are needed.

Step 1b - Apply cache-checker skill
  Check lineage-results/ for an existing saved result.
  Check ast-output/attribute-index.json for a fast lookup.
  If [CACHE HIT]: show summary, ask user: cached or fresh?
  If [INDEX HIT]: use index locations, skip Steps 2-5.
  If [CACHE MISS]: proceed with full scan below.

Step 2 - Apply db-scanner skill
  Scan repo/ for DB schema, JPA entities, SQL scripts.
  Find the attribute at the database layer.

Step 3 - Apply sql-scanner skill
  Scan repo/ for SQL files, stored procedures, triggers.
  Find the attribute in SQL logic layer.

Step 3b - Apply plpgsql-scanner skill
  Read ast-output/plpgsql-ast.json.
  Find PL/pgSQL functions and procedures that read,
  write, or transform the attribute. If no functions
  exist in the repo, state that clearly and continue.

Step 4 - Apply java-scanner skill
  Scan repo/ Java source for services, repositories,
  batch jobs that use the attribute.

Step 4b - Apply mapper-scanner skill
  Read ast-output/mapper-ast.json.
  Find MapStruct @Mapper interfaces and ModelMapper
  call sites where the attribute is renamed or
  converted between DTOs and entities. If no mappers
  exist in the repo, state that clearly and continue.

Step 5 - Apply api-scanner skill
  Scan repo/ for REST controllers and forms that
  expose or receive the attribute.

Step 6 - Apply tracer skill
  Connect all findings into one lineage chain
  from sink to source or source to sink.
  Label every edge with any transformation found.

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

---

SAVE ALL RESULTS TO FILES:

After completing all steps above:

1. Extract the attribute name from the ORCHESTRATOR OUTPUT.

2. Get the current timestamp:
   Run: date +%Y%m%d_%H%M%S
   Use this exact value as <timestamp>.

3. Create the output folder:
   Run: mkdir -p lineage-results/<attribute>_<timestamp>

4. Save these 4 files using the file creation tool:

   File 1: lineage-results/<attribute>_<timestamp>/lineage-report.md
   Content: the full markdown from the LINEAGE REPORT block

   File 2: lineage-results/<attribute>_<timestamp>/lineage-graph.txt
   Content: the ASCII diagram from the LINEAGE GRAPH block

   File 3: lineage-results/<attribute>_<timestamp>/lineage.json
   Content: the structured JSON from the JSON LINEAGE block

   File 4: lineage-results/<attribute>_<timestamp>/lineage-summary.txt
   Content (plain text, exactly this format):
     Attribute:       <name>
     Query:           <original user query>
     Date:            <today's date>
     Direction:       <sink-to-source | source-to-sink | both>
     Total hops:      <number from COLLECTED LINEAGE>
     Layers:          <comma-separated list from COLLECTED LINEAGE>
     Transformations: <list from TRANSFORMATIONS SUMMARY, or none>
     Primary path:    <one-line summary of the main lineage path>

5. Confirm all files were saved:

   Results saved to: lineage-results/<attribute>_<timestamp>/
   ┌─────────────────────────────────────────────────────┐
   │ lineage-report.md      <size> KB                    │
   │ lineage-graph.txt      <size> KB                    │
   │ lineage.json           <size> KB                    │
   │ lineage-summary.txt    <size> KB                    │
   └─────────────────────────────────────────────────────┘
