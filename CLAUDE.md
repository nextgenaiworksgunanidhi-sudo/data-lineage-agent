## Project
Data Lineage Agent System — traces data attributes
(email, name, id, phone etc.) from database sink all
the way back to the source application (REST API,
Spring Service, Spring Batch).

## Repo under analysis
repo/spring-petclinic — Spring Boot + MySQL application.
Java + JPA + Thymeleaf + REST controllers.

## How to use
Type /lineage "your query" to trace any attribute.

Example queries:
  /lineage "trace owner email from database to source"
  /lineage "where does pet name originate?"
  /lineage "what writes to the owners table?"
  /lineage "trace firstName from REST API to database"

## Agent flow
/lineage → orchestrator → [db-scanner, sql-scanner,
java-scanner, api-scanner] parallel → tracer →
collector → [graph-output, json-output, report-output]

## Key paths in repo
Java source:   repo/spring-petclinic/src/main/java
SQL scripts:   repo/spring-petclinic/src/main/resources
Config:        repo/spring-petclinic/src/main/resources/application.properties