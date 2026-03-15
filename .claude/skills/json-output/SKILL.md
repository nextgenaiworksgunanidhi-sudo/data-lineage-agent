---
name: json-output
description: Produces structured JSON representing the
             complete data lineage from COLLECTED LINEAGE.
             Use after collector has finished.
---

When producing JSON output:

1. Take COLLECTED LINEAGE nodes and edges

2. Structure the JSON exactly as:
{
  "lineage": {
    "attribute": "<name>",
    "direction": "source-to-sink | sink-to-source | both",
    "sensitive": true | false,
    "total_hops": <number>,
    "transformations": [],
    "paths": [
      {
        "path_id": 1,
        "type": "primary | secondary",
        "hops": [
          {
            "order": 1,
            "layer": "API | JAVA | ORM | DB",
            "component": "<exact class, table or endpoint>",
            "action": "RECEIVE | READ | WRITE | TRANSFORM | STORE | EXPOSE",
            "detail": "<specific method or column detail>"
          }
        ]
      }
    ]
  }
}

3. Use proper JSON formatting with 2-space indentation

4. Output exactly as:

   ==========================================
   JSON LINEAGE
   ==========================================
   <JSON here>
   ==========================================