import charts
import page
import read_workbook as rw
from layout import DIRECTIONS, ROOT, YEARS

OUT = ROOT / "docs" / "dashboard.html"

INTRO = (
    "One subcategory, examined in both trade directions. Subcategory 33 is the only large "
    "part of Australian trade where the country buys far more than it sells. Every chart "
    "below reads the Excel workbook, and every axis carries its unit."
)


def money(value):
    return f"{value:,.0f}"


def kpis(rows, summary):
    last = rows[-1]
    first = rows[0]
    export_cagr = (last["export"] / first["export"]) ** (1 / 9) - 1
    import_cagr = (last["import"] / first["import"]) ** (1 / 9) - 1
    return page.kpi_row(
        [
            page.kpi("Export 2025", f"${money(last['export'])}m", "Up from $6,946m in 2016", "export"),
            page.kpi("Import 2025", f"${money(last['import'])}m", "Up from $23,315m in 2016", "import"),
            page.kpi("Trade balance 2025", f"-${money(abs(last['balance']))}m", "Negative in all ten years", "negative"),
            page.kpi("Cover ratio 2025", f"{last['cover']:.2f}", "Export buys 27 cents of each import dollar", "focus"),
            page.kpi("Export growth a year", f"{export_cagr:.1%}", "Compound, 2016 to 2025", "export"),
            page.kpi("Import growth a year", f"{import_cagr:.1%}", "Compound, 2016 to 2025", "import"),
        ]
    )


def focus_table(rows):
    body = [
        [
            r["year"],
            money(r["export"]),
            money(r["import"]),
            money(r["balance"]),
            f"{r['cover']:.2f}",
            "" if r["export_growth"] is None else f"{r['export_growth']:.1%}",
            "" if r["import_growth"] is None else f"{r['import_growth']:.1%}",
        ]
        for r in rows
    ]
    return page.table(
        "Subcategory 33 petroleum, every year. Values in $ Millions.",
        ["Year", "Export", "Import", "Balance", "Cover ratio", "Export growth", "Import growth"],
        body,
    )


def subcategory_table():
    names, export_index = rw.vs_index("Export")
    _, import_index = rw.vs_index("Import")
    body = []
    for code in export_index:
        body.append(
            [
                f"{code} {names[code]}",
                f"{export_index[code][-1]:,.0f}",
                f"{import_index[code][-1]:,.0f}",
            ]
        )
    return page.table(
        "Index of each subcategory in 2025, with 2016 set to 100.",
        ["Subcategory", "Export index 2025", "Import index 2025"],
        body,
        summary="Show the index numbers behind this chart",
    )


def share_table():
    body = []
    for direction in DIRECTIONS:
        _, share = rw.cat3_share(direction)
        body.append(
            [
                f"Petroleum share of category 3, {direction.lower()}",
                f"{share['33'][0]:.1%}",
                f"{share['33'][-1]:.1%}",
            ]
        )
    return page.table(
        "Petroleum as a share of main category 3.",
        ["Measure", "2016", "2025"],
        body,
        summary="Show the share numbers behind this chart",
    )


def insights(rows):
    items = "".join(
        f'<li><span class="yr">{r["year"]}</span><span class="txt">{r["insight"]}</span></li>'
        for r in rows
    )
    return f'<ul class="insights">{items}</ul>'


def main():
    rows = rw.focus()
    summary = rw.forecast_summary()
    pairs, import_export_r = rw.vs_pairs()
    ratio_2025 = rows[-1]["import"] / rows[-1]["export"]
    _, share_export = rw.cat3_share("Export")
    _, share_import = rw.cat3_share("Import")

    out = page.head(
        "Petroleum dashboard, Australian trade 2016 to 2025",
        "A dashboard for SITC subcategory 33, petroleum, covering Australian import and export from 2016 to 2025.",
    )
    out += page.nav("dashboard.html")
    out += page.header(
        "Assessment task 3, dashboard",
        "Subcategory 33: petroleum, petroleum products and related materials",
        INTRO,
    )
    out += kpis(rows, summary)

    time_charts = ["cmp1", "cmp2", "cmp3", "cmp4a"]
    out += page.year_control(time_charts, YEARS[0], YEARS[-1])

    out += page.panel(
        "Comparison 1. Export against import",
        "Both directions on one scale, in millions of dollars. The gap between the two "
        "lines is the trade deficit.",
        page.figure(charts.focus_export_import(), "cmp1") + focus_table(rows),
        takeaway=(
            "<strong>Import outruns export in every year.</strong> Import grew 126% across the "
            "decade and export grew 104%, so the gap widened even though both sides rose."
        ),
    )

    out += page.panel(
        "Comparison 2. The trade balance",
        "Export minus import, for each year. Every column points down, so Australia bought "
        "more petroleum than it sold in all ten years.",
        page.figure(charts.focus_balance(), "cmp2"),
        takeaway=(
            "<strong>The deficit more than doubled.</strong> It widened from $16,369m in 2016 to "
            "$38,555m in 2025, and reached its worst point of $47,741m in 2022."
        ),
    )

    out += page.panel(
        "Comparison 3. Petroleum against its main category",
        "Petroleum as a share of main category 3, for import and for export. This shows how "
        "much of the energy category the subcategory carries on each side.",
        page.figure(charts.focus_share_of_main(), "cmp3") + share_table(),
        takeaway=(
            f"<strong>The two sides are not alike.</strong> Petroleum is "
            f"{share_export['33'][-1]:.1%} of category 3 export in 2025 and "
            f"{share_import['33'][-1]:.1%} of category 3 import, against "
            f"{share_import['32'][-1]:.1%} for coal and {share_import['34'][-1]:.1%} for gas."
        ),
    )

    out += page.panel(
        "Comparison 4. Petroleum against coal and gas",
        "The three subcategories of main category 3, indexed so that 2016 equals 100. An index "
        "lets subcategories of very different size share one axis.",
        page.figure(charts.focus_vs_subcategories(), "cmp4a") + subcategory_table(),
        takeaway=(
            "<strong>Gas grew fastest on the export side, and coal fell hardest after 2022.</strong> "
            f"Petroleum growth tracks coal at r = {pairs['33 against 32']['Export']:.2f} and gas at "
            f"r = {pairs['33 against 34']['Export']:.2f} on the export side."
        ),
    )

    out += page.panel(
        "Comparison 5. Import against export, year by year",
        "Each point is one year. If the two sides were independent the points would scatter. "
        "They do not.",
        page.figure(charts.focus_scatter(), "cmp5"),
        takeaway=(
            f"<strong>The two directions move together at r = {import_export_r:.2f}.</strong> "
            f"Both sides are priced off the same world oil market, so a price rise lifts import "
            f"and export at once. Because import is {ratio_2025:.2f} times larger, every price "
            "rise widens the deficit."
        ),
    )

    out += page.panel(
        "What happened in each year",
        "One line for every year from 2016 to 2025, read from the workbook.",
        insights(rows),
    )

    out += page.footer()
    out += page.TAIL
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out)
    size = OUT.stat().st_size / 1024 / 1024
    print(f"wrote {OUT.relative_to(ROOT)} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
