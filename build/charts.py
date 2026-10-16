import plotly.graph_objects as go
from plotly.subplots import make_subplots

import read_workbook as rw
import theme
from layout import DIRECTIONS, FORECAST_YEARS, YEARS

MONEY_HOVER = "%{y:,.0f}"


def money(value):
    return f"{value:,.0f}"


def short_name(name, limit=34):
    if name is None:
        return ""
    return name if len(name) <= limit else name[: limit - 1] + "…"


def apply(figure, title, x_title, y_title, height=420, legend=True):
    figure.update_layout(**theme.layout(title, x_title, y_title, height, legend))
    return figure


def total_trade():
    totals = {d: rw.totals(d) for d in DIRECTIONS}
    balance = [totals["Export"][y] - totals["Import"][y] for y in YEARS]
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.13,
        subplot_titles=(
            "Total export and total import",
            "Trade balance, export minus import",
        ),
    )
    for direction in DIRECTIONS:
        figure.add_trace(
            go.Scatter(
                x=YEARS,
                y=[totals[direction][y] for y in YEARS],
                name=direction,
                mode="lines+markers",
                line={"color": theme.DIRECTION_COLOUR[direction], "width": 2},
                marker={"size": 8},
                hovertemplate=f"{direction} %{{y:,.0f}}<extra></extra>",
            ),
            row=1,
            col=1,
        )
    figure.add_trace(
        go.Bar(
            x=YEARS,
            y=balance,
            name="Trade balance",
            marker={"color": [theme.POSITIVE if v >= 0 else theme.NEGATIVE for v in balance]},
            hovertemplate="Balance %{y:,.0f}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    apply(figure, "Australian trade, 2016 to 2025", "Year", "$ Millions", height=640)
    figure.update_yaxes(**theme.axis("$ Millions"), row=1, col=1)
    figure.update_yaxes(**theme.axis("$ Millions"), row=2, col=1)
    figure.update_xaxes(**theme.axis(""), row=1, col=1)
    figure.update_xaxes(**theme.axis("Year"), row=2, col=1)
    figure.update_annotations(font={"size": 13, "color": theme.LIGHT["secondary"]})
    return figure


def main_small_multiples(metric):
    if metric == "value":
        reader = rw.main_values
        y_title = "$ Millions"
        title = "Raw dollar value trend, every main category, import and export"
    elif metric == "index":
        reader = rw.main_index
        y_title = "Index (2016 = 100)"
        title = "Analytical trend, every main category indexed to 2016, import and export"
    else:
        raise SystemExit(f"unknown metric {metric}")
    data = {d: reader(d) for d in DIRECTIONS}
    names, _ = data["Export"]
    codes = list(names)
    figure = make_subplots(
        rows=2,
        cols=5,
        shared_xaxes=True,
        vertical_spacing=0.17,
        horizontal_spacing=0.05,
        subplot_titles=[f"{c} {short_name(names[c], 26)}" for c in codes],
    )
    for position, code in enumerate(codes):
        row = position // 5 + 1
        column = position % 5 + 1
        for direction in DIRECTIONS:
            _, values = data[direction]
            figure.add_trace(
                go.Scatter(
                    x=YEARS,
                    y=values[code],
                    name=direction,
                    legendgroup=direction,
                    showlegend=position == 0,
                    mode="lines",
                    line={"color": theme.DIRECTION_COLOUR[direction], "width": 2},
                    hovertemplate=f"{direction} %{{y:,.0f}}<extra></extra>",
                ),
                row=row,
                col=column,
            )
    apply(figure, title, "Year", y_title, height=620)
    for row in (1, 2):
        for column in range(1, 6):
            x_spec = theme.axis("Year" if row == 2 else "")
            x_spec["dtick"] = 2
            figure.update_xaxes(**x_spec, row=row, col=column)
            figure.update_yaxes(
                **theme.axis(y_title if column == 1 else ""), row=row, col=column
            )
    figure.update_annotations(font={"size": 11, "color": theme.LIGHT["secondary"]})
    figure.update_layout(
        legend={"y": 1.09, "yanchor": "bottom", "x": 1, "xanchor": "right"},
        margin={"l": 70, "r": 30, "t": 120, "b": 70},
    )
    return figure


def main_statistical():
    figure = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.12,
        subplot_titles=(
            "Average size against volatility",
            "Largest outlier year by growth z-score",
        ),
    )
    for direction in DIRECTIONS:
        names, stats = rw.main_stats(direction)
        figure.add_trace(
            go.Scatter(
                x=[stats[c][3] for c in stats],
                y=[stats[c][0] for c in stats],
                name=direction,
                mode="markers+text",
                text=[c for c in stats],
                textposition="top center",
                textfont={"size": 11, "color": theme.LIGHT["secondary"]},
                marker={
                    "color": theme.DIRECTION_COLOUR[direction],
                    "size": 11,
                    "line": {"color": theme.LIGHT["surface"], "width": 2},
                },
                hovertemplate=(
                    f"{direction} category %{{text}}<br>"
                    "mean %{y:,.0f}<br>variation %{x:.2f}<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )
    for direction in DIRECTIONS:
        names, zscores = rw.main_zscore(direction)
        codes = list(zscores)
        peaks = []
        peak_years = []
        for code in codes:
            values = [
                (abs(v), v, YEARS[1:][i])
                for i, v in enumerate(zscores[code])
                if v is not None
            ]
            best = max(values)
            peaks.append(best[1])
            peak_years.append(best[2])
        figure.add_trace(
            go.Bar(
                x=codes,
                y=peaks,
                name=direction,
                legendgroup=direction,
                showlegend=False,
                marker={"color": theme.DIRECTION_COLOUR[direction]},
                text=peak_years,
                textposition="outside",
                textfont={"size": 10, "color": theme.LIGHT["secondary"]},
                customdata=peak_years,
                hovertemplate=(
                    f"{direction} category %{{x}}<br>"
                    "outlier year %{customdata}<br>z %{y:.2f}<extra></extra>"
                ),
            ),
            row=1,
            col=2,
        )
    apply(figure, "Statistical trend, every main category, import and export", "", "", height=470)
    figure.update_xaxes(**theme.axis("Coefficient of variation"), row=1, col=1)
    figure.update_yaxes(**theme.axis("Mean value ($ Millions)"), row=1, col=1)
    figure.update_xaxes(
        **theme.axis("Main category, labelled with its outlier year"), type="category", row=1, col=2
    )
    figure.update_yaxes(**theme.axis("Z-score of year on year growth"), row=1, col=2)
    figure.update_annotations(font={"size": 13, "color": theme.LIGHT["secondary"]})
    figure.update_layout(barmode="group")
    return figure


def share_slope():
    figure = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.22,
        subplot_titles=("Export share of total", "Import share of total"),
    )
    for column, direction in enumerate(DIRECTIONS, start=1):
        names, share = rw.main_share(direction)
        codes = sorted(share, key=lambda c: share[c][-1])
        labels = [f"{c} {short_name(names[c], 28)}" for c in codes]
        colour = theme.DIRECTION_COLOUR[direction]
        for position, code in enumerate(codes):
            figure.add_trace(
                go.Scatter(
                    x=[share[code][0], share[code][-1]],
                    y=[labels[position], labels[position]],
                    mode="lines",
                    line={"color": theme.LIGHT["axis"], "width": 2},
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=1,
                col=column,
            )
        figure.add_trace(
            go.Scatter(
                x=[share[c][0] for c in codes],
                y=labels,
                mode="markers",
                name="2016 share",
                legendgroup="2016",
                showlegend=column == 1,
                marker={
                    "color": theme.LIGHT["surface"],
                    "size": 11,
                    "line": {"color": theme.CONTEXT, "width": 2},
                },
                hovertemplate="%{y}<br>2016 share %{x:.1%}<extra></extra>",
            ),
            row=1,
            col=column,
        )
        figure.add_trace(
            go.Scatter(
                x=[share[c][-1] for c in codes],
                y=labels,
                mode="markers",
                name=f"2025 share, {direction.lower()}",
                legendgroup=f"2025-{direction}",
                showlegend=True,
                marker={
                    "color": colour,
                    "size": 11,
                    "line": {"color": theme.LIGHT["surface"], "width": 2},
                },
                hovertemplate="%{y}<br>2025 share %{x:.1%}<extra></extra>",
            ),
            row=1,
            col=column,
        )
        figure.add_trace(
            go.Scatter(
                x=[0.455] * len(codes),
                y=labels,
                mode="text",
                showlegend=False,
                text=[f"{share[c][-1]:.1%}" for c in codes],
                textposition="middle right",
                textfont={"size": 11, "color": theme.LIGHT["secondary"]},
                hoverinfo="skip",
            ),
            row=1,
            col=column,
        )
    apply(
        figure,
        "Share of total by main category, 2016 against 2025",
        "Share of direction total",
        "Main category",
        height=560,
    )
    for column in (1, 2):
        figure.update_xaxes(
            **theme.axis("Share of direction total"),
            tickformat=".0%",
            range=[-0.02, 0.5],
            row=1,
            col=column,
        )
        figure.update_yaxes(
            **theme.axis("Main category" if column == 1 else ""),
            type="category",
            row=1,
            col=column,
        )
    figure.update_annotations(font={"size": 13, "color": theme.LIGHT["secondary"]})
    figure.update_layout(
        legend={"y": -0.18, "yanchor": "top", "x": 0, "xanchor": "left"},
        margin={"l": 70, "r": 30, "t": 80, "b": 110},
    )
    return figure


def correlation_heatmap(direction):
    codes, matrix = rw.correlation(direction)
    names, _ = rw.main_values(direction)
    values = [[matrix[r][c] for c in codes] for r in codes]
    labels = [f"{c}" for c in codes]
    figure = go.Figure(
        go.Heatmap(
            z=values,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0.0, theme.NEGATIVE],
                [0.5, "#f0efec"],
                [1.0, theme.POSITIVE],
            ],
            text=[[f"{v:.2f}" for v in row] for row in values],
            texttemplate="%{text}",
            textfont={"size": 11},
            colorbar={
                "title": {"text": "Correlation", "font": {"size": 12}},
                "tickfont": {"size": 11},
                "outlinewidth": 0,
            },
            hovertemplate="category %{y} against %{x}<br>r %{z:.2f}<extra></extra>",
        )
    )
    apply(
        figure,
        f"{direction}: how the main categories move together, growth correlation",
        "Main category",
        "Main category",
        height=520,
        legend=False,
    )
    return figure


def cat3_subcategories(metric):
    if metric == "value":
        reader = rw.cat3_values
        y_title = "$ Millions"
        title = "Main category 3 and its subcategories, import and export"
        tickformat = None
    else:
        reader = rw.cat3_share
        y_title = "Share of main category 3"
        title = "Subcategory share of main category 3, import and export"
        tickformat = ".0%"
    figure = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.1,
        subplot_titles=("Export", "Import"),
    )
    for column, direction in enumerate(DIRECTIONS, start=1):
        names, values = reader(direction)
        for code in values:
            if metric == "share" and code == "3":
                continue
            colour = theme.SUBCATEGORY_COLOUR.get(code, theme.CONTEXT)
            figure.add_trace(
                go.Scatter(
                    x=YEARS,
                    y=values[code],
                    name=f"{code} {short_name(names[code], 22)}",
                    legendgroup=code,
                    showlegend=column == 1,
                    mode="lines+markers",
                    line={"color": colour, "width": 3 if code == "33" else 2},
                    marker={"size": 8 if code == "33" else 6},
                    hovertemplate=f"{code} %{{y:,.2f}}<extra></extra>",
                ),
                row=1,
                col=column,
            )
    apply(figure, title, "Year", y_title, height=480)
    for column in (1, 2):
        figure.update_xaxes(**theme.axis("Year"), row=1, col=column)
        axis_spec = theme.axis(y_title if column == 1 else "")
        if tickformat:
            axis_spec["tickformat"] = tickformat
        figure.update_yaxes(**axis_spec, row=1, col=column)
    figure.update_annotations(font={"size": 13, "color": theme.LIGHT["secondary"]})
    return figure


def focus_export_import():
    rows = rw.focus()
    figure = go.Figure()
    for direction, key in (("Export", "export"), ("Import", "import")):
        figure.add_trace(
            go.Scatter(
                x=YEARS,
                y=[r[key] for r in rows],
                name=f"Petroleum {direction.lower()}",
                mode="lines+markers",
                line={"color": theme.DIRECTION_COLOUR[direction], "width": 2},
                marker={"size": 8},
                hovertemplate=f"{direction} %{{y:,.0f}}<extra></extra>",
            )
        )
    peak = max(r["import"] for r in rows)
    apply(
        figure,
        "Subcategory 33 petroleum, export against import",
        "Year",
        "$ Millions",
        height=460,
    )
    figure.update_layout(
        annotations=[
            theme.annotation(
                "2020<br>COVID cuts import 41%<br>and export 37%",
                2020,
                rows[4]["import"],
                ax=-10,
                ay=-70,
            ),
            theme.annotation(
                "2022<br>price shock lifts import 91%<br>to the decade peak",
                2022,
                peak,
                ax=10,
                ay=-50,
            ),
        ]
    )
    return figure


def focus_balance():
    rows = rw.focus()
    balance = [r["balance"] for r in rows]
    figure = go.Figure(
        go.Bar(
            x=YEARS,
            y=balance,
            name="Petroleum trade balance",
            marker={"color": theme.NEGATIVE},
            text=[money(v) for v in balance],
            textposition="outside",
            textfont={"size": 10, "color": theme.LIGHT["secondary"]},
            hovertemplate="Balance %{y:,.0f}<extra></extra>",
        )
    )
    apply(
        figure,
        "Subcategory 33 petroleum, trade balance stays negative every year",
        "Year",
        "$ Millions",
        height=440,
        legend=False,
    )
    figure.update_yaxes(range=[min(balance) * 1.25, 0])
    return figure


def focus_vs_subcategories():
    figure = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.1,
        subplot_titles=("Export", "Import"),
    )
    for column, direction in enumerate(DIRECTIONS, start=1):
        names, values = rw.vs_index(direction)
        for code in values:
            figure.add_trace(
                go.Scatter(
                    x=YEARS,
                    y=values[code],
                    name=f"{code} {short_name(names[code], 22)}",
                    legendgroup=code,
                    showlegend=column == 1,
                    mode="lines+markers",
                    line={
                        "color": theme.SUBCATEGORY_COLOUR[code],
                        "width": 3 if code == "33" else 2,
                    },
                    marker={"size": 8 if code == "33" else 6},
                    hovertemplate=f"{code} index %{{y:,.0f}}<extra></extra>",
                ),
                row=1,
                col=column,
            )
    apply(
        figure,
        "Petroleum against coal and gas, index 2016 = 100",
        "Year",
        "Index (2016 = 100)",
        height=480,
    )
    for column in (1, 2):
        figure.update_xaxes(**theme.axis("Year"), row=1, col=column)
        figure.update_yaxes(
            **theme.axis("Index (2016 = 100)" if column == 1 else ""), row=1, col=column
        )
    figure.update_annotations(font={"size": 13, "color": theme.LIGHT["secondary"]})
    return figure


def focus_scatter():
    rows = rw.focus()
    _, correlation = rw.vs_pairs()
    xs = [r["export"] for r in rows]
    ys = [r["import"] for r in rows]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    line_x = [min(xs), max(xs)]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=line_x,
            y=[slope * x + intercept for x in line_x],
            name="Fitted line",
            mode="lines",
            line={"color": theme.CONTEXT, "width": 2, "dash": "dash"},
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            name="One point per year",
            mode="markers+text",
            text=[str(y) for y in YEARS],
            textposition="top center",
            textfont={"size": 10, "color": theme.LIGHT["secondary"]},
            marker={
                "color": theme.PETROLEUM,
                "size": 12,
                "line": {"color": theme.LIGHT["surface"], "width": 2},
            },
            hovertemplate="%{text}<br>export %{x:,.0f}<br>import %{y:,.0f}<extra></extra>",
        )
    )
    apply(
        figure,
        f"Petroleum import moves with petroleum export, growth correlation r = {correlation:.2f}",
        "Petroleum export ($ Millions)",
        "Petroleum import ($ Millions)",
        height=470,
    )
    return figure


def focus_share_of_main():
    figure = go.Figure()
    for direction in DIRECTIONS:
        names, share = rw.cat3_share(direction)
        figure.add_trace(
            go.Scatter(
                x=YEARS,
                y=share["33"],
                name=f"Petroleum share of category 3, {direction.lower()}",
                mode="lines+markers",
                line={"color": theme.DIRECTION_COLOUR[direction], "width": 2},
                marker={"size": 8},
                hovertemplate=f"{direction} %{{y:.1%}}<extra></extra>",
            )
        )
    apply(
        figure,
        "Petroleum as a share of main category 3",
        "Year",
        "Share of main category 3",
        height=440,
    )
    figure.update_yaxes(tickformat=".0%")
    return figure


def forecast_chart():
    rows = rw.forecast()
    ai = {r["year"]: r["ai"] for r in rw.ai_comparison()}
    actual_years = [r["year"] for r in rows if r["actual"] is not None]
    actual = [r["actual"] for r in rows if r["actual"] is not None]
    bridge_year = actual_years[-1]
    bridge_value = actual[-1]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=actual_years,
            y=actual,
            name="Actual import, 2016 to 2025",
            mode="lines+markers",
            line={"color": theme.FORECAST_COLOUR["actual"], "width": 3},
            marker={"size": 8},
            hovertemplate="Actual %{y:,.0f}<extra></extra>",
        )
    )
    series = [
        ("linear", "My linear trend forecast"),
        ("cagr", "My CAGR forecast"),
        ("target", "My target path, 3% a year lower"),
    ]
    for key, label in series:
        values = [r[key] for r in rows if r[key] is not None]
        figure.add_trace(
            go.Scatter(
                x=[bridge_year] + FORECAST_YEARS,
                y=[bridge_value] + values,
                name=label,
                mode="lines+markers",
                line={
                    "color": theme.FORECAST_COLOUR[key],
                    "width": 2,
                    "dash": theme.FORECAST_DASH[key],
                },
                marker={"size": 7},
                hovertemplate=f"{label} %{{y:,.0f}}<extra></extra>",
            )
        )
    figure.add_trace(
        go.Scatter(
            x=[bridge_year] + FORECAST_YEARS,
            y=[bridge_value] + [ai[y] for y in FORECAST_YEARS],
            name="Claude Sonnet 5",
            mode="lines+markers",
            line={
                "color": theme.FORECAST_COLOUR["ai"],
                "width": 2,
                "dash": theme.FORECAST_DASH["ai"],
            },
            marker={"size": 7},
            hovertemplate="Claude Sonnet 5 %{y:,.0f}<extra></extra>",
        )
    )
    apply(
        figure,
        "Petroleum import, ten years of actuals and five years of forecasts",
        "Year",
        "$ Millions",
        height=520,
    )
    figure.add_vrect(
        x0=bridge_year,
        x1=FORECAST_YEARS[-1],
        fillcolor=theme.LIGHT["grid"],
        opacity=0.35,
        line_width=0,
        layer="below",
    )
    figure.update_layout(
        annotations=[
            theme.annotation(
                "Forecast period<br>2026 to 2030", 2028, max(actual) * 0.98, ax=0, ay=-30
            )
        ]
    )
    return figure


def change_point_chart():
    rows = rw.change_points()
    years = [r["year"] for r in rows]
    figure = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.1,
        subplot_titles=("Export", "Import"),
    )
    for column, direction in enumerate(DIRECTIONS, start=1):
        prefix = direction.lower()
        rises = [r[f"{prefix}_rise"] for r in rows]
        falls = [r[f"{prefix}_fall"] for r in rows]
        rise_names = [r[f"{prefix}_rise_name"] for r in rows]
        fall_names = [r[f"{prefix}_fall_name"] for r in rows]
        figure.add_trace(
            go.Bar(
                x=years,
                y=rises,
                name="Largest rise",
                legendgroup="rise",
                showlegend=column == 1,
                marker={"color": theme.POSITIVE},
                customdata=rise_names,
                hovertemplate="%{x} rise %{y:,.0f}<br>%{customdata}<extra></extra>",
            ),
            row=1,
            col=column,
        )
        figure.add_trace(
            go.Bar(
                x=years,
                y=falls,
                name="Largest fall",
                legendgroup="fall",
                showlegend=column == 1,
                marker={"color": theme.NEGATIVE},
                customdata=fall_names,
                hovertemplate="%{x} fall %{y:,.0f}<br>%{customdata}<extra></extra>",
            ),
            row=1,
            col=column,
        )
    apply(
        figure,
        "Change point for each year, largest rise and largest fall by main category",
        "Year",
        "$ Millions",
        height=480,
    )
    for column in (1, 2):
        figure.update_xaxes(**theme.axis("Year"), row=1, col=column)
        figure.update_yaxes(
            **theme.axis("$ Millions change" if column == 1 else ""), row=1, col=column
        )
    figure.update_annotations(font={"size": 13, "color": theme.LIGHT["secondary"]})
    figure.update_layout(barmode="relative")
    return figure


def divergence_chart():
    _, growth_e = rw.main_growth("Export")
    _, coal = rw.vs_growth("Export")
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=YEARS[1:],
            y=coal["32"],
            name="32 Coal export growth",
            marker={"color": theme.COAL},
            hovertemplate="Coal %{y:.0%}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Bar(
            x=YEARS[1:],
            y=growth_e["2"],
            name="Main category 2 export growth, holds iron ore",
            marker={"color": theme.CONTEXT},
            hovertemplate="Category 2 %{y:.0%}<extra></extra>",
        )
    )
    apply(
        figure,
        "The 2022 divergence, coal against the iron ore category",
        "Year",
        "Year on year growth",
        height=450,
    )
    figure.update_yaxes(tickformat=".0%")
    figure.update_layout(
        barmode="group",
        annotations=[
            theme.annotation(
                "2022: coal rises 124%<br>while category 2 falls",
                2022,
                max(coal["32"]),
                ax=20,
                ay=-40,
            )
        ],
    )
    return figure


def backtest_chart():
    rows, mape = rw.backtest()
    train = [r for r in rows if r["linear"] is None]
    test = [r for r in rows if r["linear"] is not None]
    bridge = train[-1]
    figure = go.Figure()
    figure.add_vrect(
        x0=train[0]["year"] - 0.5,
        x1=bridge["year"] + 0.5,
        fillcolor=theme.LIGHT["plane"],
        line_width=0,
        layer="below",
    )
    figure.add_trace(
        go.Scatter(
            x=[r["year"] for r in rows],
            y=[r["actual"] for r in rows],
            name="Actual import",
            mode="lines+markers",
            line={"color": theme.FORECAST_COLOUR["actual"], "width": 3},
            marker={"size": 8},
            hovertemplate="Actual %{y:,.0f}<extra></extra>",
        )
    )
    series = [
        ("linear", f"Linear trend, {mape['linear']:.1%} average error"),
        ("cagr", f"CAGR method, {mape['cagr']:.1%} average error"),
        ("recent", f"Recent window, the Claude Sonnet 5 method, {mape['recent']:.1%} average error"),
    ]
    for key, label in series:
        figure.add_trace(
            go.Scatter(
                x=[bridge["year"]] + [r["year"] for r in test],
                y=[bridge["actual"]] + [r[key] for r in test],
                name=label,
                mode="lines+markers",
                line={
                    "color": theme.FORECAST_COLOUR[key if key != "recent" else "ai"],
                    "width": 2,
                    "dash": theme.FORECAST_DASH[key if key != "recent" else "ai"],
                },
                marker={"size": 7},
                hovertemplate=f"{label} %{{y:,.0f}}<extra></extra>",
            )
        )
    figure.add_annotation(
        x=train[len(train) // 2]["year"],
        y=max(r["actual"] for r in rows),
        text="Training years<br>the methods were fitted here",
        showarrow=False,
        font={"size": 11, "color": theme.LIGHT["secondary"]},
    )
    figure.add_annotation(
        x=test[len(test) // 2]["year"],
        y=max(r["actual"] for r in rows),
        text="Test years<br>every method missed low",
        showarrow=False,
        font={"size": 11, "color": theme.LIGHT["secondary"]},
    )
    apply(
        figure,
        "Backtest, each method fitted on 2016 to 2021 and asked to predict 2022 to 2025",
        "Year",
        "$ Millions",
        height=480,
    )
    return figure
