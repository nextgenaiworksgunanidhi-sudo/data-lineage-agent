---
name: mapper-scanner
description: Scans mapper-ast.json to find field renames and conversions
             between DTOs and entities via MapStruct or ModelMapper.
             Use when tracing attribute through the mapping layer.
---

When scanning mappers for an attribute:

PRIORITY: Read ast-output/mapper-ast.json first.

1. Check meta.total_mapstruct_mappers and meta.total_modelmapper_calls.
   If both are 0, state:
   "No MapStruct or ModelMapper mappings found in repo."
   and continue — do NOT treat as an error.

2. Search mappers[*].mappings[*] for the attribute and its variants:

   a) source_field matching any attribute variant
      — the attribute ENTERS this mapper method from the source class
      — record source_class, source_field, target_class, target_field

   b) target_field matching any attribute variant
      — the attribute EXITS this mapper method into the target class
      — record source_class, source_field, target_class, target_field

   For each match also note:
   - transform type:
       DIRECT     — source_field == target_field (same name, no rename)
       RENAME     — source_field != target_field (field was renamed)
       CONVERT    — qualifiedByName is set (custom converter method used)
       EXPRESSION — expression is set (inline Java expression used)
   - expression value if present (e.g. "java(source.getPhone())")
   - qualified_by_name value if present (e.g. "formatPhone")

3. Search model_mapper_calls[*] for the attribute:

   a) source_field or target_field matching any variant
      — explicit addMapping() call renames the field
      — record source_field, target_field, transform

   b) If only source_class / target_class available (no field detail):
      — state that ModelMapper performs class-level mapping;
        field mapping is determined at runtime by convention
        (matching field names mapped automatically)

4. For each match build a lineage hop:
   - The attribute flows FROM source_class.source_field
     INTO target_class.target_field
   - If transform is RENAME: flag this clearly — the field name
     changes at this layer and downstream layers will use the
     target_field name instead of the source_field name

5. Output exactly as:

   ==========================================
   MAPPER SCAN RESULT
   ==========================================
   MAPSTRUCT MAPPERS: <count>
   MODELMAPPER CALLS: <count>

   (if none found)
   No MapStruct or ModelMapper mappings found in repo.
   ==========================================

   (if found — repeat block per matching mapping)
   ------------------------------------------
   MAPPER:       <MapperClassName>  [MapStruct | ModelMapper]
   METHOD:       <methodName()>
   SOURCE:       <SourceClass>.<sourceField>
   TARGET:       <TargetClass>.<targetField>
   TRANSFORM:    DIRECT | RENAME | CONVERT | EXPRESSION
   EXPRESSION:   <value or null>
   QUALIFIED_BY: <qualifiedByName value or null>
   NOTE:         <any important lineage implication>
   ------------------------------------------
   ==========================================
