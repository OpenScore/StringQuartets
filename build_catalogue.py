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

For each score we build
1. download links in several file formats, and for both score and parts. 
2. external links to
    - IMSLP's PDFs (own column)
    - two score viewers:
        - MuseScore.com (MuseScore file, view and play online, paywall to download)
        - OurTextScores (.mxl web editor).
    - YouTube recordings
"""

import argparse
import html
from pathlib import Path
from urllib.parse import urlencode

RAW_BASE = "https://raw.githubusercontent.com/OpenScore/StringQuartets/refs/heads/main/scores"
IMSLP_BASE = "https://imslp.org/wiki/Special:ReverseLookup"
ourtext_BASE = "https://www.ourtextscores.com/score-editor/index.html"
# Note: MUSESCORE_BASE not needed, already in metadata
YOUTUBE_BASE = ""
PART_NAMES = ["Violin_1", "Violin_2", "Viola", "Violoncello"]


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


def split_composer_name(composer_rec: dict) -> tuple[str, str]:
    """Return (last_name, first_name) for a composer, derived from the
    'path' field (already in 'Last,_First...' form, e.g. 'Beethoven,_Ludwig_van'),
    falling back to splitting 'name' on the last space if 'path' is missing."""
    path = composer_rec.get("path", "")
    if "," in path:
        last, first = path.split(",", 1)
        return last.replace("_", " ").strip(), first.replace("_", " ").strip()

    full_name = composer_rec.get("name", "Unknown")
    if " " in full_name:
        first, last = full_name.rsplit(" ", 1)
        return last, first
    return full_name, ""


def build_rows(composers: dict, sets_: dict, scores: dict) -> list[dict]:
    rows = []
    for score_id, score in scores.items():
        set_id = score.get("set_id")
        set_rec = sets_.get(set_id, {})
        composer_id = set_rec.get("composer_id")
        composer_rec = composers.get(composer_id, {})

        composer_last, composer_first = split_composer_name(composer_rec)
        set_name = set_rec.get("name", "\u2014")
        score_name = score.get("name", "\u2014")
        score_path = score.get("path", "")
        movements = set_rec.get("movements", 0)

        version = str(score.get("musescore_version", "")).strip()
        if version.startswith("3"):
            extension = "mscx"
        elif version.startswith("4"):
            extension = "mscz"
        else:
            raise ValueError(
                f"Score {score_id}: unsupported musescore_version {version!r}; "
                "expected a version starting with 3 or 4"
            )
        musescore_url_file = f"{RAW_BASE}/{score_path}/sq{score_id}.{extension}"
        mxl_url = f"{RAW_BASE}/{score_path}/sq{score_id}.mxl"
        pdf_url = f"{RAW_BASE}/{score_path}/sq{score_id}.pdf"

        # External:
        ourtext_url = f"{ourtext_BASE}?{urlencode({'score': mxl_url})}"
        imslp_id = str(score.get("imslp", "")).lstrip("#").strip()
        imslp_url = f"{IMSLP_BASE}/{imslp_id}" if imslp_id else None
        recording_url = str(set_rec.get("recording", "") or "").strip() or None
        musescore_url = score.get("link")

        part_urls = {
            part_name: f"{RAW_BASE}/{score_path}/sq{score_id}-Part-{part_name}.pdf"
            for part_name in PART_NAMES
        }

        # TODO consider requests call to check all URLs exist (in addition to the check_links script).

        rows.append(
            {
                "composer_last": composer_last,
                "composer_first": composer_first,
                "set": set_name,
                "score": score_name,
                "our_id": score_id,
                "movements": movements,
                "musescore_file_url": musescore_url_file,
                "musescore_extension": extension,
                "mxl_url": mxl_url,
                "pdf_url": pdf_url,
                "ourtext_url": ourtext_url,
                "imslp_url": imslp_url,
                "musescore_url": musescore_url,
                "recording_url": recording_url,
                "part_urls": part_urls,
            }
        )

    rows.sort(key=lambda r: (r["composer_last"].lower(), r["composer_first"].lower(), r["score"].lower()))
    return rows


def render_row(row: dict) -> str:
    our_id = html.escape(str(row["our_id"]))
    movements = html.escape(str(row["movements"]))
    composer_last = html.escape(row["composer_last"])
    composer_first = html.escape(row["composer_first"])
    score_name = html.escape(row["score"])
    if row["set"] != row["score"] and row["set"] != "—":
        score_name = (
            f'<span class="work-title">{html.escape(row["set"])}</span>'
            f'<span class="movement-title">{score_name}</span>'
        )
    musescore_file_url = html.escape(row["musescore_file_url"], quote=True)
    download_attrs = ""
    if row["musescore_extension"] == "mscx":
        filename = html.escape(f'sq{row["our_id"]}.mscx', quote=True)
        download_attrs = f' data-download="{filename}" download="{filename}"'
    mxl_url = html.escape(row["mxl_url"], quote=True)
    pdf_url = html.escape(row["pdf_url"], quote=True)

    files_cell = (
        f'<a href="{musescore_file_url}" title="{musescore_file_url}"{download_attrs} target="_blank" rel="noopener">MuseScore</a>; '
        f'<a href="{mxl_url}" title="{mxl_url}" target="_blank" rel="noopener">MusicXML</a>; '
        f'<a href="{pdf_url}" title="{pdf_url}" target="_blank" rel="noopener">PDF</a>'
    )

    ext_links = []
    for key, label in [
        ("imslp_url", "IMSLP.org"),
        ("musescore_url", "MuseScore.com"),
        ("ourtext_url", "OurTextScores.com"),
        ("recording_url", "YouTube.com"),
    ]:
        url = row.get(key)
        if url and url.startswith(("http://", "https://")):
            safe = html.escape(url, quote=True)
            ext_links.append(f'<a href="{safe}" title="{safe}" target="_blank" rel="noopener">{label}</a>')
    external_cell = "; ".join(ext_links)

    parts_cell = "; ".join(
        f'<a href="{html.escape(part_url, quote=True)}" '
        f'title="{html.escape(part_url, quote=True)}" '
        'target="_blank" '
        f'rel="noopener">{html.escape(part_name)}</a>'
        for part_name, part_url in row["part_urls"].items()
    )

    return (
        "<tr>"
        f"<td>{composer_last}</td>"
        f"<td>{composer_first}</td>"
        f'<td class="title-cell">{score_name}</td>'
        f"<td>{our_id}</td>"
        f"<td>{movements}</td>"
        f"<td>{files_cell}</td>"
        f"<td>{parts_cell}</td>"
        f'<td>{external_cell}</td>'
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

    .title-cell {{ max-width: 22rem; overflow-wrap: anywhere; }}
    .work-title, .movement-title {{ display: block; }}
    .movement-title {{ font-size: 0.9em; color: #555; }}

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
    {movement_count} movements across
    {scores_count} quartets by
    {composers_count} composers.
    Click any column header to sort; use the search box to filter (across any field).    
  </p>
  <p>
  Score files are provided in several formats:
  <ol>
      <li>MuseScore, for use in MuseScore studio (layout set out by us, manually),</li>
      <li>MusicXML, which is usable in almost any score reader (layout may be broken),</li>
      <li>PDF images (converted directly from the MuseScore, so layout should be correct).</li>
  </ol>
  </p>
  <p>
  Parts are provided in PDF only.
  These PDFs are made directly from the MuseScore;
  layout should be correct but there be occasional issues
  (please report any you come across).
  </p>
  <p>
  External links are provided to:
  <ol>
      <li>IMSLP.org for the source edition (PDF) on which ours is based.
      <li>MuseScore.com to view and play online
      (but note that downloads are behind a paywall, so use the score/part download links instead)
      <li>OurTextScores.com to view and even edit the mxl form online.
      <li>YouTube.com to view a YouTube recording (available in most but not all cases).
  </ol>           
  </p>
  <p>
  We hope you enjoy this resource!
  </p>
  <p>
  <a href="https://markgotham.github.io/" title="https://markgotham.github.io/" target="_blank" rel="noopener">Mark Gotham</a>,
  on behalf of the OSQ team.
  </p>

  <table id="catalogue">
    <thead>
      <tr>
        <th>Last Name</th>
        <th>First Name</th>
        <th>Work Title</th>
        <th>Our ID</th>
        <th>Mvts</th>
        <th>Score Files</th>
        <th>Part Files</th>
        <th>External</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>

  <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
  <script src="https://cdn.datatables.net/2.1.7/js/dataTables.min.js"></script>
  <script>
    // Raw XML normally as plain code in the browser. Download a local Blob instead.
    document.addEventListener('click', async function (event) {{
      const link = event.target.closest('a[data-download]');
      if (!link) return;
      event.preventDefault();
      if (link.dataset.busy) return;
      link.dataset.busy = 'true';
      link.setAttribute('aria-busy', 'true');
      try {{
        const response = await fetch(link.href);
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const download = document.createElement('a');
        download.href = url;
        download.download = link.dataset.download;
        document.body.appendChild(download);
        download.click();
        download.remove();
        setTimeout(function () {{ URL.revokeObjectURL(url); }}, 60000);
      }} catch (error) {{
        alert('Download failed: ' + error.message +
              '. You can right-click the link and choose Save link as.');
      }} finally {{
        delete link.dataset.busy;
        link.removeAttribute('aria-busy');
      }}
    }});
    $(document).ready(function () {{
      $('#catalogue').DataTable({{
        pageLength: -1,
        lengthMenu: [[25, 50, 100, 250, 500, -1], [25, 50, 100, 250, 500, 'All']],
        order: [[0, 'asc'], [1, 'asc']]
      }});
    }});
  </script>
</body>
</html>
"""


def main():
    input_dir = Path("./data")
    # out = Path("./data/index.html")
    out = Path("../fourscoreandmore.org/openscore/stringquartets/index.html")

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
        movement_count=sum(int(record.get("movements", 0)) for record in sets_.values()),
        scores_count=len({score.get("set_id") for score in scores.values()}),
        sets_count=len(sets_),
        composers_count=len(composers),
    )

    output_path.write_text(page, encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
