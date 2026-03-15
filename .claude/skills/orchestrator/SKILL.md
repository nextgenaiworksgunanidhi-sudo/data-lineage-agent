---
name: orchestrator
description: Parses a natural language lineage query to
             extract the attribute name, name variants,
             direction of tracing and which scanner
             agents to activate. Use at the start of
             every /lineage pipeline run.
---

When orchestrating a lineage query:

1. Extract the attribute name from the query
   Examples: email, name, pet name, firstName, owner id

2. Build a list of name variants to search for:
   email     → email, EMAIL, email_address, emailAddress
   name      → name, full_name, firstName, lastName, first_name
   id        → id, owner_id, ownerId, pet_id, petId
   phone     → phone, phone_number, phoneNumber, contact

3. Identify the trace direction:
   "from database" or "from DB"  → sink-to-source
   "to database"  or "to DB"     → source-to-sink
   "where does X originate"      → sink-to-source
   "what writes to X"            → source-to-sink
   not specified                 → both directions

4. Decide scanners needed:
   Always include: db-scanner, java-scanner, api-scanner
   Include sql-scanner if SQL files exist in repo/

5. Output exactly as:

   ==========================================
   ORCHESTRATOR OUTPUT
   ==========================================
   ATTRIBUTE:  <name>
   VARIANTS:   <comma separated variants>
   DIRECTION:  sink-to-source | source-to-sink | both
   SCANNERS:   db-scanner, sql-scanner, java-scanner, api-scanner
   STARTING LAYER: DB | API
   ==========================================