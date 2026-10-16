from pathlib import Path

import charts
from layout import ROOT

OUT = ROOT / "build" / "preview"

FIGURES = {
    "01_total_trade": lambda: charts.total_trade(),
    "02_main_value": lambda: charts.main_small_multiples("value"),
    "03_main_index": lambda: charts.main_small_multiples("index"),
    "04_main_statistical": lambda: charts.main_statistical(),
    "05_share_slope": lambda: charts.share_slope(),
    "06_correl_export": lambda: charts.correlation_heatmap("Export"),
    "07_correl_import": lambda: charts.correlation_heatmap("Import"),
    "08_change_points": lambda: charts.change_point_chart(),
    "09_divergence": lambda: charts.divergence_chart(),
    "10_cat3_value": lambda: charts.cat3_subcategories("value"),
    "11_cat3_share": lambda: charts.cat3_subcategories("share"),
    "12_focus_export_import": lambda: charts.focus_export_import(),
    "13_focus_balance": lambda: charts.focus_balance(),
    "14_focus_vs_subs": lambda: charts.focus_vs_subcategories(),
    "15_focus_scatter": lambda: charts.focus_scatter(),
    "16_focus_share": lambda: charts.focus_share_of_main(),
    "17_forecast": lambda: charts.forecast_chart(),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, build in FIGURES.items():
        figure = build()
        width = 1500 if "main_" in name or "share_slope" in name else 1100
        figure.write_image(OUT / f"{name}.png", width=width, scale=2)
        print(f"wrote {name}.png")


if __name__ == "__main__":
    main()
