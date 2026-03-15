---
name: tracer
description: Connects all scan results into one complete
             lineage chain showing full path from source
             to sink or sink to source. Use after all
             scanner agents have produced their results.
---

When tracing the full lineage chain:

1. Collect all labeled scan results from conversation:
   DB SCAN RESULT
   SQL SCAN RESULT
   JAVA SCAN RESULT
   API SCAN RESULT

2. Build the chain based on direction from orchestrator:

   For SINK-TO-SOURCE (DB → API):
   Database Column
     ↑ mapped by JPA Entity
     ↑ queried by Repository
     ↑ used by Service
     ↑ returned by Controller
     ↑ exposed via REST endpoint or Form

   For SOURCE-TO-SINK (API → DB):
   REST endpoint or Form
     ↓ received by Controller
     ↓ passed to Service
     ↓ saved by Repository
     ↓ mapped to JPA Entity
     ↓ stored in Database Column

3. For each hop in the chain specify:
   - Layer name in CAPS
   - Exact component (class name, table name, endpoint)
   - Action happening at this hop
   - Data format at this hop (if it changes)

4. Flag any gaps where trace is unclear

5. Identify if attribute is ever TRANSFORMED:
   - Masked (em***@domain.com)
   - Encrypted
   - Formatted
   - Renamed (email → emailAddress)

6. Output exactly as:

   ==========================================
   LINEAGE CHAIN
   ==========================================
   ATTRIBUTE: <name>
   DIRECTION: sink-to-source | source-to-sink
   
   [LAYER] Component — Action
     ↑ or ↓
   [LAYER] Component — Action
     ↑ or ↓
   ... (all hops)

   SOURCE: <final source endpoint/class>
   SINK:   <final sink table/column>
   
   TRANSFORMATIONS: none | <list>
   GAPS:  none | <list of unclear hops>
   ==========================================