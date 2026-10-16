import plotly.io as pio

import theme

CSS = """
:root {
  color-scheme: light;
  --surface: #fcfcfb;
  --plane: #f9f9f7;
  --text: #0b0b0b;
  --secondary: #52514e;
  --muted: #898781;
  --grid: #e1e0d9;
  --axis: #c3c2b7;
  --border: rgba(11,11,11,0.10);
  --export: #2a78d6;
  --import: #eb6834;
  --petroleum: #4a3aa7;
  --negative: #e34948;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--plane);
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 16px;
  line-height: 1.55;
}
.wrap { max-width: 1240px; margin: 0 auto; padding: 32px 20px 80px; }
header.page { border-bottom: 2px solid var(--text); padding-bottom: 20px; margin-bottom: 28px; }
header.page .eyebrow {
  text-transform: uppercase; letter-spacing: .09em; font-size: 12px;
  color: var(--muted); font-weight: 600; margin: 0 0 8px;
}
header.page h1 { font-size: 30px; line-height: 1.2; margin: 0 0 10px; font-weight: 650; }
header.page p { margin: 0; color: var(--secondary); max-width: 80ch; }
nav.top { margin: 0 0 24px; display: flex; gap: 14px; flex-wrap: wrap; }
nav.top a {
  color: var(--secondary); text-decoration: none; font-size: 14px; font-weight: 550;
  border: 1px solid var(--border); border-radius: 999px; padding: 6px 14px; background: var(--surface);
}
nav.top a:hover { border-color: var(--text); color: var(--text); }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(176px, 1fr)); gap: 12px; margin: 0 0 28px; }
.kpi { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
.kpi .label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; font-weight: 600; }
.kpi .value { font-size: 26px; font-weight: 650; margin-top: 4px; letter-spacing: -0.01em; }
.kpi .note { font-size: 12.5px; color: var(--secondary); margin-top: 3px; }
.kpi.export { border-left: 4px solid var(--export); }
.kpi.import { border-left: 4px solid var(--import); }
.kpi.focus { border-left: 4px solid var(--petroleum); }
.kpi.negative { border-left: 4px solid var(--negative); }
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px 20px 10px; margin: 0 0 24px; }
.panel > h2 { font-size: 19px; margin: 0 0 4px; font-weight: 640; }
.panel > .lede { margin: 0 0 14px; color: var(--secondary); max-width: 88ch; }
.panel > .takeaway {
  margin: 10px 0 4px; padding: 11px 14px; background: var(--plane);
  border-left: 3px solid var(--petroleum); border-radius: 0 6px 6px 0;
  color: var(--secondary); font-size: 15px;
}
.panel > .takeaway strong { color: var(--text); }
.controls {
  display: flex; gap: 16px; align-items: center; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 18px; margin: 0 0 24px;
}
.controls label { font-size: 13px; font-weight: 600; color: var(--secondary); }
.controls select, .controls button {
  font: inherit; font-size: 14px; padding: 6px 12px; border-radius: 7px;
  border: 1px solid var(--axis); background: var(--surface); color: var(--text); cursor: pointer;
}
.controls button:hover, .controls select:hover { border-color: var(--text); }
.plot { width: 100%; overflow-x: auto; }
table.data { border-collapse: collapse; width: 100%; font-size: 13.5px; font-variant-numeric: tabular-nums; }
table.data caption { text-align: left; font-size: 13px; color: var(--muted); padding: 6px 0 10px; }
table.data th, table.data td { padding: 7px 10px; border-bottom: 1px solid var(--grid); text-align: right; }
table.data th:first-child, table.data td:first-child { text-align: left; font-variant-numeric: normal; }
table.data thead th { border-bottom: 2px solid var(--axis); color: var(--secondary); font-weight: 650; }
table.data td.text { text-align: left; font-variant-numeric: normal; color: var(--secondary); }
.scroll { overflow-x: auto; }
details.table { margin: 6px 0 12px; }
details.table summary {
  cursor: pointer; font-size: 13.5px; color: var(--secondary); font-weight: 600;
  padding: 7px 0; user-select: none;
}
details.table summary:hover { color: var(--text); }
.insights { list-style: none; margin: 0; padding: 0; }
.insights li { display: grid; grid-template-columns: 62px 1fr; gap: 14px; padding: 9px 0; border-bottom: 1px solid var(--grid); }
.insights li:last-child { border-bottom: 0; }
.insights .yr { font-weight: 680; color: var(--petroleum); font-variant-numeric: tabular-nums; }
.insights .txt { color: var(--secondary); }
footer.page { margin-top: 40px; padding-top: 18px; border-top: 1px solid var(--border); color: var(--muted); font-size: 13px; }
footer.page a { color: var(--secondary); }
@media (max-width: 680px) {
  header.page h1 { font-size: 24px; }
  .kpi .value { font-size: 21px; }
}
"""


def head(title, description):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
"""


TAIL = """</div>
</body>
</html>
"""


def nav(active):
    items = [
        ("index.html", "Overview"),
        ("dashboard.html", "Petroleum dashboard"),
        ("storyboard.html", "Storyboard"),
    ]
    links = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == active else ""}>{label}</a>'
        for href, label in items
    )
    return f'<nav class="top">{links}</nav>\n'


def header(eyebrow, title, intro):
    return (
        f'<header class="page"><p class="eyebrow">{eyebrow}</p>'
        f"<h1>{title}</h1><p>{intro}</p></header>\n"
    )


def footer():
    return (
        '<footer class="page">'
        "Built from <code>24503993_A3.xlsx</code>. Every number on this page is read from that "
        "workbook, so the spreadsheet and these charts cannot disagree. "
        "Values are in millions of Australian dollars. "
        "Source: ABS Australian International Trade, 2016 to 2025."
        "</footer>\n"
    )


_first = {"done": False}


def reset():
    _first["done"] = False


def figure(fig, div_id):
    include = "inline" if not _first["done"] else False
    _first["done"] = True
    html = pio.to_html(
        fig,
        include_plotlyjs=include,
        full_html=False,
        div_id=div_id,
        config={"displayModeBar": False, "responsive": True},
    )
    return f'<div class="plot">{html}</div>\n'


def panel(title, lede, body, takeaway=None):
    out = f'<section class="panel"><h2>{title}</h2>'
    if lede:
        out += f'<p class="lede">{lede}</p>'
    out += body
    if takeaway:
        out += f'<p class="takeaway">{takeaway}</p>'
    return out + "</section>\n"


def kpi(label, value, note, kind=""):
    return (
        f'<div class="kpi {kind}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="note">{note}</div></div>'
    )


def kpi_row(tiles):
    return f'<div class="kpis">{"".join(tiles)}</div>\n'


def table(caption, headers, rows, summary="Show the numbers behind this chart"):
    head_cells = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = ""
        for index, cell in enumerate(row):
            klass = ' class="text"' if index == 0 or isinstance(cell, str) else ""
            cells += f"<td{klass}>{cell}</td>"
        body += f"<tr>{cells}</tr>"
    return (
        f'<details class="table"><summary>{summary}</summary><div class="scroll">'
        f'<table class="data"><caption>{caption}</caption>'
        f"<thead><tr>{head_cells}</tr></thead><tbody>{body}</tbody></table>"
        "</div></details>\n"
    )


def year_control(div_ids, first_year, last_year):
    ids = ",".join(f'"{i}"' for i in div_ids)
    options = "".join(
        f'<option value="{y}">{y}</option>' for y in range(first_year, last_year + 1)
    )
    return f"""<div class="controls">
<label for="fromYear">Show years from</label>
<select id="fromYear">{options}</select>
<label for="toYear">to</label>
<select id="toYear">{options}</select>
<button id="resetYears" type="button">Reset to all years</button>
<span style="font-size:13px;color:var(--muted)">The range applies to every time chart on this page.</span>
</div>
<script>
(function () {{
  var ids = [{ids}];
  var from = document.getElementById("fromYear");
  var to = document.getElementById("toYear");
  from.value = "{first_year}";
  to.value = "{last_year}";
  function apply() {{
    var a = parseInt(from.value, 10);
    var b = parseInt(to.value, 10);
    if (a > b) {{ var t = a; a = b; b = t; }}
    ids.forEach(function (id) {{
      var el = document.getElementById(id);
      if (el && window.Plotly) {{
        Plotly.relayout(el, {{"xaxis.range": [a - 0.5, b + 0.5]}});
      }}
    }});
  }}
  from.addEventListener("change", apply);
  to.addEventListener("change", apply);
  document.getElementById("resetYears").addEventListener("click", function () {{
    from.value = "{first_year}";
    to.value = "{last_year}";
    apply();
  }});
}})();
</script>
"""
