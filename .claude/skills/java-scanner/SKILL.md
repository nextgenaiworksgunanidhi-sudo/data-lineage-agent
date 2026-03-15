---
name: java-scanner
description: Scans Java Spring source code in repo/ to
             find where an attribute flows through
             services, repositories, batch jobs, event
             listeners and data mappers.
             Use when tracing attribute through the
             Java application layer.
---

When scanning Java source for an attribute:

PRIORITY: Read ast-output/java-ast.json first.

1. Read ast-output/java-ast.json and search for the
   attribute and its variants in these locations:

   ENTITY LAYER — summary.entities[*]:
   - Search fields[*].name against attribute variants
   - If found: record entity class name, field name,
     Java type, and annotations (e.g. @Column, @NotBlank)
   - Check field.relationship for @OneToMany/@ManyToOne
   - Check field.join_column for FK column name
   - Check field.column_name for @Column(name=...) overrides

   REPOSITORY LAYER — summary.repositories[*]:
   - Search methods[*].name against attribute variants
     (e.g. findByTelephone, findByName)
   - Search methods[*].query for JPQL containing variants
   - If found: record repository class, method signature,
     return type, and any @Query value

   SERVICE LAYER — summary.services[*]:
   - Search methods[*].name against attribute variants
   - Search methods[*].parameters[*].name against variants
   - If found: record service class, method name, and
     whether the attribute is a parameter or return value

   CONTROLLER LAYER — summary.controllers[*]:
   - Search methods[*].parameters[*].name against variants
   - Search methods[*].name against variants
   - If found: record controller class, HTTP method,
     URL path, and how the attribute enters/exits

2. For each match found, record:
   - Layer: ENTITY | REPOSITORY | SERVICE | CONTROLLER
   - Class name and method or field name
   - Action: DEFINES | READS | WRITES | TRANSFORMS | PASSES
   - Where data comes from and where it goes next

3. If the attribute is NOT found in any section of
   java-ast.json, state:
   "Attribute not found in Java layer"
   Do NOT fall back to scanning raw source files.

4. Output exactly as:

   ==========================================
   JAVA SCAN RESULT
   ==========================================
   LAYER:    ENTITY | REPOSITORY | SERVICE | CONTROLLER | BATCH
   CLASS:    <ClassName.java>
   METHOD:   <methodName()>
   ACTION:   DEFINES | READS | WRITES | TRANSFORMS | PASSES
   FROM:     <where data comes from>
   TO:       <where data goes next>
   DETAIL:   <any transformation or business logic note>
   ------------------------------------------
   (repeat for each finding)
   ==========================================
