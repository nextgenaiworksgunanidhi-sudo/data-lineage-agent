---
name: graph-output
description: Produces a clear visual ASCII lineage
             diagram from the COLLECTED LINEAGE.
             Use after collector has finished.
---

When producing the graph output:

1. Take COLLECTED LINEAGE nodes and edges

2. Draw a top-down ASCII box diagram:
   - Each node is a box with layer label and component name
   - Each edge is an arrow (↓ for source-to-sink, ↑ for sink-to-source)
   - Label each arrow with the action/relationship
   - Mark SOURCE node clearly at top or bottom
   - Mark SINK node clearly at opposite end

3. Use this box style:
   ┌─────────────────────────────────┐
   │ [LAYER]  Component name         │
   │ action description              │
   └─────────────────────────────────┘

4. Use arrows between boxes:
   ↓ action label      (source-to-sink direction)
   ↑ action label      (sink-to-source direction)

5. Add a legend at the bottom:
   [API]  = REST endpoint or web form
   [JAVA] = Spring Java class/method
   [ORM]  = JPA Repository / Entity
   [DB]   = Database table/column

6. Output exactly as:

   ==========================================
   LINEAGE GRAPH
   ==========================================
   
   <ASCII diagram here>
   
   LEGEND:
   [API]  REST endpoint or web form
   [JAVA] Spring Java class/method
   [ORM]  JPA Repository / Entity
   [DB]   Database table/column
   ==========================================