"""Shared chart style so every figure in the project looks consistent."""
import matplotlib.pyplot as plt

from src import config

# One fixed colour per energy source / concept, used in every chart
COLORS = {
    "coal": "#5b5b5b",
    "gas": "#b07aa1",
    "hydro": "#4e79a7",
    "solar": "#f2b701",
    "wind": "#59a14f",
    "central_import": "#9c755f",
    "load": "#2f6db3",
    "highlight": "#d1495b",
    "muted": "#a0a0a0",
}
SOURCE_ORDER = ["coal", "hydro", "solar", "wind", "gas", "central_import"]
SOURCE_LABELS = {"coal": "Coal", "hydro": "Hydro", "solar": "Solar", "wind": "Wind",
                 "gas": "Gas", "central_import": "Central/imports"}


def setup():
    """Apply the project style. Call once at the top of a notebook."""
    plt.rcParams.update({
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.frameon": False,
    })


def save(fig, name: str):
    """Save a figure to reports/figures/<name>.png."""
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGURES / f"{name}.png", dpi=130, bbox_inches="tight")
