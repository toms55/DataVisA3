import shutil
import subprocess
import tempfile
from pathlib import Path

import charts
import plotly.graph_objects as go
import read_workbook as rw
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from layout import FORECAST_YEARS, ROOT, YEARS
from recalc import PROFILE

FIGDIR = ROOT / "build" / "report_figs"
DOCX = ROOT / "out" / "24503993_A3.docx"
PDF = ROOT / "out" / "24503993_A3.pdf"

PAGES_URL = "https://toms55.github.io/DataVisA3/"

INK = RGBColor(0x0B, 0x0B, 0x0B)
SECONDARY = RGBColor(0x52, 0x51, 0x4E)
ACCENT = RGBColor(0x1F, 0x38, 0x64)
SHORT_NAMES = {
    "0": "Food and live animals",
    "1": "Beverages and tobacco",
    "2": "Crude materials",
    "3": "Mineral fuels",
    "4": "Animal and vegetable oils",
    "5": "Chemicals",
    "6": "Manufactured goods by material",
    "7": "Machinery and transport",
    "8": "Miscellaneous manufactures",
    "9": "Commodities not classified",
}


_short_by_name = {}


def short(full_name):
    if not _short_by_name:
        names, _ = rw.main_values("Export")
        for code, name in names.items():
            _short_by_name[name] = SHORT_NAMES[code]
    return _short_by_name.get(full_name, full_name)


SANS = "Liberation Sans"
MONO = "Liberation Mono"

FIGURES = {
    "f01_total": (lambda: charts.total_trade(), 1200, 760, 1.45),
    "f02_raw": (lambda: charts.main_small_multiples("value", 16, 4, 0.085), 1300, 760, 1.7),
    "f03_index": (lambda: charts.main_small_multiples("index", 16, 4, 0.085), 1300, 760, 1.7),
    "f04_share": (lambda: charts.share_slope(20, 0.33), 1450, 700, 1.45),
    "f05_stats": (lambda: charts.main_statistical(), 1400, 520, 1.5),
    "f06_change": (lambda: charts.change_point_chart(), 1300, 520, 1.45),
    "f07_correl": (lambda: charts.correlation_heatmap("Export"), 1050, 540, 1.3),
    "f08_cat3": (lambda: charts.cat3_subcategories("value"), 1300, 520, 1.45),
    "f09_cat3share": (lambda: charts.cat3_subcategories("share"), 1300, 520, 1.45),
    "f10_diverge": (lambda: charts.divergence_chart(), 1150, 480, 1.35),
    "f11_focus": (lambda: charts.focus_export_import(), 1150, 500, 1.35),
    "f12_balance": (lambda: charts.focus_balance(), 1150, 470, 1.35),
    "f13_vssubs": (lambda: charts.focus_vs_subcategories(), 1300, 520, 1.45),
    "f14_scatter": (lambda: charts.focus_scatter(), 1050, 500, 1.3),
    "f15_forecast": (lambda: charts.forecast_chart(), 1250, 560, 1.4),
}

FONT_KEYS = ("font", "tickfont", "titlefont", "insidetextfont", "outsidetextfont", "textfont")


def scale_fonts(node, factor):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in FONT_KEYS and isinstance(value, dict) and value.get("size"):
                value["size"] = round(value["size"] * factor, 1)
            else:
                scale_fonts(value, factor)
    elif isinstance(node, list):
        for item in node:
            scale_fonts(item, factor)
    return node


def enlarge(figure, factor):
    spec = figure.to_dict()
    scale_fonts(spec.get("data", []), factor)
    layout = scale_fonts(spec["layout"], factor)
    base = layout.setdefault("font", {})
    base["size"] = round(base.get("size", 12) * factor, 1)
    legend = layout.get("legend", {})
    if isinstance(legend.get("y"), (int, float)) and legend["y"] < 0:
        legend["y"] = round(legend["y"] * factor, 3)
    margin = layout.get("margin", {})
    for side in ("l", "r", "t", "b"):
        if side in margin:
            margin[side] = round(margin[side] * factor)
    return go.Figure(spec)


def render_figures():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    for name, (build, width, height, factor) in FIGURES.items():
        path = FIGDIR / f"{name}.png"
        figure = enlarge(build(), factor)
        figure.write_image(path, width=width, height=height, scale=2)
    return FIGDIR


def money(value):
    return f"{value:,.0f}"


class Report:
    def __init__(self):
        self.document = Document()
        self.figure_number = 0
        self._setup()

    def _setup(self):
        section = self.document.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(1.9)
        section.bottom_margin = Cm(1.9)
        section.left_margin = Cm(2.1)
        section.right_margin = Cm(2.1)
        normal = self.document.styles["Normal"]
        normal.font.name = SANS
        normal.font.size = Pt(10.5)
        normal.font.color.rgb = INK
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = 1.08

    def title(self, text, subtitle, meta):
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(text)
        run.font.name = SANS
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = ACCENT
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(subtitle)
        run.font.name = SANS
        run.font.size = Pt(12)
        run.font.color.rgb = SECONDARY
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(meta)
        run.font.name = SANS
        run.font.size = Pt(9.5)
        run.font.color.rgb = SECONDARY
        paragraph.paragraph_format.space_after = Pt(10)

    def heading(self, text, size=13):
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(text)
        run.font.name = SANS
        run.font.size = Pt(size)
        run.font.bold = True
        run.font.color.rgb = ACCENT
        paragraph.paragraph_format.space_before = Pt(10)
        paragraph.paragraph_format.space_after = Pt(3)

    def sub(self, text):
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(text)
        run.font.name = SANS
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = INK
        paragraph.paragraph_format.space_before = Pt(7)
        paragraph.paragraph_format.space_after = Pt(2)

    def text(self, body):
        paragraph = self.document.add_paragraph(body)
        paragraph.paragraph_format.space_after = Pt(5)
        return paragraph

    def bullets(self, items):
        for item in items:
            paragraph = self.document.add_paragraph(item, style="List Bullet")
            paragraph.paragraph_format.space_after = Pt(2)
            for run in paragraph.runs:
                run.font.size = Pt(10.5)
                run.font.name = SANS

    def numbers(self, items):
        for index, item in enumerate(items, start=1):
            paragraph = self.document.add_paragraph()
            run = paragraph.add_run(f"{index}.  {item}")
            run.font.size = Pt(10.5)
            run.font.name = SANS
            paragraph.paragraph_format.left_indent = Cm(0.75)
            paragraph.paragraph_format.first_line_indent = Cm(-0.75)
            paragraph.paragraph_format.space_after = Pt(3)

    def figure(self, name, caption, width_cm=16.8):
        self.figure_number += 1
        paragraph = self.document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.paragraph_format.space_after = Pt(1)
        paragraph.add_run().add_picture(str(FIGDIR / f"{name}.png"), width=Cm(width_cm))
        caption_paragraph = self.document.add_paragraph()
        run = caption_paragraph.add_run(f"Figure {self.figure_number}. {caption}")
        run.font.name = SANS
        run.font.size = Pt(9)
        run.font.color.rgb = SECONDARY
        run.font.italic = True
        caption_paragraph.paragraph_format.space_after = Pt(6)
        return self.figure_number

    def table(self, headers, rows, widths=None):
        table = self.document.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        for index, header in enumerate(headers):
            cell = table.rows[0].cells[index]
            cell.text = ""
            run = cell.paragraphs[0].add_run(header)
            run.font.name = SANS
            run.font.bold = True
            run.font.size = Pt(9)
        for row in rows:
            cells = table.add_row().cells
            for index, value in enumerate(row):
                cells[index].text = ""
                run = cells[index].paragraphs[0].add_run(str(value))
                run.font.name = SANS
                run.font.size = Pt(9)
        if widths:
            for row in table.rows:
                for index, width in enumerate(widths):
                    row.cells[index].width = Cm(width)
        self.document.add_paragraph().paragraph_format.space_after = Pt(2)
        return table

    def quote(self, body):
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(body)
        run.font.size = Pt(9)
        run.font.name = MONO
        paragraph.paragraph_format.left_indent = Cm(0.8)
        paragraph.paragraph_format.space_after = Pt(4)
        return paragraph

    def save(self, path):
        path.parent.mkdir(exist_ok=True)
        self.document.save(path)


def build_content(report):
    focus = rw.focus()
    summary = rw.forecast_summary()
    pairs, import_export_r = rw.vs_pairs()
    _, correl_export = rw.correlation("Export")
    _, correl_import = rw.correlation("Import")
    _, cat3_share_export = rw.cat3_share("Export")
    _, cat3_share_import = rw.cat3_share("Import")
    _, cat3_correl_export = rw.cat3_correl("Export")
    _, zscore_export = rw.main_zscore("Export")
    _, main_summary_export = rw.main_summary("Export")
    _, main_summary_import = rw.main_summary("Import")
    _, stats_export = rw.main_stats("Export")
    change = rw.change_points()
    forecast = rw.forecast()
    ai = rw.ai_comparison()
    backtest_rows, mape = rw.backtest()
    totals_export = rw.totals("Export")
    totals_import = rw.totals("Import")
    names, _ = rw.main_values("Export")

    first = focus[0]
    last = focus[-1]
    ratio_2025 = last["import"] / last["export"]
    cat7_share = rw.main_share("Import")[1]["7"]
    cat4_2025 = rw.main_values("Export")[1]["4"][-1]
    cat2_2025 = rw.main_values("Export")[1]["2"][-1]
    sheet_count = rw.sheet_count()
    import_years = sorted(totals_import)
    import_rises = sum(
        1
        for a, b in zip(import_years, import_years[1:])
        if totals_import[b] > totals_import[a]
    )
    ai_rows = rw.focus()
    ai_step = (ai_rows[-4]["import"] - ai_rows[-1]["import"]) / 3
    balance_2022 = totals_export[2022] - totals_import[2022]
    balance_2025 = totals_export[2025] - totals_import[2025]
    worst = min(focus, key=lambda r: r["balance"])

    report.title(
        "Australian International Trade, 2016 to 2025",
        "What ten years of trade data say about Australian fuel security",
        "32146 Visual Analytics, Assessment Task 3. Student 24503993. "
        f"Dashboard and storyboard at {PAGES_URL}",
    )

    report.heading("1. Executive summary")
    report.text(
        f"Australian export grew from ${money(totals_export[2016])}m in 2016 to "
        f"${money(totals_export[2025])}m in 2025. Import grew from ${money(totals_import[2016])}m "
        f"to ${money(totals_import[2025])}m. The trade balance looks healthy at first sight, but "
        f"it peaked at ${money(balance_2022)}m in 2022 and then fell "
        f"{abs(balance_2025 / balance_2022 - 1):.0%} to ${money(balance_2025)}m by 2025. The "
        "surplus of the last decade rested on a single price event and it is draining away."
    )
    report.text(
        "Main category 3, mineral fuels, lubricants and related materials, is the largest mover "
        "in seven of the nine year transitions in the dataset. It sets the direction of the "
        "decade in both directions of trade. Inside it sits the finding this report is built "
        "around."
    )
    report.text(
        f"Subcategory 33, petroleum, is the only large part of Australian trade where the country "
        f"buys far more than it sells. Export grew {last['export'] / first['export'] - 1:.0%} "
        f"across the decade and import grew {last['import'] / first['import'] - 1:.0%}, so the "
        f"deficit widened from ${money(abs(first['balance']))}m to ${money(abs(last['balance']))}m. "
        f"Import and export move together at a correlation of {import_export_r:.2f}, because both "
        f"are priced off the same world oil market. Import is {ratio_2025:.2f} times the size of "
        "export, so every oil price rise widens the deficit. Australia "
        "cannot export its way out of this gap."
    )
    report.text(
        f"The recommendation is a target. Cutting petroleum import 3% a year from "
        f"2025 reaches ${money(summary['Target import 2030 ($ Millions)'])}m by 2030. The straight "
        f"line fit on ten years of data has an R squared of only "
        f"{summary['Linear trend R squared']:.2f}, so no five year point forecast on this series "
        "deserves confidence. Section 12 shows Claude Sonnet 5, given the same ten numbers, forecasting "
        "the opposite direction."
    )

    report.heading("2. Data collection and preparation")
    report.text(
        "The data is the Australian International Trade dataset from the Australian Bureau of "
        "Statistics, supplied as 2026-Spring-Ass3-V20.xlsx. It holds two sheets, one for export "
        "and one for import, covering 2016 to 2025. Each sheet is wide. Row 1 names the category, "
        "row 2 gives the unit, row 3 gives the ABS series identifier, and rows 4 to 13 hold the ten "
        "years. There are 10 main categories, 67 subcategories and one total column, which is 78 "
        "series in each direction."
    )
    report.text(
        "The source file was never edited. A Python script reads it and writes a new workbook, "
        "24503993_A3.xlsx. Four checks run on every build. The extract must produce 1,560 rows, "
        "all ten years must be present in both directions, every unit must read $ Millions, and "
        "the ten main categories must sum to the published total. That last check passes within "
        "6 million dollars in the worst year, which is 0.0013% of the total and is consistent with "
        "ten independently rounded series. There are no blank cells anywhere in the source."
    )
    report.text(
        "Every analytical and statistical result in this report lives in the workbook as a live "
        "Excel formula. A verification script recomputes growth, index, "
        "share, CAGR, the descriptive statistics, the trend fits, the z-scores, the correlation "
        "matrices, the change points and the forecasts independently, then compares them against "
        "the recalculated spreadsheet to six decimal places. The build fails if any cell "
        "disagrees or holds an error value."
    )

    report.heading("3. Dataset characteristics and data types")
    report.text(
        "The dataset mixes several data types and each one drives a different visual choice. The "
        "table below lists every field in the source file and every measure derived from it."
    )
    report.table(
        ["Field or measure", "Data type", "Values", "What the type drives"],
        [
            [
                "Year",
                "Temporal, ordinal",
                "2016 to 2025, ten points",
                "A real time axis on every time series in this report",
            ],
            [
                "Main category",
                "Categorical, nominal",
                "10 SITC codes of one digit",
                "One panel per category, because ten series cannot share one palette",
            ],
            [
                "Subcategory",
                "Categorical, nominal, nested in main category",
                "67 SITC codes of two digits",
                "The two level hierarchy that sections 6 and 7 analyse",
            ],
            [
                "Direction",
                "Categorical, nominal, binary",
                "Import, export",
                "Colour on every chart, so both directions are always visible",
            ],
            [
                "Value",
                "Continuous, ratio scale",
                "$ Millions",
                "Line height, column length and every axis scale",
            ],
            [
                "Growth and share",
                "Continuous, derived ratio",
                "Percent",
                "Comparison between categories of different size",
            ],
            [
                "Index",
                "Continuous, derived, rebased to 100",
                "Index points, 2016 = 100",
                "Growth rate comparison with size removed",
            ],
            [
                "Z-score",
                "Continuous, derived, standardised",
                "Standard deviations",
                "An outlier threshold at 2, the same for every category",
            ],
            [
                "Correlation",
                "Continuous, derived, bounded",
                "r, from minus 1 to 1",
                "A diverging colour scale centred on zero",
            ],
        ],
        widths=[3.0, 4.2, 3.6, 6.0],
    )
    report.text(
        "One limit in that table deserves emphasis. The dataset records dollars, so it cannot separate a "
        "price change from a volume change. Where this report states a cause it says whether the "
        "evidence supports a price reading or a volume reading, and it does not claim a volume "
        "effect that the data cannot show."
    )

    report.heading("4. The patterns built in Excel, and how they reach the dashboard")
    report.text(
        f"The workbook holds {sheet_count} sheets and 19 native Excel time series charts. Each "
        "chart carries a "
        "title and a label on both axes. The analysis sheets are these."
    )
    report.table(
        ["Sheet", "Pattern it holds", "Type"],
        [
            ["Main-Analytics", "Growth, index, share, CAGR, contribution to growth", "Analytical"],
            ["Main-Stats", "Mean, median, spread, coefficient of variation, trend fit, z-score", "Statistical"],
            ["Balance", "Export minus import, and the cover ratio", "Analytical"],
            ["Correlation", "Two 10 by 10 correlation matrices on growth", "Statistical"],
            ["ChangePoints", "Largest rise and fall in each year, with a cause", "Analytical"],
            ["Cat3-SubAnalytics", "Main category 3 against its subcategories", "Analytical"],
            ["Pet33-Focus", "The focus subcategory, with an insight for each year", "Analytical"],
            ["Pet33-vs-Sub", "Petroleum against coal and gas, with correlations", "Statistical"],
            ["Pet33-Forecast", "Linear trend and CAGR forecasts, and the target path", "Statistical"],
            ["AI-Comparison", "My forecast against the Claude Sonnet 5 forecast", "Analytical"],
        ],
        widths=[4.0, 9.4, 2.8],
    )
    report.text(
        "The deployment into the application is literal. The dashboard and the "
        "storyboard do not recompute anything. A reader module opens the recalculated workbook and "
        "reads the finished values out of these sheets, so a marker who changes a cell in the "
        "spreadsheet and rebuilds will see the charts move. The spreadsheet is the single source "
        "of every number in this report and on both web pages."
    )
    report.text(
        "One implementation note is worth recording. The openpyxl library writes modern Excel "
        "function names without the _xlfn prefix that the file format requires, so LibreOffice "
        "returns #NAME? for them. Every formula in the workbook therefore uses a legacy function "
        "name, such as FORECAST and STDEVP rather than FORECAST.LINEAR and STDEV.P. Both spellings "
        "are valid in current Excel, and the legacy names work in both applications."
    )

    report.heading("5. All ten main categories, raw, analytical and statistical trends")
    report.figure(
        "f02_raw",
        "Raw dollar value trend for every main category, both directions, in $ Millions. One panel "
        "per category so that small categories stay readable next to large ones.",
    )
    report.text(
        "Ten categories cannot share one set of colours without becoming unreadable, so the raw "
        "view uses one panel per category and keeps colour for the one distinction that matters "
        "everywhere in this report, which is import against export. The export side is "
        f"concentrated. Category 2 contributed ${money(main_summary_export['2'][1])}m of export "
        f"growth and category 3 contributed ${money(main_summary_export['3'][1])}m. The import side "
        f"is broader, and category 7 alone contributed ${money(main_summary_import['7'][1])}m."
    )
    report.figure(
        "f03_index",
        "Analytical trend. The same ten categories with 2016 set to 100, which removes size and "
        "compares growth rate instead.",
    )
    report.text(
        f"Indexing reorders the winners. Category 4 is the smallest category in dollars but grew "
        f"fastest, at a CAGR of {main_summary_export['4'][0]:.1%} on the export side. Category 1 is "
        f"the laggard at {main_summary_export['1'][0]:.1%}, and it is the only category whose export "
        "ends the decade near where it started. A raw chart hides both facts behind the scale of "
        "categories 2 and 3."
    )
    report.figure(
        "f04_share",
        "Each main category as a share of its own direction total, in 2016 and again in 2025.",
    )
    report.text(
        f"The export mix shifted and the import mix did not. Category 2 rose to "
        f"{rw.main_share('Export')[1]['2'][-1]:.1%} of all export by 2025. On the import side "
        f"category 7 moved only from {cat7_share[0]:.1%} to {cat7_share[-1]:.1%}, inside a decade "
        f"range of {min(cat7_share):.1%} to {max(cat7_share):.1%}. Australia changed what it sells "
        "and did not change what it buys."
    )
    report.figure(
        "f05_stats",
        "Statistical trend. Average size against the coefficient of variation on the left, and the "
        "single most unusual growth year for each category on the right, measured as a z-score.",
    )
    report.text(
        f"The left panel separates the steady categories from the volatile ones. Category 3 has the "
        f"highest export volatility at a coefficient of variation of {stats_export['3'][3]:.2f}, "
        f"while its trend fit explains only {stats_export['3'][9]:.0%} of the variance. A category "
        "this volatile cannot be forecast with a straight line, and section 11 returns to that "
        "point. The right panel shows that the outlier years cluster. The manufacturing categories "
        "peak in 2020 and energy peaks in 2022."
    )

    report.heading("6. How the main categories relate, and the change point in each year")
    report.figure(
        "f07_correl",
        "Correlation of year on year growth between every pair of main categories, export side. "
        "Blue means the pair moves together and red means it moves apart.",
    )
    report.text(
        f"The two largest export categories are unrelated. Category 3 against category 2 is "
        f"r = {correl_export['3']['2']:.2f}, which is effectively zero across nine growth years. "
        f"Category 3 instead moves with category 6 at r = {correl_export['3']['6']:.2f} and with "
        f"category 5 at r = {correl_export['3']['5']:.2f}, because all three follow the same world "
        f"price cycle. On the import side category 3 against category 7 is "
        f"r = {correl_import['3']['7']:.2f}. This matters for policy. The two pillars of Australian "
        "export do not hedge each other, because separate cycles drive them and those cycles "
        "happen to overlap."
    )
    report.figure(
        "f06_change",
        "The main category that rose most and the one that fell most in each year, both directions, "
        "in $ Millions of change.",
    )
    report.text(
        "Requirement 3 asks for the change point in every year, so the workbook records all nine "
        "transitions. The table below gives the largest export "
        "mover and the cause. Causes drawn from outside the data cite a sourced research note."
    )
    report.table(
        ["Year", "Largest export mover", "Change", "Cause"],
        [
            [
                str(row["year"]),
                short(
                    row["export_rise_name"]
                    if abs(row["export_rise"]) >= abs(row["export_fall"])
                    else row["export_fall_name"]
                ),
                money(row["export_rise"])
                if abs(row["export_rise"]) >= abs(row["export_fall"])
                else money(row["export_fall"]),
                row["cause"].split(".")[0] + ".",
            ]
            for row in change
        ],
        widths=[1.4, 4.2, 2.2, 8.4],
    )
    report.text(
        "Two findings in that table correct a reading that the headline numbers invite. First, "
        "China restricted Australian coal from late 2020 until March 2023, yet coal export value "
        "rose 124% in 2022, in the middle of the restriction, and fell for three years after it "
        "ended. Price drove the value, and Australia redirected volume to other "
        "buyers. Second, the 2022 fall in iron ore against the rise in coal has a separate cause. "
        "The iron ore price had already fallen from its April 2021 record to a low in November "
        "2021, before energy prices spiked in 2022. These are two separate price cycles crossing."
    )
    report.figure(
        "f10_diverge",
        "The 2022 divergence. Coal export growth against main category 2, which holds iron ore.",
    )

    report.heading("7. Main category against subcategory, inside category 3")
    report.text(
        "The causes in this section are argued from inside the data, as requirement 4 asks. Main "
        "category 3 holds exactly three subcategories, which are 32 coal, 33 petroleum and 34 gas."
    )
    report.figure(
        "f08_cat3",
        "Main category 3 and its three subcategories, both directions, in $ Millions.",
    )
    report.figure(
        "f09_cat3share",
        "Each subcategory as a share of main category 3, both directions.",
    )
    report.text(
        f"The export side and the import side are different categories in practice. On export, "
        f"petroleum is only {cat3_share_export['33'][-1]:.1%} of category 3 in 2025, behind both "
        f"coal and gas. On import, petroleum is {cat3_share_import['33'][-1]:.1%} of the category, "
        f"against {cat3_share_import['32'][-1]:.1%} for coal and {cat3_share_import['34'][-1]:.1%} for gas. "
        "Any statement about \"category 3 imports\" is a statement about petroleum alone."
    )
    report.text(
        f"Each subcategory tracks its parent closely on growth. Petroleum sits at "
        f"r = {cat3_correl_export['33'][0]:.2f}, coal at r = {cat3_correl_export['32'][0]:.2f} and "
        f"gas at r = {cat3_correl_export['34'][0]:.2f}. The subcategories amplify the main "
        "category. The composition did shift, though. Gas rose from "
        f"{cat3_share_export['34'][0]:.1%} to {cat3_share_export['34'][-1]:.1%} of category 3 export "
        f"while coal fell from {cat3_share_export['32'][0]:.1%} to "
        f"{cat3_share_export['32'][-1]:.1%}."
    )
    report.text(
        "One change point can be read from inside the data alone. In 2025 category 3 export fell "
        "18% while petroleum import fell only 6%. If a single demand collapse were driving both "
        "sides they would fall together. They do not, so the export fall is a price effect on what "
        "Australia sells."
    )

    report.heading("8. The dashboard")
    report.text(
        f"The dashboard is at {PAGES_URL}dashboard.html and covers subcategory 33 in both "
        "directions on one screen. It carries a six tile summary row, five named comparisons, an "
        "insight for each of the ten years, a closing 2030 outlook panel that carries the Claude "
        "Sonnet 5 forecast, and a year range control that re-scales every time "
        "chart at once. Each chart has a collapsible table of the numbers beneath it."
    )
    report.bullets(
        [
            "Comparison 1, export against import on one scale, with the 2020 and 2022 change points "
            "annotated on the plot itself.",
            "Comparison 2, the trade balance as columns, every one of them negative.",
            "Comparison 3, petroleum against its own main category, which exposes the asymmetry "
            "between the two directions.",
            "Comparison 4, petroleum against coal and gas on a common index.",
            "Comparison 5, import against export as a scatter with the fitted line, which is where "
            "the central finding of this report becomes visible.",
        ]
    )
    report.figure(
        "f11_focus",
        "The dashboard anchor chart. Subcategory 33 petroleum, export against import, in $ Millions.",
    )
    report.text(
        f"Import exceeds export in every year of the decade. The 2020 dip and the 2022 peak appear "
        f"on both lines at once, which is the first visual clue that a shared price drives both "
        f"sides. Import fell {abs(last['import_growth']):.0%} in 2025 to "
        f"${money(last['import'])}m, which is still {last['import'] / first['import']:.1f} times "
        "the 2016 level."
    )
    report.figure(
        "f12_balance",
        "The petroleum trade balance for each year, in $ Millions. Every column points down.",
    )
    report.text(
        f"The deficit reached its worst point of ${money(abs(worst['balance']))}m in "
        f"{worst['year']}, which is {abs(worst['balance']) / abs(last['balance']):.2f} times the "
        f"2025 figure. The cover ratio in 2025 is {last['cover']:.2f}, so each dollar of petroleum "
        f"import is matched by {last['cover'] * 100:.0f} cents of petroleum export."
    )

    report.heading("9. The storyboard")
    report.text(
        f"The storyboard is at {PAGES_URL}storyboard.html. Where the dashboard answers questions in "
        "any order, the storyboard makes one argument in a fixed order across thirteen panels. It "
        "starts with total Australian trade, moves through the ten main categories in their raw, "
        "indexed and statistical forms, works through the change point of each year, descends into "
        "main category 3, then into subcategory 33, and closes with the forecast and the Claude "
        "Sonnet 5 comparison. Every panel carries both trade directions and ends with a stated takeaway, so "
        "a reader cannot reach the end without having been told what each chart is for."
    )
    report.figure(
        "f01_total",
        "The storyboard opening. Total export, total import and the balance between them, in "
        "$ Millions.",
    )
    report.text(
        f"This panel sets up every panel after it. Export fell "
        f"{1 - totals_export[2025] / max(totals_export.values()):.0%} from its 2022 peak, while "
        f"import rose in {import_rises} of the nine transitions and set its decade high of "
        f"${money(totals_import[2025])}m in 2025. The surplus quoted in section 1 narrows from "
        "both ends at once, which no single series on the chart shows on its own."
    )
    report.figure(
        "f13_vssubs",
        "Petroleum against coal and gas, indexed to 2016, both directions.",
    )
    report.text(
        f"Petroleum growth tracks coal at r = {pairs['33 against 32']['Export']:.2f} and gas at "
        f"r = {pairs['33 against 34']['Export']:.2f} on the export side. On the import side those "
        f"fall to {pairs['33 against 32']['Import']:.2f} and "
        f"{pairs['33 against 34']['Import']:.2f}, because the coal and gas import series are tiny "
        "and noisy. The export side of category 3 is one coherent energy story and the import side "
        "is a petroleum story with two rounding errors attached."
    )

    report.heading("10. Trends and outliers compared")
    report.text(
        "An outlier here comes from a calculation. The workbook computes a z-score for each year of "
        "growth against that category's own mean growth, so a value above 2 marks a year that is "
        "unusual for that category."
    )
    report.table(
        ["Category", "Outlier year", "Growth that year", "Z-score"],
        [
            ["8 Miscellaneous manufactured articles", "2020", "-10%", f"{min(zscore_export['8']):.2f}"],
            ["6 Manufactured goods by material", "2020", "-16%", f"{min(zscore_export['6']):.2f}"],
            ["7 Machinery and transport equipment", "2020", "-14%", f"{min(zscore_export['7']):.2f}"],
            ["3 Mineral fuels", "2022", "+99%", f"{max(zscore_export['3']):.2f}"],
            ["9 Commodities not classified elsewhere", "2025", "+47%", f"{max(zscore_export['9']):.2f}"],
        ],
        widths=[7.0, 2.6, 3.0, 3.6],
    )
    report.text(
        "The outliers fall into three groups and each has a different explanation. The 2020 group "
        "is the manufacturing categories, cut by the COVID demand collapse. The 2022 outlier is "
        "energy, lifted by the price shock after the invasion of Ukraine. The 2025 outlier is "
        "category 9, and that one is worth care. Category 9 rose $21,245m in 2025 while gold inside "
        "it rose $23,854m, so gold accounts for more than the whole category movement, offset by a "
        "$3,006m fall in confidential items. Gold rose 44% in price over 2025 against a 67% rise in "
        "Australian gold export value, so price explains most of the rise but not all of it. The "
        "remaining gap points to volume or refining throughput, which this dataset cannot separate."
    )

    report.heading("11. Ten years of gain and loss, the target, and the forecast")
    report.text(
        f"The product chosen for this section is petroleum import, subcategory 33. It stood at "
        f"${money(first['import'])}m in 2016 against petroleum export of ${money(first['export'])}m, "
        f"and by 2025 it had reached ${money(last['import'])}m against export of "
        f"${money(last['export'])}m. Across the ten years Australia lost ground on it. Import rose "
        f"${money(summary['Change 2016 to 2025 ($ Millions)'])}m, which is a rise of "
        f"{summary['Change 2016 to 2025 (percent)']:.0%}, at a compound rate of "
        f"{summary['Import CAGR 2016 to 2025']:.1%} a year. The petroleum trade deficit widened by "
        f"${money(abs(summary['Balance 2025 ($ Millions)']) - abs(summary['Balance 2016 ($ Millions)']))}m "
        "over the same period. The loss is a larger bill every year for a "
        "product Australia increasingly does not refine for itself."
    )
    report.figure(
        "f14_scatter",
        "Petroleum import against petroleum export, one point per year, with the fitted line.",
    )
    report.text(
        f"This chart carries the central finding. The two directions move together at "
        f"r = {import_export_r:.2f}. Both are priced off the same world oil market, so they rise "
        f"and fall as one. Because import is {ratio_2025:.2f} times the size of export, a price "
        f"rise adds ${ratio_2025:.2f} to the import bill for every dollar it adds to export "
        "earnings. "
        "Growing petroleum export cannot close this gap. Only buying less, or refining more at "
        "home, can."
    )
    report.figure(
        "f15_forecast",
        "Petroleum import. Ten years of actual values, two forecast methods, the target path and "
        "the Claude Sonnet 5 forecast, in $ Millions.",
    )
    report.text(
        "The workbook carries two forecast methods, both as live formulas. A straight line fitted "
        "to 2016 to 2025 gives "
        f"${money(forecast[-1]['linear'])}m by 2030. Growing the 2025 value at the decade compound "
        f"rate gives ${money(forecast[-1]['cagr'])}m. Both point upward and neither should be "
        f"trusted far. The straight line explains only {summary['Linear trend R squared']:.0%} of "
        "the variance, because this series follows a world price."
    )
    report.text(
        f"The target is therefore a decision. Cutting petroleum "
        f"import 3% a year from the 2025 level reaches "
        f"${money(summary['Target import 2030 ($ Millions)'])}m in 2030, which is "
        f"${money(summary['Linear forecast 2030 less target ($ Millions)'])}m below where the "
        "straight line would otherwise land."
    )
    report.table(
        ["Year", "Linear trend", "CAGR method", "Target path", "Claude Sonnet 5"],
        [
            [
                str(row["year"]),
                money(row["linear"]),
                money(row["cagr"]),
                money(row["target"]),
                money(entry["ai"]),
            ]
            for row, entry in zip(forecast[len(YEARS):], ai)
        ],
        widths=[2.0, 3.6, 3.6, 3.4, 3.6],
    )

    report.heading("12. Comparison against the Claude Sonnet 5 forecast")
    report.text(
        "The AI model used here is Claude Sonnet 5, model id claude-sonnet-5. It was given the ten "
        "annual petroleum import values and the unit, and nothing "
        "else. It received none of this analysis, no change point notes, no refinery history, no "
        "export side and no target. The run was on 16 October 2026, "
        "with no tools available. The prompt and the reply are "
        "reproduced word for word in Appendix A so that the comparison can be audited."
    )

    report.sub("12.1 What Claude Sonnet 5 produced")
    report.text(
        "The model did two things. It described the decade, and it forecast each year from 2026 to "
        "2030. Its description was accurate. It found the 2022 peak of 65,082, the 2020 dip to "
        "22,720, and the three year decline to 52,742 in 2025, and it noted that 2025 is still "
        "more than double the 2016 level. It also stated its method, which was to extrapolate the "
        f"2022 to 2025 fall of {money(ai_step)} million a year. A reader can therefore check it."
    )
    report.text(
        f"The forecast is where the two analyses part. The model projects "
        f"${money(ai[-1]['ai'])}m for 2030, a fall of "
        f"{abs(ai[-1]['ai'] / last['import'] - 1):.0%} from 2025. My linear trend projects "
        f"${money(forecast[-1]['linear'])}m, a rise of "
        f"{forecast[-1]['linear'] / last['import'] - 1:.0%}. The difference in 2030 is "
        f"${money(abs(ai[-1]['difference']))}m, which is more than the entire 2016 import value of "
        f"${money(first['import'])}m. The gap widens every year of the forecast, from "
        f"{abs(ai[0]['percent']):.0%} in 2026 to {abs(ai[-1]['percent']):.0%} in 2030."
    )

    report.sub("12.2 Why the two answers disagree")
    report.text(
        "Both methods are correctly executed. The whole "
        "difference comes from one unstated choice, which is how much history to fit. The model used "
        "the last four years, which contain only the fall from the 2022 peak, so it had to project "
        "a fall. I used all ten years, which contain the climb to that peak, so I had to project a "
        "rise. Neither window is obviously right, and neither of us justified the choice from the "
        "data. That is the most useful thing this comparison exposed, and it is a criticism of my "
        "own method as much as of the model."
    )

    report.sub("12.3 Testing both methods on data they have not seen")
    report.text(
        "A disagreement can be settled by a backtest. Each method was fitted to 2016 to 2021 only, "
        "then asked to predict 2022 to 2025, which it had not seen. The recent window method "
        "reproduces the Claude Sonnet 5 approach, extrapolating the change over the last few years of the "
        "training period. The Pet33-Backtest sheet in the workbook holds this as live formulas."
    )
    report.table(
        ["Year", "Actual", "Linear trend", "CAGR method", "Recent window, the Claude Sonnet 5 approach"],
        [
            [
                str(row["year"]),
                money(row["actual"]),
                money(row["linear"]),
                money(row["cagr"]),
                money(row["recent"]),
            ]
            for row in backtest_rows
            if row["linear"] is not None
        ]
        + [
            [
                "Mean error",
                "",
                f"{mape['linear']:.1%}",
                f"{mape['cagr']:.1%}",
                f"{mape['recent']:.1%}",
            ]
        ],
        widths=[2.4, 2.8, 3.2, 3.2, 4.6],
    )
    report.text(
        f"Every method failed, and badly. The best of the three was the CAGR method at "
        f"{mape['cagr']:.1%} mean absolute error. My linear trend scored {mape['linear']:.1%}. The "
        f"recent window method, which is the one the model chose, was the worst at "
        f"{mape['recent']:.1%}, predicting ${money(backtest_rows[-1]['recent'])}m for 2025 against "
        f"an actual of ${money(backtest_rows[-1]['actual'])}m. On the evidence available, the model "
        "picked the weakest of the three approaches."
    )
    report.text(
        "The more important reading is that all three were wrong by a wide margin in the same "
        "direction. Every method under-forecast, because the 2022 price shock was not present in "
        "the training data and could not be inferred from it. No amount of curve fitting on ten "
        "annual points will anticipate an invasion. This is the strongest argument in the report "
        "for treating the 2026 to 2030 numbers as a planning range, and "
        "for setting a target."
    )

    report.sub("12.4 What Claude Sonnet 5 could not know")
    report.bullets(
        [
            "That the 2020 dip and the 2022 peak are price events. That "
            f"only becomes visible from the two way data, where import and export move together at "
            f"r = {import_export_r:.2f}. The model was given the import side alone, so it could not "
            "see the mechanism at all.",
            "That two Australian refineries closed in 2021, which shifts the mix of imports from "
            "crude towards refined product and puts a floor under the bill. No amount of care with "
            "ten numbers recovers a fact that is not in them.",
            "That the series is too noisy to support a point forecast. The straight line fit "
            f"explains only {summary['Linear trend R squared']:.0%} of the variance. The model "
            "returned five exact figures with no range and no caveat, which reads as far more "
            "certain than the data permits.",
            "That its own method had the worst backtest record of the three. It had no way to test "
            "itself, because testing needs a held out period and a second method to compare "
            "against, and it was given neither.",
        ]
    )

    report.sub("12.5 Advantages of using AI here")
    report.numbers(
        [
            "Speed. The reply returned in seconds and needed no spreadsheet, no chart and no "
            "build step.",
            "Independence. The model had no stake in my conclusion and had not spent hours forming "
            "an opinion. It read the series cold, which is exactly why it chose a different window "
            "and exposed that my own window was an unexamined assumption.",
            f"A stated method. It said it was extrapolating the 2022 to 2025 fall at {money(ai_step)} a "
            "year. Because it said so, the method could be backtested and found wanting. An "
            "assistant that only returned numbers would have been useless here.",
            "Pattern description. Its reading of the decade shape was correct and would be a "
            "reasonable first summary for a reader meeting the series for the first time.",
        ]
    )

    report.sub("12.6 Disadvantages of using AI here")
    report.numbers(
        [
            "No causal knowledge. It could not know why 2022 happened, so it could not judge "
            "whether to carry that movement forward. Every useful cause in this report came from "
            "outside the dataset.",
            "Confidence without uncertainty. Five exact numbers, no error band, no warning that "
            "the series resists forecasting. A policy reader would take those figures at face "
            "value.",
            "It answers only the question asked. Given the import column, it analysed the import "
            "column. It did not ask for the export side, which is where the actual finding of this "
            "report lives. A human analyst would have asked.",
            "It cannot check itself against reality. It had no held out period, no second method "
            "and no way to measure its own error, so its weakest-performing method was presented "
            "with the same assurance as its strongest observation.",
            "One run is not evidence. This comparison rests on a single response. A different "
            "phrasing, or the same prompt run again, could give different numbers, and nothing in "
            "the output would signal that.",
        ]
    )

    report.sub("12.7 What this means for using AI in visual analytics")
    report.text(
        "Claude Sonnet 5 was useful here as an adversary. It made a different "
        "defensible choice of window, which forced me to backtest a choice I had not examined. A "
        "second opinion whose method is stated and then measured improves the analysis. The same "
        "output read at face value, as five confident numbers, would have made it worse than "
        "having no forecast at all."
    )

    report.heading("13. Visualisation techniques, and the problems handled")
    report.text(
        "Each technique was chosen for one job. Time series lines carry the trends, columns carry a signed "
        "quantity such as the balance, small multiples where ten categories had to be compared at "
        "once, a dumbbell for a before and after comparison, a heatmap for the correlation matrix, "
        "and a scatter with a fitted line for the relationship between the two trade directions. "
        "Five problems came up and each needed a decision."
    )
    report.numbers(
        [
            "Ten categories, eight safe colours. Cycling hues past eight makes series "
            "indistinguishable, so the ten category charts became small multiples. Colour was then "
            "freed for the one distinction that matters everywhere, import against export.",
            f"Different magnitudes on one chart. Category 4 export is ${money(cat4_2025)}m against "
            f"${money(cat2_2025)}m for category 2, a ratio of 1 to {cat2_2025 / cat4_2025:.0f}. A "
            "second y axis was rejected, because two scales on one frame invite false comparison. "
            "Indexing to 2016 and small multiples solved it honestly.",
            "Labels colliding. The first share chart put ten end of line labels on top of each other "
            "and was unreadable. It was rebuilt as a dumbbell on a category axis, with the values in "
            "a fixed column clear of the markers.",
            "Grouped bars that did not group. The outlier chart first used a label of category and "
            "year, and because the outlier year differs by direction it produced twenty separate "
            "categories instead of ten pairs. The year moved to a bar label and the axis became the "
            "category alone.",
            "Colour that fails for colourblind readers. Every "
            "set of colours that appears together was run through a contrast and colour vision "
            "checker, and two of the hues sit below the contrast floor on a light background, so "
            "every chart that uses them also ships a table of its numbers.",
        ]
    )

    report.heading("14. The dashboard against the storyboard")
    report.table(
        ["", "Dashboard", "Storyboard"],
        [
            ["What it is for", "Looking something up", "Being walked through an argument"],
            ["Order of reading", "Any order the reader likes", "Fixed, top to bottom"],
            ["Strength", "Density and comparison on one screen, with filters", "Causation and sequence, each panel sets up the next"],
            ["Weakness", "Shows what happened and leaves the cause out. A reader can misread it with no guard rail", "Slow to scan, and cannot answer a question it was not built to answer"],
            ["Best audience", "An analyst who already knows the domain", "A policy reader meeting the data for the first time"],
        ],
        widths=[3.2, 6.4, 6.6],
    )
    report.text(
        "The two methods failed in opposite ways while this task was built, which is the clearest "
        "evidence for using both. The dashboard shows that the petroleum deficit widened, but a "
        "reader can look at it and conclude that Australia should export more petroleum, which the "
        "data says will not work. The storyboard forces the scatter in section 11 in front of the "
        "reader before it allows any recommendation. The storyboard cannot be filtered, though, so "
        "a reader who wants 2020 to 2023 alone has to go to the dashboard. Together they cover both "
        "needs. Separately each leaves a real gap."
    )

    report.heading("15. Recommendations")
    report.text(
        "These recommendations cover the industries this study touches. Those industries are "
        "refining, fuel import logistics, and the energy export industries that fund them."
    )
    report.numbers(
        [
            f"Set the petroleum import bill as a tracked target. The path in this "
            f"report cuts it 3% a year to ${money(summary['Target import 2030 ($ Millions)'])}m by "
            "2030. A forecast on this series is too unreliable to steer by. A target is a "
            "decision and can be measured against each year.",
            "Do not pursue petroleum export growth as a fuel security measure. Import and export "
            f"move together at r = {import_export_r:.2f} and import is {ratio_2025:.2f} times "
            "larger, so "
            "a higher oil price widens the deficit no matter how much Australia sells. This is the "
            "single clearest policy finding in the data.",
            "Treat the two remaining refineries as the variable that matters. Refining capacity is "
            "what decides whether Australia imports crude or finished product, and that mix is the "
            "part of the bill domestic policy can still influence.",
            "Do not read the energy export surplus as durable cover for the fuel bill. Category 3 "
            f"export has fallen three years in a row and has the highest volatility of any category, "
            f"at a coefficient of variation of {stats_export['3'][3]:.2f}. The surplus that funded "
            "the import bill in 2022 has already shrunk 65%.",
            "Diversify with care, because the two largest export categories do not hedge each "
            f"other. Categories 2 and 3 correlate at r = {correl_export['3']['2']:.2f}, which looks "
            "like good diversification, but both are commodity price cycles. Timing kept them "
            "uncorrelated over this decade.",
            "Collect volume alongside value. Every limit in this report comes from the dataset "
            "holding dollars only. Separating price from volume would settle several questions this "
            "analysis could only bound.",
        ]
    )

    report.heading("16. Conclusion")
    report.text(
        f"The decade surplus peaked on a price shock and has fallen "
        f"{abs(balance_2025 / balance_2022 - 1):.0%} since. Subcategory 33 runs the other way, and "
        "section 11 shows why selling more petroleum cannot close it. One decision follows, which "
        "is to track the import bill against a target. The backtest in section 12.3 shows no method "
        "here forecasts this series. Every number above lives in the submitted workbook as a live "
        "formula, and the report, the dashboard and the storyboard all read that one file."
    )

    report.heading("Appendix A. The Claude Sonnet 5 prompt and the reply, word for word")
    report.text(
        "Run on 16 October 2026 using Claude Sonnet 5, model id claude-sonnet-5, "
        "with no tools available. The model was given the ten values below and no other information "
        "about this project."
    )
    report.sub("The prompt")
    report.quote(logged("## The prompt, word for word"))
    report.sub("The reply")
    report.quote(logged("## The reply, word for word"))

    report.heading("Appendix B. Sources")
    report.text(
        "The data comes from the Australian Bureau of Statistics, Australian International Trade, "
        "2016 to 2025, supplied as 2026-Spring-Ass3-V20.xlsx. External causes cited in section 6 and section 10 "
        "are recorded with their sources in data/research_notes.md, submitted with the dashboard "
        "source. The notes cover the 2020 COVID demand collapse, the 2022 energy price shock, the "
        "Kwinana and Altona refinery closures, China's coal restrictions, the iron ore price cycle "
        "and the 2025 gold price rise."
    )


def logged(section):
    text = (ROOT / "data" / "ai_forecast.md").read_text()
    return text.split(section)[1].split("```")[1].strip()


def to_pdf():
    with tempfile.TemporaryDirectory() as workdir:
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--norestore",
                "--nolockcheck",
                f"-env:UserInstallation=file://{PROFILE}",
                "--convert-to",
                "pdf:writer_pdf_Export:"
                '{"UseLosslessCompression":{"type":"boolean","value":"true"},'
                '"ReduceImageResolution":{"type":"boolean","value":"false"}}',
                "--outdir",
                workdir,
                str(DOCX),
            ],
            capture_output=True,
            text=True,
        )
        produced = Path(workdir) / DOCX.with_suffix(".pdf").name
        if not produced.exists():
            raise SystemExit("LibreOffice did not produce the PDF")
        shutil.move(str(produced), str(PDF))


def page_count():
    data = PDF.read_bytes()
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages") or data.count(b"/Type/Page") - data.count(b"/Type/Pages")


def main():
    render_figures()
    report = Report()
    build_content(report)
    report.save(DOCX)
    to_pdf()
    print(f"wrote {DOCX.relative_to(ROOT)} and {PDF.relative_to(ROOT)}")
    print(f"figures: {report.figure_number}")
    print(f"pages: {page_count()}")


if __name__ == "__main__":
    main()
