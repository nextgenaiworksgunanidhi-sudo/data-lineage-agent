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

   BATCH LAYER — summary.batch_components[*]:
   - Check all entries where batch_role is one of:
       batch_reader    → reads rows containing the attribute
       batch_processor → transforms the attribute between read and write
       batch_writer    → writes rows containing the attribute
       batch_scoped    → @JobScope/@StepScope bean that may pass attribute
       batch_config    → @Bean method defining Step/Job/Tasklet
   - For each reader: record class, implements[], fields that match attribute
   - For each processor: note if attribute is transformed (renamed/computed)
   - For each writer: record class, what it writes and to where
   - For batch_config: trace which reader → processor → writer the Step wires together
   - If batch_components is empty: state "No Spring Batch components found"
     and continue — do NOT treat this as an error.

2. For each match found, record:
   - Layer: ENTITY | REPOSITORY | SERVICE | CONTROLLER | BATCH
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

   (for batch components — add this block after regular findings)
   ------------------------------------------
   [BATCH LAYER]
   ROLE:       READER | PROCESSOR | WRITER | SCOPED | CONFIG
   CLASS:      <ClassName.java>
   IMPLEMENTS: <ItemReader<X> | ItemProcessor<I,O> | ItemWriter<X>>
   ACTION:     READS | TRANSFORMS | WRITES
   FROM:       <data source — DB table, file, queue>
   TO:         <next component in chain — processor or writer>
   CHAIN:      <Reader → Processor → Writer if determinable from @Bean Step config>
   TRANSFORM:  none | <description — e.g. maps firstName to fname>
   ------------------------------------------
   (if no batch components found)
   [BATCH LAYER] No Spring Batch components found in repo.
   ==========================================
