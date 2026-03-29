---
name: openlineage-output
description: Produces an OpenLineage 1.0 compliant JSON document from
             COLLECTED LINEAGE. Compatible with DataHub, Marquez, Atlan,
             Apache Atlas and any OpenLineage-aware data catalog.
             Use after collector has finished. Saves openlineage.json
             to the lineage-results folder for the current run.
---

When producing the OpenLineage output:

## OpenLineage Concepts (map lineage findings to these)

  Run      → one execution of the lineage pipeline for this attribute
  Job      → each component/class that processes the attribute
             (one Job per hop: controller, entity, repo, etc.)
  Dataset  → each data store or API surface that holds the attribute
             (one Dataset per layer boundary: form, table, endpoint)
  Facet    → metadata attached to a Run, Job, or Dataset

## Structure to produce

Emit one JSON object per lineage event (one event = one hop/edge).
Wrap all events in a top-level array.

Each event follows the OpenLineage RunEvent schema:

{
  "eventType": "COMPLETE",
  "eventTime": "<ISO-8601 timestamp of pipeline run>",
  "run": {
    "runId": "<uuid — generate a stable UUID from attribute+timestamp>",
    "facets": {
      "processing_engine": {
        "_producer": "https://github.com/data-lineage-agent",
        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/ProcessingEngineFacet.json",
        "name": "Data Lineage Agent",
        "version": "1.0.0"
      }
    }
  },
  "job": {
    "namespace": "spring-petclinic",
    "name": "<component name — e.g. OwnerController.processCreationForm>",
    "facets": {
      "jobType": {
        "_producer": "https://github.com/data-lineage-agent",
        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/JobTypeJobFacet.json",
        "processingType": "BATCH",
        "integration": "SPRING_MVC",
        "jobType": "CONTROLLER | ENTITY | REPOSITORY | DATABASE | API_FORM | API_VIEW"
      }
    }
  },
  "inputs": [
    {
      "namespace": "<source system namespace>",
      "name": "<source component>",
      "facets": {
        "schema": {
          "_producer": "https://github.com/data-lineage-agent",
          "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
          "fields": [
            {
              "name": "<source_attribute>",
              "type": "<data type>",
              "description": "<optional description>"
            }
          ]
        },
        "columnLineage": {
          "_producer": "https://github.com/data-lineage-agent",
          "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/ColumnLineageDatasetFacet.json",
          "fields": {
            "<target_attribute>": {
              "inputFields": [
                {
                  "namespace": "<source namespace>",
                  "name": "<source component>",
                  "field": "<source_attribute>",
                  "transformations": [
                    {
                      "type": "DIRECT | INDIRECT",
                      "subtype": "NONE | VALIDATE | RENAME | CONVERT | FORMAT | MASK | TRUNCATE",
                      "description": "<human readable description>",
                      "masking": false
                    }
                  ]
                }
              ]
            }
          }
        }
      }
    }
  ],
  "outputs": [
    {
      "namespace": "<target system namespace>",
      "name": "<target component>",
      "facets": {
        "schema": {
          "_producer": "https://github.com/data-lineage-agent",
          "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
          "fields": [
            {
              "name": "<target_attribute>",
              "type": "<data type>",
              "description": "<optional description>"
            }
          ]
        },
        "dataQuality": {
          "_producer": "https://github.com/data-lineage-agent",
          "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DataQualityMetricsInputDatasetFacet.json",
          "columnMetrics": {
            "<target_attribute>": {
              "nullCount": null,
              "distinctCount": null,
              "validations": ["<@Pattern value or constraint if known>"]
            }
          }
        }
      }
    }
  ]
}

## Namespace conventions

Use these namespace values for spring-petclinic:

  Web Form layer:    "spring-petclinic://ui/forms"
  Controller layer:  "spring-petclinic://app/controllers"
  Entity layer:      "spring-petclinic://app/entities"
  Repository layer:  "spring-petclinic://app/repositories"
  Database layer:    "spring-petclinic://db/owners"  (use actual table)
  View layer:        "spring-petclinic://ui/views"

## Sensitive data facet

If sensitive=true, add this facet to every Dataset that holds the attribute:

  "sensitiveData": {
    "_producer": "https://github.com/data-lineage-agent",
    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DataSourceDatasetFacet.json",
    "pii": true,
    "category": "PHONE | EMAIL | NAME | ADDRESS | SSN | OTHER"
  }

## Output format

1. Emit the full array of RunEvents:

   ==========================================
   OPENLINEAGE OUTPUT
   ==========================================
   ```json
   [
     { ... event 1 ... },
     { ... event 2 ... },
     ...
   ]
   ```
   ==========================================

2. Save to the lineage-results folder for the current run:
   - The folder was already created by report-output in Step 7.
   - Use the same folder: lineage-results/<attribute>_<timestamp>/
   - Find it with: ls -td lineage-results/*/ | head -1
   - Save as: openlineage.json

3. Confirm save with one line:
   Saved: lineage-results/<folder>/openlineage.json  (<size> KB)
