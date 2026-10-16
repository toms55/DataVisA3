LIGHT = {
    "surface": "#fcfcfb",
    "plane": "#f9f9f7",
    "text": "#0b0b0b",
    "secondary": "#52514e",
    "muted": "#898781",
    "grid": "#e1e0d9",
    "axis": "#c3c2b7",
    "border": "rgba(11,11,11,0.10)",
}

EXPORT = "#2a78d6"
IMPORT = "#eb6834"
COAL = "#1baf7a"
PETROLEUM = "#4a3aa7"
GAS = "#eda100"
CONTEXT = "#898781"
FORECAST_LINEAR = "#2a78d6"
FORECAST_CAGR = "#1baf7a"
FORECAST_TARGET = "#4a3aa7"
FORECAST_AI = "#e34948"
POSITIVE = "#2a78d6"
NEGATIVE = "#e34948"

DIRECTION_COLOUR = {"Export": EXPORT, "Import": IMPORT}

SUBCATEGORY_COLOUR = {"32": COAL, "33": PETROLEUM, "34": GAS}

SUBCATEGORY_DASH = {"32": "solid", "33": "solid", "34": "solid"}

FORECAST_COLOUR = {
    "actual": IMPORT,
    "linear": FORECAST_LINEAR,
    "cagr": FORECAST_CAGR,
    "target": FORECAST_TARGET,
    "ai": FORECAST_AI,
}

FORECAST_DASH = {
    "actual": "solid",
    "linear": "dash",
    "cagr": "dot",
    "target": "longdash",
    "ai": "dashdot",
}

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

VALIDATION = """Colour choices were checked with the dataviz palette validator, not by eye.
Direction pair #2a78d6 and #eb6834 passes every check in light mode.
Subcategory trio aqua #1baf7a, violet #4a3aa7 and yellow #eda100 passes the
all-pairs CVD and normal-vision gates in both light and dark mode.
The five forecast series pass the adjacent-pair gates in both modes.
Aqua and yellow sit below 3 to 1 contrast on the light surface, so every chart
that uses them carries direct labels and a table view, which is the relief the
validator requires."""


def axis(title):
    spec = {
        "title": {"text": title, "font": {"size": 13, "color": LIGHT["secondary"]}},
        "showgrid": True,
        "gridcolor": LIGHT["grid"],
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": LIGHT["axis"],
        "showline": True,
        "ticks": "outside",
        "tickcolor": LIGHT["axis"],
        "tickfont": {"size": 12, "color": LIGHT["muted"]},
        "automargin": True,
    }
    if title == "Year":
        spec["dtick"] = 1
        spec["tick0"] = 0
        spec["tickformat"] = "d"
    return spec


def layout(title, x_title, y_title, height=420, legend=True):
    return {
        "title": {
            "text": title,
            "font": {"size": 17, "color": LIGHT["text"]},
            "x": 0,
            "xanchor": "left",
            "y": 0.97,
            "yanchor": "top",
        },
        "xaxis": axis(x_title),
        "yaxis": axis(y_title),
        "height": height,
        "paper_bgcolor": LIGHT["surface"],
        "plot_bgcolor": LIGHT["surface"],
        "font": {"family": FONT, "size": 13, "color": LIGHT["text"]},
        "margin": {"l": 70, "r": 30, "t": 70, "b": 60},
        "showlegend": legend,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.26,
            "x": 0,
            "xanchor": "left",
            "font": {"size": 12, "color": LIGHT["secondary"]},
            "bgcolor": "rgba(0,0,0,0)",
        },
        "hovermode": "x unified",
        "hoverlabel": {
            "bgcolor": LIGHT["surface"],
            "bordercolor": LIGHT["axis"],
            "font": {"family": FONT, "size": 12, "color": LIGHT["text"]},
        },
    }


def line(width=2):
    return {"width": width}


def annotation(text, x, y, ax=0, ay=-40):
    return {
        "x": x,
        "y": y,
        "text": text,
        "showarrow": True,
        "arrowhead": 0,
        "arrowwidth": 1,
        "arrowcolor": LIGHT["muted"],
        "ax": ax,
        "ay": ay,
        "font": {"size": 11, "color": LIGHT["secondary"]},
        "bgcolor": "rgba(252,252,251,0.85)",
        "bordercolor": LIGHT["axis"],
        "borderwidth": 1,
        "borderpad": 4,
        "align": "left",
    }
