import zipfile

from layout import ROOT

OUT = ROOT / "out" / "24503993_A3_dashboard.zip"

README = """Dashboard and storyboard source, 24503993, Assessment Task 3
===========================================================

This archive replaces the Tableau .twbx file. The brief asks for a packaged
dashboard workbook. This project uses Python and Plotly instead, which the
rubric allows under "Tableau or other apps".

HOW TO VIEW THE DASHBOARD WITH NO INSTALL
-----------------------------------------
Open site/index.html in any web browser. Nothing is downloaded and no server
runs. Plotly is inlined into each page, so the charts, the hover values and
the year range control all work straight from disk.

The same three pages are live at:
    https://toms55.github.io/DataVisA3/

WHAT IS IN HERE
---------------
site/index.html        Landing page, key numbers, links to the other two pages
site/dashboard.html    The dashboard for subcategory 33, five comparisons
site/storyboard.html   The storyboard, thirteen panels in order
build/                 The Python that builds everything
data/                  The extracted data, the forecast, the AI run, the research notes
shell.nix              The exact build environment

HOW THE PIECES FIT
------------------
The Excel workbook 24503993_A3.xlsx is the source of every number. Each
analytical and statistical pattern lives there as a live Excel formula.
build/read_workbook.py opens the workbook and reads the finished values, so
the dashboard, the storyboard and the report all display the spreadsheet and
never recompute it. Change a cell in the workbook, rebuild, and the charts
move.

TO REBUILD FROM SOURCE
----------------------
The build needs the source dataset 2026-Spring-Ass3-V20.xlsx in the project
root. On a machine with Nix:

    nix-shell --run 'cd build && python3 extract.py'
    nix-shell --run 'cd build && python3 build_workbook.py && python3 recalc.py'
    nix-shell --run 'cd build && python3 verify_workbook.py'
    nix-shell --run 'cd build && python3 forecast.py'
    nix-shell --run 'cd build && python3 build_index.py && python3 build_dashboard.py && python3 build_storyboard.py'
    nix-shell --run 'cd build && python3 build_report.py'
    nix-shell --run 'cd build && python3 verify_all.py'

verify_all.py is the gate. It recomputes every workbook formula and compares
it against the recalculated spreadsheet, confirms both pages are self
contained and cover import and export, and checks the report page count and
headline numbers.

THE AI COMPARISON
-----------------
data/ai_forecast.md holds the AI run used in section 12 of the report. The
prompt, the reply, the model and the date are recorded word for word. The
model received the ten annual import values and nothing else.
"""

SOURCE = [
    "build/extract.py",
    "build/layout.py",
    "build/build_workbook.py",
    "build/recalc.py",
    "build/read_workbook.py",
    "build/verify_workbook.py",
    "build/theme.py",
    "build/charts.py",
    "build/page.py",
    "build/forecast.py",
    "build/build_index.py",
    "build/build_dashboard.py",
    "build/build_storyboard.py",
    "build/build_report.py",
    "build/render_previews.py",
    "build/package.py",
    "build/verify_all.py",
    "data/trade.csv",
    "data/forecast.csv",
    "data/forecast_summary.csv",
    "data/ai_forecast.csv",
    "data/ai_forecast.md",
    "data/research_notes.md",
    "shell.nix",
]

PAGES = ["index.html", "dashboard.html", "storyboard.html"]


def main():
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", README)
        for name in PAGES:
            archive.write(ROOT / "docs" / name, f"site/{name}")
        for relative in SOURCE:
            path = ROOT / relative
            if not path.exists():
                raise SystemExit(f"missing {relative}")
            archive.write(path, relative)
    size = OUT.stat().st_size / 1024 / 1024
    with zipfile.ZipFile(OUT) as archive:
        count = len(archive.namelist())
    print(f"wrote {OUT.relative_to(ROOT)} ({size:.1f} MB, {count} files)")


if __name__ == "__main__":
    main()
