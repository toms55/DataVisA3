import csv

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference, ScatterChart, Series
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from layout import (
    DIRECTIONS,
    FIRST_YEAR_ROW,
    FOCUS_MAIN,
    FOCUS_SUB,
    FOCUS_SUBS,
    FORECAST_YEARS,
    ROOT,
    TARGET,
    TOTAL_CODE,
    YEARS,
    level_of,
    read_source,
    source_ref,
)

TITLE = Font(bold=True, size=13, color="1F3864")
BOLD = Font(bold=True)
HEAD = Font(bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
EXPORT_FILL = PatternFill("solid", fgColor="DDEBF7")
IMPORT_FILL = PatternFill("solid", fgColor="FCE4D6")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

MONEY = "#,##0"
PCT = "0.0%"
RATIO = "0.00"
INDEX = "#,##0.0"

REG = {}


def key_years_ref():
    return "'Keys'!$B$3:$B$12"


def reg_row(name, code):
    first, codes = REG[name]
    return first + codes.index(code)


def write_block(worksheet, row, title, years, codes, names, cell, number_format):
    worksheet.cell(row, 1, title).font = TITLE
    row += 1
    worksheet.cell(row, 1, "Code").font = HEAD
    worksheet.cell(row, 1).fill = HEAD_FILL
    worksheet.cell(row, 2, "Category").font = HEAD
    worksheet.cell(row, 2).fill = HEAD_FILL
    for offset, year in enumerate(years):
        target = worksheet.cell(row, 3 + offset, year)
        target.font = HEAD
        target.fill = HEAD_FILL
        target.alignment = Alignment(horizontal="center")
    row += 1
    first = row
    for code in codes:
        worksheet.cell(row, 1, code)
        worksheet.cell(row, 2, names[code])
        for offset, year in enumerate(years):
            target = worksheet.cell(row, 3 + offset, cell(code, year))
            target.number_format = number_format
            target.border = BOX
        row += 1
    return row + 1, first


def write_columns(worksheet, row, title, headers, codes, names, cells, formats):
    worksheet.cell(row, 1, title).font = TITLE
    row += 1
    worksheet.cell(row, 1, "Code").font = HEAD
    worksheet.cell(row, 1).fill = HEAD_FILL
    worksheet.cell(row, 2, "Category").font = HEAD
    worksheet.cell(row, 2).fill = HEAD_FILL
    for offset, header in enumerate(headers):
        target = worksheet.cell(row, 3 + offset, header)
        target.font = HEAD
        target.fill = HEAD_FILL
        target.alignment = Alignment(horizontal="center", wrap_text=True)
    row += 1
    first = row
    for code in codes:
        worksheet.cell(row, 1, code)
        worksheet.cell(row, 2, names[code])
        for offset, build in enumerate(cells):
            target = worksheet.cell(row, 3 + offset, build(code))
            target.number_format = formats[offset]
            target.border = BOX
        row += 1
    return row + 1, first


def set_widths(worksheet, widths):
    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width


def build_keys(workbook):
    worksheet = workbook.create_sheet("Keys")
    worksheet.cell(1, 1, "Numeric keys used by the trend and forecast formulas").font = TITLE
    worksheet.cell(2, 1, "Index").font = BOLD
    worksheet.cell(2, 2, "Year").font = BOLD
    worksheet.cell(2, 3, "Forecast year").font = BOLD
    for offset, year in enumerate(YEARS):
        worksheet.cell(3 + offset, 1, offset + 1)
        worksheet.cell(3 + offset, 2, year)
    for offset, year in enumerate(FORECAST_YEARS):
        worksheet.cell(3 + offset, 3, year)
    set_widths(worksheet, {"A": 10, "B": 10, "C": 14})
    return worksheet


def copy_source(workbook, layout):
    for direction in DIRECTIONS:
        worksheet = workbook.create_sheet(f"{direction}-dataset")
        for row_index, row in enumerate(layout[direction]["rows"], start=1):
            for column_index, value in enumerate(row, start=1):
                cell = worksheet.cell(row_index, column_index, value)
                if row_index == 1:
                    cell.font = BOLD
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
                if row_index >= FIRST_YEAR_ROW and column_index > 1:
                    cell.number_format = MONEY
        worksheet.column_dimensions["A"].width = 12
        worksheet.freeze_panes = "B4"


def build_tidy(workbook, layout):
    for direction in DIRECTIONS:
        worksheet = workbook.create_sheet(f"{direction}-tidy")
        headers = [
            "Direction",
            "Year",
            "Code",
            "Level",
            "Category",
            "Unit",
            "Series ID",
            f"Value ($ Millions, {direction.lower()})",
        ]
        for column_index, header in enumerate(headers, start=1):
            cell = worksheet.cell(1, column_index, header)
            cell.font = HEAD
            cell.fill = HEAD_FILL
        row = 2
        info = layout[direction]
        for code in info["order"]:
            for year in YEARS:
                worksheet.cell(row, 1, direction)
                worksheet.cell(row, 2, year)
                worksheet.cell(row, 3, code)
                worksheet.cell(row, 4, level_of(code))
                worksheet.cell(row, 5, info["names"][code])
                worksheet.cell(row, 6, "$ Millions")
                worksheet.cell(row, 7, info["rows"][2][info["order"].index(code) + 1])
                value = worksheet.cell(
                    row, 8, f"={source_ref(direction, code, year, layout)}"
                )
                value.number_format = MONEY
                row += 1
        set_widths(
            worksheet,
            {"A": 11, "B": 8, "C": 8, "D": 8, "E": 58, "F": 12, "G": 12, "H": 18},
        )
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = f"A1:H{row - 1}"


def build_main_analytics(workbook, layout):
    worksheet = workbook.create_sheet("Main-Analytics")
    worksheet.cell(1, 1, "Main category analytics, import and export").font = TITLE
    worksheet.cell(
        2,
        1,
        "Every cell is a live formula that reads the two dataset sheets. "
        "Values are in $ Millions unless the block says otherwise.",
    )
    row = 4
    for direction in DIRECTIONS:
        info = layout[direction]
        mains = info["mains"]
        names = info["names"]

        def value_cell(code, year, direction=direction):
            return f"={source_ref(direction, code, year, layout)}"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: value ($ Millions)",
            YEARS,
            mains,
            names,
            value_cell,
            MONEY,
        )
        REG[f"value-{direction}"] = (first, mains)

        def growth_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            before = source_ref(direction, code, year - 1, layout)
            return f"=IFERROR({now}/{before}-1,\"\")"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: year on year growth",
            YEARS[1:],
            mains,
            names,
            growth_cell,
            PCT,
        )
        REG[f"growth-{direction}"] = (first, mains)

        def index_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            base = source_ref(direction, code, YEARS[0], layout)
            return f"={now}/{base}*100"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: index (2016 = 100)",
            YEARS,
            mains,
            names,
            index_cell,
            INDEX,
        )
        REG[f"index-{direction}"] = (first, mains)

        def share_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            total = source_ref(direction, TOTAL_CODE, year, layout)
            return f"={now}/{total}"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: share of {direction.lower()} total",
            YEARS,
            mains,
            names,
            share_cell,
            PCT,
        )
        REG[f"share-{direction}"] = (first, mains)

        last = YEARS[-1]
        base = YEARS[0]
        span = last - base

        def cagr(code, direction=direction, last=last, base=base, span=span):
            end = source_ref(direction, code, last, layout)
            start = source_ref(direction, code, base, layout)
            return f"=POWER({end}/{start},1/{span})-1"

        def contribution(code, direction=direction, last=last, base=base):
            end = source_ref(direction, code, last, layout)
            start = source_ref(direction, code, base, layout)
            return f"={end}-{start}"

        def growth_share(code, direction=direction, last=last, base=base):
            end = source_ref(direction, code, last, layout)
            start = source_ref(direction, code, base, layout)
            total_end = source_ref(direction, TOTAL_CODE, last, layout)
            total_start = source_ref(direction, TOTAL_CODE, base, layout)
            return f"=({end}-{start})/({total_end}-{total_start})"

        row, first = write_columns(
            worksheet,
            row,
            f"{direction}: decade summary",
            [
                "CAGR 2016 to 2025",
                "Contribution to growth ($ Millions)",
                "Share of total growth",
            ],
            mains,
            names,
            [cagr, contribution, growth_share],
            [PCT, MONEY, PCT],
        )
        REG[f"summary-{direction}"] = (first, mains)

    set_widths(worksheet, {"A": 8, "B": 46})
    for column in range(3, 3 + len(YEARS)):
        worksheet.column_dimensions[get_column_letter(column)].width = 14
    return worksheet


def build_main_stats(workbook, layout):
    worksheet = workbook.create_sheet("Main-Stats")
    worksheet.cell(1, 1, "Main category statistics, import and export").font = TITLE
    worksheet.cell(
        2,
        1,
        "The outlier z-score measures each year of growth against the mean growth "
        "of that category. A value above 2 marks an outlier year.",
    )
    row = 4
    for direction in DIRECTIONS:
        info = layout[direction]
        mains = info["mains"]
        names = info["names"]
        column = info["columns"]
        first_row = FIRST_YEAR_ROW
        last_row = FIRST_YEAR_ROW + len(YEARS) - 1

        def span(code, direction=direction, column=column, first_row=first_row, last_row=last_row):
            return f"'{direction}-dataset'!{column[code]}{first_row}:{column[code]}{last_row}"

        builders = [
            lambda code: f"=AVERAGE({span(code)})",
            lambda code: f"=MEDIAN({span(code)})",
            lambda code: f"=STDEVP({span(code)})",
            lambda code: f"=STDEVP({span(code)})/AVERAGE({span(code)})",
            lambda code: f"=MIN({span(code)})",
            lambda code: f"=MAX({span(code)})",
            lambda code: f"=MAX({span(code)})-MIN({span(code)})",
            lambda code: f"=SLOPE({span(code)},{key_years_ref()})",
            lambda code: f"=INTERCEPT({span(code)},{key_years_ref()})",
            lambda code: f"=RSQ({span(code)},{key_years_ref()})",
        ]
        row, first = write_columns(
            worksheet,
            row,
            f"{direction}: descriptive and trend statistics ($ Millions)",
            [
                "Mean",
                "Median",
                "Standard deviation",
                "Coefficient of variation",
                "Minimum",
                "Maximum",
                "Range",
                "Trend slope ($ Millions per year)",
                "Trend intercept",
                "Trend R squared",
            ],
            mains,
            names,
            builders,
            [MONEY, MONEY, MONEY, RATIO, MONEY, MONEY, MONEY, MONEY, MONEY, RATIO],
        )
        REG[f"stats-{direction}"] = (first, mains)

        growth_first, growth_codes = REG[f"growth-{direction}"]
        growth_last_column = get_column_letter(3 + len(YEARS) - 2)

        def zscore(code, year, direction=direction, growth_first=growth_first, growth_codes=growth_codes, growth_last_column=growth_last_column):
            target_row = growth_first + growth_codes.index(code)
            cell = f"'Main-Analytics'!{get_column_letter(3 + YEARS[1:].index(year))}{target_row}"
            band = f"'Main-Analytics'!$C${target_row}:${growth_last_column}${target_row}"
            return f"=({cell}-AVERAGE({band}))/STDEVP({band})"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: outlier z-score of year on year growth",
            YEARS[1:],
            mains,
            names,
            zscore,
            RATIO,
        )
        REG[f"zscore-{direction}"] = (first, mains)

    set_widths(worksheet, {"A": 8, "B": 46})
    for column in range(3, 14):
        worksheet.column_dimensions[get_column_letter(column)].width = 15
    return worksheet


def build_balance(workbook, layout):
    worksheet = workbook.create_sheet("Balance")
    worksheet.cell(1, 1, "Trade balance and cover ratio by main category").font = TITLE
    worksheet.cell(
        2,
        1,
        "Balance is export minus import. Cover ratio is export divided by import. "
        "A ratio below 1 means Australia buys more than it sells.",
    )
    mains = layout["Export"]["mains"]
    names = layout["Export"]["names"]
    codes = mains + [TOTAL_CODE]
    all_names = dict(names)
    all_names[TOTAL_CODE] = "TOTAL, all categories"
    row = 4

    def balance_cell(code, year):
        export = source_ref("Export", code, year, layout)
        imports = source_ref("Import", code, year, layout)
        return f"={export}-{imports}"

    row, first = write_block(
        worksheet,
        row,
        "Trade balance, export minus import ($ Millions)",
        YEARS,
        codes,
        all_names,
        balance_cell,
        MONEY,
    )
    REG["balance"] = (first, codes)

    def cover_cell(code, year):
        export = source_ref("Export", code, year, layout)
        imports = source_ref("Import", code, year, layout)
        return f"=IFERROR({export}/{imports},\"\")"

    row, first = write_block(
        worksheet,
        row,
        "Cover ratio, export divided by import",
        YEARS,
        codes,
        all_names,
        cover_cell,
        RATIO,
    )
    REG["cover"] = (first, codes)
    set_widths(worksheet, {"A": 8, "B": 46})
    for column in range(3, 3 + len(YEARS)):
        worksheet.column_dimensions[get_column_letter(column)].width = 14
    return worksheet


def build_correlation(workbook, layout):
    worksheet = workbook.create_sheet("Correlation")
    worksheet.cell(
        1, 1, "Correlation between main categories, on year on year growth"
    ).font = TITLE
    worksheet.cell(
        2,
        1,
        "Each cell is the correlation of two categories across the nine growth years. "
        "A value near zero means the two categories move independently.",
    )
    row = 4
    last_column = get_column_letter(3 + len(YEARS) - 2)
    for direction in DIRECTIONS:
        mains = layout[direction]["mains"]
        names = layout[direction]["names"]
        growth_first, growth_codes = REG[f"growth-{direction}"]
        worksheet.cell(row, 1, f"{direction}: growth correlation matrix").font = TITLE
        row += 1
        worksheet.cell(row, 1, "Code").font = HEAD
        worksheet.cell(row, 1).fill = HEAD_FILL
        worksheet.cell(row, 2, "Category").font = HEAD
        worksheet.cell(row, 2).fill = HEAD_FILL
        for offset, code in enumerate(mains):
            cell = worksheet.cell(row, 3 + offset, code)
            cell.font = HEAD
            cell.fill = HEAD_FILL
            cell.alignment = Alignment(horizontal="center")
        row += 1
        first = row
        for code in mains:
            worksheet.cell(row, 1, code)
            worksheet.cell(row, 2, names[code])
            left = growth_first + growth_codes.index(code)
            for offset, other in enumerate(mains):
                right = growth_first + growth_codes.index(other)
                band_a = f"'Main-Analytics'!$C${left}:${last_column}${left}"
                band_b = f"'Main-Analytics'!$C${right}:${last_column}${right}"
                cell = worksheet.cell(row, 3 + offset, f"=CORREL({band_a},{band_b})")
                cell.number_format = RATIO
                cell.border = BOX
                cell.fill = EXPORT_FILL if direction == "Export" else IMPORT_FILL
            row += 1
        REG[f"correl-{direction}"] = (first, mains)
        row += 1
    set_widths(worksheet, {"A": 8, "B": 46})
    for column in range(3, 13):
        worksheet.column_dimensions[get_column_letter(column)].width = 9
    return worksheet


CAUSES = {
    2017: "Mineral fuels export rises 23,447 million on higher coal and LNG prices and new LNG capacity. Machinery import rises 14,601 million.",
    2018: "Mineral fuels export rises 31,120 million as LNG output reaches full capacity. Mineral fuels import rises 10,707 million on a higher oil price.",
    2019: "Crude materials export rises 29,536 million. Iron ore alone rises 32,099 million after a supply shock cut Brazilian output.",
    2020: "COVID cuts mineral fuels export 37,467 million and mineral fuels import 15,686 million. Categories 6, 7 and 8 are the statistical outliers of the year.",
    2021: "Crude materials export rises 46,211 million at the iron ore price peak. Mineral fuels export recovers 37,574 million.",
    2022: "Mineral fuels export rises 124,939 million after the invasion of Ukraine. Mineral fuels import rises 31,254 million on the same price shock.",
    2023: "Mineral fuels export falls 55,785 million as energy prices retreat from the 2022 peak. Machinery import still rises 16,455 million.",
    2024: "Mineral fuels export falls 24,707 million and crude materials export falls 23,373 million as energy and iron ore prices both ease.",
    2025: "Mineral fuels export falls 30,661 million. Category 9 rises 21,245 million, and gold alone accounts for 23,854 million of that.",
}

INSIGHTS = {
    2016: "Baseline year. Import is 3.4 times export, so the deficit starts at 16,369 million.",
    2017: "Import rises 26% against export at 10%, so the deficit widens by 5,334 million.",
    2018: "Both sides grow near 40%, the fastest of the decade, and the deficit passes 28,000 million.",
    2019: "Export rises 9% while import falls 4%. This is the only year the deficit narrows while total trade grows.",
    2020: "COVID cuts import 41% and export 37%. The deficit is the smallest of the decade at 14,965 million.",
    2021: "Trade rebounds near 50% on both sides and the deficit returns to the 2017 level.",
    2022: "Import rises 91% and export 48%. The deficit reaches its worst point at 47,741 million.",
    2023: "The first year of unwind. Import falls 8% and export falls 9%, but the deficit stays above 44,000 million.",
    2024: "Import falls 6% while export is flat, so the deficit narrows for a third year.",
    2025: "Import falls 6% to 52,742 million, still 2.3 times the 2016 level. The deficit settles at 38,555 million.",
}

TARGET_RATE = 0.03


def build_change_points(workbook, layout):
    worksheet = workbook.create_sheet("ChangePoints")
    worksheet.cell(1, 1, "Change points for each year, 2017 to 2025").font = TITLE
    worksheet.cell(
        2,
        1,
        "The helper blocks hold the dollar change of every main category. "
        "The summary names the largest rise and the largest fall in each year.",
    )
    row = 4
    for direction in DIRECTIONS:
        info = layout[direction]

        def change_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            before = source_ref(direction, code, year - 1, layout)
            return f"={now}-{before}"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: dollar change by main category ($ Millions)",
            YEARS[1:],
            info["mains"],
            info["names"],
            change_cell,
            MONEY,
        )
        REG[f"change-{direction}"] = (first, info["mains"])

    worksheet.cell(row, 1, "Summary of change points").font = TITLE
    row += 1
    headers = [
        "Year",
        "Export largest rise",
        "Export rise ($ Millions)",
        "Export largest fall",
        "Export fall ($ Millions)",
        "Import largest rise",
        "Import rise ($ Millions)",
        "Import largest fall",
        "Import fall ($ Millions)",
        "Possible cause",
    ]
    for offset, header in enumerate(headers, start=1):
        cell = worksheet.cell(row, offset, header)
        cell.font = HEAD
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    row += 1
    first_summary = row
    for offset, year in enumerate(YEARS[1:]):
        worksheet.cell(row, 1, year)
        column = 2
        for direction in DIRECTIONS:
            change_first, change_codes = REG[f"change-{direction}"]
            last_row = change_first + len(change_codes) - 1
            letter = get_column_letter(3 + offset)
            band = f"${letter}${change_first}:${letter}${last_row}"
            names = f"$B${change_first}:$B${last_row}"
            worksheet.cell(
                row, column, f"=INDEX({names},MATCH(MAX({band}),{band},0))"
            )
            rise = worksheet.cell(row, column + 1, f"=MAX({band})")
            rise.number_format = MONEY
            worksheet.cell(
                row, column + 2, f"=INDEX({names},MATCH(MIN({band}),{band},0))"
            )
            fall = worksheet.cell(row, column + 3, f"=MIN({band})")
            fall.number_format = MONEY
            column += 4
        cell = worksheet.cell(row, 10, CAUSES[year])
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        row += 1
    REG["changepoints"] = (first_summary, YEARS[1:])
    set_widths(
        worksheet,
        {"A": 10, "B": 34, "C": 14, "D": 34, "E": 14, "F": 34, "G": 14, "H": 34, "I": 14, "J": 70},
    )
    for column in range(3, 12):
        if get_column_letter(column) not in {"C", "E", "G", "I", "J"}:
            worksheet.column_dimensions[get_column_letter(column)].width = 13
    return worksheet


def build_cat3(workbook, layout):
    worksheet = workbook.create_sheet("Cat3-SubAnalytics")
    worksheet.cell(
        1, 1, "Main category 3 against its subcategories, import and export"
    ).font = TITLE
    worksheet.cell(
        2,
        1,
        "Subcategories 32, 33 and 34 make up main category 3. "
        "Every cause argued from this sheet comes from inside the data.",
    )
    codes = [FOCUS_MAIN] + FOCUS_SUBS
    row = 4
    for direction in DIRECTIONS:
        names = layout[direction]["names"]

        def value_cell(code, year, direction=direction):
            return f"={source_ref(direction, code, year, layout)}"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: value ($ Millions)",
            YEARS,
            codes,
            names,
            value_cell,
            MONEY,
        )
        REG[f"cat3-value-{direction}"] = (first, codes)

        def share_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            main = source_ref(direction, FOCUS_MAIN, year, layout)
            return f"={now}/{main}"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: share of main category 3",
            YEARS,
            codes,
            names,
            share_cell,
            PCT,
        )
        REG[f"cat3-share-{direction}"] = (first, codes)

        def growth_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            before = source_ref(direction, code, year - 1, layout)
            return f"={now}/{before}-1"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: year on year growth",
            YEARS[1:],
            codes,
            names,
            growth_cell,
            PCT,
        )
        REG[f"cat3-growth-{direction}"] = (first, codes)

        def index_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            base = source_ref(direction, code, YEARS[0], layout)
            return f"={now}/{base}*100"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: index (2016 = 100)",
            YEARS,
            codes,
            names,
            index_cell,
            INDEX,
        )
        REG[f"cat3-index-{direction}"] = (first, codes)

        growth_first, growth_codes = REG[f"cat3-growth-{direction}"]
        last_column = get_column_letter(3 + len(YEARS) - 2)
        main_row = growth_first + growth_codes.index(FOCUS_MAIN)

        def correl(code, main_row=main_row, growth_first=growth_first, growth_codes=growth_codes, last_column=last_column):
            target = growth_first + growth_codes.index(code)
            band_a = f"$C${target}:${last_column}${target}"
            band_b = f"$C${main_row}:${last_column}${main_row}"
            return f"=CORREL({band_a},{band_b})"

        row, first = write_columns(
            worksheet,
            row,
            f"{direction}: growth correlation against main category 3",
            ["Correlation with main category 3"],
            codes,
            names,
            [correl],
            [RATIO],
        )
        REG[f"cat3-correl-{direction}"] = (first, codes)

    set_widths(worksheet, {"A": 8, "B": 46})
    for column in range(3, 3 + len(YEARS)):
        worksheet.column_dimensions[get_column_letter(column)].width = 14
    return worksheet


def build_focus(workbook, layout):
    worksheet = workbook.create_sheet("Pet33-Focus")
    name = layout["Export"]["names"][FOCUS_SUB]
    worksheet.cell(1, 1, f"Focus subcategory 33, {name}").font = TITLE
    worksheet.cell(
        2,
        1,
        "One row per year. The insight column reads the change in that year against "
        "the year before it.",
    )
    headers = [
        "Year",
        "Export ($ Millions)",
        "Import ($ Millions)",
        "Balance ($ Millions)",
        "Cover ratio",
        "Export growth",
        "Import growth",
        "Export 3 year average",
        "Import 3 year average",
        "Export growth z-score",
        "Import growth z-score",
        "Insight for the year",
    ]
    row = 4
    for offset, header in enumerate(headers, start=1):
        cell = worksheet.cell(row, offset, header)
        cell.font = HEAD
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    row += 1
    first = row
    for year in YEARS:
        export = source_ref("Export", FOCUS_SUB, year, layout)
        imports = source_ref("Import", FOCUS_SUB, year, layout)
        worksheet.cell(row, 1, year)
        worksheet.cell(row, 2, f"={export}").number_format = MONEY
        worksheet.cell(row, 3, f"={imports}").number_format = MONEY
        worksheet.cell(row, 4, f"={export}-{imports}").number_format = MONEY
        worksheet.cell(row, 5, f"={export}/{imports}").number_format = RATIO
        if year == YEARS[0]:
            worksheet.cell(row, 6, "")
            worksheet.cell(row, 7, "")
        else:
            previous_export = source_ref("Export", FOCUS_SUB, year - 1, layout)
            previous_import = source_ref("Import", FOCUS_SUB, year - 1, layout)
            worksheet.cell(row, 6, f"={export}/{previous_export}-1").number_format = PCT
            worksheet.cell(row, 7, f"={imports}/{previous_import}-1").number_format = PCT
        if year < YEARS[2]:
            worksheet.cell(row, 8, "")
            worksheet.cell(row, 9, "")
        else:
            window_export = ",".join(
                source_ref("Export", FOCUS_SUB, y, layout) for y in range(year - 2, year + 1)
            )
            window_import = ",".join(
                source_ref("Import", FOCUS_SUB, y, layout) for y in range(year - 2, year + 1)
            )
            worksheet.cell(row, 8, f"=AVERAGE({window_export})").number_format = MONEY
            worksheet.cell(row, 9, f"=AVERAGE({window_import})").number_format = MONEY
        cell = worksheet.cell(row, 12, INSIGHTS[year])
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        row += 1
    last = row - 1
    for offset, year in enumerate(YEARS):
        target = first + offset
        if year == YEARS[0]:
            continue
        for column, letter in ((10, "F"), (11, "G")):
            band = f"${letter}${first + 1}:${letter}${last}"
            cell = worksheet.cell(
                target, column, f"=({letter}{target}-AVERAGE({band}))/STDEVP({band})"
            )
            cell.number_format = RATIO
    REG["focus"] = (first, YEARS)
    set_widths(
        worksheet,
        {"A": 8, "B": 14, "C": 14, "D": 14, "E": 11, "F": 12, "G": 12, "H": 14, "I": 14, "J": 12, "K": 12, "L": 82},
    )
    return worksheet


def build_focus_vs_sub(workbook, layout):
    worksheet = workbook.create_sheet("Pet33-vs-Sub")
    worksheet.cell(
        1, 1, "Subcategory 33 against the other subcategories of main category 3"
    ).font = TITLE
    worksheet.cell(
        2,
        1,
        "Petroleum is compared against coal and against gas on levels, on growth "
        "and on correlation, for import and for export.",
    )
    codes = FOCUS_SUBS
    row = 4
    for direction in DIRECTIONS:
        names = layout[direction]["names"]

        def index_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            base = source_ref(direction, code, YEARS[0], layout)
            return f"={now}/{base}*100"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: index (2016 = 100)",
            YEARS,
            codes,
            names,
            index_cell,
            INDEX,
        )
        REG[f"vs-index-{direction}"] = (first, codes)

        def growth_cell(code, year, direction=direction):
            now = source_ref(direction, code, year, layout)
            before = source_ref(direction, code, year - 1, layout)
            return f"={now}/{before}-1"

        row, first = write_block(
            worksheet,
            row,
            f"{direction}: year on year growth",
            YEARS[1:],
            codes,
            names,
            growth_cell,
            PCT,
        )
        REG[f"vs-growth-{direction}"] = (first, codes)

    worksheet.cell(row, 1, "Pairwise growth correlation").font = TITLE
    row += 1
    worksheet.cell(row, 1, "Pair").font = HEAD
    worksheet.cell(row, 1).fill = HEAD_FILL
    for offset, direction in enumerate(DIRECTIONS):
        cell = worksheet.cell(row, 2 + offset, f"{direction} correlation")
        cell.font = HEAD
        cell.fill = HEAD_FILL
    cell = worksheet.cell(row, 4, "Import against export of subcategory 33")
    cell.font = HEAD
    cell.fill = HEAD_FILL
    row += 1
    first_pairs = row
    last_column = get_column_letter(3 + len(YEARS) - 2)
    pairs = [(FOCUS_SUB, "32"), (FOCUS_SUB, "34"), ("32", "34")]
    for left_code, right_code in pairs:
        label = f"{left_code} against {right_code}"
        worksheet.cell(row, 1, label)
        for offset, direction in enumerate(DIRECTIONS):
            growth_first, growth_codes = REG[f"vs-growth-{direction}"]
            left = growth_first + growth_codes.index(left_code)
            right = growth_first + growth_codes.index(right_code)
            band_a = f"$C${left}:${last_column}${left}"
            band_b = f"$C${right}:${last_column}${right}"
            cell = worksheet.cell(row, 2 + offset, f"=CORREL({band_a},{band_b})")
            cell.number_format = RATIO
        row += 1
    export_first, export_codes = REG["vs-growth-Export"]
    import_first, import_codes = REG["vs-growth-Import"]
    export_row = export_first + export_codes.index(FOCUS_SUB)
    import_row = import_first + import_codes.index(FOCUS_SUB)
    cell = worksheet.cell(
        first_pairs,
        4,
        f"=CORREL($C${export_row}:${last_column}${export_row},"
        f"$C${import_row}:${last_column}${import_row})",
    )
    cell.number_format = RATIO
    REG["vs-pairs"] = (first_pairs, pairs)
    set_widths(worksheet, {"A": 30, "B": 22, "C": 22, "D": 34})
    for column in range(3, 3 + len(YEARS)):
        if column > 4:
            worksheet.column_dimensions[get_column_letter(column)].width = 14
    return worksheet


def build_forecast(workbook, layout):
    worksheet = workbook.create_sheet("Pet33-Forecast")
    worksheet.cell(1, 1, "Subcategory 33 import, ten year trend and five year forecast").font = TITLE
    worksheet.cell(
        2,
        1,
        "Two forecast methods, both live formulas. The linear trend fits a straight line "
        "to 2016 to 2025. The CAGR method grows the 2025 value at the decade rate.",
    )
    headers = [
        "Year",
        "Actual import ($ Millions)",
        "Linear trend forecast ($ Millions)",
        "CAGR forecast ($ Millions)",
        "Target path ($ Millions)",
        "Linear forecast less target ($ Millions)",
    ]
    row = 4
    for offset, header in enumerate(headers, start=1):
        cell = worksheet.cell(row, offset, header)
        cell.font = HEAD
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    row += 1
    first = row
    for year in YEARS:
        worksheet.cell(row, 1, year)
        cell = worksheet.cell(row, 2, f"={source_ref('Import', FOCUS_SUB, year, layout)}")
        cell.number_format = MONEY
        row += 1
    last_actual = row - 1
    actual_band = f"$B${first}:$B${last_actual}"
    base_cell = f"$B${first}"
    final_cell = f"$B${last_actual}"
    span = YEARS[-1] - YEARS[0]
    first_forecast = row
    for year in FORECAST_YEARS:
        worksheet.cell(row, 1, year)
        linear = worksheet.cell(
            row, 3, f"=FORECAST(A{row},{actual_band},{key_years_ref()})"
        )
        linear.number_format = MONEY
        cagr = worksheet.cell(
            row,
            4,
            f"={final_cell}*POWER(POWER({final_cell}/{base_cell},1/{span}),A{row}-{YEARS[-1]})",
        )
        cagr.number_format = MONEY
        target = worksheet.cell(
            row, 5, f"={final_cell}*POWER(1-{TARGET_RATE},A{row}-{YEARS[-1]})"
        )
        target.number_format = MONEY
        gap = worksheet.cell(row, 6, f"=C{row}-E{row}")
        gap.number_format = MONEY
        row += 1
    last_forecast = row - 1
    REG["forecast"] = (first, YEARS + FORECAST_YEARS)
    REG["forecast-rows"] = (first, last_actual, first_forecast, last_forecast)

    row += 1
    worksheet.cell(row, 1, "Ten year outcome and the five year target").font = TITLE
    row += 1
    summary = [
        ("Import 2016 ($ Millions)", f"={base_cell}", MONEY),
        ("Import 2025 ($ Millions)", f"={final_cell}", MONEY),
        ("Change 2016 to 2025 ($ Millions)", f"={final_cell}-{base_cell}", MONEY),
        ("Change 2016 to 2025 (percent)", f"={final_cell}/{base_cell}-1", PCT),
        ("Import CAGR 2016 to 2025", f"=POWER({final_cell}/{base_cell},1/{span})-1", PCT),
        (
            "Linear trend slope ($ Millions per year)",
            f"=SLOPE({actual_band},{key_years_ref()})",
            MONEY,
        ),
        (
            "Linear trend R squared",
            f"=RSQ({actual_band},{key_years_ref()})",
            RATIO,
        ),
        (
            "Balance 2016 ($ Millions)",
            f"={source_ref('Export', FOCUS_SUB, YEARS[0], layout)}-{source_ref('Import', FOCUS_SUB, YEARS[0], layout)}",
            MONEY,
        ),
        (
            "Balance 2025 ($ Millions)",
            f"={source_ref('Export', FOCUS_SUB, YEARS[-1], layout)}-{source_ref('Import', FOCUS_SUB, YEARS[-1], layout)}",
            MONEY,
        ),
        ("Target reduction rate each year", f"={TARGET_RATE}", PCT),
        ("Target import 2030 ($ Millions)", f"=E{last_forecast}", MONEY),
        (
            "Linear forecast 2030 less target ($ Millions)",
            f"=F{last_forecast}",
            MONEY,
        ),
    ]
    first_summary = row
    for label, formula, fmt in summary:
        worksheet.cell(row, 1, label).font = BOLD
        cell = worksheet.cell(row, 2, formula)
        cell.number_format = fmt
        row += 1
    REG["forecast-summary"] = (first_summary, [label for label, _, _ in summary])
    set_widths(worksheet, {"A": 44, "B": 20, "C": 22, "D": 20, "E": 20, "F": 26})
    return worksheet


def build_backtest(workbook, layout):
    worksheet = workbook.create_sheet("Pet33-Backtest")
    worksheet.cell(1, 1, "Backtest of the forecast methods on subcategory 33 import").font = TITLE
    worksheet.cell(
        2,
        1,
        "Each method is fitted on 2016 to 2021 only, then asked to predict 2022 to 2025, "
        "which it has not seen. The recent window method copies the approach the AI chose.",
    )
    headers = [
        "Year",
        "Actual ($ Millions)",
        "Linear trend fitted to 2016-2021",
        "CAGR method fitted to 2016-2021",
        "Recent window method, the AI approach",
        "Linear error",
        "CAGR error",
        "Recent window error",
    ]
    row = 4
    for offset, header in enumerate(headers, start=1):
        cell = worksheet.cell(row, offset, header)
        cell.font = HEAD
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    row += 1
    first = row
    train_last_year = 2021
    for year in YEARS:
        worksheet.cell(row, 1, year)
        cell = worksheet.cell(row, 2, f"={source_ref('Import', FOCUS_SUB, year, layout)}")
        cell.number_format = MONEY
        row += 1
    train_rows = (first, first + (train_last_year - YEARS[0]))
    train_band = f"$B${train_rows[0]}:$B${train_rows[1]}"
    train_years = f"'Keys'!$B$3:$B${3 + (train_last_year - YEARS[0])}"
    base = f"$B${train_rows[0]}"
    final = f"$B${train_rows[1]}"
    span = train_last_year - YEARS[0]
    window_start = f"$B${train_rows[1] - 3}"
    for offset, year in enumerate(YEARS):
        if year <= train_last_year:
            continue
        target = first + offset
        step = year - train_last_year
        linear = worksheet.cell(
            target, 3, f"=FORECAST(A{target},{train_band},{train_years})"
        )
        linear.number_format = MONEY
        cagr = worksheet.cell(
            target,
            4,
            f"={final}*POWER(POWER({final}/{base},1/{span}),{step})",
        )
        cagr.number_format = MONEY
        recent = worksheet.cell(
            target, 5, f"={final}+(({final}-{window_start})/3)*{step}"
        )
        recent.number_format = MONEY
        for column, source in ((6, "C"), (7, "D"), (8, "E")):
            error = worksheet.cell(
                target, column, f"=ABS({source}{target}-B{target})/B{target}"
            )
            error.number_format = PCT
    last = first + len(YEARS) - 1
    row = last + 2
    worksheet.cell(row, 1, "Mean absolute percentage error, 2022 to 2025").font = BOLD
    for column, letter in ((6, "F"), (7, "G"), (8, "H")):
        cell = worksheet.cell(
            row, column, f"=AVERAGE({letter}{train_rows[1] + 1}:{letter}{last})"
        )
        cell.number_format = PCT
        cell.font = BOLD
    REG["backtest"] = (first, YEARS)
    REG["backtest-mape"] = (row, ["linear", "cagr", "recent"])
    set_widths(
        worksheet,
        {"A": 8, "B": 16, "C": 20, "D": 20, "E": 22, "F": 14, "G": 14, "H": 18},
    )
    return worksheet


def read_ai_forecast():
    path = ROOT / "data" / "ai_forecast.csv"
    if not path.exists():
        return {}
    with path.open() as handle:
        return {int(r["year"]): float(r["value"]) for r in csv.DictReader(handle)}


def build_ai_comparison(workbook):
    worksheet = workbook.create_sheet("AI-Comparison")
    worksheet.cell(1, 1, "My forecast against the AI forecast, subcategory 33 import").font = TITLE
    ai = read_ai_forecast()
    note = (
        "The AI received the ten annual values and nothing else. "
        "It saw none of this analysis."
        if ai
        else "Waiting for the AI run. Rebuild this workbook after ai_forecast.py writes data/ai_forecast.csv."
    )
    worksheet.cell(2, 1, note)
    headers = [
        "Year",
        "My linear trend ($ Millions)",
        "My CAGR method ($ Millions)",
        "AI forecast ($ Millions)",
        "AI less my linear trend ($ Millions)",
        "AI less my linear trend (percent)",
    ]
    row = 4
    for offset, header in enumerate(headers, start=1):
        cell = worksheet.cell(row, offset, header)
        cell.font = HEAD
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    row += 1
    first = row
    _, _, first_forecast, _ = REG["forecast-rows"]
    for offset, year in enumerate(FORECAST_YEARS):
        source_row = first_forecast + offset
        worksheet.cell(row, 1, year)
        worksheet.cell(row, 2, f"='Pet33-Forecast'!C{source_row}").number_format = MONEY
        worksheet.cell(row, 3, f"='Pet33-Forecast'!D{source_row}").number_format = MONEY
        if year in ai:
            worksheet.cell(row, 4, ai[year]).number_format = MONEY
            worksheet.cell(row, 5, f"=D{row}-B{row}").number_format = MONEY
            worksheet.cell(row, 6, f"=IFERROR(D{row}/B{row}-1,\"\")").number_format = PCT
        row += 1
    REG["ai"] = (first, FORECAST_YEARS)
    set_widths(worksheet, {"A": 10, "B": 24, "C": 24, "D": 22, "E": 28, "F": 28})
    return worksheet


SHEET_NOTES = [
    ("Keys", "Numeric year keys that the trend and forecast formulas read."),
    ("Export-dataset", "The source export data, copied without any change."),
    ("Import-dataset", "The source import data, copied without any change."),
    ("Export-tidy", "The export data in long format, one row per category and year."),
    ("Import-tidy", "The import data in long format, one row per category and year."),
    ("Main-Analytics", "Growth, index, share, CAGR and growth contribution for the 10 main categories."),
    ("Main-Stats", "Mean, median, spread, trend and the outlier z-score for the 10 main categories."),
    ("Balance", "Export minus import, and the cover ratio, by main category."),
    ("Correlation", "How the main categories move against each other."),
    ("ChangePoints", "The largest rise and the largest fall in each year, with a possible cause."),
    ("Cat3-SubAnalytics", "Main category 3 against subcategories 32, 33 and 34."),
    ("Pet33-Focus", "The focus subcategory, one row per year, with an insight for each year."),
    ("Pet33-vs-Sub", "Subcategory 33 against coal and gas, on index, growth and correlation."),
    ("Pet33-Forecast", "The ten year trend and the five year forecast, with the target path."),
    ("Pet33-Backtest", "Each forecast method fitted to 2016 to 2021, then tested against 2022 to 2025."),
    ("AI-Comparison", "My forecast against the AI forecast."),
]


def build_readme(workbook, chart_notes, pages_url):
    worksheet = workbook.create_sheet("README", 0)
    worksheet.cell(1, 1, "Australian International Trade, 2016 to 2025").font = Font(
        bold=True, size=16, color="1F3864"
    )
    worksheet.cell(2, 1, "32146 Visual Analytics, Assessment Task 3. Student 24503993.")
    worksheet.cell(4, 1, "How to read this workbook").font = TITLE
    lines = [
        "Every number in the analysis sheets is a live formula. The two dataset sheets hold the source data and no formula.",
        "All money values are in $ Millions, which is the unit the source uses.",
        "The focus main category is 3, Mineral fuels, lubricants and related materials.",
        "The focus subcategory is 33, Petroleum, petroleum products and related materials.",
        "Growth, share and CAGR columns are fractions shown as percentages.",
        "The dashboard and the storyboard read this workbook, so a change here changes the charts.",
    ]
    row = 5
    for line in lines:
        worksheet.cell(row, 1, line)
        row += 1
    row += 1
    worksheet.cell(row, 1, "The dashboard and the storyboard").font = TITLE
    row += 1
    worksheet.cell(row, 1, pages_url)
    row += 2
    worksheet.cell(row, 1, "Sheets").font = TITLE
    row += 1
    worksheet.cell(row, 1, "Sheet").font = HEAD
    worksheet.cell(row, 1).fill = HEAD_FILL
    worksheet.cell(row, 2, "What it holds").font = HEAD
    worksheet.cell(row, 2).fill = HEAD_FILL
    row += 1
    for name, note in SHEET_NOTES + chart_notes:
        worksheet.cell(row, 1, name)
        worksheet.cell(row, 2, note)
        row += 1
    set_widths(worksheet, {"A": 24, "B": 104})
    return worksheet


def style_axes(chart, x_title, y_title):
    chart.x_axis.title = x_title
    chart.y_axis.title = y_title
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.height = 11
    chart.width = 26


def row_series_chart(
    workbook, sheet_name, anchor, title, y_title, source_sheet, block, year_count, kind="line"
):
    first, codes = REG[block]
    source = workbook[source_sheet]
    chart = LineChart() if kind == "line" else BarChart()
    if kind == "bar":
        chart.type = "col"
    chart.title = title
    style_axes(chart, "Year", y_title)
    data = Reference(
        source,
        min_col=2,
        max_col=2 + year_count,
        min_row=first,
        max_row=first + len(codes) - 1,
    )
    chart.add_data(data, titles_from_data=True, from_rows=True)
    categories = Reference(
        source, min_col=3, max_col=2 + year_count, min_row=first - 1, max_row=first - 1
    )
    chart.set_categories(categories)
    workbook[sheet_name].add_chart(chart, anchor)


def column_series_chart(
    workbook, sheet_name, anchor, title, y_title, source_sheet, first, last, columns, kind="line"
):
    source = workbook[source_sheet]
    chart = LineChart() if kind == "line" else BarChart()
    if kind == "bar":
        chart.type = "col"
    chart.title = title
    style_axes(chart, "Year", y_title)
    for column in columns:
        data = Reference(source, min_col=column, max_col=column, min_row=first - 1, max_row=last)
        chart.add_data(data, titles_from_data=True)
    categories = Reference(source, min_col=1, max_col=1, min_row=first, max_row=last)
    chart.set_categories(categories)
    workbook[sheet_name].add_chart(chart, anchor)


CHART_SHEETS = [
    ("Chart-Main-Value", "Raw dollar value trends for all 10 main categories, import and export."),
    ("Chart-Main-Index", "Analytical trends. The same 10 categories indexed to 2016."),
    ("Chart-Main-Share", "Analytical trends. Each category as a share of the direction total."),
    ("Chart-Main-Stats", "Statistical trends. The outlier z-score of growth for all 10 categories."),
    ("Chart-Balance", "Trade balance by main category, and the all category total."),
    ("Chart-Cat3", "Main category 3 against subcategories 32, 33 and 34."),
    ("Chart-Pet33", "The focus subcategory. Export against import, the balance, and the forecast."),
]


def build_charts(workbook):
    for name, _ in CHART_SHEETS:
        workbook.create_sheet(name)
    years = len(YEARS)
    growth_years = years - 1

    row_series_chart(
        workbook, "Chart-Main-Value", "A1",
        "Export by main category, 2016 to 2025", "$ Millions",
        "Main-Analytics", "value-Export", years,
    )
    row_series_chart(
        workbook, "Chart-Main-Value", "A24",
        "Import by main category, 2016 to 2025", "$ Millions",
        "Main-Analytics", "value-Import", years,
    )
    row_series_chart(
        workbook, "Chart-Main-Index", "A1",
        "Export by main category, index 2016 = 100", "Index (2016 = 100)",
        "Main-Analytics", "index-Export", years,
    )
    row_series_chart(
        workbook, "Chart-Main-Index", "A24",
        "Import by main category, index 2016 = 100", "Index (2016 = 100)",
        "Main-Analytics", "index-Import", years,
    )
    row_series_chart(
        workbook, "Chart-Main-Share", "A1",
        "Export share of total by main category", "Share of export total",
        "Main-Analytics", "share-Export", years,
    )
    row_series_chart(
        workbook, "Chart-Main-Share", "A24",
        "Import share of total by main category", "Share of import total",
        "Main-Analytics", "share-Import", years,
    )
    row_series_chart(
        workbook, "Chart-Main-Stats", "A1",
        "Export growth outlier z-score by main category", "Z-score of year on year growth",
        "Main-Stats", "zscore-Export", growth_years, kind="bar",
    )
    row_series_chart(
        workbook, "Chart-Main-Stats", "A24",
        "Import growth outlier z-score by main category", "Z-score of year on year growth",
        "Main-Stats", "zscore-Import", growth_years, kind="bar",
    )
    row_series_chart(
        workbook, "Chart-Balance", "A1",
        "Trade balance by main category, export minus import", "$ Millions",
        "Balance", "balance", years,
    )
    row_series_chart(
        workbook, "Chart-Balance", "A24",
        "Cover ratio by main category, export divided by import", "Cover ratio",
        "Balance", "cover", years,
    )
    row_series_chart(
        workbook, "Chart-Cat3", "A1",
        "Main category 3 and its subcategories, export", "$ Millions",
        "Cat3-SubAnalytics", "cat3-value-Export", years,
    )
    row_series_chart(
        workbook, "Chart-Cat3", "A24",
        "Main category 3 and its subcategories, import", "$ Millions",
        "Cat3-SubAnalytics", "cat3-value-Import", years,
    )
    row_series_chart(
        workbook, "Chart-Cat3", "A47",
        "Subcategory share of main category 3, export", "Share of main category 3",
        "Cat3-SubAnalytics", "cat3-share-Export", years,
    )
    row_series_chart(
        workbook, "Chart-Cat3", "A70",
        "Subcategory share of main category 3, import", "Share of main category 3",
        "Cat3-SubAnalytics", "cat3-share-Import", years,
    )

    focus_first, focus_years = REG["focus"]
    focus_last = focus_first + len(focus_years) - 1
    column_series_chart(
        workbook, "Chart-Pet33", "A1",
        "Subcategory 33 petroleum, export against import", "$ Millions",
        "Pet33-Focus", focus_first, focus_last, [2, 3],
    )
    column_series_chart(
        workbook, "Chart-Pet33", "A24",
        "Subcategory 33 petroleum, trade balance", "$ Millions",
        "Pet33-Focus", focus_first, focus_last, [4], kind="bar",
    )
    row_series_chart(
        workbook, "Chart-Pet33", "A47",
        "Petroleum against coal and gas, export index 2016 = 100", "Index (2016 = 100)",
        "Pet33-vs-Sub", "vs-index-Export", years,
    )
    row_series_chart(
        workbook, "Chart-Pet33", "A70",
        "Petroleum against coal and gas, import index 2016 = 100", "Index (2016 = 100)",
        "Pet33-vs-Sub", "vs-index-Import", years,
    )
    forecast_first, _, _, forecast_last = REG["forecast-rows"]
    column_series_chart(
        workbook, "Chart-Pet33", "A93",
        "Subcategory 33 import, actual, forecast and target", "$ Millions",
        "Pet33-Forecast", forecast_first, forecast_last, [2, 3, 4, 5],
    )
    return CHART_SHEETS


PAGES_URL = "Dashboard and storyboard: https://toms55.github.io/DataVisA3/"


def main():
    layout = read_source()
    workbook = Workbook()
    workbook.remove(workbook.active)
    build_keys(workbook)
    copy_source(workbook, layout)
    build_tidy(workbook, layout)
    build_main_analytics(workbook, layout)
    build_main_stats(workbook, layout)
    build_balance(workbook, layout)
    build_correlation(workbook, layout)
    build_change_points(workbook, layout)
    build_cat3(workbook, layout)
    build_focus(workbook, layout)
    build_focus_vs_sub(workbook, layout)
    build_forecast(workbook, layout)
    build_backtest(workbook, layout)
    build_ai_comparison(workbook)
    chart_notes = build_charts(workbook)
    build_readme(workbook, list(chart_notes), PAGES_URL)
    TARGET.parent.mkdir(exist_ok=True)
    workbook.save(TARGET)
    print(f"wrote {TARGET.relative_to(ROOT)} with {len(workbook.sheetnames)} sheets")
    print("sheets:", ", ".join(workbook.sheetnames))


if __name__ == "__main__":
    main()
