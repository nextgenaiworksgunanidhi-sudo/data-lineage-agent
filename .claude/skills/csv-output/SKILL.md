---
name: csv-output
description: Produces a CSV lineage matrix from COLLECTED LINEAGE.
             Each row represents one hop (source → target) with columns:
             source_system, source_component, source_attribute,
             target_system, target_component, target_attribute,
             transformation, sensitive.
             Use after collector has finished. Saves lineage-matrix.csv
             to the lineage-results folder for the current run.
---

When producing the CSV lineage matrix:

1. Take COLLECTED LINEAGE nodes and edges from the conversation.

2. For every edge in the lineage (each arrow between two nodes),
   produce one CSV row with these columns:

   source_system
     The layer/system the attribute is LEAVING.
     Use: "Web Form" | "Spring MVC" | "JPA Entity" | "Spring Data JPA"
          | "Hibernate ORM" | "MySQL" | "H2" | "Postgres"
          | "Thymeleaf View" | "REST API" | "Spring Batch"
          | "MapStruct" | "ModelMapper" | "PL/pgSQL"

   source_component
     The exact class name, table name, or template file.
     Examples: OwnerController.java, Owner.java,
               OwnerRepository.java, owners (table),
               createOrUpdateOwnerForm.html

   source_attribute
     The attribute name as it exists IN the source component.
     Use the exact field name, column name, or form field name.
     If the attribute was renamed at a previous hop, use the
     name that this source component knows it by.

   target_system
     The layer/system the attribute is ENTERING.
     Same vocabulary as source_system above.

   target_component
     The exact class name, table name, or template file
     of the receiving component.

   target_attribute
     The attribute name as it exists IN the target component.
     If a RENAME transformation happens on this edge,
     target_attribute will differ from source_attribute.

   transformation
     One of:
       NONE       — value passes through unchanged
       VALIDATE   — format/constraint check applied (value unchanged)
       RENAME     — field name changes between source and target
       CONVERT    — type conversion (e.g. String → Integer)
       FORMAT     — formatting applied (e.g. date format change)
       MASK       — value is partially hidden (e.g. ***-***-1234)
       TRUNCATE   — value is shortened (e.g. SUBSTR applied)
       UPPER      — UPPER() applied
       LOWER      — LOWER() applied
       COALESCE   — null substitution applied
       EXPRESSION — inline expression used in mapper/function
     If multiple apply, join with " + " (e.g. "VALIDATE + FORMAT")

   sensitive
     true  — attribute is PII or security-sensitive
             (phone, email, ssn, password, credit card, etc.)
     false — not sensitive

3. Build the full CSV:
   - First row: header line with column names
   - One row per edge in the lineage chain
   - Quote any value that contains a comma
   - Use UTF-8 encoding

4. Output the CSV in a fenced code block labeled csv:

   ==========================================
   CSV LINEAGE MATRIX
   ==========================================
   ```csv
   source_system,source_component,source_attribute,target_system,target_component,target_attribute,transformation,sensitive
   <row 1>
   <row 2>
   ...
   ```
   ==========================================

5. Save the CSV to the lineage-results folder for the current run:
   - The folder was already created by report-output in Step 7.
   - Use the same folder: lineage-results/<attribute>_<timestamp>/
   - Find it with: ls -td lineage-results/*/ | head -1
   - Save as: lineage-matrix.csv

6. Confirm save with one line:
   Saved: lineage-results/<folder>/lineage-matrix.csv  (<size> KB)
