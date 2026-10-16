import page
import read_workbook as rw
from layout import ROOT

OUT = ROOT / "docs" / "index.html"

INTRO = (
    "Australian International Trade from 2016 to 2025, built for readers in public policy and "
    "government. Ten main categories, 67 subcategories, import and export, in millions of "
    "Australian dollars."
)


def money(value):
    return f"{value:,.0f}"


def main():
    page.reset()
    totals_export = rw.totals("Export")
    totals_import = rw.totals("Import")
    summary = rw.forecast_summary()
    balance_2025 = totals_export[2025] - totals_import[2025]
    balance_2022 = totals_export[2022] - totals_import[2022]

    out = page.head(
        "Australian International Trade 2016 to 2025",
        "Dashboard and storyboard for Australian International Trade, 2016 to 2025, focused on petroleum.",
    )
    out += page.nav("index.html")
    out += page.header(
        "32146 Visual Analytics, assessment task 3",
        "Australian International Trade, 2016 to 2025",
        INTRO,
    )
    out += page.kpi_row(
        [
            page.kpi("Total export 2025", f"${money(totals_export[2025])}m", "Peaked at $593,865m in 2022", "export"),
            page.kpi("Total import 2025", f"${money(totals_import[2025])}m", "Rose every year after 2020", "import"),
            page.kpi("Trade balance 2025", f"${money(balance_2025)}m", f"Down 65% from ${money(balance_2022)}m in 2022", "focus"),
            page.kpi("Petroleum balance 2025", f"-${money(abs(summary['Balance 2025 ($ Millions)']))}m", "Negative in all ten years", "negative"),
        ]
    )
    out += page.panel(
        "Start here",
        None,
        """
<a class="cta" href="dashboard.html">
<span class="go">Click here to see the dashboard &rarr;</span>
<span class="why">It covers one subcategory on a single screen, with five comparisons, an insight
for every one of the ten years, and a year range control to narrow the window. Use it to look
something up in any order.</span>
</a>
<a class="cta" href="storyboard.html">
<span class="go">Click here to view the storyboard &rarr;</span>
<span class="why">It runs thirteen panels in a fixed order, from total Australian trade down to
subcategory 33. Use it to be walked through the argument. Read it top to bottom.</span>
</a>
<p style="margin:14px 0 0;color:var(--secondary);max-width:80ch">
Both pages read the same Excel workbook, <code>24503993_A3.xlsx</code>. Every analytical and
statistical pattern lives in that workbook as a live formula. These pages display those numbers
and do not recompute them.
</p>
""",
    )
    out += page.panel(
        "The focus of this study",
        None,
        """
<p style="margin:0 0 14px;color:var(--secondary);max-width:80ch">
<strong>Main category 3</strong>, mineral fuels, lubricants and related materials, is the largest
mover in seven of the nine year transitions in the dataset. It sets the direction of the decade.
</p>
<p style="margin:0 0 14px;color:var(--secondary);max-width:80ch">
<strong>Subcategory 33</strong>, petroleum, petroleum products and related materials, is the focus.
It is the only large part of Australian trade where the country buys far more than it sells. Export
doubled across the decade and import more than doubled, so the gap between them widened from
$16,369m to $38,555m.
</p>
<p style="margin:0;color:var(--secondary);max-width:80ch">
Reading the charts: <strong style="color:var(--export)">blue marks export</strong> and
<strong style="color:var(--import)">orange marks import</strong> on every chart on both pages.
Hover any chart for exact values. Each chart has a "Show the numbers" panel underneath with the
table behind it.
</p>
""",
    )
    out += page.footer()
    out += page.TAIL
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
