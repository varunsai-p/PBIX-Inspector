import streamlit as st
import pandas as pd
import zipfile
import json
import io
import re
import os
import tempfile
from pathlib import Path
import networkx as nx

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Power BI Metadata Extractor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* ── Root Variables ── */
:root {
    --bg: #0a0c10;
    --surface: #111318;
    --surface2: #181c24;
    --border: #1e2330;
    --accent: #f7c948;
    --accent2: #3b82f6;
    --accent3: #10b981;
    --danger: #ef4444;
    --text: #e8eaf0;
    --text-muted: #6b7280;
    --mono: 'JetBrains Mono', monospace;
    --sans: 'Syne', sans-serif;
}

/* ── Global Reset ── */
.stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem !important; max-width: 1400px !important; }

/* ── Hero Header ── */
.hero {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 2.5rem 0 2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2.5rem;
}
.hero-title {
    font-family: var(--sans);
    font-size: 2.8rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin: 0;
}
.hero-title span { color: var(--accent); }
.hero-subtitle {
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--text-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}
.hero-badge {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.4rem 0.9rem;
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--accent);
    letter-spacing: 0.08em;
}

/* ── Upload Zone ── */
.upload-zone {
    border: 2px dashed var(--border);
    border-radius: 12px;
    padding: 3rem 2rem;
    text-align: center;
    background: var(--surface);
    transition: border-color 0.2s;
    margin-bottom: 2rem;
}
.upload-zone:hover { border-color: var(--accent); }
.upload-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.upload-title {
    font-family: var(--sans);
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 0.3rem 0;
}
.upload-hint {
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--text-muted);
    letter-spacing: 0.06em;
}

/* ── Metric Cards ── */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
    margin-bottom: 2.5rem;
}
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.metric-card.yellow::before { background: var(--accent); }
.metric-card.blue::before   { background: var(--accent2); }
.metric-card.green::before  { background: var(--accent3); }
.metric-card.red::before    { background: var(--danger); }
.metric-card.purple::before { background: #a855f7; }

.metric-label {
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.metric-value {
    font-family: var(--sans);
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1;
}
.metric-card.yellow .metric-value { color: var(--accent); }
.metric-card.blue   .metric-value { color: var(--accent2); }
.metric-card.green  .metric-value { color: var(--accent3); }
.metric-card.red    .metric-value { color: var(--danger); }
.metric-card.purple .metric-value { color: #a855f7; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid var(--border) !important;
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.06em !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.2rem !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface2) !important;
    color: var(--accent) !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── DataFrames ── */
.stDataFrame {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden;
}
.stDataFrame thead th {
    background: var(--surface2) !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}
.stDataFrame tbody tr:hover { background: var(--surface2) !important; }

/* ── Search / Inputs ── */
.stTextInput input, .stSelectbox select {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.82rem !important;
}
.stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(247,201,72,0.15) !important;
}
label { font-family: var(--mono) !important; font-size: 0.72rem !important; color: var(--text-muted) !important; letter-spacing: 0.08em !important; }

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent !important; }

/* ── Buttons ── */
.stDownloadButton button, .stButton button {
    background: var(--accent) !important;
    color: #0a0c10 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    padding: 0.5rem 1.2rem !important;
    transition: opacity 0.15s !important;
}
.stDownloadButton button:hover, .stButton button:hover { opacity: 0.85 !important; }

/* ── Code blocks / DAX ── */
.dax-formula {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 0.8rem 1rem;
    font-family: var(--mono);
    font-size: 0.78rem;
    color: #93c5fd;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0.3rem 0;
}

/* ── Section labels ── */
.section-label {
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

/* ── Dep pill ── */
.dep-pill {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.2rem 0.55rem;
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--accent2);
    margin: 2px;
}

/* ── Alerts / Info ── */
.stAlert { border-radius: 8px !important; font-family: var(--mono) !important; font-size: 0.8rem !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    color: var(--text) !important;
    background: var(--surface) !important;
    border-radius: 6px !important;
}

/* ── Graph container ── */
.graph-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
}

/* ── Source badge ── */
.source-badge {
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 20px;
    font-family: var(--mono);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.06em;
}
.source-sql   { background: rgba(59,130,246,0.15); color: #93c5fd; border: 1px solid rgba(59,130,246,0.3); }
.source-excel { background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }
.source-other { background: rgba(168,85,247,0.15); color: #d8b4fe; border: 1px solid rgba(168,85,247,0.3); }

/* ── rel arrow ── */
.rel-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 0.5rem;
    font-family: var(--mono);
    font-size: 0.78rem;
}
.rel-table { color: var(--accent); font-weight: 700; }
.rel-col   { color: var(--text-muted); }
.rel-arrow { color: var(--accent2); font-size: 1rem; }
.rel-type  { margin-left: auto; color: var(--text-muted); font-size: 0.68rem; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--text-muted);
    font-family: var(--mono);
    font-size: 0.82rem;
}
.empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; display: block; }
</style>
""", unsafe_allow_html=True)


# ── PBIX Extraction Engine v3 ────────────────────────────────────────────────
#
# KEY BUGS FIXED vs v2:
#   1. Alias resolution was GLOBAL — aliases are PER-VISUAL scope.
#      "c" maps to "customers" in one visual, "categories" in another.
#   2. SourceRef uses "Source" (alias key) NOT "Entity" — must resolve via From.
#   3. Measures "Tables Used" was always "—" for cloud — now filled from visual usage.
#   4. Data source showed raw Dataset ID string — now shows clean friendly name.
#   5. Malformed entity names like "Min(Refresh Status" now filtered out.

import json, re, zipfile, io
from collections import defaultdict


SUPPORTED_EXTENSIONS = [".pbix", ".pbit", ".bim", ".tmdl", ".json"]


def extract_any(uploaded_file, filename: str = "") -> dict:
    """
    Auto-detect file format and extract. Supports:
      .pbix / .pbit  — Power BI ZIP (Desktop always has DAX; Cloud may not)
      .bim           — Tabular Model JSON (always has full DAX)
      .json          — XMLA / TMSL JSON export (always has full DAX)
      .tmdl          — TMDL folder zipped (always has full DAX)
    """
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    file_bytes = uploaded_file.read()

    # Plain JSON formats (.bim, .json, or auto-detected by first byte)
    if ext in (".bim", ".json") or (
        file_bytes[:1] in (b"{", b"[") and ext not in (".pbix", ".pbit")
    ):
        return _extract_from_json_bytes(file_bytes, filename)

    # ZIP-based formats
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as z:
            names = z.namelist()
            tmdl_files = [n for n in names if n.endswith(".tmdl")]
            if tmdl_files or ext == ".tmdl":
                return _extract_from_tmdl_zip(z, names, filename)
            return _extract_from_pbix_zip(z, names, file_bytes, filename)
    except zipfile.BadZipFile:
        # Last resort: try as plain JSON
        return _extract_from_json_bytes(file_bytes, filename)


def _extract_from_json_bytes(file_bytes: bytes, filename: str) -> dict:
    """Parse .bim / XMLA JSON / TMSL JSON."""
    result = _empty_result()
    result["report_type"] = "Desktop"
    result["parse_log"].append(f"Format: BIM/XMLA JSON — {filename}")
    obj = _try_tmsl_json(file_bytes)
    if obj:
        _parse_tmsl(obj, result)
        result["parse_log"].append("✅ Parsed TMSL/BIM JSON — full DAX available")
    else:
        result["errors"].append("Could not parse as TMSL/BIM JSON.")
    return _finalise(result)


def _extract_from_tmdl_zip(z: zipfile.ZipFile, names: list, filename: str) -> dict:
    """Parse a zipped TMDL folder."""
    result = _empty_result()
    result["report_type"] = "Desktop"
    result["parse_log"].append(f"Format: TMDL folder — {filename}")
    tmdl_contents = {}
    for name in names:
        if name.endswith(".tmdl"):
            try:
                tmdl_contents[name] = z.read(name).decode("utf-8", errors="replace")
            except Exception:
                pass
    if tmdl_contents:
        model = _parse_tmdl_folder(tmdl_contents)
        _parse_tmsl({"model": model}, result)
        result["parse_log"].append(f"✅ Parsed TMDL — {len(tmdl_contents)} files — full DAX available")
    else:
        result["errors"].append("No .tmdl files found in ZIP.")
    return _finalise(result)


def _extract_from_pbix_zip(z: zipfile.ZipFile, names: list, file_bytes: bytes, filename: str) -> dict:
    """Original PBIX/PBIT extraction logic."""
    result = _empty_result()
    result["zip_contents"] = names
    result["parse_log"].append(f"ZIP entries: {', '.join(names)}")

    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if ext == ".pbit":
        result["report_type"] = "Desktop"
        result["parse_log"].append("Format: PBIT template — full DAX always available")

    meta = _read_json(z, "Metadata", encoding="utf-16-le")
    if meta:
        result["report_type"] = meta.get("CreatedFrom", "Desktop")
        result["parse_log"].append(
            f"CreatedFrom={result['report_type']}  "
            f"AutoRels={len(meta.get('AutoCreatedRelationships', []))}")

    schema_parsed = False
    for candidate in ["DataModelSchema", "DataModel/schema.json", "Model/schema.json"]:
        if candidate in names:
            raw = z.read(candidate)
            obj = _try_tmsl_json(raw)
            if obj:
                _parse_tmsl(obj, result)
                schema_parsed = True
                result["parse_log"].append(f"✅ Parsed TMSL from {candidate} — full DAX available")
                break

    if "Report/Layout" in names:
        try:
            raw = z.read("Report/Layout")
            layout = json.loads(raw.decode("utf-16-le", errors="replace"))
            _parse_report_layout(layout, result, schema_parsed)
            result["parse_log"].append("✅ Parsed Report/Layout")
        except Exception as e:
            result["errors"].append(f"Report/Layout error: {e}")

    if "DiagramLayout" in names:
        obj = _try_json_any(z.read("DiagramLayout"))
        if obj:
            _parse_diagram_layout(obj, result)
            result["parse_log"].append("✅ Parsed DiagramLayout")

    if "Connections" in names:
        try:
            conn = json.loads(z.read("Connections").decode("utf-8", errors="replace"))
            _parse_connections(conn, result)
            result["parse_log"].append("✅ Parsed Connections")
        except Exception as e:
            result["errors"].append(f"Connections error: {e}")

    return _finalise(result)


def _empty_result() -> dict:
    return {
        "tables": [], "columns": [], "measures": [],
        "relationships": [], "sources": [],
        "pages": [], "visuals": [],
        "errors": [], "parse_log": [],
        "report_type": "unknown",
    }


def _finalise(result: dict) -> dict:
    """Dedup, validate, derive dependencies."""
    def valid(n): return bool(n) and not ("(" in n and ")" not in n)
    result["tables"]   = [t for t in result["tables"]   if valid(t.get("Table Name",""))]
    result["columns"]  = [c for c in result["columns"]  if valid(c.get("Table",""))]
    result["measures"] = [m for m in result["measures"]
                          if valid(m.get("Table","")) and valid(m.get("Measure Name",""))]
    result["visuals"]  = [v for v in result["visuals"]
                          if all(valid(t.strip()) for t in v.get("Tables Used","").split(",") if t.strip())]
    result["tables"]        = _dedup(result["tables"],        "Table Name")
    result["columns"]       = _dedup(result["columns"],       "Column Name","Table")
    for m in result["measures"]:
        m["Measure Name"] = m["Measure Name"].strip()
    result["measures"]      = _dedup(result["measures"],      "Measure Name","Table")
    result["relationships"] = _dedup(result["relationships"], "From Table","From Column","To Table","To Column")
    result["sources"]       = _dedup(result["sources"],       "Source Type","Server")
    result["measures"]      = _derive_measure_usage(result["measures"], result["tables"])
    if not result["tables"] and not result["measures"] and not result["sources"]:
        result["_demo"] = True
        result = _demo_data(result)
    return result


# Backward-compatible alias
def extract_pbix(uploaded_file) -> dict:
    name = getattr(uploaded_file, "name", "file.pbix")
    return extract_any(uploaded_file, name)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — TMSL parser (Desktop)
# ─────────────────────────────────────────────────────────────────────────────

def _try_tmsl_json(raw: bytes):
    for enc in ("utf-8","utf-16","utf-16-le","utf-16-be","latin-1"):
        try:
            text = raw.decode(enc, errors="replace").lstrip("\ufeff").lstrip()
            start = next((i for i,c in enumerate(text) if c in "{["), -1)
            if start < 0: continue
            obj = json.loads(text[start:])
            if isinstance(obj, dict) and any(k in obj for k in
                    ("model","Model","tables","relationships","dataSources",
                     "create","createOrReplace","name",           # XMLA / BIM root keys
                     "compatibilityLevel")):                      # BIM root key
                return obj
        except Exception:
            continue
    return None


def _parse_tmsl(schema: dict, result: dict):
    model = schema
    for key in ("model","Model","create","createOrReplace"):
        if key in schema and isinstance(schema[key], dict):
            model = schema[key]; break
    if "database" in model and isinstance(model["database"], dict):
        model = model["database"].get("model", model["database"])

    mquery_text = []
    for tbl in model.get("tables", []):
        tname = tbl.get("name","")
        if any(tname.startswith(p) for p in ("DateTableTemplate","LocalDateTable")):
            continue
        src_type = "Import"
        mq_parts = []
        for part in tbl.get("partitions",[]):
            mode = str(part.get("mode","")).lower()
            if "directquery" in mode: src_type = "DirectQuery"
            elif "dual" in mode:      src_type = "Dual"
            src = part.get("source",{})
            if isinstance(src, dict):
                expr = src.get("expression","")
                if isinstance(expr,list): expr = "\n".join(expr)
                if expr: mq_parts.append(expr); mquery_text.append(expr)

        # Derive a meaningful Row Count label from partition metadata
        raw_row_count = tbl.get("rowCount", None)
        if raw_row_count is not None:
            row_count = f"{int(raw_row_count):,}"           # real count from BIM/PBIX
        else:
            combined_mq = "\n".join(mq_parts)
            if src_type == "DirectQuery":
                row_count = "DirectQuery (live)"
            elif "Table.FromRows" in combined_mq or "Binary.Decompress" in combined_mq:
                # Inline/embedded table — try to decode row count from Base64
                import base64 as _b64, zlib as _zl
                b64_match = re.search(r'Binary\.FromText\s*\(\s*"([^"]+)"', combined_mq)
                if b64_match:
                    try:
                        decoded = _zl.decompress(_b64.b64decode(b64_match.group(1)), -15)
                        import json as _j
                        rows = _j.loads(decoded)
                        row_count = f"{len(rows)} rows (embedded)"
                    except Exception:
                        row_count = "Embedded table"
                else:
                    row_count = "Embedded table"
            elif "RangeStart" in combined_mq or "RangeEnd" in combined_mq:
                row_count = "Incremental refresh"           # date-filtered partition
            elif combined_mq.strip().upper().startswith("CALENDAR") or src_type == "calculated":
                row_count = "Calculated table"
            elif _source_from_mquery(combined_mq) not in ("Unknown",""):
                src_label = _source_from_mquery(combined_mq).split(":")[0]  # e.g. "BigQuery"
                row_count = f"Live in {src_label}"          # remote source, no local cache
            else:
                row_count = "N/A"

        result["tables"].append({
            "Table Name":  tname, "Source": _source_from_mquery("\n".join(mq_parts)),
            "Type": src_type, "Row Count": row_count,
            "Is Hidden": str(tbl.get("isHidden",False)), "Description": tbl.get("description",""),
        })
        for col in tbl.get("columns",[]):
            col_type = col.get("type","data")
            expr = col.get("expression","")
            if isinstance(expr,list): expr = "\n".join(expr)
            result["columns"].append({
                "Column Name": col.get("name",""), "Table": tname,
                "Data Type": col.get("dataType","Unknown"),
                "Is Calculated": "Yes" if col_type in ("calculated","calculatedTableColumn") else "No",
                "Expression": expr, "Is Hidden": str(col.get("isHidden",False)),
                "Format String": col.get("formatString",""),
            })
        for m in tbl.get("measures",[]):
            expr = m.get("expression","")
            if isinstance(expr,list): expr = "\n".join(expr)
            # Strip trailing annotation lines (e.g. "annotation PBI_FormatHint = {...}")
            clean_lines = [l for l in expr.splitlines()
                           if not l.strip().startswith("annotation ")]
            expr = "\n".join(clean_lines).strip()
            result["measures"].append({
                "Measure Name": m.get("name",""), "Table": tname, "DAX Formula": expr,
                "Format String": m.get("formatString",""), "Is Hidden": str(m.get("isHidden",False)),
                "Description": m.get("description",""),
                "Tables Used":"", "Columns Used":"", "Measures Used":"",
            })

    cardinality_labels = {"manyToOne":"Many-to-One","oneToMany":"One-to-Many",
                          "oneToOne":"One-to-One","manyToMany":"Many-to-Many"}
    for rel in model.get("relationships",[]):
        result["relationships"].append({
            "From Table": rel.get("fromTable",""), "From Column": rel.get("fromColumn",""),
            "To Table": rel.get("toTable",""),     "To Column": rel.get("toColumn",""),
            "Relationship Type": cardinality_labels.get(rel.get("type",""),"Many-to-One"),
            "Cross Filter": "Both" if "both" in str(rel.get("crossFilteringBehavior","")).lower() else "Single",
            "Active": str(rel.get("isActive",True)),
        })
    for ds in model.get("dataSources",[]):
        conn_str = ds.get("connectionString","")
        server, database = _parse_conn_string(conn_str)
        result["sources"].append({
            "Source Type": _norm_source_type(ds.get("type",ds.get("connectionType","Unknown"))),
            "Server": server or ds.get("server",ds.get("location","")),
            "Database": database or ds.get("database",""),
            "Query": (ds.get("query","") or "")[:300],
        })
    if mquery_text:
        _scan_mquery_sources("\n".join(mquery_text), result)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Report/Layout parser  (alias scope is PER-VISUAL)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_report_layout(layout: dict, result: dict, schema_parsed: bool):
    pages, visuals = [], []

    # Global discovery across visuals
    discovered_tables   = {}
    discovered_columns  = defaultdict(set)   # table -> {(col_name, data_type)}
    discovered_measures = defaultdict(set)   # table -> {measure_name}
    measure_usage       = defaultdict(lambda: {"tables": set(), "columns": set()})

    # underlyingType code → readable data type
    _UTYPE = {
        1:   "Text",    2:   "Decimal",  6:   "Integer",
        8:   "Boolean", 9:   "Date",     10:  "DateTime",
        11:  "Time",    260: "Decimal",  519: "DateTime",
    }

    for section in layout.get("sections", []):
        page_name = section.get("displayName", section.get("name","Page"))
        pages.append(page_name)

        for vc in section.get("visualContainers", []):
            vis = _parse_one_visual(vc)
            if not vis:
                continue

            all_tables = vis["tables"]
            measures   = vis["measures"]   # [(entity, prop)]
            columns    = vis["columns"]    # [(entity, prop)]

            for tname in all_tables:
                discovered_tables[tname] = True
            for ent, col, dtype in columns:
                discovered_columns[ent].add((col, dtype))
            for ent, mname in measures:
                mname = mname.strip()
                discovered_measures[ent].add(mname)
                key = (ent, mname)
                measure_usage[key]["tables"].update(all_tables)
                measure_usage[key]["columns"].update(col for e2, col, _ in columns if e2 == ent)

            visuals.append({
                "Page":         page_name,
                "Visual Type":  vis["type"],
                "Tables Used":  ", ".join(sorted(all_tables)),
                "Measures Used": ", ".join(f"{e}[{p}]" for e,p in measures),
                "Columns Used":  ", ".join(f"{e}[{col}]" for e,col,_ in columns),
            })

    result["pages"]   = pages
    result["visuals"] = visuals

    if schema_parsed:
        return  # TMSL already has full detail; visuals tab is supplemental

    # ── Populate tables, columns, measures from visual discovery ──
    known_tables = {t["Table Name"] for t in result["tables"]}
    for tname in discovered_tables:
        if tname not in known_tables:
            result["tables"].append({
                "Table Name":   tname,
                "Source":       "Power BI Service (cloud dataset)",
                "Type":         "Cloud",
                "Row Count":    "Stored in Power BI Service",
                "Est. Columns": "Unknown",
                "Is Hidden":    "False",
                "Description":  "",
            })
            known_tables.add(tname)

    known_cols = {(c["Table"], c["Column Name"]) for c in result["columns"]}
    for tname, cols in discovered_columns.items():
        for col, dtype in cols:
            if (tname, col) not in known_cols:
                result["columns"].append({
                    "Column Name":   col,
                    "Table":         tname,
                    "Data Type":     dtype,
                    "Is Calculated": "No",
                    "Expression":    "",
                    "Is Hidden":     "False",
                    "Format String": "",
                    "Note":          "Used in report visuals",
                })
                known_cols.add((tname, col))

    known_meas = {(m["Table"], m["Measure Name"]) for m in result["measures"]}
    for tname, mset in discovered_measures.items():
        for mname in mset:
            if (tname, mname) not in known_meas:
                usage    = measure_usage.get((tname, mname), {})
                co_tables = sorted(usage.get("tables", set()))   # includes own table
                co_cols   = sorted(usage.get("columns", set()))
                result["measures"].append({
                    "Measure Name":  mname,
                    "Table":         tname,
                    "DAX Formula":   "Not available — DAX stored in Power BI Service. "
                                     "Open the dataset in Power BI Desktop or via XMLA endpoint to view DAX.",
                    "Format String": "", "Is Hidden": "False", "Description": "",
                    "Tables Used":   ", ".join(co_tables) if co_tables else tname,
                    "Columns Used":  ", ".join(co_cols)   if co_cols   else "—",
                    "Measures Used": "—",
                })
                known_meas.add((tname, mname))


def _parse_one_visual(vc: dict) -> dict | None:
    """Parse ONE visual with its own alias scope."""
    def safe_json(s):
        if not s: return {}
        try: return json.loads(s)
        except: return {}

    def expand(obj):
        """Recursively parse all JSON-encoded strings."""
        if isinstance(obj, str):
            try: return expand(json.loads(obj))
            except: return obj
        elif isinstance(obj, dict):  return {k: expand(v) for k,v in obj.items()}
        elif isinstance(obj, list):  return [expand(i) for i in obj]
        return obj

    config = expand(safe_json(vc.get("config", "{}")))
    query  = expand(safe_json(vc.get("query",  "{}")))
    dt     = expand(safe_json(vc.get("dataTransforms", "{}")))

    sv    = config.get("singleVisual", {})
    vtype = sv.get("visualType", "unknown")

    # Build alias map ONLY for this visual
    aliases: dict[str,str] = {}
    def collect_aliases(obj):
        if isinstance(obj, dict):
            for f in obj.get("From", []):
                if isinstance(f, dict) and f.get("Name") and f.get("Entity"):
                    aliases[f["Name"]] = f["Entity"]
            for v in obj.values(): collect_aliases(v)
        elif isinstance(obj, list):
            for i in obj: collect_aliases(i)
    collect_aliases(sv); collect_aliases(query); collect_aliases(dt)

    def resolve(src_ref: dict) -> str:
        if not isinstance(src_ref, dict): return ""
        source = src_ref.get("Source","")
        entity = src_ref.get("Entity","")
        return aliases.get(source, entity or source)

    measures: list = []; columns: list = []
    seen_m: set = set(); seen_c: set = set()

    AGG_FN = {0:"Sum",1:"Avg",2:"Count",3:"Min",4:"Max",5:"CountRows",
              6:"StDev",7:"StDevP",8:"Var",9:"VarP",10:"Median",11:"CountDistinct"}

    # underlyingType → readable data type name
    _UTYPE = {1:"Text",2:"Decimal",6:"Integer",8:"Boolean",9:"Date",
              10:"DateTime",11:"Time",260:"Decimal",519:"DateTime",1048576:"Text"}

    # ── Step A: build lookup from dataTransforms selects ──
    # queryName -> (displayName, underlyingType)
    dt_lookup: dict[str, tuple[str,str]] = {}
    for sel in dt.get("selects", []):
        qname = sel.get("queryName","")
        dname = sel.get("displayName","")
        utype_raw = (sel.get("type") or {}).get("underlyingType", 0)
        dtype = _UTYPE.get(utype_raw, "Unknown")
        if qname:
            dt_lookup[qname] = (dname, dtype)

    # Also build col→dtype lookup from dataTransforms (entity-based)
    col_dtype: dict[tuple,str] = {}   # (entity, col) -> dtype
    for sel in dt.get("selects", []):
        utype_raw = (sel.get("type") or {}).get("underlyingType", 0)
        dtype = _UTYPE.get(utype_raw, "Unknown")
        expr = sel.get("expr", {})
        if isinstance(expr, dict):
            c2 = expr.get("Column", {})
            if isinstance(c2, dict):
                ent2 = (c2.get("Expression") or {}).get("SourceRef",{}).get("Entity","")
                col2 = c2.get("Property","")
                if ent2 and col2:
                    col_dtype[(ent2, col2)] = dtype
            agg2 = expr.get("Aggregation",{})
            if isinstance(agg2, dict):
                inner2 = (agg2.get("Expression") or {}).get("Column",{})
                if isinstance(inner2, dict):
                    ent2 = (inner2.get("Expression") or {}).get("SourceRef",{}).get("Entity","")
                    col2 = inner2.get("Property","")
                    if ent2 and col2:
                        col_dtype[(ent2, col2)] = dtype

    # Also build queryRef → display name map from projections in singleVisual
    agg_display: dict[str,str] = {}   # Name / queryName -> displayName
    for qname, (dname, _) in dt_lookup.items():
        if dname:
            agg_display[qname] = dname

    def collect_refs(obj):
        if not isinstance(obj, (dict, list)):
            return
        if isinstance(obj, list):
            for i in obj: collect_refs(i)
            return

        # ── Explicit Measure ──
        m = obj.get("Measure")
        if isinstance(m, dict):
            ent  = resolve((m.get("Expression") or {}).get("SourceRef",{}))
            prop = (m.get("Property","") or "").strip()
            if ent and prop and (ent, prop) not in seen_m:
                seen_m.add((ent, prop)); measures.append((ent, prop))

        # ── Plain Column — extract dtype ──
        c = obj.get("Column")
        if isinstance(c, dict):
            ent  = resolve((c.get("Expression") or {}).get("SourceRef",{}))
            prop = c.get("Property","")
            if ent and prop and (ent, prop) not in seen_c:
                seen_c.add((ent, prop))
                dtype = col_dtype.get((ent, prop), "Unknown")
                columns.append((ent, prop, dtype))

        # ── Aggregation(Column) → implicit measure ──
        agg = obj.get("Aggregation")
        if isinstance(agg, dict):
            fn_code  = agg.get("Function", -1)
            fn_name  = AGG_FN.get(fn_code, f"Agg{fn_code}")
            inner    = (agg.get("Expression") or {}).get("Column", {})
            if isinstance(inner, dict):
                ent      = resolve((inner.get("Expression") or {}).get("SourceRef", {}))
                col_prop = inner.get("Property","")
                if ent and col_prop:
                    native   = obj.get("NativeReferenceName","")
                    obj_name = obj.get("Name","")
                    dt_dname = agg_display.get(obj_name,"")
                    display  = native or dt_dname
                    if display:
                        if (ent, display) not in seen_m:
                            seen_m.add((ent, display))
                            measures.append((ent, display))
                        if (ent, col_prop) not in seen_c:
                            seen_c.add((ent, col_prop))
                            dtype = col_dtype.get((ent, col_prop), "Unknown")
                            columns.append((ent, col_prop, dtype))

        for v in obj.values(): collect_refs(v)

    collect_refs(sv); collect_refs(query); collect_refs(dt)

    tables = set(aliases.values())
    tables.update(e for e,_ in measures)
    tables.update(e for e,_,_ in columns)

    def valid(n): return bool(n) and not ("(" in n and ")" not in n)
    tables   = {t for t in tables   if valid(t)}
    measures = [(e,p) for e,p in measures if valid(e) and valid(p)]
    columns  = [(e,p,d) for e,p,d in columns  if valid(e) and valid(p)]

    return {"type":vtype, "aliases":aliases, "tables":tables,
            "measures":measures, "columns":columns}


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — DiagramLayout
# ─────────────────────────────────────────────────────────────────────────────

def _parse_diagram_layout(obj: dict, result: dict):
    known = {t["Table Name"] for t in result["tables"]}
    node_order = []
    for diag in obj.get("diagrams", []):
        for node in diag.get("nodes", []):
            tname = node.get("nodeIndex", "")
            if not tname:
                continue
            node_order.append(tname)
            h = node.get("size", {}).get("height", 0)
            est_cols = max(0, (h - 40) // 28)
            est_cols_str = f"~{est_cols} columns" if est_cols > 0 else "Unknown"

            if tname in {t["Table Name"] for t in result["tables"]}:
                for t in result["tables"]:
                    if t["Table Name"] == tname:
                        if t.get("Row Count") in ("N/A", ""):
                            t["Row Count"] = "Stored in Power BI Service"
                        t["Est. Columns"] = est_cols_str
                        break
            elif tname not in known:
                result["tables"].append({
                    "Table Name":   tname,
                    "Source":       "Power BI Service (cloud dataset)",
                    "Type":         "Cloud",
                    "Row Count":    "Stored in Power BI Service",
                    "Est. Columns": est_cols_str,
                    "Is Hidden":    "False",
                    "Description":  "",
                })
                known.add(tname)

    # Store the authoritative node order for column metadata mapping
    result["diag_node_order"] = node_order



# ─────────────────────────────────────────────────────────────────────────────
# PBIP Report folder parser — visual.json files
# ─────────────────────────────────────────────────────────────────────────────

def _parse_visual_json_files(visual_jsons: list, page_jsons: list, result: dict,
                              page_id_map: dict = None):
    """
    Parse PBIP .Report folder visual.json files.
    page_id_map: {page_id (str) -> displayName (str)} — built from file paths in ZIP.
                 Each vis_obj may carry a '_page_id' key injected by the caller.
    """
    discovered_tables   = {}
    discovered_columns  = defaultdict(set)
    discovered_measures = defaultdict(set)
    measure_usage       = defaultdict(lambda: {"tables": set(), "columns": set()})
    pages_set, pages_ordered, visuals = set(), [], []

    # Build id→displayName map from page_jsons
    id_to_name = dict(page_id_map) if page_id_map else {}
    for obj in page_jsons:
        if "displayName" in obj and "name" in obj:
            id_to_name[obj["name"]] = obj["displayName"]
            if obj["displayName"] not in pages_set:
                pages_set.add(obj["displayName"])
                pages_ordered.append(obj["displayName"])

    AGG_FN = {0:"Sum",1:"Avg",2:"Count",3:"Min",4:"Max",5:"CountRows",10:"Median",11:"CountDistinct"}

    for vis_obj in visual_jsons:
        vis   = vis_obj.get("visual", {})
        vtype = vis.get("visualType", "unknown")
        query_state = vis.get("query", {}).get("queryState", {})
        all_tables, meas_display, col_display = set(), [], []

        # Resolve page name: prefer injected _page_id, fallback to first page
        page_id   = vis_obj.get("_page_id", "")
        page_name = id_to_name.get(page_id, pages_ordered[0] if pages_ordered else "Page 1")

        for role, role_data in query_state.items():
            for proj in role_data.get("projections", []):
                field      = proj.get("field", {})
                native_ref = proj.get("nativeQueryRef", "")

                m = field.get("Measure", {})
                if m:
                    ent  = (m.get("Expression") or {}).get("SourceRef", {}).get("Entity", "")
                    prop = (m.get("Property", "") or "").strip()
                    if ent and prop:
                        all_tables.add(ent); discovered_tables[ent] = True
                        discovered_measures[ent].add(prop)
                        measure_usage[(ent, prop)]["tables"].add(ent)
                        meas_display.append(f"{ent}[{prop}]")

                c = field.get("Column", {})
                if c:
                    ent  = (c.get("Expression") or {}).get("SourceRef", {}).get("Entity", "")
                    prop = c.get("Property", "")
                    if ent and prop:
                        all_tables.add(ent); discovered_tables[ent] = True
                        discovered_columns[ent].add((prop, "Unknown"))
                        col_display.append(f"{ent}[{prop}]")

                agg = field.get("Aggregation", {})
                if agg:
                    fn     = AGG_FN.get(agg.get("Function", -1), "Agg")
                    inner  = (agg.get("Expression") or {}).get("Column", {})
                    ent    = (inner.get("Expression") or {}).get("SourceRef", {}).get("Entity", "") if inner else ""
                    prop   = inner.get("Property", "") if inner else ""
                    display = native_ref or f"{fn}({prop})"
                    if ent:
                        all_tables.add(ent); discovered_tables[ent] = True
                        discovered_measures[ent].add(display)
                        measure_usage[(ent, display)]["tables"].add(ent)
                        if prop: discovered_columns[ent].add((prop, "Unknown"))
                        meas_display.append(f"{ent}[{display}]")

        visuals.append({
            "Page":          page_name,
            "Visual Type":   vtype,
            "Tables Used":   ", ".join(sorted(all_tables)),
            "Measures Used": ", ".join(meas_display),
            "Columns Used":  ", ".join(col_display),
        })

    # Enrich Columns Used on each visual by resolving measure column dependencies
    # Build measure → columns lookup from result["measures"]
    meas_col_map = {}   # (table, measure_name) -> [col_ref, ...]
    for m in result.get("measures", []):
        cols = m.get("Columns Used", "—")
        if cols and cols != "—":
            key = (m["Table"], m["Measure Name"])
            meas_col_map[key] = [c.strip() for c in cols.split(",") if c.strip()]

    # Also build stripped-name lookup (measure names with trailing spaces)
    meas_col_map_stripped = {
        (t, n.strip()): v for (t, n), v in meas_col_map.items()
    }

    enriched_visuals = []
    for v in visuals:
        extra_cols = []
        for mref in v.get("Measures Used", "").split(","):
            mref = mref.strip()
            if not mref: continue
            # mref format: "Table[MeasureName]"
            bracket = mref.find("[")
            if bracket > 0:
                tbl  = mref[:bracket].strip()
                mname = mref[bracket+1:].rstrip("]").strip()
                cols = (meas_col_map.get((tbl, mname)) or
                        meas_col_map_stripped.get((tbl, mname)) or [])
                for col in cols:
                    if col not in extra_cols and col not in (v.get("Columns Used") or ""):
                        extra_cols.append(col)
        if extra_cols:
            existing = v.get("Columns Used", "") or ""
            combined = ", ".join(filter(None, [existing] + extra_cols))
            v = dict(v); v["Columns Used"] = combined
        enriched_visuals.append(v)

    result["pages"]   = pages_ordered if pages_ordered else ["Page 1"]
    result["visuals"] = enriched_visuals

    known_tables = {t["Table Name"] for t in result["tables"]}
    for tname in discovered_tables:
        if tname not in known_tables:
            result["tables"].append({
                "Table Name": tname, "Source": "Power BI Service (cloud dataset)",
                "Type": "Cloud", "Row Count": "Stored in Power BI Service",
                "Est. Columns": "Unknown", "Is Hidden": "False", "Description": "",
            })
            known_tables.add(tname)

    known_cols = {(c["Table"], c["Column Name"]) for c in result["columns"]}
    for tname, cols in discovered_columns.items():
        for col, dtype in cols:
            if (tname, col) not in known_cols:
                result["columns"].append({
                    "Column Name": col, "Table": tname, "Data Type": dtype,
                    "Is Calculated": "No", "Expression": "",
                    "Is Hidden": "False", "Format String": "", "Note": "Used in report visuals",
                })
                known_cols.add((tname, col))

    known_meas = {(m["Table"], m["Measure Name"]) for m in result["measures"]}
    for tname, mset in discovered_measures.items():
        for mname in mset:
            if (tname, mname) not in known_meas:
                usage = measure_usage.get((tname, mname), {})
                result["measures"].append({
                    "Measure Name": mname, "Table": tname,
                    "DAX Formula": "Not available — DAX stored in Power BI Service.",
                    "Format String": "", "Is Hidden": "False", "Description": "",
                    "Tables Used": ", ".join(sorted(usage.get("tables", {tname}))),
                    "Columns Used": "—", "Measures Used": "—",
                })
                known_meas.add((tname, mname))


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Connections
# ─────────────────────────────────────────────────────────────────────────────

def _parse_connections(conn: dict, result: dict):
    for c in conn.get("Connections",[]):
        conn_str = c.get("ConnectionString","")
        server, database = _parse_conn_string(conn_str)
        result["sources"].append({
            "Source Type": _norm_source_type(c.get("ConnectionType","Unknown")),
            "Server":      server or conn_str[:200],
            "Database":    database, "Query": "",
        })
    for artifact in conn.get("RemoteArtifacts",[]):
        dataset_id = artifact.get("DatasetId","")
        report_id  = artifact.get("ReportId","")
        if dataset_id:
            result["sources"].append({
                "Source Type": "Power BI Service",
                "Server":      "Power BI Service (cloud dataset)",
                "Database":    f"Dataset ID: {dataset_id}",
                "Query":       f"Report ID: {report_id}\n\n"
                               "Cloud-connected thin report.\n"
                               "DAX formulas and M queries are stored in Power BI Service.\n"
                               "To access them: open the dataset in Power BI Desktop "
                               "or connect via XMLA endpoint.",
            })


# ─────────────────────────────────────────────────────────────────────────────
# TMDL folder parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_tmdl_folder(files: dict) -> dict:
    """
    Parse TMDL folder files into a TMSL-compatible model dict.
    files = {filename: content_string}
    """
    model = {"tables": [], "relationships": [], "dataSources": []}

    for fname, content in files.items():
        fname_lower = fname.lower()
        # Table files: tables/TableName.tmdl or any .tmdl with 'table' declaration
        if "table" in fname_lower or re.search(r'^table\s', content, re.MULTILINE):
            table = _parse_tmdl_table(content)
            if table and table.get("name"):
                model["tables"].append(table)
        # Relationships
        if "relationship" in fname_lower:
            model["relationships"].extend(_parse_tmdl_relationships(content))
        # Data sources
        if "datasource" in fname_lower.replace(" ","") or "datasource" in content.lower()[:200]:
            model["dataSources"].extend(_parse_tmdl_datasources(content))

    return model


def _parse_tmdl_table(content: str) -> dict:
    """Parse a single TMDL table block into a dict."""
    lines = content.split('\n')
    table_name = None
    columns, measures, partitions = [], [], []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Table declaration
        m = re.match(r'^table\s+(.+)$', stripped)
        if m and table_name is None:
            table_name = m.group(1).strip("'\"")
            i += 1; continue

        # Column
        m = re.match(r'^column\s+(.+)$', stripped)
        if m:
            col = {"name": m.group(1).strip("'\""), "dataType": "string"}
            i += 1
            while i < len(lines):
                sub = lines[i].strip()
                if not sub or re.match(r'^(column|measure|partition|table)\s', sub): break
                dt = re.match(r'^dataType:\s*(.+)$', sub)
                if dt: col["dataType"] = dt.group(1).strip()
                fmt = re.match(r'^formatString:\s*(.+)$', sub)
                if fmt: col["formatString"] = fmt.group(1).strip().strip('"')
                i += 1
            columns.append(col)
            continue

        # Measure — single-line: measure Name = Expression
        m = re.match(r'^measure\s+(.+?)\s*=\s*(.*)$', stripped)
        if m:
            mname = m.group(1).strip("'\"")
            expr_first = m.group(2).strip()
            i += 1
            expr_lines = [expr_first] if expr_first else []
            fmt_str = ""
            while i < len(lines):
                sub = lines[i]
                sub_s = sub.strip()
                if not sub_s: i += 1; continue
                indent = len(sub) - len(sub.lstrip('\t '))
                # Stop at next table-level declaration
                if indent <= 1 and re.match(r'^(column|measure|partition|table|relationship)\s', sub_s):
                    break
                fmt = re.match(r'^formatString:\s*(.+)$', sub_s)
                if fmt: fmt_str = fmt.group(1).strip().strip('"'); i += 1; continue
                if re.match(r'^(isHidden|description|displayFolder|annotation|changedProperty|lineageTag):', sub_s):
                    i += 1; continue
                if indent >= 2:
                    expr_lines.append(sub_s)
                i += 1
            measures.append({
                "name": mname,
                "expression": "\n".join(expr_lines).strip(),
                "formatString": fmt_str,
            })
            continue

        # Partition
        m = re.match(r'^partition\s+(.+?)\s*=\s*(\w+)', stripped)
        if m:
            part_name = m.group(1).strip("'\"")
            mode = m.group(2)
            i += 1
            expr_lines = []; in_expr = False
            while i < len(lines):
                sub   = lines[i]
                sub_s = sub.strip().rstrip('\r')
                indent = len(sub) - len(sub.lstrip('\t '))

                # Skip mode:, lineageTag:, annotation lines inside partition
                if re.match(r'^(mode|lineageTag|annotation)\b', sub_s):
                    i += 1; continue

                # "source =" or "expression =" — value on same line OR empty (multi-line)
                m2 = re.match(r'^(?:expression|source)\s*=\s*(.*)$', sub_s)
                if m2:
                    val = m2.group(1).strip()
                    if val:                       # inline value (rare)
                        expr_lines.append(val)
                    else:                         # empty → multi-line follows
                        in_expr = True
                    i += 1; continue

                # bare "source" or "expression" keyword on its own line
                if re.match(r'^(?:source|expression)\s*$', sub_s):
                    in_expr = True; i += 1; continue

                # Collect expression body (indented under source =)
                if in_expr:
                    if indent >= 3:
                        expr_lines.append(sub_s); i += 1; continue
                    elif not sub_s:               # blank line inside expr
                        i += 1; continue
                    else:
                        break                     # back to table-level

                # Stop at next table-level keyword
                if sub_s and indent <= 1 and re.match(
                        r'^(column|measure|partition|table|relationship|annotation)\s', sub_s):
                    break
                i += 1

            partitions.append({
                "name": part_name, "mode": mode,
                "source": {"type": "m", "expression": "\n".join(expr_lines)},
            })
            continue

        i += 1

    if not table_name:
        return {}
    return {"name": table_name, "columns": columns, "measures": measures, "partitions": partitions}


def _parse_tmdl_relationships(content: str) -> list:
    rels, cur = [], {}
    for line in content.split('\n'):
        s = line.strip().rstrip('\r')
        if re.match(r'^relationship\s+', s):
            if cur.get("fromTable"): rels.append(cur)
            cur = {}
            continue
        # Handle dot-notation: "fromColumn: Table.Column" or separate fromTable:/fromColumn:
        for key, tbl_attr, col_attr in [
            ("fromColumn:", "fromTable", "fromColumn"),
            ("toColumn:",   "toTable",   "toColumn"),
        ]:
            if s.startswith(key):
                val = s[len(key):].strip()
                if '.' in val:               # Table.Column combined format
                    tbl, col = val.split('.', 1)
                    cur[tbl_attr] = tbl.strip()
                    cur[col_attr] = col.strip()
                else:
                    cur[col_attr] = val      # column only (table set separately)
        if s.startswith("fromTable:"):   cur["fromTable"] = s[len("fromTable:"):].strip()
        if s.startswith("toTable:"):     cur["toTable"]   = s[len("toTable:"):].strip()
        if s.startswith("cardinality:"): cur["type"]      = s[len("cardinality:"):].strip()
        if s.startswith("crossFilteringBehavior:"):
            cur["crossFilteringBehavior"] = s[len("crossFilteringBehavior:"):].strip()
        if s.startswith("isActive:"):    cur["isActive"]  = s[len("isActive:"):].strip()
    if cur.get("fromTable"): rels.append(cur)
    return rels


def _parse_tmdl_datasources(content: str) -> list:
    sources, cur = [], {}
    for line in content.split('\n'):
        s = line.strip()
        if re.match(r'^datasource\s+', s, re.IGNORECASE):
            if cur: sources.append(cur)
            cur = {"type": "structured"}
            continue
        if s.startswith("server:"):   cur["server"]   = s[7:].strip()
        if s.startswith("database:"): cur["database"] = s[9:].strip()
        if s.startswith("type:"):     cur["type"]     = s[5:].strip()
    if cur: sources.append(cur)
    return sources


# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — External Column Metadata (TSV from VertiPaq / DAX Studio)
# ─────────────────────────────────────────────────────────────────────────────

# SSAS ExplicitDataType codes → readable names
_SSAS_DTYPE = {
    2: "Text", 4: "Text", 6: "Integer", 7: "Decimal",
    8: "Boolean", 9: "DateTime", 10: "DateTime", 11: "Time",
    17: "Binary", 19: "Unknown"
}

def _merge_external_columns(tsv: str, result: dict):
    """
    Parse a TSV dump of the SSAS Column table and add all columns to result.

    The TSV has columns (0-indexed):
      0=ID, 1=TableID, 2=ExplicitName, 3=InferredName, 4=ExplicitDataType,
      5=InferredDataType, 8=IsHidden, 19=Type (1=data,3=rowNumber,4=calculated),
      20=SourceColumn, 23=FormatString

    TableID is matched to table names by:
      1. Exact column count match against DiagramLayout node heights
      2. Or by the order tables appear in DiagramLayout (same order as SSAS stores them)
    """
    import io as _io, csv

    lines = tsv.strip().splitlines()
    if not lines:
        return

    # Skip header row if present (starts with "[ID]" or "ID")
    first = lines[0].strip().lstrip("[")
    if first.lower().startswith("id"):
        lines = lines[1:]

    # Parse rows: group columns by TableID
    from collections import defaultdict, OrderedDict
    table_cols_raw = defaultdict(list)

    for line in lines:
        parts = line.split('\t')
        if len(parts) < 20:
            continue
        try:
            col_name  = parts[2].strip()
            table_id  = parts[1].strip()
            dtype_raw = int(parts[4].strip()) if parts[4].strip().isdigit() else 19
            is_hidden = parts[8].strip().lower() == 'true'
            col_type  = parts[19].strip()   # 1=data, 3=rowNumber, 4=calculated
            src_col   = parts[20].strip() if len(parts) > 20 else col_name
            fmt_str   = parts[23].strip() if len(parts) > 23 else ""
        except (IndexError, ValueError):
            continue

        # Skip RowNumber system columns
        if col_type == '3' or col_name.startswith('RowNumber-'):
            continue

        dtype = _SSAS_DTYPE.get(dtype_raw, f"Type{dtype_raw}")
        table_cols_raw[table_id].append({
            "col_name":    col_name,
            "dtype":       dtype,
            "is_hidden":   is_hidden,
            "src_col":     src_col,
            "fmt_str":     fmt_str,
            "is_calculated": col_type == '4',
        })

    if not table_cols_raw:
        return

    # Map TableIDs to table names using the known tables in result
    # Strategy: match by column count against DiagramLayout Est. Columns
    # (DiagramLayout gives ~N columns per table; we pick closest match)
    known_tables = {t["Table Name"]: t for t in result["tables"]}

    # Extract estimated column counts per table from the "Est. Columns" field
    est_col_counts = {}  # table_name -> int
    for tname, tdata in known_tables.items():
        est = tdata.get("Est. Columns", "")
        m = re.search(r'(\d+)', str(est))
        if m:
            est_col_counts[tname] = int(m.group(1))

    # Map TableIDs to table names using positional order.
    # SSAS stores tables in creation order matching DiagramLayout node order.
    # Lower TableID = earlier position in DiagramLayout node list.
    #
    # We read DiagramLayout node order directly from the result to get the
    # correct sequence (DiagramLayout adds nodes in SSAS creation order).
    tid_to_tname: dict[str, str] = {}

    # Sort TableIDs numerically (SSAS creation order)
    sorted_tids = sorted(table_cols_raw.keys(), key=lambda x: int(x) if x.isdigit() else 0)

    # Get DiagramLayout node order from result (stored in "diag_node_order" if available)
    # Fallback: use known table names sorted to best match
    diag_node_order = result.get("diag_node_order", [])
    if not diag_node_order:
        # Fallback: use all known table names in their result order
        diag_node_order = [t["Table Name"] for t in result["tables"]]

    for tid, tname in zip(sorted_tids, diag_node_order):
        tid_to_tname[tid] = tname

    result["parse_log"].append(f"Column metadata TableID mapping: {tid_to_tname}")

    if not tid_to_tname:
        result["errors"].append(
            "Could not map column metadata TableIDs to table names. "
            "Check that the column TSV matches the uploaded PBIX."
        )
        return

    # Replace/augment columns in result
    # Remove old partial columns for tables we now have full data for
    mapped_tnames = set(tid_to_tname.values())
    result["columns"] = [c for c in result["columns"]
                         if c["Table"] not in mapped_tnames]

    # Add all columns from the external metadata
    for tid, cols in table_cols_raw.items():
        tname = tid_to_tname.get(tid)
        if not tname:
            continue
        for c in cols:
            result["columns"].append({
                "Column Name":   c["col_name"],
                "Table":         tname,
                "Data Type":     c["dtype"],
                "Is Calculated": "Yes" if c["is_calculated"] else "No",
                "Expression":    "",
                "Is Hidden":     str(c["is_hidden"]),
                "Format String": c["fmt_str"],
                "Note":          "From column metadata",
            })

    # Update Est. Columns on tables that are now fully resolved
    for tid, tname in tid_to_tname.items():
        actual = len(table_cols_raw[tid])
        for t in result["tables"]:
            if t["Table Name"] == tname:
                t["Est. Columns"]  = f"{actual} columns"
                t["Row Count"]     = t.get("Row Count", "Stored in Power BI Service")
                break

    result["columns"] = _dedup(result["columns"], "Column Name", "Table")


# ─────────────────────────────────────────────────────────────────────────────
# Step 6 — External Measure Metadata (DAX formulas from DAX Studio)
# ─────────────────────────────────────────────────────────────────────────────

def _merge_external_measures(tsv: str, result: dict):
    """
    Parse a TSV dump of TMSCHEMA_MEASURES from DAX Studio / VertiPaq Analyzer
    and update measures in result with real DAX formulas.

    Expected TSV columns (0-indexed):
      0=ID, 1=TableID, 2=Name, 3=Description, 4=Expression (DAX),
      5=FormatString, 6=IsHidden, 7=State, ...

    TableID is resolved using the same diag_node_order mapping as columns.
    Alternatively if TableID is not available, matching is done by measure name.
    """
    lines = tsv.strip().splitlines()
    if not lines:
        return

    # Detect and skip header row
    first = lines[0].strip().lstrip("[")
    if first.lower().startswith("id"):
        lines = lines[1:]

    # Build TableID → table name mapping (reuse diag_node_order)
    diag_node_order = result.get("diag_node_order", [])
    tid_to_tname: dict[str, str] = {}
    # We need the same mapping used for columns — try to infer from existing data
    # by matching known table names positionally
    for t in result["tables"]:
        pass  # table names are resolved via diag_node_order below

    # Parse all measures from TSV
    parsed_measures: list[dict] = []
    for line in lines:
        parts = line.split('\t')
        if len(parts) < 5:
            continue
        try:
            meas_id    = parts[0].strip()
            table_id   = parts[1].strip()
            name       = parts[2].strip()
            desc       = parts[3].strip() if len(parts) > 3 else ""
            expression = parts[4].strip() if len(parts) > 4 else ""
            fmt_str    = parts[5].strip() if len(parts) > 5 else ""
            is_hidden  = parts[6].strip().lower() == 'true' if len(parts) > 6 else False
        except (IndexError, ValueError):
            continue

        if not name:
            continue

        parsed_measures.append({
            "table_id":   table_id,
            "name":       name,
            "expression": expression,
            "fmt_str":    fmt_str,
            "desc":       desc,
            "is_hidden":  is_hidden,
        })

    if not parsed_measures:
        return

    # Build TableID → table name mapping using diag_node_order
    # (same positional logic as column mapping — lower TableID = earlier position)
    if diag_node_order:
        # Collect unique TableIDs from measures, sorted numerically
        unique_tids = sorted(set(m["table_id"] for m in parsed_measures if m["table_id"]),
                             key=lambda x: int(x) if x.isdigit() else 0)
        for tid, tname in zip(unique_tids, diag_node_order):
            tid_to_tname[tid] = tname
        result["parse_log"].append(f"Measure metadata TableID mapping: {tid_to_tname}")

    # Update existing measures with real DAX, or add new ones
    existing_by_name: dict[str, dict] = {}
    for m in result["measures"]:
        existing_by_name[m["Measure Name"].strip().lower()] = m

    new_measures = []
    for pm in parsed_measures:
        name_key = pm["name"].strip().lower()

        # Resolve table name: try TableID mapping, then match by measure name
        tname = tid_to_tname.get(pm["table_id"], "")
        if not tname:
            # Fallback: use the table from existing measure with same name
            existing = existing_by_name.get(name_key)
            tname = existing["Table"] if existing else ""

        if not tname:
            # Can't determine table — add with unknown table
            tname = f"Table {pm['table_id']}" if pm["table_id"] else "Unknown"

        if name_key in existing_by_name:
            # Update existing measure with real DAX
            m = existing_by_name[name_key]
            m["DAX Formula"]   = pm["expression"] or m.get("DAX Formula", "")
            m["Format String"] = pm["fmt_str"]    or m.get("Format String", "")
            m["Description"]   = pm["desc"]       or m.get("Description", "")
            m["Is Hidden"]     = str(pm["is_hidden"])
            if tname:
                m["Table"] = tname
        else:
            # New measure not previously discovered from visuals
            new_measures.append({
                "Measure Name":  pm["name"],
                "Table":         tname,
                "DAX Formula":   pm["expression"],
                "Format String": pm["fmt_str"],
                "Is Hidden":     str(pm["is_hidden"]),
                "Description":   pm["desc"],
                "Tables Used":   "",
                "Columns Used":  "",
                "Measures Used": "",
            })

    result["measures"].extend(new_measures)

    # Re-run dependency analysis now that we have real DAX
    result["measures"] = _derive_measure_usage(result["measures"], result["tables"])
    result["measures"] = _dedup(result["measures"], "Measure Name", "Table")

    result["parse_log"].append(
        f"DAX formulas merged: {len(parsed_measures)} measures processed, "
        f"{len(new_measures)} newly added"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Post-processing: derive measure usage / DAX dependencies
# ─────────────────────────────────────────────────────────────────────────────

def _derive_measure_usage(measures, tables):
    table_names   = {t["Table Name"] for t in tables}
    measure_names = {m["Measure Name"] for m in measures}
    # Also build a stripped set so "count id " matches "count id" etc.
    measure_names_stripped = {m.strip() for m in measure_names}
    out = []
    for m in measures:
        dax = m.get("DAX Formula","")
        if "Not available" in dax:
            if not m.get("Tables Used"): m["Tables Used"] = m.get("Table","")
            if not m.get("Columns Used"): m["Columns Used"] = "—"
            m["Measures Used"] = "—"
        else:
            # 1. Tables used — word-boundary match
            tables_used = sorted({t for t in table_names
                                   if re.search(rf"\b{re.escape(t)}\b", dax, re.IGNORECASE)})

            # 2. Measure refs — bare [X] or [X ] where X.strip() is a known measure name
            measure_refs = sorted({
                mn for mn in measure_names
                if mn != m["Measure Name"] and mn.strip() != m["Measure Name"].strip()
                and re.search(rf"\[{re.escape(mn)}\s*\]", dax, re.IGNORECASE)
            })
            # Also match stripped versions (handles trailing-space measure names)
            for mn_stripped in measure_names_stripped:
                if mn_stripped == m["Measure Name"].strip():
                    continue
                if re.search(rf"\[\s*{re.escape(mn_stripped)}\s*\]", dax, re.IGNORECASE):
                    # Find the original name
                    orig = next((n for n in measure_names if n.strip() == mn_stripped), mn_stripped)
                    if orig not in measure_refs:
                        measure_refs = sorted(set(list(measure_refs) + [orig]))

            # 3. Column refs — Table[Column], excluding measure names (with/without spaces)
            table_col_refs = re.findall(r"'?([A-Za-z_][\w\s]*)'?\[([^\]]+)\]", dax)
            col_strs = sorted({
                f"{tbl}[{col}]"
                for tbl, col in table_col_refs
                if col.strip() not in measure_names_stripped
            })

            # 4. Bare [X] refs — not a measure, not already captured
            already = {col for _, col in table_col_refs}
            for bare in re.findall(r"(?<!['\w])\[([^\]]+)\]", dax):
                if bare.strip() not in measure_names_stripped and bare not in already:
                    col_strs.append(f"[{bare}]")
            col_strs = sorted(set(col_strs))

            m["Tables Used"]   = ", ".join(tables_used)   or m.get("Table","")
            m["Columns Used"]  = ", ".join(col_strs)       or "—"
            m["Measures Used"] = ", ".join(measure_refs)   or "—"
        out.append(m)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_MQUERY_PATTERNS = [
    (r'Sql\.(?:Database|Databases)\s*\(\s*"([^"]+)"\s*(?:,\s*"([^"]+)")?',  "SQL Server"),
    (r'AzureSQL\.Database\s*\(\s*"([^"]+)"\s*(?:,\s*"([^"]+)")?',           "Azure SQL"),
    (r'AnalysisServices\.Database\s*\(\s*"([^"]+)"\s*(?:,\s*"([^"]+)")?',   "Analysis Services"),
    (r'Excel\.Workbook\b',                                                    "Excel"),
    (r'SharePoint\.(?:Files|Tables|Lists)\s*\(\s*"([^"]+)"',                "SharePoint"),
    (r'Csv\.Document\b',                                                      "CSV"),
    (r'Folder\.Files\s*\(\s*"([^"]+)"',                                      "Folder"),
    (r'Web\.Contents\s*\(\s*"([^"]+)"',                                      "Web/API"),
    (r'OData\.Feed\s*\(\s*"([^"]+)"',                                        "OData"),
    (r'Oracle\.Database\s*\(\s*"([^"]+)"',                                   "Oracle"),
    (r'MySQL\.Database\s*\(\s*"([^"]+)"\s*(?:,\s*"([^"]+)")?',              "MySQL"),
    (r'PostgreSQL\.Database\s*\(\s*"([^"]+)"\s*(?:,\s*"([^"]+)")?',         "PostgreSQL"),
    (r'Snowflake\.Databases\s*\(\s*"([^"]+)"',                               "Snowflake"),
    (r'Table\.FromRows\s*\(',                                                   "Inline Table"),
    (r'GoogleBigQuery\.Database\s*\(\s*"([^"]+)"',                           "BigQuery"),
    (r'GoogleBigQuery\.Database\s*\(\s*\)',                                   "BigQuery"),
    (r'Databricks\.Catalogs\s*\(\s*"([^"]+)"',                               "Databricks"),
]

def _scan_mquery_sources(text, result):
    seen = {(s["Source Type"],s["Server"]) for s in result["sources"]}
    for pattern, src_type in _MQUERY_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            server   = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
            database = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
            # For GoogleBigQuery.Database() with no args, extract project from next line
            if src_type == "BigQuery" and not server:
                proj = re.search(r'#"([^"]+)"\s*=\s*Source\{', text[m.start():m.start()+500])
                schema = re.search(r'Name="([^"]+)",Kind="Schema"', text[m.start():m.start()+500])
                server   = proj.group(1)   if proj   else "Google BigQuery"
                database = schema.group(1) if schema else ""
            key = (src_type, server)
            if key not in seen:
                seen.add(key)
                result["sources"].append({"Source Type":src_type,"Server":server,"Database":database,"Query":""})

def _source_from_mquery(mq):
    if not mq: return "Unknown"
    for pattern, src_type in _MQUERY_PATTERNS:
        m = re.search(pattern, mq, re.IGNORECASE)
        if m:
            server = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
            # For no-arg BigQuery, extract project name from next line
            if src_type == "BigQuery" and not server:
                proj = re.search(r'#"([^"]+)"\s*=\s*Source\{', mq[m.start():m.start()+400])
                server = proj.group(1) if proj else "Google BigQuery"
            return f"{src_type}: {server}" if server else src_type
    return "Unknown"
def _parse_conn_string(s):
    server = database = ""
    for pair in (s or "").split(";"):
        if "=" not in pair: continue
        k,_,v = pair.partition("="); k = k.strip().lower()
        if k in ("data source","server","host","datasource"): server = v.strip()
        elif k in ("initial catalog","database","catalog"):   database = v.strip()
    return server, database

def _norm_source_type(raw):
    mapping = {"sql":"SQL Server","sqlserver":"SQL Server","azuresql":"Azure SQL",
               "excel":"Excel","xlsx":"Excel","sharepoint":"SharePoint","web":"Web/API",
               "odata":"OData","oracle":"Oracle","mysql":"MySQL","postgresql":"PostgreSQL",
               "snowflake":"Snowflake","databricks":"Databricks","bigquery":"BigQuery",
               "analysisservices":"Analysis Services","powerbi":"Power BI Service",
               "folder":"Folder","csv":"CSV"}
    key = re.sub(r"[\s_\.]","", raw.lower())
    for k,v in mapping.items():
        if k in key: return v
    return raw.title() if raw else "Unknown"

def _read_json(z, name, encoding="utf-8"):
    try:
        return json.loads(z.read(name).decode(encoding, errors="replace").lstrip("\ufeff"))
    except Exception: return None

def _try_json_any(raw):
    for enc in ("utf-8","utf-16-le","utf-16","latin-1"):
        try: return json.loads(raw.decode(enc, errors="replace").lstrip("\ufeff"))
        except Exception: continue
    return None

def _dedup(lst, *keys):
    seen, out = set(), []
    for item in lst:
        k = tuple(str(item.get(kk,"")) for kk in keys)
        if k not in seen: seen.add(k); out.append(item)
    return out

# ── Demo / Fallback Data ──────────────────────────────────────────────────────

def _demo_data(result):
    result["_demo_reason"] = "No metadata could be extracted."
    result["tables"] = [
        {"Table Name": "Sales",     "Source": "SQL Server", "Type": "Import",      "Row Count": "1,245,891", "Is Hidden": "False", "Description": ""},
        {"Table Name": "Products",  "Source": "SQL Server", "Type": "Import",      "Row Count": "8,432",     "Is Hidden": "False", "Description": ""},
        {"Table Name": "Customers", "Source": "SQL Server", "Type": "Import",      "Row Count": "124,560",   "Is Hidden": "False", "Description": ""},
        {"Table Name": "Date",      "Source": "Calculated", "Type": "Import",      "Row Count": "3,650",     "Is Hidden": "False", "Description": ""},
        {"Table Name": "Targets",   "Source": "Excel",      "Type": "Import",      "Row Count": "240",       "Is Hidden": "False", "Description": ""},
    ]
    result["columns"] = [
        {"Column Name": "Amount",  "Table": "Sales", "Data Type": "Decimal", "Is Calculated": "No",  "Expression": "", "Is Hidden": "False", "Format String": ""},
        {"Column Name": "Cost",    "Table": "Sales", "Data Type": "Decimal", "Is Calculated": "No",  "Expression": "", "Is Hidden": "False", "Format String": ""},
    ]
    result["measures"] = [
        {"Measure Name": "Total Sales",    "Table": "Sales", "DAX Formula": "Total Sales = SUM(Sales[Amount])",                           "Tables Used": "Sales",  "Columns Used": "Sales[Amount]",  "Measures Used": "—", "Format String": "", "Is Hidden": "False", "Description": ""},
        {"Measure Name": "Gross Profit",   "Table": "Sales", "DAX Formula": "Gross Profit = [Total Sales] - SUM(Sales[Cost])",            "Tables Used": "Sales",  "Columns Used": "Sales[Cost]",    "Measures Used": "Total Sales", "Format String": "", "Is Hidden": "False", "Description": ""},
        {"Measure Name": "Profit Margin %","Table": "Sales", "DAX Formula": "Profit Margin % = DIVIDE([Gross Profit], [Total Sales], 0)", "Tables Used": "Sales",  "Columns Used": "—",              "Measures Used": "Gross Profit, Total Sales", "Format String": "0.0%", "Is Hidden": "False", "Description": ""},
    ]
    result["relationships"] = []
    result["sources"] = [{"Source Type": "SQL Server", "Server": "prod-sql-01.company.com", "Database": "SalesWarehouse", "Query": ""}]
    return result


# ── Export helpers ────────────────────────────────────────────────────────────

def to_excel(data: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Drop Row Count from Tables sheet
        tdf = _df(data["tables"])
        drop = [c for c in ["Row Count","Est. Columns"] if c in tdf.columns]
        if drop: tdf = tdf.drop(columns=drop)
        tdf.to_excel(writer,                sheet_name="Tables",        index=False)
        _df(data["columns"]).to_excel(writer,        sheet_name="Columns",       index=False)
        _df(data["measures"]).to_excel(writer,       sheet_name="Measures",      index=False)
        _df(data["relationships"]).to_excel(writer,  sheet_name="Relationships", index=False)
        _df(data["sources"]).to_excel(writer,        sheet_name="Data Sources",  index=False)
        if data.get("visuals"):
            _df(data["visuals"]).to_excel(writer,    sheet_name="Visuals",       index=False)
    return buf.getvalue()

def to_json(data: dict) -> str:
    export = {k: v for k, v in data.items()
              if k in ("tables","columns","measures","relationships","sources","pages","visuals")}
    return json.dumps(export, indent=2)

def _df(lst):
    return pd.DataFrame(lst) if lst else pd.DataFrame()


# ── PBIX → PBIP folder extractor ─────────────────────────────────────────────

def pbix_to_report_zip(pbix_bytes: bytes, stem: str) -> bytes:
    """Extract PBIX Report/Layout into a .Report folder ZIP."""
    import zipfile as _zf
    files = {}
    try:
        with _zf.ZipFile(io.BytesIO(pbix_bytes)) as z:
            layout  = json.loads(z.read("Report/Layout").decode("utf-16-le","replace"))
            conn    = json.loads(z.read("Connections").decode("utf-8","replace"))
    except Exception:
        return b""

    files["report.json"] = json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.1.0/schema.json",
        "settings": layout.get("settings", {}),
    }, indent=2)

    section_names = [s.get("name","") for s in layout.get("sections",[])]
    files["pages.json"] = json.dumps({
        "pageOrder": section_names, "activePageName": section_names[0] if section_names else "",
    }, indent=2)

    for section in layout.get("sections", []):
        pname    = section.get("name","page")
        pdisplay = section.get("displayName","Page 1")
        files[f"pages/{pname}/page.json"] = json.dumps({
            "name": pname, "displayName": pdisplay,
            "height": section.get("height",720), "width": section.get("width",1280),
        }, indent=2)

        for i, vc in enumerate(section.get("visualContainers",[])):
            try:
                config   = json.loads(vc.get("config","{}"))
                sv       = config.get("singleVisual",{})
                vtype    = sv.get("visualType","unknown")
                vis_name = config.get("name", f"visual_{i}")
                pq       = sv.get("prototypeQuery",{})
                from_map = {f.get("Name",""):f.get("Entity","") for f in pq.get("From",[]) if isinstance(f,dict)}

                projections = []
                for sel in pq.get("Select",[]):
                    if not isinstance(sel,dict): continue
                    proj = {"queryRef": sel.get("Name",""), "nativeQueryRef": sel.get("NativeReferenceName","")}
                    m   = sel.get("Measure",{})
                    c   = sel.get("Column",{})
                    agg = sel.get("Aggregation",{})
                    def _ent(ref_dict):
                        return from_map.get((ref_dict.get("Expression",{}) or {}).get("SourceRef",{}).get("Source",""),"")
                    if m and isinstance(m,dict):
                        proj["field"] = {"Measure": {"Expression": {"SourceRef": {"Entity": _ent(m)}}, "Property": m.get("Property","")}}
                    elif c and isinstance(c,dict):
                        proj["field"] = {"Column": {"Expression": {"SourceRef": {"Entity": _ent(c)}}, "Property": c.get("Property","")}}
                    elif agg and isinstance(agg,dict):
                        inner = (agg.get("Expression",{}) or {}).get("Column",{})
                        proj["field"] = {"Aggregation": {
                            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": _ent(inner)}}, "Property": inner.get("Property","") if inner else ""}},
                            "Function": agg.get("Function",0)}}
                    projections.append(proj)

                vis_file = {
                    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.6.0/schema.json",
                    "name": vis_name,
                    "position": {"x":vc.get("x",0),"y":vc.get("y",0),"z":vc.get("z",0),
                                 "height":vc.get("height",300),"width":vc.get("width",300)},
                    "visual": {"visualType": vtype, "query": {"queryState": {"Values": {"projections": projections}}}},
                }
                files[f"pages/{pname}/visuals/{vis_name}/visual.json"] = json.dumps(vis_file, indent=2)
            except Exception:
                pass

    for artifact in conn.get("RemoteArtifacts",[]):
        files["localSettings.json"] = json.dumps({
            "remoteArtifacts": [{"reportId": artifact.get("ReportId","")}]
        }, indent=2)

    buf = io.BytesIO()
    with _zf.ZipFile(buf,"w",_zf.ZIP_DEFLATED) as z:
        for fname, content in files.items():
            z.writestr(f"{stem}.Report/{fname}", content.encode("utf-8"))
    return buf.getvalue()


# ── Smart file classifier ─────────────────────────────────────────────────────

def classify_and_load(files) -> tuple:
    """
    Given uploaded file objects, classify into:
      tmdl_contents  — {fname: str}   from SemanticModel TMDL files
      bim_bytes      — bytes           single .bim / XMLA JSON
      pbix_bytes     — bytes           .pbix / .pbit
      visual_jsons   — [dict]          visual.json objects  (Report folder)
      page_jsons     — [dict]          page.json objects    (Report folder)
    
    Handles:
      - A PBIP project ZIP (contains both .SemanticModel/ and .Report/ folders)
      - A ZIP of just the SemanticModel folder (all TMDL files)
      - A ZIP of just the Report folder (visual.json files)
      - Individual TMDL / .bim / .json / .pbix files
    """
    import zipfile as _zf

    tmdl_contents = {}
    bim_bytes     = None
    pbix_bytes    = None
    visual_jsons  = []
    page_jsons    = []

    for f in files:
        fname  = f.name
        ext    = ("." + fname.rsplit(".",1)[-1].lower()) if "." in fname else ""
        fbytes = f.read()

        # ── ZIP: detect contents ───────────────────────────────────────────────
        if ext == ".zip":
            try:
                with _zf.ZipFile(io.BytesIO(fbytes)) as z:
                    znames = z.namelist()
                    # Build page_id → displayName map from page.json files first
                    _page_id_map = {}
                    for zname in znames:
                        if zname.endswith("page.json") and "/pages/" in zname and "visuals" not in zname:
                            try:
                                obj = json.loads(z.read(zname).decode("utf-8","replace"))
                                if "name" in obj and "displayName" in obj:
                                    _page_id_map[obj["name"]] = obj["displayName"]
                            except: pass

                    for zname in znames:
                        zext  = ("." + zname.rsplit(".",1)[-1].lower()) if "." in zname else ""
                        zbase = zname.split("/")[-1]
                        zbytes = z.read(zname)

                        if zext == ".tmdl":
                            tmdl_contents[zbase] = zbytes.decode("utf-8","replace")

                        elif zext == ".bim" and bim_bytes is None:
                            bim_bytes = zbytes

                        elif zext in (".pbix",".pbit") and pbix_bytes is None:
                            pbix_bytes = zbytes

                        elif zext == ".json" and zbase:
                            try:
                                obj = json.loads(zbytes.decode("utf-8","replace"))
                                zpath_lower = zname.lower()

                                # visual.json — inject _page_id from path
                                if "visuals/" in zpath_lower and zbase == "visual.json":
                                    parts = zname.split("/")
                                    if "pages" in parts:
                                        pi = parts.index("pages")
                                        obj["_page_id"] = parts[pi+1] if pi+1 < len(parts) else ""
                                    visual_jsons.append(obj)

                                elif zbase in ("page.json","pages.json") \
                                   or "page" in zbase.lower():
                                    page_jsons.append(obj)

                                elif any(k in obj for k in
                                         ("model","tables","compatibilityLevel","create","createOrReplace")):
                                    bim_bytes = zbytes

                            except Exception:
                                pass

                    # Store the page_id_map so extract_from_classified can pass it through
                    if _page_id_map and not hasattr(_page_id_map, '_injected'):
                        page_jsons.append({"_page_id_map": _page_id_map})

            except Exception:
                pass
            continue

        # ── Individual files ───────────────────────────────────────────────────
        if ext == ".tmdl":
            tmdl_contents[fname] = fbytes.decode("utf-8","replace")
        elif ext == ".bim":
            bim_bytes = fbytes
        elif ext in (".pbix",".pbit"):
            pbix_bytes = fbytes
        elif ext == ".json":
            try:
                obj = json.loads(fbytes.decode("utf-8","replace"))
                if "visualType" in str(obj) or "visual" in fname.lower():
                    visual_jsons.append(obj)
                elif "page" in fname.lower() or "displayName" in str(obj):
                    page_jsons.append(obj)
                elif any(k in obj for k in ("model","tables","compatibilityLevel","create")):
                    bim_bytes = fbytes
                else:
                    page_jsons.append(obj)
            except Exception:
                pass

    return tmdl_contents, bim_bytes, pbix_bytes, visual_jsons, page_jsons


def extract_from_classified(tmdl_contents, bim_bytes, pbix_bytes, visual_jsons, page_jsons):
    """
    Run extraction on classified file collections.
    Returns (sem_data, rep_data) — either can be None.
    """
    sem_data = None
    rep_data = None

    # ── SemanticModel extraction ───────────────────────────────────────────────
    if tmdl_contents:
        model = _parse_tmdl_folder(tmdl_contents)
        sem_data = _empty_result()
        sem_data["report_type"] = "Desktop"
        sem_data["parse_log"].append(f"TMDL: {len(tmdl_contents)} files — {', '.join(sorted(tmdl_contents.keys()))}")
        _parse_tmsl({"model": model}, sem_data)
        sem_data = _finalise(sem_data)
        sem_data["_source"] = "SemanticModel (TMDL)"

    elif bim_bytes:
        obj = _try_tmsl_json(bim_bytes)
        if obj:
            sem_data = _empty_result()
            sem_data["report_type"] = "Desktop"
            _parse_tmsl(obj, sem_data)
            sem_data = _finalise(sem_data)
            sem_data["_source"] = "SemanticModel (BIM/JSON)"

    elif pbix_bytes and not visual_jsons:
        class _FF:
            def __init__(self,b): self._b=b; self.name="upload.pbix"
            def read(self): return self._b
        sem_data = extract_any(_FF(pbix_bytes), "upload.pbix")
        sem_data["_source"] = "PBIX"

    # ── Report extraction ─────────────────────────────────────────────────────
    if visual_jsons:
        # Extract page_id_map injected during ZIP parsing
        page_id_map = {}
        real_page_jsons = []
        for pj in page_jsons:
            if "_page_id_map" in pj:
                page_id_map.update(pj["_page_id_map"])
            else:
                real_page_jsons.append(pj)

        rep_data = _empty_result()
        rep_data["report_type"] = "Cloud"
        rep_data["_source"] = f"Report ({len(visual_jsons)} visual.json files)"
        rep_data["parse_log"].append(f"Report: {len(visual_jsons)} visuals, {len(real_page_jsons)} page files, {len(page_id_map)} page IDs mapped")
        _parse_visual_json_files(visual_jsons, real_page_jsons, rep_data, page_id_map=page_id_map)
        rep_data = _finalise(rep_data)

    elif pbix_bytes and not sem_data:
        # PBIX with no TMDL — extract report layout from it
        class _FF:
            def __init__(self,b): self._b=b; self.name="upload.pbix"
            def read(self): return self._b
        rep_data = extract_any(_FF(pbix_bytes), "upload.pbix")
        rep_data["_source"] = "PBIX Report"

    return sem_data, rep_data


def merge_results(sem, rep):
    if sem and rep:
        merged = dict(sem)
        merged["pages"]   = rep.get("pages",   sem.get("pages",   []))
        merged["visuals"] = rep.get("visuals",  sem.get("visuals", []))
        sem_src_keys = {(s["Source Type"],s["Server"]) for s in merged["sources"]}
        for s in rep.get("sources",[]):
            if (s["Source Type"],s["Server"]) not in sem_src_keys:
                merged["sources"].append(s)
        merged["_source"]   = f"{sem.get('_source','SemanticModel')} + {rep.get('_source','Report')}"
        merged["parse_log"] = sem.get("parse_log",[]) + rep.get("parse_log",[])
        return merged
    return sem or rep or {}


# ── Relationship renderer ─────────────────────────────────────────────────────

def render_rel_table(rels):
    if not rels:
        st.markdown('<div class="empty-state"><span class="empty-icon">🔗</span>No relationships defined.</div>', unsafe_allow_html=True)
        return
    for r in rels:
        active_color = "#10b981" if str(r.get("Active","True"))=="True" else "#6b7280"
        st.markdown(f"""
        <div class="rel-row">
            <span class="rel-table">{r['From Table']}</span>
            <span class="rel-col">[{r['From Column']}]</span>
            <span class="rel-arrow">→</span>
            <span class="rel-table">{r['To Table']}</span>
            <span class="rel-col">[{r['To Column']}]</span>
            <span class="rel-type" style="color:{active_color}">{r.get('Relationship Type','Many-to-One')} · {'Active' if str(r.get('Active','True'))=='True' else 'Inactive'}</span>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ── UI ────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
  <div>
    <p class="hero-subtitle">Power BI · Metadata Analysis Tool</p>
    <h1 class="hero-title">PBIX<span> Inspector</span></h1>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.5rem">
    <span class="hero-badge">v3.0.0</span>
    <span style="font-family:var(--mono);font-size:0.68rem;color:var(--text-muted)">ZIP · PBIX · PBIT · BIM · TMDL</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Single upload ─────────────────────────────────────────────────────────────

uploaded = st.file_uploader(
    "Upload file",
    type=["zip", "pbix", "pbit", "bim", "json"],
    help="Upload a ZIP of your PBIP project folder, a .pbix/.pbit, or a .bim/.json",
    label_visibility="collapsed",
    key="main_uploader",
)

if uploaded is None:
    st.markdown("""
    <div style="background:var(--surface);border:2px dashed var(--border);border-radius:12px;
                padding:2.5rem 2rem;text-align:center;margin-bottom:1.5rem">
      <div style="font-size:2.5rem;margin-bottom:0.75rem">📂</div>
      <div style="font-family:var(--sans);font-weight:700;font-size:1.1rem;
                  color:var(--text);margin-bottom:0.5rem">
        Drop your file here or click to browse
      </div>
      <div style="font-family:var(--mono);font-size:0.72rem;color:var(--text-muted)">
        .zip &nbsp;·&nbsp; .pbix &nbsp;·&nbsp; .pbit &nbsp;·&nbsp; .bim &nbsp;·&nbsp; .json (XMLA)
      </div>
    </div>
    """, unsafe_allow_html=True)

    # What to upload
    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem">

      <div style="background:var(--surface);border:1px solid rgba(247,201,72,0.4);
                  border-radius:10px;padding:1.1rem">
        <div style="font-family:var(--sans);font-weight:700;font-size:0.88rem;
                    color:var(--accent);margin-bottom:0.5rem">⭐ Best — PBIP Project ZIP</div>
        <div style="font-family:var(--mono);font-size:0.68rem;color:var(--text-muted);line-height:1.7">
          Right-click the project folder containing<br>
          <code style="color:var(--accent)">New dashboard.SemanticModel</code><br>
          <code style="color:var(--accent)">New dashboard.Report</code><br>
          → Compress to ZIP → upload<br><br>
          Gives: full DAX + all columns + visuals
        </div>
      </div>

      <div style="background:var(--surface);border:1px solid rgba(59,130,246,0.4);
                  border-radius:10px;padding:1.1rem">
        <div style="font-family:var(--sans);font-weight:700;font-size:0.88rem;
                    color:#93c5fd;margin-bottom:0.5rem">🖥️ Desktop — PBIX / PBIT</div>
        <div style="font-family:var(--mono);font-size:0.68rem;color:var(--text-muted);line-height:1.7">
          Upload a <code style="color:#93c5fd">.pbix</code> or <code style="color:#93c5fd">.pbit</code>
          saved from Power BI Desktop<br><br>
          Gives: full DAX + columns + visuals<br><br>
          <em>Cloud-connected .pbix gives visuals only (no DAX)</em>
        </div>
      </div>

      <div style="background:var(--surface);border:1px solid rgba(16,185,129,0.4);
                  border-radius:10px;padding:1.1rem">
        <div style="font-family:var(--sans);font-weight:700;font-size:0.88rem;
                    color:#6ee7b7;margin-bottom:0.5rem">📋 Model Only — BIM / JSON</div>
        <div style="font-family:var(--mono);font-size:0.68rem;color:var(--text-muted);line-height:1.7">
          Upload a <code style="color:#6ee7b7">.bim</code> or XMLA
          <code style="color:#6ee7b7">.json</code> from<br>
          Tabular Editor or SSMS<br><br>
          Gives: full DAX + all columns<br>
          <em>(no visual / report data)</em>
        </div>
      </div>

    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Extract ───────────────────────────────────────────────────────────────────
with st.spinner("Extracting metadata…"):
    tmdl, bim, pbix_b, visual_jsons, page_jsons = classify_and_load([uploaded])

    # If PBIX with no TMDL — also extract report visuals from its Report/Layout
    if pbix_b and not visual_jsons:
        import zipfile as _zf
        try:
            with _zf.ZipFile(io.BytesIO(pbix_b)) as z:
                if "Report/Layout" in z.namelist():
                    layout = json.loads(z.read("Report/Layout").decode("utf-16-le","replace"))
                    for section in layout.get("sections",[]):
                        page_jsons.append({"name": section.get("name",""), "displayName": section.get("displayName","Page 1")})
                        for i, vc in enumerate(section.get("visualContainers",[])):
                            try:
                                config   = json.loads(vc.get("config","{}"))
                                sv       = config.get("singleVisual",{})
                                pq       = sv.get("prototypeQuery",{})
                                from_map = {f.get("Name",""):f.get("Entity","") for f in pq.get("From",[]) if isinstance(f,dict)}
                                vis_obj  = {"$schema":"pbix","name":config.get("name",f"v{i}"),
                                            "visual":{"visualType":sv.get("visualType","unknown"),"query":{"queryState":{}}}}
                                projs = []
                                for sel in pq.get("Select",[]):
                                    if not isinstance(sel,dict): continue
                                    def _ent(d):
                                        return from_map.get((d.get("Expression",{}) or {}).get("SourceRef",{}).get("Source",""),"")
                                    proj = {"queryRef":sel.get("Name",""),"nativeQueryRef":sel.get("NativeReferenceName","")}
                                    m2=sel.get("Measure",{}); c2=sel.get("Column",{}); a2=sel.get("Aggregation",{})
                                    if m2 and isinstance(m2,dict):
                                        proj["field"]={"Measure":{"Expression":{"SourceRef":{"Entity":_ent(m2)}},"Property":m2.get("Property","")}}
                                    elif c2 and isinstance(c2,dict):
                                        proj["field"]={"Column":{"Expression":{"SourceRef":{"Entity":_ent(c2)}},"Property":c2.get("Property","")}}
                                    elif a2 and isinstance(a2,dict):
                                        inn=(a2.get("Expression",{}) or {}).get("Column",{})
                                        proj["field"]={"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Entity":_ent(inn)}},"Property":inn.get("Property","") if inn else ""}},"Function":a2.get("Function",0)}}
                                    projs.append(proj)
                                vis_obj["visual"]["query"]["queryState"]={"Values":{"projections":projs}}
                                visual_jsons.append(vis_obj)
                            except Exception:
                                pass
        except Exception:
            pass

    sem_data, rep_data = extract_from_classified(tmdl, bim, pbix_b, visual_jsons, page_jsons)
    data = merge_results(sem_data, rep_data)

if not data:
    st.error("Could not extract any metadata from the uploaded file.")
    st.stop()

file_mb     = uploaded.size / (1024 * 1024)
report_type = data.get("report_type", "unknown")
source_label= data.get("_source", "")

# ── Status banner ─────────────────────────────────────────────────────────────
if data.get("_demo"):
    st.warning("⚠️ No metadata extracted. Showing demo data.", icon="⚠️")
elif sem_data and rep_data:
    st.success("✅ **Full extraction** — SemanticModel (DAX + schema) + Report (visuals) extracted and merged.", icon="✅")
elif sem_data:
    st.success("🗄️ **Model extracted** — full DAX, all columns, relationships.", icon="🗄️")
elif rep_data:
    st.info("📊 **Report extracted** — visual metadata only. For full DAX, upload the PBIP project ZIP.", icon="📊")

if data.get("errors"):
    with st.expander("⚠️ Extraction warnings"):
        for e in data["errors"]: st.warning(e)


# ── Metric cards ──────────────────────────────────────────────────────────────
n_tables = len(data["tables"]); n_cols = len(data["columns"])
n_meas   = len(data["measures"]); n_rels = len(data["relationships"])
n_src    = len(data["sources"]); n_pages = len(data.get("pages",[]))

st.markdown(f"""
<div class="metrics-row" style="grid-template-columns:repeat(6,1fr)">
  <div class="metric-card yellow"><div class="metric-label">Tables</div><div class="metric-value">{n_tables}</div></div>
  <div class="metric-card blue"><div class="metric-label">Columns</div><div class="metric-value">{n_cols}</div></div>
  <div class="metric-card green"><div class="metric-label">Measures</div><div class="metric-value">{n_meas}</div></div>
  <div class="metric-card red"><div class="metric-label">Relationships</div><div class="metric-value">{n_rels}</div></div>
  <div class="metric-card purple"><div class="metric-label">Sources</div><div class="metric-value">{n_src}</div></div>
  <div class="metric-card" style="border-top:2px solid #f97316"><div class="metric-label">Pages</div><div class="metric-value" style="color:#f97316">{n_pages}</div></div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
(tab_overview, tab_tables, tab_columns, tab_measures,
 tab_deps, tab_rels, tab_sources, tab_visuals, tab_export) = st.tabs([
    "📊 Overview", "🗂 Tables", "🔢 Columns", "📐 Measures",
    "🔍 Dependencies", "🔗 Relationships", "🔌 Data Sources", "🖼 Visuals", "⬇️ Export",
])


# ─────────────────────────────────────────────
# Tab 1 — Overview
# ─────────────────────────────────────────────
with tab_overview:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="section-label">File Info</p>', unsafe_allow_html=True)
        rtype_display = {"Cloud":"☁️ Cloud/Thin Report","Desktop":"🖥️ Desktop Report"}.get(report_type,f"❓ {report_type}")
        st.markdown(f"""
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1rem;">
          <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid var(--border)">
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text-muted)">Filename</span>
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text)">{uploaded.name}</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid var(--border)">
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text-muted)">File Size</span>
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text)">{file_mb:.2f} MB</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid var(--border)">
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text-muted)">Report Type</span>
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text)">{rtype_display}</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:0.4rem 0">
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text-muted)">Pages</span>
            <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text)">{", ".join(data.get("pages",[])) or "—"}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<p class="section-label" style="margin-top:1.5rem">Storage Mode</p>', unsafe_allow_html=True)
        if data["tables"]:
            types = pd.DataFrame(data["tables"])["Type"].value_counts().reset_index()
            types.columns = ["Type","Count"]
            st.dataframe(types, use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<p class="section-label">Tables in Model</p>', unsafe_allow_html=True)
        if data["tables"]:
            tdf = pd.DataFrame(data["tables"])
            show_cols = [c for c in ["Table Name","Type","Source","Is Hidden"] if c in tdf.columns]
            st.dataframe(tdf[show_cols], use_container_width=True, hide_index=True)

    if data.get("parse_log"):
        with st.expander("🔬 Extraction Log"):
            st.code("\n".join(data["parse_log"]))


# ─────────────────────────────────────────────
# Tab 2 — Tables
# ─────────────────────────────────────────────
with tab_tables:
    if report_type == "Cloud":
        st.markdown('<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:0.75rem 1rem;margin-bottom:1rem;font-family:var(--mono);font-size:0.72rem;color:var(--text-muted)"><span style="color:#a855f7">☁️</span> Cloud report — column schema stored in Power BI Service. Upload SemanticModel files for full details.</div>', unsafe_allow_html=True)

    cs1, cs2 = st.columns([2,1])
    with cs1: search_t = st.text_input("Search tables", placeholder="Filter…", key="search_tables")
    with cs2:
        mode_opts = ["All"] + sorted({r.get("Type","") for r in data["tables"]} - {""})
        mode_filter = st.selectbox("Storage mode", mode_opts, key="table_mode_filter")

    tdf = pd.DataFrame(data["tables"]) if data["tables"] else pd.DataFrame(columns=["Table Name","Source","Type"])
    if mode_filter != "All": tdf = tdf[tdf["Type"] == mode_filter]
    if search_t: tdf = tdf[tdf.apply(lambda r: search_t.lower() in str(r).lower(), axis=1)]
    show = [c for c in ["Table Name","Type","Source","Is Hidden","Description"] if c in tdf.columns]
    st.dataframe(tdf[show] if show else tdf, use_container_width=True, hide_index=True, height=480)

    if data["tables"]:
        tdf_all = pd.DataFrame(data["tables"])
        type_counts = tdf_all["Type"].value_counts()
        colors = {"Import":"var(--accent3)","DirectQuery":"var(--accent2)","Cloud":"#a855f7","Dual":"var(--accent)"}
        badges = "".join(f'<span style="background:var(--surface2);border:1px solid var(--border);border-radius:20px;padding:0.2rem 0.7rem;font-family:var(--mono);font-size:0.7rem;color:{colors.get(m,"var(--text-muted)")};margin-right:0.5rem">{m}: {c}</span>' for m,c in type_counts.items())
        st.markdown(f'<div style="margin-top:0.75rem">{badges}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Tab 3 — Columns
# ─────────────────────────────────────────────
with tab_columns:
    if report_type == "Cloud" and data["columns"]:
        n_vc = len(data["columns"]); n_vt = len({c["Table"] for c in data["columns"]})
        st.markdown(f'<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:0.75rem 1rem;margin-bottom:1rem;font-family:var(--mono);font-size:0.72rem;color:var(--text-muted)"><span style="color:#a855f7">☁️</span> Showing <strong style="color:var(--text)">{n_vc} column(s)</strong> across <strong style="color:var(--text)">{n_vt} table(s)</strong> — only columns used in report visuals are visible. Full schema is in the SemanticModel.</div>', unsafe_allow_html=True)

    cc1, cc2 = st.columns([2,1])
    with cc1: search_c = st.text_input("Search columns", placeholder="Column or table…", key="search_cols")
    with cc2:
        table_opts = ["All"] + sorted({r.get("Table","") for r in data["columns"]} - {""})
        table_filter = st.selectbox("Filter by table", table_opts, key="col_table_filter")

    cdf = pd.DataFrame(data["columns"]) if data["columns"] else pd.DataFrame(columns=["Column Name","Table","Data Type","Is Calculated"])
    if table_filter != "All": cdf = cdf[cdf["Table"] == table_filter]
    if search_c: cdf = cdf[cdf.apply(lambda r: search_c.lower() in str(r).lower(), axis=1)]
    show = [c for c in ["Column Name","Table","Data Type","Is Calculated","Format String","Is Hidden","Expression","Note"] if c in cdf.columns]
    st.dataframe(cdf[show] if show else cdf, use_container_width=True, hide_index=True, height=480)

    if not cdf.empty and "Data Type" in cdf.columns:
        with st.expander("📊 Data Type Breakdown"):
            dt = cdf["Data Type"].value_counts().reset_index(); dt.columns=["Data Type","Count"]
            st.dataframe(dt, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# Tab 4 — Measures
# ─────────────────────────────────────────────
with tab_measures:
    mc1, mc2, mc3 = st.columns([2,1,1])
    with mc1: search_m = st.text_input("Search measures", placeholder="Name or keyword…", key="search_meas")
    with mc2:
        m_table_opts = ["All"] + sorted({r.get("Table","") for r in data["measures"]} - {""})
        m_table_filter = st.selectbox("Filter by table", m_table_opts, key="meas_table_filter")
    with mc3:
        view_mode = st.selectbox("View", ["Cards (detailed)","Table (compact)"], key="meas_view_mode")

    mdf = pd.DataFrame(data["measures"]) if data["measures"] else pd.DataFrame()
    if not mdf.empty:
        if m_table_filter != "All": mdf = mdf[mdf["Table"] == m_table_filter]
        if search_m: mdf = mdf[mdf.apply(lambda r: search_m.lower() in str(r).lower(), axis=1)]

    if mdf.empty:
        st.markdown('<div class="empty-state"><span class="empty-icon">📐</span>No measures found.</div>', unsafe_allow_html=True)
    elif "Table" in view_mode:
        show = [c for c in ["Measure Name","Table","DAX Formula","Tables Used","Columns Used","Measures Used","Format String"] if c in mdf.columns]
        st.dataframe(mdf[show], use_container_width=True, hide_index=True, height=500)
    else:
        is_cloud_report = report_type == "Cloud" and not sem_data
        if is_cloud_report:
            st.markdown('<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:0.75rem 1rem;margin-bottom:1rem;font-family:var(--mono);font-size:0.72rem;color:var(--text-muted)"><span style="color:#a855f7">☁️</span> DAX formulas stored in Power BI Service. Upload SemanticModel files (left box) to see full DAX.</div>', unsafe_allow_html=True)

        for _, row in mdf.iterrows():
            dax      = row.get("DAX Formula","")
            is_cloud = "Not available" in dax
            label    = f"**{row['Measure Name']}**  ·  _{row.get('Table','')}_"
            if is_cloud: label += "  &nbsp;`☁️`"
            if row.get("Format String"): label += f"  &nbsp;`{row['Format String']}`"

            with st.expander(label):
                if is_cloud:
                    st.markdown('<div style="background:var(--surface2);border:1px solid var(--border);border-left:3px solid #a855f7;border-radius:6px;padding:0.8rem 1rem;font-family:var(--mono);font-size:0.78rem;color:var(--text-muted);font-style:italic">DAX stored in Power BI Service.<br><span style="color:var(--text);font-style:normal;">Upload SemanticModel TMDL files in the left uploader to see full DAX.</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="dax-formula">{dax}</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                u1, u2, u3 = st.columns(3)
                def _pills(vals, color, bg):
                    if not vals or vals == "—": return f'<span style="color:var(--text-muted);font-family:var(--mono);font-size:0.75rem">—</span>'
                    return "".join(f'<span style="background:{bg};border:1px solid {color};border-radius:4px;padding:0.15rem 0.5rem;font-family:var(--mono);font-size:0.72rem;color:{color};margin:2px;display:inline-block">{v.strip()}</span>' for v in vals.split(",") if v.strip())

                with u1:
                    st.markdown("**📋 Tables Used**")
                    st.markdown(_pills(row.get("Tables Used","—"), "var(--accent)", "rgba(247,201,72,0.1)"), unsafe_allow_html=True)
                with u2:
                    st.markdown("**🔢 Columns Used**")
                    st.markdown(_pills(row.get("Columns Used","—"), "#93c5fd", "rgba(59,130,246,0.1)"), unsafe_allow_html=True)
                with u3:
                    st.markdown("**🔗 Measures Used**")
                    st.markdown(_pills(row.get("Measures Used","—"), "#6ee7b7", "rgba(16,185,129,0.1)"), unsafe_allow_html=True)

                if row.get("Description"):
                    st.markdown(f'<div style="margin-top:0.5rem;font-family:var(--mono);font-size:0.72rem;color:var(--text-muted)">📝 {row["Description"]}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Tab 5 — Dependencies
# ─────────────────────────────────────────────
with tab_deps:
    st.markdown('<p class="section-label">Measure Dependency Matrix</p>', unsafe_allow_html=True)
    if data["measures"]:
        dep_rows = [{"Measure":m["Measure Name"],"Home Table":m.get("Table",""),"Tables Used":m.get("Tables Used","—"),"Columns Used":m.get("Columns Used","—"),"Measures Used":m.get("Measures Used","—")} for m in data["measures"]]
        st.dataframe(pd.DataFrame(dep_rows), use_container_width=True, hide_index=True, height=360)

        edges = [(m["Measure Name"],dep.strip()) for m in data["measures"] for dep in m.get("Measures Used","—").split(",") if m.get("Measures Used","—")!="—" and dep.strip()]
        if edges:
            G = nx.DiGraph(); G.add_edges_from(edges)
            rows_html = "".join(f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border)"><span class="dep-pill">{s}</span><span style="color:var(--accent2)">→</span><span class="dep-pill" style="color:var(--accent3)">{t}</span></div>' for s,t in edges)
            st.markdown(f'<div class="graph-container"><div style="font-family:var(--mono);font-size:0.72rem;color:var(--text-muted);margin-bottom:1rem">{G.number_of_nodes()} measures · {G.number_of_edges()} dependency edges</div>{rows_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state"><span class="empty-icon">🔍</span>No measure-to-measure dependencies.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><span class="empty-icon">📐</span>No measures to analyze.</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Tab 6 — Relationships
# ─────────────────────────────────────────────
with tab_rels:
    st.markdown('<p class="section-label">Model Relationships</p>', unsafe_allow_html=True)
    if not data["relationships"] and report_type == "Cloud":
        st.info("Relationships are defined in the SemanticModel. Upload TMDL files to see them.", icon="🗄️")
    render_rel_table(data["relationships"])
    if data["relationships"]:
        st.markdown("---")
        st.dataframe(pd.DataFrame(data["relationships"]), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# Tab 7 — Data Sources
# ─────────────────────────────────────────────
with tab_sources:
    st.markdown('<p class="section-label">Connected Sources</p>', unsafe_allow_html=True)
    if not data["sources"]:
        st.markdown('<div class="empty-state"><span class="empty-icon">🔌</span>No data sources found. Upload SemanticModel files.</div>', unsafe_allow_html=True)
    else:
        for s in data["sources"]:
            stype = s.get("Source Type","Unknown").lower()
            badge_cls = "source-sql" if "sql" in stype or "azure" in stype else ("source-excel" if "excel" in stype or "sharepoint" in stype else "source-other")
            db_html  = f'<div style="font-family:var(--mono);font-size:0.72rem;color:var(--text-muted);margin-top:0.3rem">{s["Database"]}</div>' if s.get("Database") else ""
            q_html   = f'<div class="dax-formula" style="margin-top:0.5rem;color:var(--text-muted)">{s["Query"]}</div>' if s.get("Query") else ""
            st.markdown(f'<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1rem 1.2rem;margin-bottom:0.75rem"><div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.3rem"><span class="source-badge {badge_cls}">{s.get("Source Type","Unknown")}</span><span style="font-family:var(--mono);font-size:0.82rem;color:var(--text)">{s.get("Server","")}</span></div>{db_html}{q_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Tab 8 — Visuals
# ─────────────────────────────────────────────
with tab_visuals:
    st.markdown('<p class="section-label">Report Visuals</p>', unsafe_allow_html=True)
    visuals = data.get("visuals",[])
    if not visuals:
        st.markdown('<div class="empty-state"><span class="empty-icon">🖼</span>No visual data. Upload Report files (right box) or a .pbix.</div>', unsafe_allow_html=True)
    else:
        vdf = pd.DataFrame(visuals)
        col1, col2 = st.columns([1,2])
        with col1:
            st.markdown('<p class="section-label">Visual Types</p>', unsafe_allow_html=True)
            vc = vdf["Visual Type"].value_counts().reset_index(); vc.columns=["Visual Type","Count"]
            st.dataframe(vc, use_container_width=True, hide_index=True)
        with col2:
            st.markdown('<p class="section-label">Tables per Page</p>', unsafe_allow_html=True)
            pt = vdf.groupby("Page")["Tables Used"].apply(lambda x: ", ".join(sorted({t.strip() for v in x for t in v.split(",") if t.strip()}))).reset_index()
            pt.columns=["Page","Tables Used"]
            st.dataframe(pt, use_container_width=True, hide_index=True)
        st.markdown('<p class="section-label" style="margin-top:1.5rem">All Visuals</p>', unsafe_allow_html=True)
        show = [c for c in ["Page","Visual Type","Tables Used","Measures Used","Columns Used"] if c in vdf.columns]
        st.dataframe(vdf[show], use_container_width=True, hide_index=True, height=400)


# ─────────────────────────────────────────────
# Tab 9 — Export
# ─────────────────────────────────────────────
with tab_export:
    st.markdown('<p class="section-label">Export Metadata</p>', unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    stem = "metadata"

    with e1:
        st.markdown("#### 📊 Excel Workbook")
        st.markdown('<span style="font-family:var(--mono);font-size:0.72rem;color:var(--text-muted)">All sheets: Tables, Columns, Measures, Relationships, Sources, Visuals</span>', unsafe_allow_html=True)
        st.download_button("Download .xlsx", data=to_excel(data), file_name=f"{stem}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with e2:
        for key, label in [("tables","Tables"),("measures","Measures"),("columns","Columns")]:
            st.markdown(f"#### 📄 {label} CSV")
            st.download_button(f"Download {label.lower()}.csv", data=_df(data[key]).to_csv(index=False), file_name=f"{stem}_{key}.csv", mime="text/csv", key=f"dl_{key}")

    with e3:
        st.markdown("#### 🔣 JSON")
        st.download_button("Download .json", data=to_json(data), file_name=f"{stem}.json", mime="application/json")

    st.markdown("---")
    st.markdown('<p class="section-label">Preview</p>', unsafe_allow_html=True)
    preview_choice = st.selectbox("Preview dataset", ["Tables","Columns","Measures","Relationships","Data Sources","Visuals"])
    preview_map = {"Tables":data["tables"],"Columns":data["columns"],"Measures":data["measures"],"Relationships":data["relationships"],"Data Sources":data["sources"],"Visuals":data.get("visuals",[])}
    st.dataframe(_df(preview_map[preview_choice]), use_container_width=True, hide_index=True, height=320)