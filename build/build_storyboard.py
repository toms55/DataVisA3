import charts
import page
import read_workbook as rw
from layout import DIRECTIONS, ROOT, YEARS

OUT = ROOT / "docs" / "storyboard.html"

INTRO = (
    "A story told in order, from the whole of Australian trade down to one subcategory. "
    "Every panel carries both trade directions. Read it top to bottom."
)


def money(value):
    return f"{value:,.0f}"


def change_point_table():
    rows = rw.change_points()
    body = [
        [
            r["year"],
            f"{r['export_rise_name']} ({money(r['export_rise'])})",
            f"{r['export_fall_name']} ({money(r['export_fall'])})",
            f"{r['import_rise_name']} ({money(r['import_rise'])})",
            r["cause"],
        ]
        for r in rows
    ]
    return page.table(
        "The largest mover in each year, with a possible cause. Values in $ Millions.",
        ["Year", "Export largest rise", "Export largest fall", "Import largest rise", "Possible cause"],
        body,
        summary="Show the change point for every year, 2017 to 2025",
    )


def summary_table():
    body = []
    for direction in DIRECTIONS:
        names, values = rw.main_summary(direction)
        for code in values:
            body.append(
                [
                    f"{code} {names[code]}",
                    direction,
                    f"{values[code][0]:.1%}",
                    money(values[code][1]),
                    f"{values[code][2]:.1%}",
                ]
            )
    return page.table(
        "Decade summary for every main category, both directions.",
        ["Main category", "Direction", "CAGR 2016 to 2025", "Contribution to growth", "Share of total growth"],
        body,
        summary="Show the decade summary for all ten main categories",
    )


def stats_table():
    body = []
    for direction in DIRECTIONS:
        names, stats = rw.main_stats(direction)
        for code in stats:
            body.append(
                [
                    f"{code} {names[code]}",
                    direction,
                    money(stats[code][0]),
                    f"{stats[code][3]:.2f}",
                    money(stats[code][7]),
                    f"{stats[code][9]:.2f}",
                ]
            )
    return page.table(
        "Descriptive and trend statistics for every main category.",
        ["Main category", "Direction", "Mean", "Coefficient of variation", "Trend slope a year", "Trend R squared"],
        body,
        summary="Show the statistics for all ten main categories",
    )


def ai_table():
    rows = rw.ai_comparison()
    body = [
        [
            r["year"],
            money(r["linear"]),
            money(r["cagr"]),
            money(r["ai"]),
            money(r["difference"]),
            f"{r['percent']:.1%}",
        ]
        for r in rows
    ]
    return page.table(
        "My two forecasts against the Claude Sonnet 5 forecast. Values in $ Millions.",
        ["Year", "My linear trend", "My CAGR method", "Claude Sonnet 5", "Sonnet less my linear", "Sonnet less my linear, percent"],
        body,
        summary="Show the forecast comparison numbers",
    )


def backtest_table():
    rows, mape = rw.backtest()
    body = []
    for r in rows:
        if r["linear"] is None:
            continue
        body.append(
            [
                r["year"],
                money(r["actual"]),
                money(r["linear"]),
                money(r["cagr"]),
                money(r["recent"]),
                f"{r['linear_error']:.1%}",
                f"{r['cagr_error']:.1%}",
                f"{r['recent_error']:.1%}",
            ]
        )
    body.append(
        [
            "Average error",
            "",
            "",
            "",
            "",
            f"{mape['linear']:.1%}",
            f"{mape['cagr']:.1%}",
            f"{mape['recent']:.1%}",
        ]
    )
    return page.table(
        "Each method was fitted on 2016 to 2021 only, then asked to predict the four years it "
        "had never seen. Values in $ Millions.",
        [
            "Year",
            "Actual",
            "Linear",
            "CAGR",
            "Recent window",
            "Linear error",
            "CAGR error",
            "Recent window error",
        ],
        body,
        summary="Show the backtest numbers",
    )


def ai_prompt():
    log = (ROOT / "data" / "ai_forecast.md").read_text()
    text = log.split("## The prompt, word for word")[1].split("```")[1].strip()
    return page.quote("Show the exact prompt the model received", text)


def main():
    rows = rw.focus()
    summary = rw.forecast_summary()
    pairs, import_export_r = rw.vs_pairs()
    _, backtest_mape = rw.backtest()
    _, correl_export = rw.correlation("Export")
    _, cat3_correl = rw.cat3_correl("Export")
    _, share_export = rw.cat3_share("Export")

    out = page.head(
        "Storyboard, Australian trade 2016 to 2025",
        "A storyboard of Australian international trade from 2016 to 2025, from the ten main categories down to subcategory 33, petroleum.",
    )
    out += page.nav("storyboard.html")
    out += page.header(
        "Assessment task 3, storyboard",
        "From ten main categories down to one subcategory",
        INTRO,
    )

    out += page.panel(
        "1. The surplus that peaked, then faded",
        "Total export, total import and the balance between them.",
        page.figure(charts.total_trade(), "st1"),
        takeaway=(
            "<strong>The record surplus did not last.</strong> The balance grew from $4,124m in "
            "2016 to $176,863m in 2022, then fell 65% to $62,232m by 2025. Export fell back from "
            "its 2022 peak while import kept climbing."
        ),
    )

    out += page.panel(
        "2. Who drove the decade, in raw dollars",
        "All ten main categories, in millions of dollars, for both directions. One panel per "
        "category so that every category is visible at its own scale.",
        page.figure(charts.main_small_multiples("value"), "st2") + summary_table(),
        takeaway=(
            "<strong>Export is concentrated and import is broad.</strong> Categories 2 and 3 carry "
            "most of the export story. On the import side category 7, machinery and transport "
            "equipment, is the largest single block in every year."
        ),
    )

    out += page.panel(
        "3. The same ten categories, indexed to 2016",
        "Setting every category to 100 in 2016 removes size and shows growth rate instead. This "
        "is the analytical view of the same data.",
        page.figure(charts.main_small_multiples("index"), "st3"),
        takeaway=(
            "<strong>Indexing reorders the winners.</strong> Category 4 is tiny in dollars but grew "
            "fastest of all. Category 1, beverages and tobacco, is the only category whose export "
            "ends the decade near where it started."
        ),
    )

    out += page.panel(
        "4. How the shares shifted",
        "Each category as a share of its own direction total, in 2016 and again in 2025.",
        page.figure(charts.share_slope(), "st4"),
        takeaway=(
            "<strong>The import mix barely moved and the export mix did.</strong> Category 2 rose to "
            "34.5% of export. On the import side category 7 held about 41% across the whole decade."
        ),
    )

    out += page.panel(
        "5. The statistical view, size against volatility",
        "The left panel plots average size against the coefficient of variation. The right panel "
        "shows the single most unusual growth year for each category, measured as a z-score.",
        page.figure(charts.main_statistical(), "st5") + stats_table(),
        takeaway=(
            "<strong>2020 and 2022 own the outliers.</strong> On the export side 2020 is the outlier "
            "year for the three manufacturing categories 6, 7 and 8, and 2022 is the outlier for "
            "category 3. Category 9 breaks out in 2025."
        ),
    )

    out += page.panel(
        "6. The change point in every year",
        "For each year from 2017 to 2025, the main category that rose most and the one that fell "
        "most, in both directions.",
        page.figure(charts.change_point_chart(), "st6") + change_point_table(),
        takeaway=(
            "<strong>One category sets the direction of the decade.</strong> Main category 3 is the "
            "largest mover in seven of the nine year transitions, up or down."
        ),
    )

    out += page.panel(
        "7. How the main categories move against each other",
        "The correlation of year on year growth between every pair of main categories, for each "
        "direction. Blue means the pair rises and falls together, red means they move apart.",
        page.figure(charts.correlation_heatmap("Export"), "st7a")
        + page.figure(charts.correlation_heatmap("Import"), "st7b"),
        takeaway=(
            "<strong>The two largest export categories are unrelated.</strong> Category 3 against "
            f"category 2 is r = {correl_export['3']['2']:.2f}, which is effectively zero. Category 3 "
            f"moves instead with category 6 at r = {correl_export['3']['6']:.2f}, because both follow "
            "the same world price cycle."
        ),
    )

    out += page.panel(
        "8. Inside main category 3",
        "Main category 3 and its three subcategories, coal, petroleum and gas, in both directions.",
        page.figure(charts.cat3_subcategories("value"), "st8")
        + page.figure(charts.cat3_subcategories("share"), "st8b"),
        takeaway=(
            "<strong>The export side and the import side are different categories in practice.</strong> "
            f"On export, petroleum is only {share_export['33'][-1]:.0%} of category 3 in 2025, behind "
            "coal and gas. On import, petroleum is almost the whole category. Each subcategory tracks "
            f"its parent closely, petroleum at r = {cat3_correl['33'][0]:.2f}."
        ),
    )

    out += page.panel(
        "9. The 2022 divergence",
        "Coal export growth against main category 2, the category that holds iron ore.",
        page.figure(charts.divergence_chart(), "st9"),
        takeaway=(
            "<strong>This is two price cycles crossing, not one commodity replacing another.</strong> "
            "Coal rose 124% in 2022 while the iron ore category fell. Across the whole decade the "
            "two are only weakly related, so 2022 is a coincidence of timing rather than a rule."
        ),
    )

    out += page.panel(
        "10. The one category Australia buys more than it sells",
        "Subcategory 33, petroleum, on both sides.",
        page.figure(charts.focus_export_import(), "st10"),
        takeaway=(
            "<strong>Petroleum is the mirror image of the rest of Australian trade.</strong> Import "
            "reached $52,742m in 2025 against export of $14,187m. The deficit widened from $16,369m "
            "in 2016 to $38,555m in 2025."
        ),
    )

    out += page.panel(
        "11. Why the gap keeps widening",
        "Each point is one year, with petroleum export on one axis and petroleum import on the other.",
        page.figure(charts.focus_scatter(), "st11"),
        takeaway=(
            f"<strong>The two sides move together at r = {import_export_r:.2f}.</strong> Both are "
            "priced off the same world oil market. Because import is about three times larger than "
            "export, any price rise widens the deficit instead of closing it. Two refinery closures "
            "in 2021 shifted the mix of what Australia imports from crude towards refined product."
        ),
    )

    out += page.panel(
        "12. Ten years back, five years forward",
        "Petroleum import, the ten actual years and the five forecast years, with the target path.",
        page.figure(charts.forecast_chart(), "st12"),
        takeaway=(
            f"<strong>Across ten years Australia lost ground.</strong> Petroleum import rose "
            f"${money(summary['Change 2016 to 2025 ($ Millions)'])}m, a rise of "
            f"{summary['Change 2016 to 2025 (percent)']:.0%}. The target path cuts import 3% a year "
            f"to ${money(summary['Target import 2030 ($ Millions)'])}m by 2030. The straight line fit "
            f"has an R squared of only {summary['Linear trend R squared']:.2f}, so the forecast is a "
            "wide band and not a precise number."
        ),
    )

    out += page.panel(
        "13. What Claude Sonnet 5 saw, and what it missed",
        "Claude Sonnet 5, model id claude-sonnet-5, received the ten annual import values and nothing "
        "else. It saw no part of "
        "this analysis, no export data, no change point work and no target. The question was the "
        "same one this storyboard answers in panel 12. The answers point in opposite directions, "
        "so this panel tests both of them.",
        ai_prompt()
        + ai_table()
        + page.notes(
            "Why the two answers disagree",
            [
                "The model fitted the last four years. It took the fall from the 2022 peak and "
                "continued it, which gives an average fall of about $4,113m a year.",
                "This analysis fitted all ten years. Over ten years the series rises, so the same "
                "data read over a longer window points up instead of down.",
                "Neither choice is wrong on its face. The window is the whole argument, and the "
                "model stated its window plainly, which is what made the disagreement checkable.",
            ],
        )
        + page.figure(charts.backtest_chart(), "st13")
        + backtest_table()
        + page.notes(
            "What Claude Sonnet 5 could not know",
            [
                "The 2020 dip and the 2022 peak are price events, not demand events. Petroleum "
                f"import and export move together at r = {import_export_r:.2f}, which only the two "
                "way data shows. The model received the import side alone.",
                "Two Australian refineries closed in 2020 and 2021. That cut domestic refining "
                "capacity, raised the refined product share of imports and put a floor under the "
                "volume. No part of that is visible in ten annual totals.",
                "The ten year linear fit has an R squared of "
                f"{summary['Linear trend R squared']:.2f}. The series is too noisy for a confident "
                "five year forecast. The model gave five exact numbers and no error range, which "
                "reads as more certain than the data allows.",
            ],
        ),
        takeaway=(
            "<strong>The backtest says the Claude Sonnet 5 method was the worst of the three, and that all "
            "three failed.</strong> Fitted on 2016 to 2021 and asked for 2022 to 2025, the recent "
            f"window method the model used was out by {backtest_mape['recent']:.1%} on average, "
            f"against {backtest_mape['cagr']:.1%} for CAGR and "
            f"{backtest_mape['linear']:.1%} for the linear trend. Every method missed low, because "
            "the 2022 price shock cannot be inferred from the years before it. That is the real "
            "finding. A five year point forecast of a world priced commodity is a guess whoever "
            "makes it, so the target path in panel 12 is worth more than any of these lines, "
            "because a target is a decision and a forecast is only a guess."
        ),
    )

    out += page.footer()
    out += page.TAIL
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
