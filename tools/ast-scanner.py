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

        cls_info = {
            "name":        cls.name,
            "layer":       layer,
            "annotations": list(ann_names),
            "extends":     cls.extends.name if cls.extends else None,
            "fields":      [],
            "methods":     [],
        }

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
    entities     = []
    repositories = []
    services     = []
    controllers  = []

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

    return {
        "meta": {
            "total_files_scanned": len(java_files),
            "total_parsed":        len(results),
            "parse_errors":        len(errors),
        },
        "summary": {
            "entities":     entities,
            "repositories": repositories,
            "services":     services,
            "controllers":  controllers,
        },
        "raw": results,
        "errors": errors,
    }


# ════════════════════════════════════════════════════════════════════════════
# SQL AST SCANNER
# ════════════════════════════════════════════════════════════════════════════

def _sql_dialect(path: Path) -> str:
    """Detect sqlglot dialect from the file's parent folder name."""
    parts = path.parts
    for part in parts:
        if part == "mysql":
            return "mysql"
        if part == "postgres":
            return "postgres"
    return "sqlite"   # H2 is closest to SQLite for sqlglot purposes


def _preprocess_sql(source: str) -> str:
    """Normalise MySQL-specific syntax that sqlglot can't handle."""
    import re
    # INSERT IGNORE INTO tbl  →  INSERT INTO tbl
    source = re.sub(r'(?i)\bINSERT\s+IGNORE\s+INTO\b', 'INSERT INTO', source)
    # INSERT IGNORE tbl  (without INTO)
    source = re.sub(r'(?i)\bINSERT\s+IGNORE\b', 'INSERT INTO', source)
    return source


def scan_sql_file(path: Path) -> dict:
    """Parse one SQL file with sqlglot and extract schema + DML references."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        source = _preprocess_sql(source)
        dialect = _sql_dialect(path)
        statements = sqlglot.parse(source, dialect=dialect,
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
                        col_entry = {
                            "column": col_def.name,
                            "type":   col_def.args.get("kind").sql() if col_def.args.get("kind") else None,
                            "constraints": [c.sql() for c in col_def.find_all(exp.ColumnConstraint)],
                        }
                        cols.append(col_entry)
                tables_created[tbl_name] = {"columns": cols}

        # ── INSERT ────────────────────────────────────────────────────────
        elif isinstance(stmt, exp.Insert):
            tbl = stmt.find(exp.Table)
            cols = [c.name for c in stmt.find_all(exp.Column)]
            # values are literals — grab them as strings
            vals = [v.sql() for v in stmt.find_all(exp.Literal)]
            inserts.append({
                "table":   tbl.name if tbl else None,
                "columns": cols,
                "values":  vals[:len(cols)] if cols else vals,
            })

        # ── UPDATE ────────────────────────────────────────────────────────
        elif isinstance(stmt, exp.Update):
            tbl = stmt.find(exp.Table)
            sets = []
            for eq in stmt.find_all(exp.EQ):
                col = eq.find(exp.Column)
                val = eq.right
                if col:
                    sets.append({"column": col.name, "value": val.sql() if val else None})
            updates.append({
                "table": tbl.name if tbl else None,
                "sets":  sets,
            })

        # ── SELECT ────────────────────────────────────────────────────────
        elif isinstance(stmt, exp.Select):
            from_tables = [t.name for t in stmt.find_all(exp.Table)]
            sel_cols    = [c.sql() for c in stmt.find_all(exp.Column)]
            selects.append({
                "tables":  from_tables,
                "columns": sel_cols,
            })

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
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def print_summary(java_data: dict, sql_data: dict) -> None:
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
    print(f"\n  Output written to:")
    print(f"    {JAVA_OUT}")
    print(f"    {SQL_OUT}")
    print("═" * 54 + "\n")


def main():
    print(f"Scanning Java files in {REPO} …")
    java_data = scan_java(REPO)
    JAVA_OUT.write_text(json.dumps(java_data, indent=2, default=str), encoding="utf-8")

    print(f"Scanning SQL files in {REPO} …")
    sql_data = scan_sql(REPO)
    SQL_OUT.write_text(json.dumps(sql_data, indent=2, default=str), encoding="utf-8")

    print_summary(java_data, sql_data)


if __name__ == "__main__":
    main()
