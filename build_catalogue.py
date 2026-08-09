#!/usr/bin/env python3
"""
Build a searchable/sortable HTML catalogue of the OpenScore String Quartets
corpus from composers.yaml / sets.yaml / scores.yaml / corpus.yaml.

Usage:
    python3 build_catalogue.py [--input-dir DIR] [--output FILE] [--yaml-parser {pyyaml,strictyaml}]

Defaults:
    --input-dir   /data/
    --output      /data/index.html
    --yaml-parser pyyaml

The YAML files can be parsed with either
PyYAML (default; no install, but infers numeric keys/values as ints)
or
StrictYAML (as per i the files' own header comments;
keeps everything as strings, but is a non-standard-library dependency).

Either works fine here,
all IDs are set to strings after parsing so the rest
of the script behaves identically regardless of which one is used.

For each score we build download links for the .mscx, .mxl, and .pdf files,
using the pattern:
    https://github.com/OpenScore/StringQuartets/raw/refs/heads/main/scores/<score path>/sq<score id>.<format>
"""

import argparse
import html
from pathlib import Path

RAW_BASE = "https://github.com/OpenScore/StringQuartets/raw/refs/heads/main/scores"
IMSLP_BASE = "https://imslp.org/wiki/Special:ImagefromIndex"


def load_yaml(path: Path, parser: str = "pyyaml") -> dict:
    """
    Parse a top-level {id: record} YAML file into a plain nested dict,
    using either PyYAML or StrictYAML,
    and make all ID fields all strings
    so downstream lookups work the same regardless of parser choice.
    """
    text = path.read_text(encoding="utf-8")

    if parser == "strictyaml":
        import strictyaml as sy

        raw = sy.load(text).data
    elif parser == "pyyaml":
        import yaml

        raw = yaml.safe_load(text)
    else:
        raise ValueError(f"Unknown YAML parser: {parser!r}")

    return _normalize_ids(raw)


def _normalize_ids(data: dict) -> dict:
    """
    StrictYAML keeps all scalars as strings;
    PyYAML infers numeric-looking scalars as ints.
    Normalise top-level keys and known foreign-key fields
    (set_id, composer_id)
    to strings so the two parsers are interchangeable.
    """
    normalized = {}
    for key, record in data.items():
        key = str(key)
        if isinstance(record, dict):
            record = dict(record)
            for field in ("set_id", "composer_id"):
                if field in record:
                    record[field] = str(record[field])
        normalized[key] = record
    return normalized


def build_rows(composers: dict, sets_: dict, scores: dict) -> list[dict]:
    rows = []
    for score_id, score in scores.items():
        set_id = score.get("set_id")
        set_rec = sets_.get(set_id, {})
        composer_id = set_rec.get("composer_id")
        composer_rec = composers.get(composer_id, {})

        composer_name = composer_rec.get("name", "Unknown")
        set_name = set_rec.get("name", "\u2014")
        score_name = score.get("name", "\u2014")
        score_path = score.get("path", "")

        mscx_url = f"{RAW_BASE}/{score_path}/sq{score_id}.mscx"
        mxl_url = f"{RAW_BASE}/{score_path}/sq{score_id}.mxl"
        pdf_url = f"{RAW_BASE}/{score_path}/sq{score_id}.pdf"

        imslp_id = str(score.get("imslp", "")).lstrip("#").strip()
        imslp_url = f"{IMSLP_BASE}/{imslp_id}" if imslp_id else None

        rows.append(
            {
                "composer": composer_name,
                "set": set_name,
                "score": score_name,
                "mscx_url": mscx_url,
                "mxl_url": mxl_url,
                "pdf_url": pdf_url,
                "imslp_url": imslp_url,
            }
        )

    rows.sort(key=lambda r: (r["composer"].lower(), r["set"].lower(), r["score"].lower()))
    return rows


def render_row(row: dict) -> str:
    composer = html.escape(row["composer"])
    score_name = html.escape(row["score"])
    mscx_url = html.escape(row["mscx_url"], quote=True)
    mxl_url = html.escape(row["mxl_url"], quote=True)
    pdf_url = html.escape(row["pdf_url"], quote=True)

    files_cell = (
        f'<a href="{mscx_url}" target="_blank" rel="noopener">MuseScore</a>; '
        f'<a href="{mxl_url}" target="_blank" rel="noopener">MusicXML</a>; '
        f'<a href="{pdf_url}" target="_blank" rel="noopener">PDF</a>'
    )

    if row["imslp_url"]:
        imslp_url = html.escape(row["imslp_url"], quote=True)
        imslp_cell = f'<a href="{imslp_url}" target="_blank" rel="noopener">IMSLP</a>'
    else:
        imslp_cell = ""

    return (
        "<tr>"
        f"<td>{composer}</td>"
        f"<td>{score_name}</td>"
        f"<td>{files_cell}</td>"
        f"<td>{imslp_cell}</td>"
        "</tr>"
    )


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OpenScore String Quartets Catalogue</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/2.1.7/css/dataTables.dataTables.min.css">
  <style>
    /* -- Layout -- */
    body {{
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 0.92rem;
      line-height: 1.5;
      margin: 2rem auto;
      max-width: 1200px;
      padding: 0 1rem;
      color: #222;
      background: #fff;
    }}
    h1 {{
      font-size: 1.6rem;
      font-weight: normal;
      margin-bottom: 0.25rem;
    }}
    p.subtitle {{
      color: #555;
      margin-top: 0;
      margin-bottom: 1.5rem;
    }}

    /* -- Table -- */
    #catalogue {{
      width: 100%;
      border-collapse: collapse;
    }}
    #catalogue thead th {{
      background: #f5f5f5;
      border-bottom: 2px solid #ccc;
      padding: 0.5rem 0.75rem;
      text-align: left;
      white-space: nowrap;
      cursor: pointer;
    }}
    #catalogue tbody tr:nth-child(even) {{
      background: #fafafa;
    }}
    #catalogue tbody td {{
      padding: 0.4rem 0.75rem;
      border-bottom: 1px solid #e8e8e8;
      vertical-align: top;
    }}
    #catalogue a {{
      color: #1a5276;
      text-decoration: none;
    }}
    #catalogue a:hover {{
      text-decoration: underline;
    }}

    /* -- DataTables overrides -- */
    .dataTables_wrapper .dataTables_filter input {{
      margin-left: 0.4rem;
      border: 1px solid #ccc;
      border-radius: 3px;
      padding: 0.25rem 0.5rem;
    }}
    .dataTables_wrapper .dataTables_info,
    .dataTables_wrapper .dataTables_filter {{
      margin-bottom: 0.75rem;
    }}
  </style>
</head>
<body>
  <h1>OpenScore String Quartets Catalogue</h1>
  <p class="subtitle">
    {scores_count} scores across {sets_count} sets by {composers_count} composers.
    Click any column header to sort; use the search box to filter.
  </p>

  <table id="catalogue">
    <thead>
      <tr>
        <th>Composer</th>
        <th>Score</th>
        <th>Files</th>
        <th>IMSLP</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>

  <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
  <script src="https://cdn.datatables.net/2.1.7/js/dataTables.min.js"></script>
  <script>
    $(document).ready(function () {{
      $('#catalogue').DataTable({{
        pageLength: 50,
        lengthMenu: [25, 50, 100, 250, 500],
        order: [[0, 'asc'], [1, 'asc']]
      }});
    }});
  </script>
</body>
</html>
"""


def main():
    input_dir = Path("./data")
    out = Path("./data/index.html")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=input_dir)
    parser.add_argument("--output", default=out)
    parser.add_argument(
        "--yaml-parser",
        choices=["pyyaml", "strictyaml"],
        default="pyyaml",
        help="Which YAML library to parse the input files with (default: pyyaml).",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    composers = load_yaml(input_dir / "composers.yaml", args.yaml_parser)
    sets_ = load_yaml(input_dir / "sets.yaml", args.yaml_parser)
    scores = load_yaml(input_dir / "scores.yaml", args.yaml_parser)
    # this catalogue lists one row per downloadable score file.
    # We use the actual parsed counts instead so the subtitle matches the table.

    rows = build_rows(composers, sets_, scores)
    rows_html = "\n".join(render_row(r) for r in rows)

    page = PAGE_TEMPLATE.format(
        rows=rows_html,
        scores_count=len(rows),
        sets_count=len(sets_),
        composers_count=len(composers),
    )

    output_path.write_text(page, encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()