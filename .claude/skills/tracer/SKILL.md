---
name: tracer
description: Connects all scan results into one complete
             lineage chain showing full path from source
             to sink or sink to source. Labels every edge
             with any transformation (RENAME, CONVERT,
             CASE_TRANSFORM, etc.) found at that hop.
             Use after all scanner agents have produced their results.
---

When tracing the full lineage chain:

1. Collect ALL labeled scan results from the conversation:
   DB SCAN RESULT
   SQL SCAN RESULT
   PLPGSQL SCAN RESULT
   JAVA SCAN RESULT
   MAPPER SCAN RESULT
   API SCAN RESULT

2. Build the ordered node list based on direction from orchestrator:

   For SINK-TO-SOURCE (DB → API):
   [DB]       Database column
   [ORM]      JPA Entity field
   [ORM]      Repository query
   [PLPGSQL]  Stored function/procedure  (if present)
   [MAPPER]   MapStruct / ModelMapper    (if present)
   [BATCH]    Batch Reader/Processor/Writer (if present)
   [SERVICE]  Service method             (if present)
   [JAVA]     Controller method
   [API]      REST endpoint or Form

   For SOURCE-TO-SINK (API → DB):
   [API]      REST endpoint or Form
   [JAVA]     Controller method
   [SERVICE]  Service method             (if present)
   [BATCH]    Batch Reader/Processor/Writer (if present)
   [MAPPER]   MapStruct / ModelMapper    (if present)
   [PLPGSQL]  Stored function/procedure  (if present)
   [ORM]      Repository / JPA Entity
   [DB]       Database column

   Skip any layer that has no findings for this attribute.

3. For each edge (arrow between two nodes) determine the edge label:

   EDGE LABEL RULES — check in this priority order:

   a) MAPPER edge — if [MAPPER SCAN RESULT] shows this attribute
      crossing a mapper between these two nodes:
      - source_field != target_field  → label: RENAME: fieldA → fieldB
      - transform = CONVERT           → label: CONVERT: qualifiedByName
      - transform = EXPRESSION        → label: EXPRESSION: <expr snippet>
      - transform = DIRECT            → label: (no transform label needed)

   b) PLPGSQL edge — if [PLPGSQL SCAN RESULT] shows a transformation
      on this attribute inside the function body:
      - CASE_TRANSFORM  → label: UPPER(field) applied
      - TRUNCATE        → label: SUBSTR(field) — value truncated
      - TYPE_CONVERT    → label: CONVERT: TO_CHAR / TO_DATE / etc.
      - NULL_HANDLE     → label: COALESCE(field, default)
      - CONDITIONAL     → label: CASE WHEN field — conditional branch
      - MERGE           → label: CONCAT / || — merged with other value
      - REPLACE         → label: REPLACE(field, ...) applied

   c) JAVA/SERVICE edge — if java-scanner shows type or format conversion:
      - Type change (String → Integer, etc.) → label: CONVERT: TypeA → TypeB
      - toString / parse call visible in method name → label: CONVERT

   d) No transformation found on this edge → draw plain arrow, no label

4. Format each node and its outgoing edge exactly as:

   [LAYER] ComponentName — action description
     ↓ fieldName (DataType)
     ↓ ── LABEL ──►
   [NEXT LAYER] NextComponent

   Rules:
   - First ↓/↑ line carries the field name and current data type
   - Second ↓/↑ line carries the transformation label (omit if no transform)
   - Use ↓ for source-to-sink, ↑ for sink-to-source
   - ── LABEL ──► is only shown when a transformation is present on that edge
   - Data type on the arrow reflects the type AFTER any conversion at that node

5. Flag any gaps where the trace is unclear:
   - Field name changes unexpectedly with no mapper found
   - Type changes with no converter found
   - Layer is skipped but data must cross it

6. Identify all TRANSFORMATIONS in a summary section at the end:
   List every edge where a label was applied, in chain order.
   For each: source node → target node | transform type | detail

7. Output exactly as:

   ==========================================
   LINEAGE CHAIN
   ==========================================
   ATTRIBUTE: <name>
   DIRECTION: sink-to-source | source-to-sink

   [LAYER] ComponentName — action
     ↓ fieldName (Type)
     ↓ ── RENAME: phoneNumber → telephone ──►
   [MAPPER] CustomerMapper.toCustomer()
     ↓ telephone (String)
     ↓ ── UPPER() applied ──►
   [PLPGSQL] validate_customer
     ↓ telephone (VARCHAR)
   [DB] customers.telephone

   SOURCE: <final source>
   SINK:   <final sink>

   TRANSFORMATIONS SUMMARY:
   • [API] → [MAPPER]   RENAME: phoneNumber → telephone
   • [MAPPER] → [PLPGSQL]  UPPER() → CASE_TRANSFORM
   (or: none)

   GAPS: none | <list of unclear hops>
   ==========================================
