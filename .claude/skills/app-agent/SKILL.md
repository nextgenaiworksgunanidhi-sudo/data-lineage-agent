---
name: app-agent
description: Application specialist agent. Calls
             java-scanner, api-scanner and mapper-scanner
             skills in sequence and combines results into
             one application layer finding. Runs in parallel
             with db-agent. Use for any lineage query.
---

When acting as app-agent:

1. Apply the java-scanner skill
   Collect result labeled [JAVA SCAN RESULT]

2. Apply the api-scanner skill
   Collect result labeled [API SCAN RESULT]

3. If ast-output/mapper-ast.json exists:
   Apply the mapper-scanner skill
   Collect result labeled [MAPPER SCAN RESULT]

4. Combine all three into:
   [APP AGENT RESULT]
   Contains: entity fields, repo methods, service
   methods, API endpoints, field renames/mappings
