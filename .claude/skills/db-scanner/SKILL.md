---
name: db-scanner
description: Scans the repo/ folder for database schema
             files, JPA entity classes, Spring Data
             repositories and SQL DDL scripts to find
             where an attribute exists at the DB layer.
             Use when tracing any attribute through the
             database layer.
---

When scanning the database layer for an attribute:

PRIORITY: Read ast-output/sql-ast.json first.

1. Read ast-output/sql-ast.json and search for the
   attribute and its variants in these locations:

   a) summary.all_tables[TABLE_NAME].columns[*].column
      — exact column name match against attribute variants
      — if found: record table name, column name, type,
        and constraints from that column entry

   b) summary.column_index[COLUMN_NAME]
      — lists every table that contains a given column name
      — use this for a fast existence check across all tables

   c) raw[*].inserts[*].table
      — tables that are written to in data.sql files
      — confirms the column receives real data at runtime

2. Also read ast-output/java-ast.json and search in:

   a) summary.entities[*].fields[*].name
      — match against attribute variants
      — if found: record entity class, field name, Java type,
        and field annotations (@Column, @NotBlank, etc.)
      — check field.relationship for @OneToMany/@ManyToOne
      — check field.join_column for FK column name

   b) summary.repositories[*].methods[*].name
      — match method names against variants (e.g. findByEmail)
      — check method.query for JPQL referencing the attribute

3. For each match found, record:
   - Table name
   - Column name (use field.column_name override if present,
     otherwise convert Java camelCase to snake_case)
   - Data type and constraints from sql-ast.json
   - JPA Entity class name and Java field name from java-ast.json
   - Repository class and any query methods using the attribute
   - Any foreign key relationships

4. If the attribute is NOT found in either AST file, state:
   "Attribute not found in DB layer"
   Do NOT fall back to scanning raw source files.

5. Output exactly as:

   ==========================================
   DB SCAN RESULT
   ==========================================
   TABLE:      <table name>
   COLUMN:     <column name>
   TYPE:       <data type and constraints>
   JPA ENTITY: <ClassName.java> field: <fieldName>
   REPOSITORY: <RepositoryName.java>
   QUERIES:    <list of query methods using attribute>
   FK REFS:    <any foreign key references>
   ==========================================
