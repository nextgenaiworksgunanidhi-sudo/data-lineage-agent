#!/usr/bin/env python3
"""
AST Scanner for Data Lineage Agent System
Parses Java and SQL files in repo/ using javalang and sqlglot.
Outputs structured JSON to ast-output/ for use by scanner skills.
"""

import json
import os
import sys
from pathlib import Path

# ── dependency check ────────────────────────────────────────────────────────

missing = []
try:
    import javalang
except ImportError:
    missing.append("javalang")

try:
    import sqlglot
    import sqlglot.expressions as exp
except ImportError:
    missing.append("sqlglot")

if missing:
    print(f"Missing required libraries: {', '.join(missing)}")
    print(f"Install with:  pip install {' '.join(missing)}")
    sys.exit(1)

# ── paths ────────────────────────────────────────────────────────────────────

ROOT      = Path(__file__).parent.parent          # data-lineage/
REPO      = ROOT / "repo"
OUT_DIR   = ROOT / "ast-output"
JAVA_OUT  = OUT_DIR / "java-ast.json"
SQL_OUT   = OUT_DIR / "sql-ast.json"

PLPGSQL_OUT = OUT_DIR / "plpgsql-ast.json"

OUT_DIR.mkdir(exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# JAVA AST SCANNER
# ════════════════════════════════════════════════════════════════════════════

SPRING_ANNOTATIONS = {
    "entity":     {"Entity"},
    "repository": {"Repository"},
    "service":    {"Service"},
    "controller": {"Controller", "RestController"},
    "mapping":    {"RequestMapping", "GetMapping", "PostMapping",
                   "PutMapping", "DeleteMapping", "PatchMapping"},
}

# Spring Batch interface names (simple and generic forms)
BATCH_READER_IFACES    = {"ItemReader", "ItemStreamReader", "FlatFileItemReader",
                           "JdbcCursorItemReader", "JpaPagingItemReader",
                           "JdbcPagingItemReader", "RepositoryItemReader"}
BATCH_PROCESSOR_IFACES = {"ItemProcessor"}
BATCH_WRITER_IFACES    = {"ItemWriter", "ItemStreamWriter", "FlatFileItemWriter",
                           "JdbcBatchItemWriter", "JpaItemWriter",
                           "RepositoryItemWriter"}
BATCH_SCOPE_ANNOTATIONS = {"JobScope", "StepScope"}
BATCH_RETURN_TYPES      = {"Step", "Job", "Tasklet", "Flow", "JobExecutionDecider"}


def annotation_names(node) -> set:
    """Return the set of annotation names on a type/method declaration."""
    names = set()
    for ann in getattr(node, "annotations", []) or []:
        names.add(ann.name)
    return names


def annotation_value(annotations, name: str, element: str = "value"):
    """Extract a single annotation element value, or None."""
    for ann in annotations or []:
        if ann.name == name and ann.element:
            # element may be a MemberReference, Literal, or list
            el = ann.element
            if hasattr(el, "value"):
                return el.value.strip('"')
            if hasattr(el, "member"):
                return el.member
            if isinstance(el, list):
                return [
                    (e.value.strip('"') if hasattr(e, "value") else str(e))
                    for e in el
                ]
    return None


def field_annotations(field) -> list:
    names = []
    for ann in getattr(field, "annotations", []) or []:
        names.append(ann.name)
    return names


def parse_java_file(path: Path) -> dict | None:
    """Parse one .java file and return a structured dict, or None on error."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = javalang.parse.parse(source)
    except Exception as e:
        return {"file": str(path.relative_to(ROOT)), "error": str(e)}

    result = {
        "file":        str(path.relative_to(ROOT)),
        "package":     tree.package.name if tree.package else None,
        "imports":     [i.path for i in (tree.imports or [])],
        "classes":     [],
    }

    for _, cls in tree.filter(javalang.tree.ClassDeclaration):
        ann_names = annotation_names(cls)
        layer = _detect_layer(ann_names)

        implements_names = [i.name for i in (cls.implements or [])]
        batch_role = _detect_batch_role(ann_names, implements_names)

        cls_info = {
            "name":        cls.name,
            "layer":       layer,
            "annotations": list(ann_names),
            "extends":     cls.extends.name if cls.extends else None,
            "implements":  implements_names,
            "fields":      [],
            "methods":     [],
        }
        if batch_role:
            cls_info["batch_role"] = batch_role

        # ── @Entity / @Table details ──────────────────────────────────────
        if layer == "entity":
            for ann in (cls.annotations or []):
                if ann.name == "Table" and ann.element:
                    el = ann.element
                    if hasattr(el, "value"):
                        cls_info["table_name"] = el.value.strip('"')
                    elif isinstance(el, list):
                        for pair in el:
                            if hasattr(pair, "name") and pair.name == "name":
                                cls_info["table_name"] = pair.value.value.strip('"')

        # ── Fields ───────────────────────────────────────────────────────
        for _, field_decl in javalang.tree.FieldDeclaration and \
                [(p, n) for p, n in tree.filter(javalang.tree.FieldDeclaration)
                 if _in_class(p, cls.name)]:
            f_anns = field_annotations(field_decl)
            for declarator in field_decl.declarators:
                field_info = {
                    "name":        declarator.name,
                    "type":        _type_name(field_decl.type),
                    "annotations": f_anns,
                }
                # extract @Column(name=...) override if present
                for ann in (field_decl.annotations or []):
                    if ann.name == "Column" and ann.element:
                        el = ann.element
                        if isinstance(el, list):
                            for pair in el:
                                if hasattr(pair, "name") and pair.name == "name":
                                    field_info["column_name"] = pair.value.value.strip('"')
                    if ann.name in ("JoinColumn",):
                        if ann.element:
                            el = ann.element
                            if hasattr(el, "value"):
                                field_info["join_column"] = el.value.strip('"')
                            elif isinstance(el, list):
                                for pair in el:
                                    if hasattr(pair, "name") and pair.name == "name":
                                        field_info["join_column"] = pair.value.value.strip('"')
                    if ann.name in ("OneToMany", "ManyToOne", "OneToOne", "ManyToMany"):
                        field_info["relationship"] = ann.name
                cls_info["fields"].append(field_info)

        # ── Methods ──────────────────────────────────────────────────────
        for _, method in javalang.tree.MethodDeclaration and \
                [(p, n) for p, n in tree.filter(javalang.tree.MethodDeclaration)
                 if _in_class(p, cls.name)]:
            m_anns = annotation_names(method)
            m_info = {
                "name":        method.name,
                "return_type": _type_name(method.return_type) if method.return_type else "void",
                "parameters":  [
                    {"name": p.name, "type": _type_name(p.type)}
                    for p in (method.parameters or [])
                ],
                "annotations": list(m_anns),
            }

            # endpoint mapping
            for ann in (method.annotations or []):
                if ann.name in SPRING_ANNOTATIONS["mapping"]:
                    m_info["http_method"] = _http_method(ann.name)
                    if ann.element:
                        el = ann.element
                        if hasattr(el, "value"):
                            m_info["path"] = el.value.strip('"')
                        elif isinstance(el, list):
                            for pair in el:
                                if hasattr(pair, "name") and pair.name in ("value", "path"):
                                    v = pair.value
                                    m_info["path"] = v.value.strip('"') if hasattr(v, "value") else str(v)
                # @Query value
                if ann.name == "Query" and ann.element:
                    el = ann.element
                    if hasattr(el, "value"):
                        m_info["query"] = el.value.strip('"')
                    elif isinstance(el, list):
                        for pair in el:
                            if hasattr(pair, "name") and pair.name == "value":
                                m_info["query"] = pair.value.value.strip('"')
                # @Bean returning a Spring Batch type → batch configuration
                if ann.name == "Bean":
                    ret = _type_name(method.return_type) if method.return_type else ""
                    # strip generic: Step<X> → Step
                    ret_base = ret.split("<")[0]
                    if ret_base in BATCH_RETURN_TYPES:
                        m_info["batch_role"]   = "batch_config"
                        m_info["batch_type"]   = ret_base

            cls_info["methods"].append(m_info)

        result["classes"].append(cls_info)

    # also capture interfaces (repositories are interfaces)
    for _, iface in tree.filter(javalang.tree.InterfaceDeclaration):
        ann_names = annotation_names(iface)
        layer = _detect_layer(ann_names)
        # JpaRepository subinterfaces have no @Repository but extend JpaRepository
        extends_names = [e.name for e in (iface.extends or [])]
        if any("Repository" in e for e in extends_names):
            layer = "repository"

        iface_info = {
            "name":        iface.name,
            "layer":       layer,
            "annotations": list(ann_names),
            "extends":     extends_names,
            "methods":     [],
        }

        for _, method in [(p, n) for p, n in tree.filter(javalang.tree.MethodDeclaration)
                          if _in_interface(p, iface.name)]:
            m_anns = annotation_names(method)
            m_info = {
                "name":        method.name,
                "return_type": _type_name(method.return_type) if method.return_type else "void",
                "parameters":  [
                    {"name": p.name, "type": _type_name(p.type)}
                    for p in (method.parameters or [])
                ],
                "annotations": list(m_anns),
            }
            for ann in (method.annotations or []):
                if ann.name == "Query" and ann.element:
                    el = ann.element
                    if hasattr(el, "value"):
                        m_info["query"] = el.value.strip('"')
            iface_info["methods"].append(m_info)

        result["classes"].append(iface_info)

    return result


def _detect_batch_role(ann_names: set, implements_names: list) -> str | None:
    """
    Return the Spring Batch role of a class, or None if it is not a batch component.
    Checks both implements list (for reader/processor/writer) and
    annotations (for @JobScope / @StepScope beans).
    """
    impl_set = set(implements_names)
    if impl_set & BATCH_READER_IFACES or any(
        i in name for name in implements_names for i in ("ItemReader",)
    ):
        return "batch_reader"
    if impl_set & BATCH_PROCESSOR_IFACES or any(
        "ItemProcessor" in name for name in implements_names
    ):
        return "batch_processor"
    if impl_set & BATCH_WRITER_IFACES or any(
        i in name for name in implements_names for i in ("ItemWriter",)
    ):
        return "batch_writer"
    if ann_names & BATCH_SCOPE_ANNOTATIONS:
        return "batch_scoped"
    return None


def _detect_layer(ann_names: set) -> str:
    for layer, anns in SPRING_ANNOTATIONS.items():
        if ann_names & anns:
            return layer
    return "other"


def _in_class(path, class_name: str) -> bool:
    for node in path:
        if isinstance(node, javalang.tree.ClassDeclaration) and node.name == class_name:
            return True
    return False


def _in_interface(path, iface_name: str) -> bool:
    for node in path:
        if isinstance(node, javalang.tree.InterfaceDeclaration) and node.name == iface_name:
            return True
    return False


def _type_name(type_node) -> str:
    if type_node is None:
        return "void"
    name = getattr(type_node, "name", str(type_node))
    args = getattr(type_node, "arguments", None)
    if args:
        inner = ", ".join(_type_name(a.type if hasattr(a, "type") else a) for a in args)
        return f"{name}<{inner}>"
    return name


def _http_method(ann_name: str) -> str:
    mapping = {
        "GetMapping":    "GET",
        "PostMapping":   "POST",
        "PutMapping":    "PUT",
        "DeleteMapping": "DELETE",
        "PatchMapping":  "PATCH",
        "RequestMapping": "REQUEST",
    }
    return mapping.get(ann_name, ann_name)


def _collect_inherited_fields(class_name: str,
                               class_index: dict,
                               visited: set | None = None) -> list:
    """Walk the extends chain and return all ancestor fields (parent-first)."""
    if visited is None:
        visited = set()
    if class_name in visited or class_name in (None, "Object"):
        return []
    visited.add(class_name)

    info = class_index.get(class_name)
    if info is None:
        return []

    parent_name = info.get("extends")
    # extends may be a string (class) or list (interfaces) — take string only
    if isinstance(parent_name, list):
        parent_name = None

    parent_fields = _collect_inherited_fields(parent_name, class_index, visited)
    return parent_fields + info.get("fields", [])


def scan_java(repo_root: Path) -> dict:
    java_files = list(repo_root.rglob("*.java"))
    results = []
    errors = []

    for jf in java_files:
        parsed = parse_java_file(jf)
        if parsed:
            if "error" in parsed:
                errors.append(parsed)
            else:
                results.append(parsed)

    # ── Build a flat class index for inheritance resolution ──────────────────
    # class_name → {fields, extends, layer}
    class_index: dict[str, dict] = {}
    for r in results:
        for cls in r.get("classes", []):
            class_index[cls["name"]] = {
                "fields":  cls.get("fields", []),
                "extends": cls.get("extends"),   # simple class name string
                "layer":   cls.get("layer", "other"),
            }

    # build summary indices
    entities          = []
    repositories      = []
    services          = []
    controllers       = []
    batch_components  = []   # readers, processors, writers, scoped beans, config

    for r in results:
        for cls in r.get("classes", []):
            layer = cls.get("layer", "other")
            entry = {"file": r["file"], "class": cls["name"], "annotations": cls["annotations"]}
            if layer == "entity":
                entry["table"] = cls.get("table_name")
                # own fields + all inherited fields from @MappedSuperclass chain
                inherited = _collect_inherited_fields(
                    cls.get("extends"), class_index, visited={cls["name"]}
                )
                entry["fields"] = inherited + cls["fields"]
                entities.append(entry)
            elif layer == "repository":
                entry["extends"]  = cls.get("extends", [])
                entry["methods"]  = cls["methods"]
                repositories.append(entry)
            elif layer == "service":
                entry["methods"] = cls["methods"]
                services.append(entry)
            elif layer == "controller":
                entry["methods"] = cls["methods"]
                controllers.append(entry)

            # ── Spring Batch: class-level reader / processor / writer ──────
            batch_role = cls.get("batch_role")
            if batch_role:
                batch_components.append({
                    "file":       r["file"],
                    "class":      cls["name"],
                    "batch_role": batch_role,
                    "implements": cls.get("implements", []),
                    "annotations": cls["annotations"],
                    "fields":     cls.get("fields", []),
                    "methods":    cls.get("methods", []),
                })

            # ── Spring Batch: @Bean methods that define Step / Job / Tasklet ─
            for method in cls.get("methods", []):
                if method.get("batch_role") == "batch_config":
                    batch_components.append({
                        "file":       r["file"],
                        "class":      cls["name"],
                        "batch_role": "batch_config",
                        "batch_type": method.get("batch_type"),
                        "method":     method["name"],
                        "parameters": method.get("parameters", []),
                        "annotations": cls["annotations"],
                    })

    return {
        "meta": {
            "total_files_scanned": len(java_files),
            "total_parsed":        len(results),
            "parse_errors":        len(errors),
        },
        "summary": {
            "entities":         entities,
            "repositories":     repositories,
            "services":         services,
            "controllers":      controllers,
            "batch_components": batch_components,
        },
        "raw": results,
        "errors": errors,
    }


# ════════════════════════════════════════════════════════════════════════════
# SQL AST SCANNER
# ════════════════════════════════════════════════════════════════════════════

def _sql_dialect(_path: Path) -> str:
    """Always use postgres — the canonical dialect for this scanner."""
    return "postgres"


def scan_sql_file(path: Path) -> dict:
    """Parse one SQL file with sqlglot (postgres dialect) and extract schema + DML references."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        statements = sqlglot.parse(source, dialect="postgres",
                                   error_level=sqlglot.ErrorLevel.WARN)
    except Exception as e:
        return {"file": str(path.relative_to(ROOT)), "error": str(e)}

    tables_created   = {}   # table_name → {columns: [...]}
    inserts          = []
    updates          = []
    selects          = []
    parse_errors     = []

    for stmt in statements:
        if stmt is None:
            continue

        # ── CREATE TABLE ──────────────────────────────────────────────────
        if isinstance(stmt, exp.Create):
            tbl_expr = stmt.find(exp.Table)
            tbl_name = tbl_expr.name if tbl_expr else None
            if tbl_name:
                cols = []
                schema = stmt.find(exp.Schema)
                if schema:
                    for col_def in schema.find_all(exp.ColumnDef):
                        kind = col_def.args.get("kind")
                        # Normalise SERIAL / BIGSERIAL / SMALLSERIAL display
                        if kind and hasattr(kind, "this"):
                            type_str = str(kind.this).upper()
                            if type_str not in ("SERIAL", "BIGSERIAL", "SMALLSERIAL"):
                                type_str = kind.sql(dialect="postgres")
                        else:
                            type_str = kind.sql(dialect="postgres") if kind else None
                        col_entry = {
                            "column": col_def.name,
                            "type":   type_str,
                            "constraints": [c.sql(dialect="postgres") for c in col_def.find_all(exp.ColumnConstraint)],
                        }
                        cols.append(col_entry)
                tables_created[tbl_name] = {"columns": cols}

        # ── INSERT ────────────────────────────────────────────────────────
        elif isinstance(stmt, exp.Insert):
            tbl = stmt.find(exp.Table)
            cols = [c.name for c in stmt.find_all(exp.Column)]
            # values are literals — grab them as strings
            vals = [v.sql() for v in stmt.find_all(exp.Literal)]
            # PostgreSQL RETURNING clause
            returning = stmt.args.get("returning")
            returning_cols = [c.sql() for c in returning.find_all(exp.Column)] if returning else []
            entry = {
                "table":   tbl.name if tbl else None,
                "columns": cols,
                "values":  vals[:len(cols)] if cols else vals,
            }
            if returning_cols:
                entry["returning"] = returning_cols
            inserts.append(entry)

        # ── UPDATE ────────────────────────────────────────────────────────
        elif isinstance(stmt, exp.Update):
            tbl = stmt.find(exp.Table)
            sets = []
            for eq in stmt.find_all(exp.EQ):
                col = eq.find(exp.Column)
                val = eq.right
                if col:
                    sets.append({"column": col.name, "value": val.sql() if val else None})
            # PostgreSQL RETURNING clause
            returning = stmt.args.get("returning")
            returning_cols = [c.sql() for c in returning.find_all(exp.Column)] if returning else []
            entry = {
                "table": tbl.name if tbl else None,
                "sets":  sets,
            }
            if returning_cols:
                entry["returning"] = returning_cols
            updates.append(entry)

        # ── SELECT ────────────────────────────────────────────────────────
        elif isinstance(stmt, exp.Select):
            from_tables = [t.name for t in stmt.find_all(exp.Table)]
            sel_cols    = [c.sql() for c in stmt.find_all(exp.Column)]
            # PostgreSQL $1, $2, ... parameter placeholders
            placeholders = [p.sql(dialect="postgres") for p in stmt.find_all(exp.Placeholder)]
            entry = {
                "tables":  from_tables,
                "columns": sel_cols,
            }
            if placeholders:
                entry["parameters"] = placeholders
            selects.append(entry)

    return {
        "file":           str(path.relative_to(ROOT)),
        "tables_created": tables_created,
        "inserts":        inserts,
        "updates":        updates,
        "selects":        selects,
        "parse_errors":   parse_errors,
    }


def scan_sql(repo_root: Path) -> dict:
    sql_files = list(repo_root.rglob("*.sql"))
    results   = []
    errors    = []

    for sf in sql_files:
        parsed = scan_sql_file(sf)
        if "error" in parsed:
            errors.append(parsed)
        else:
            results.append(parsed)

    # aggregate all tables across files
    all_tables: dict[str, dict] = {}
    for r in results:
        for tbl, info in r.get("tables_created", {}).items():
            all_tables[tbl] = info

    # aggregate all column names referenced (from inserts + creates)
    col_index: dict[str, list] = {}  # column_name → [table, ...]
    for tbl, info in all_tables.items():
        for col in info["columns"]:
            col_index.setdefault(col["column"], []).append(tbl)

    return {
        "meta": {
            "total_files_scanned": len(sql_files),
            "total_parsed":        len(results),
            "parse_errors":        len(errors),
        },
        "summary": {
            "all_tables":  all_tables,
            "column_index": col_index,
            "insert_count": sum(len(r["inserts"]) for r in results),
            "update_count": sum(len(r["updates"]) for r in results),
            "select_count": sum(len(r["selects"]) for r in results),
        },
        "raw":    results,
        "errors": errors,
    }


# ════════════════════════════════════════════════════════════════════════════
# PL/pgSQL SCANNER
# ════════════════════════════════════════════════════════════════════════════

import re as _re


def _parse_plpgsql_params(params_str: str) -> list:
    """Parse a PL/pgSQL parameter list string into [{name, type}] dicts."""
    params = []
    for part in params_str.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        # Drop IN / OUT / INOUT / VARIADIC mode keyword if present
        if tokens and tokens[0].upper() in ("IN", "OUT", "INOUT", "VARIADIC"):
            tokens = tokens[1:]
        if len(tokens) >= 2:
            params.append({"name": tokens[0], "type": " ".join(tokens[1:])})
        elif len(tokens) == 1:
            params.append({"name": "_", "type": tokens[0]})
    return params


def _scan_plpgsql_body(body: str) -> tuple:
    """
    Scan the body of a PL/pgSQL function for tables read and written.
    Returns (reads: list[str], writes: list[dict]).
    """
    # Strip DECLARE section so we only look at the executable block
    exec_block = _re.sub(r'(?is)^.*?BEGIN', '', body, count=1)
    exec_block = _re.sub(r'(?is)\bEND\s*;?\s*$', '', exec_block)

    reads  = []
    writes = []

    for m in _re.finditer(r'(?i)\bFROM\s+(\w+)', exec_block):
        tbl = m.group(1).lower()
        if tbl not in reads:
            reads.append(tbl)

    for m in _re.finditer(r'(?i)\bJOIN\s+(\w+)', exec_block):
        tbl = m.group(1).lower()
        if tbl not in reads:
            reads.append(tbl)

    for m in _re.finditer(r'(?i)\bINSERT\s+INTO\s+(\w+)', exec_block):
        entry = {"table": m.group(1).lower(), "operation": "INSERT"}
        if entry not in writes:
            writes.append(entry)

    for m in _re.finditer(r'(?i)\bUPDATE\s+(\w+)', exec_block):
        entry = {"table": m.group(1).lower(), "operation": "UPDATE"}
        if entry not in writes:
            writes.append(entry)

    for m in _re.finditer(r'(?i)\bDELETE\s+FROM\s+(\w+)', exec_block):
        entry = {"table": m.group(1).lower(), "operation": "DELETE"}
        if entry not in writes:
            writes.append(entry)

    return reads, writes


def _extract_plpgsql_functions(source: str, path: Path) -> list:
    """
    Extract all PL/pgSQL FUNCTION and PROCEDURE definitions from SQL source.
    Handles dollar-quoted bodies: AS $$ ... $$ or AS $body$ ... $body$.
    """
    results = []

    # Match CREATE [OR REPLACE] FUNCTION|PROCEDURE name(params)
    # then optionally RETURNS type, then AS $$body$$
    header_pat = _re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?'
        r'(?P<kind>FUNCTION|PROCEDURE)\s+'
        r'(?P<name>\w+)\s*\((?P<params>[^)]*)\)'
        r'(?:\s+RETURNS\s+(?P<returns>\S+))?'
        r'.*?'
        r'AS\s+(?P<dollar>\$\w*\$)'   # opening dollar-quote tag, e.g. $$ or $body$
        ,
        _re.IGNORECASE | _re.DOTALL,
    )

    for m in header_pat.finditer(source):
        tag        = _re.escape(m.group("dollar"))   # e.g. \$\$ or \$body\$
        body_start = m.end()
        body_match = _re.search(tag, source[body_start:])
        if not body_match:
            continue   # unterminated dollar-quote — skip

        body = source[body_start: body_start + body_match.start()]
        reads, writes = _scan_plpgsql_body(body)

        results.append({
            "file":       str(path.relative_to(ROOT)),
            "kind":       m.group("kind").upper(),
            "name":       m.group("name"),
            "parameters": _parse_plpgsql_params(m.group("params") or ""),
            "returns":    (m.group("returns") or "void").strip(),
            "reads":      reads,
            "writes":     writes,
        })

    return results


def scan_plpgsql(repo_root: Path) -> dict:
    """Scan all .sql files in repo_root for PL/pgSQL function/procedure definitions."""
    sql_files = list(repo_root.rglob("*.sql"))
    functions = []
    errors    = []

    for sf in sql_files:
        try:
            source   = sf.read_text(encoding="utf-8", errors="replace")
            found    = _extract_plpgsql_functions(source, sf)
            functions.extend(found)
        except Exception as e:
            errors.append({"file": str(sf.relative_to(ROOT)), "error": str(e)})

    return {
        "meta": {
            "total_files_scanned": len(sql_files),
            "total_functions":     len(functions),
            "parse_errors":        len(errors),
        },
        "functions": functions,
        "errors":    errors,
    }


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def print_summary(java_data: dict, sql_data: dict, plpgsql_data: dict) -> None:
    jm = java_data["meta"]
    sm = sql_data["meta"]
    js = java_data["summary"]
    ss = sql_data["summary"]

    print("\n" + "═" * 54)
    print("  AST SCANNER — SUMMARY")
    print("═" * 54)

    print(f"\n  JAVA ({jm['total_files_scanned']} files, "
          f"{jm['total_parsed']} parsed, "
          f"{jm['parse_errors']} errors)")
    print(f"  {'Entities':20s} {len(js['entities'])}")
    for e in js["entities"]:
        tbl = f" → table: {e['table']}" if e.get("table") else ""
        print(f"    • {e['class']}{tbl}")
        for f in e.get("fields", []):
            anns = ", ".join(f["annotations"]) if f["annotations"] else "—"
            print(f"        {f['name']:20s}  {f['type']:20s}  [{anns}]")

    print(f"\n  {'Repositories':20s} {len(js['repositories'])}")
    for r in js["repositories"]:
        ext = ", ".join(r.get("extends", []))
        print(f"    • {r['class']}  extends {ext}")
        for m in r.get("methods", []):
            q = f"  @Query: {m['query'][:60]}" if m.get("query") else ""
            print(f"        {m['name']}(){q}")

    print(f"\n  {'Services':20s} {len(js['services'])}")
    for s in js["services"]:
        print(f"    • {s['class']}  ({len(s['methods'])} methods)")

    print(f"\n  {'Controllers':20s} {len(js['controllers'])}")
    for c in js["controllers"]:
        print(f"    • {c['class']}")
        for m in c.get("methods", []):
            if m.get("http_method"):
                print(f"        {m['http_method']:8s} {m.get('path', '—'):40s} → {m['name']}()")

    batch = js.get("batch_components", [])
    print(f"\n  {'Batch Components':20s} {len(batch)}")
    if batch:
        for b in batch:
            role = b.get("batch_role", "?")
            if role == "batch_config":
                print(f"    • [CONFIG]     {b['class']}.{b.get('method','?')}() → {b.get('batch_type','?')}")
            else:
                label = {
                    "batch_reader":    "READER   ",
                    "batch_processor": "PROCESSOR",
                    "batch_writer":    "WRITER   ",
                    "batch_scoped":    "SCOPED   ",
                }.get(role, role.upper())
                impls = ", ".join(b.get("implements", [])) or "—"
                print(f"    • [{label}] {b['class']}  implements: {impls}")
    else:
        print("    (none found)")

    print(f"\n  SQL ({sm['total_files_scanned']} files, "
          f"{sm['total_parsed']} parsed, "
          f"{sm['parse_errors']} errors)")
    print(f"  {'Tables defined':20s} {len(ss['all_tables'])}")
    for tbl, info in ss["all_tables"].items():
        cols = ", ".join(c["column"] for c in info["columns"])
        print(f"    • {tbl:20s}  columns: {cols}")

    print(f"\n  INSERT statements:  {ss['insert_count']}")
    print(f"  UPDATE statements:  {ss['update_count']}")
    print(f"  SELECT statements:  {ss['select_count']}")

    pm = plpgsql_data["meta"]
    print(f"\n  PL/pgSQL ({pm['total_files_scanned']} files scanned, "
          f"{pm['total_functions']} functions found, "
          f"{pm['parse_errors']} errors)")
    if plpgsql_data["functions"]:
        for fn in plpgsql_data["functions"]:
            params = ", ".join(f"{p['name']} {p['type']}" for p in fn["parameters"]) or "—"
            print(f"    • {fn['kind']} {fn['name']}({params}) → {fn['returns']}")
            if fn["reads"]:
                print(f"        READS:  {', '.join(fn['reads'])}")
            if fn["writes"]:
                ops = ", ".join(f"{w['operation']} {w['table']}" for w in fn["writes"])
                print(f"        WRITES: {ops}")
    else:
        print("    (none found — application uses JPA/ORM for all DB operations)")

    print(f"\n  Output written to:")
    print(f"    {JAVA_OUT}")
    print(f"    {SQL_OUT}")
    print(f"    {PLPGSQL_OUT}")
    print("═" * 54 + "\n")


def main():
    print(f"Scanning Java files in {REPO} …")
    java_data = scan_java(REPO)
    JAVA_OUT.write_text(json.dumps(java_data, indent=2, default=str), encoding="utf-8")

    print(f"Scanning SQL files in {REPO} …")
    sql_data = scan_sql(REPO)
    SQL_OUT.write_text(json.dumps(sql_data, indent=2, default=str), encoding="utf-8")

    print(f"Scanning PL/pgSQL functions in {REPO} …")
    plpgsql_data = scan_plpgsql(REPO)
    PLPGSQL_OUT.write_text(json.dumps(plpgsql_data, indent=2, default=str), encoding="utf-8")

    print_summary(java_data, sql_data, plpgsql_data)


if __name__ == "__main__":
    main()
