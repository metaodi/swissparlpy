"""
Visualization module for Swiss Parliament voting data.

This module provides functionality to create visualizations of voting
results in the Swiss National Council, similar to the ggswissparl
function from the R package `swissparl`.
"""

import warnings
from pathlib import Path

from . import SwissParlResponse
from . import SwissParlClient
from typing import Union, Optional, cast

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.axes
    import matplotlib.figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn(
        "matplotlib and/or pandas is not installed. Install them with "
        "'pip install matplotlib pandas' to use visualization features.",
        ImportWarning,
    )


def _load_seating_plan() -> "pd.DataFrame":
    """Load the seating plan data from the package data directory."""
    data_dir = Path(__file__).parent / "data"
    seating_plan_path = data_dir / "seating_plan.csv"

    if not seating_plan_path.exists():
        raise FileNotFoundError(
            f"Seating plan data not found at {seating_plan_path}. "
            "Please ensure the package is properly installed."
        )

    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "pandas is required for visualization. "
            "Install it with: pip install pandas"
        )

    return pd.read_csv(seating_plan_path)


def plot_voting(  # noqa: C901
    votes: Union["pd.DataFrame", list[dict[str, object]], "SwissParlResponse"],
    seats: Optional[
        Union["pd.DataFrame", list[dict[str, object]], "SwissParlResponse"]
    ] = None,
    highlight: Optional[dict[str, list[object]]] = None,
    result: bool = False,
    result_size: int = 12,
    point_shape: str = "o",
    point_size: int = 50,
    theme: str = "scoreboard",
    ax: Optional["matplotlib.axes.Axes"] = None,
    client: Optional["SwissParlClient"] = None,
) -> Union["matplotlib.figure.Figure", "matplotlib.figure.SubFigure"]:
    """
    Plot voting results of the Swiss National Council.

    This function visualizes voting results in the Swiss National Council
    chamber, showing how each councillor voted (yes/no/abstention) using
    different themes.

    Parameters
    ----------
    votes : pandas.DataFrame or list of dict
        Voting data as retrieved with get_data(table="Voting").
        Must contain columns: 'PersonNumber', 'Decision', 'DecisionText'.
        Can also contain 'IdVote' for multiple votes.
    seats : pandas.DataFrame or list of dict, optional
        Data linking councillors (PersonNumber) to seats (SeatNumber).
        If None, attempts to retrieve current seating order via
        get_data(table="SeatOrganisationNr").
    highlight : dict, optional
        Dictionary with variable name and values to highlight councillors.
        Example: {'ParlGroupNumber': [2]} to highlight a group.
    result : bool, default False
        If True, annotate the plot with voting results counts.
    result_size : int, default 12
        Font size for result annotations.
    point_shape : str, default 'o'
        Marker shape for point-based themes. See matplotlib markers.
    point_size : int, default 50
        Size of markers for point-based themes.
    theme : str, default 'scoreboard'
        Visual theme for the plot. Options:
        - 'scoreboard': Council hall scoreboard (neon colors on black)
        - 'sym1': Colored symbols on light background with black frames
        - 'sym2': Colored symbols on light background without frames
        - 'poly1': Color-filled polygons with black edges
        - 'poly2': Color-filled polygons with white edges
        - 'poly3': Color-filled polygons without edges
    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, creates a new figure.

    Returns
    -------
    matplotlib.figure.Figure or matplotlib.figure.SubFigure
        The figure containing the visualization.

    Raises
    ------
    ImportError
        If matplotlib or pandas is not installed.
    ValueError
        If required columns are missing from the data.

    Examples
    --------
    >>> import swissparlpy as spp
    >>> # Get voting data for a specific vote
    >>> votes = spp.get_data("Voting", Language="DE", IdVote=23458)
    >>> # Create visualization
    >>> fig = spp.plot_voting(votes, theme="scoreboard")
    >>> plt.show()

    >>> # Highlight a parliamentary group
    >>> fig = spp.plot_voting(votes, highlight={'ParlGroupCode': ["S"]}, theme="poly1")
    >>> plt.show()
    """

    if not client:
        client = SwissParlClient()

    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install matplotlib"
        )

    # Convert votes to DataFrame if it's a list or SwissParlResponse
    if isinstance(votes, pd.DataFrame):
        votes_df = votes
    elif isinstance(votes, list):
        votes_df = pd.DataFrame(votes)
    elif isinstance(votes, SwissParlResponse):
        votes_df = votes.to_dataframe()
    else:
        raise ValueError(
            "votes must be a pandas DataFrame, list of dicts, or SwissParlResponse"
        )

    # Check required columns in votes
    required_vote_cols = ["PersonNumber", "Decision", "DecisionText"]
    missing_cols = [col for col in required_vote_cols if col not in votes_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in votes: {missing_cols}")

    # Handle seats data
    if seats is None:
        # Try to import and get seats data
        try:
            seats = client.get_data(
                "SeatOrganisationNr", filter="Language eq 'DE'"
            ).to_dataframe()
        except Exception as e:
            raise ValueError(
                f"Could not retrieve seating data automatically: {e}. "
                "Please provide seats parameter explicitly."
            )
        # check if the data is from the current legislative period, if not
        # warn the user that seating data might not be available
        if "IdLegislativePeriod" in votes_df.columns:
            legis = client.get_data(
                "LegislativePeriod", filter="Language eq 'DE'"
            ).to_dataframe()
            current_legis_id = int(
                legis.sort_values(by="EndDate", ascending=False).iloc[0]["ID"]
            )
            if votes_df["IdLegislativePeriod"].iloc[0] != current_legis_id:
                warnings.warn(
                    "The voting data is not from the current legislative period. "
                    "Seating data might not be up-to-date. "
                    "Consider providing seating data explicitly for "
                    "the correct legislative period."
                )
    else:
        seats = pd.DataFrame(seats)

    # Check required columns in seats
    required_seat_cols = ["SeatNumber", "PersonNumber"]
    missing_cols = [col for col in required_seat_cols if col not in seats.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in seats: {missing_cols}")

    # Load seating plan
    seating_plan = _load_seating_plan()

    # Merge data
    # First merge seating plan with seats
    data = seating_plan.merge(
        seats[["SeatNumber", "PersonNumber"]], on="SeatNumber", how="left"
    )

    # Then merge with votes (keep all votes -> right join)
    data = data.merge(votes_df, on="PersonNumber", how="right")

    # Fill missing decisions (councillors not present) with 8
    data["Decision"] = data["Decision"].fillna(8)
    data["DecisionText"] = data["DecisionText"].fillna("Missing")

    # Initialize highlight column (0 = show normally, 1 = fade out)
    data["highlight"] = 0

    # Apply highlighting if specified
    if highlight is not None:
        if not isinstance(highlight, dict) or len(highlight) != 1:
            raise ValueError(
                "highlight must be a dictionary with exactly one key-value pair"
            )

        highlight_col = list(highlight.keys())[0]
        highlight_vals = highlight[highlight_col]

        if highlight_col not in data.columns:
            raise ValueError(f"Highlight column '{highlight_col}' not found in data")

        # Fade out all items first
        data["highlight"] = 1
        # Then show highlighted items normally
        data.loc[data[highlight_col].isin(highlight_vals), "highlight"] = 0

    # Create figure if ax not provided
    fig: Optional[Union["matplotlib.figure.Figure", "matplotlib.figure.SubFigure"]] = (
        None
    )
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    else:
        fig = ax.get_figure()

    if fig is None:
        raise ValueError("Provided axes must be attached to a figure")

    # Define theme settings
    theme_config = _get_theme_config(theme)

    # Apply orientation transformation
    if theme_config["flip_x"]:
        data["x"] = -data["x"]
        data["center_x"] = -data["center_x"]
    if theme_config["flip_y"]:
        data["y"] = -data["y"]
        data["center_y"] = -data["center_y"]

    # Plot based on theme type
    if theme in ["scoreboard", "sym1", "sym2"]:
        _plot_point_theme(data, ax, theme_config, point_shape, point_size)
    else:  # poly1, poly2, poly3
        _plot_polygon_theme(data, ax, theme_config)

    # Add results if requested
    if result:
        _add_results(data, ax, theme_config, result_size, highlight is not None)

    # Set axis limits before aspect ratio to avoid massive image size
    # Calculate data range with small padding
    x_min, x_max = data["x"].min(), data["x"].max()
    y_min, y_max = data["y"].min(), data["y"].max()
    x_padding = (x_max - x_min) * 0.05
    y_padding = (y_max - y_min) * 0.05
    ax.set_xlim(x_min - x_padding, x_max + x_padding)
    ax.set_ylim(y_min - y_padding, y_max + y_padding)

    # Configure axes
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(cast(str, theme_config["bg_color"]))
    fig.patch.set_facecolor(cast(str, theme_config["bg_color"]))

    return fig


def _get_theme_config(theme: str) -> dict[str, object]:
    """Get configuration for a specific theme."""
    configs: dict[str, dict[str, object]] = {
        "scoreboard": {
            "colors": {
                1: "#00ff00",  # Neon green for yes
                2: "#ff0000",  # Neon red for no
                3: "white",  # White for abstention
                4: "black",
                5: "black",
                6: "black",
                7: "black",
                8: "black",
            },
            "seat_fill": "black",
            "seat_edge": "white",
            "bg_color": "black",
            "result_x": -2975,
            "result_y": [5500, 5200, 4900],
            "flip_x": True,
            "flip_y": False,
            "use_polygons": False,
        },
        "sym1": {
            "colors": {
                1: "#009E73",  # Green
                2: "#D55E00",  # Orange/red
                3: "grey",  # Grey
                4: "white",
                5: "white",
                6: "white",
                7: "white",
                8: "white",
            },
            "seat_fill": "white",
            "seat_edge": "black",
            "bg_color": "white",
            "result_x": 896,
            "result_y": [-5500, -5200, -4900],
            "flip_x": False,
            "flip_y": True,
            "use_polygons": False,
        },
        "sym2": {
            "colors": {
                1: "#009E73",  # Green
                2: "#D55E00",  # Orange/red
                3: "grey",  # Grey
                4: "white",
                5: "white",
                6: "white",
                7: "white",
                8: "white",
            },
            "seat_fill": "white",
            "seat_edge": "white",
            "bg_color": "white",
            "result_x": 896,
            "result_y": [-5500, -5200, -4900],
            "flip_x": False,
            "flip_y": True,
            "use_polygons": False,
        },
        "poly1": {
            "colors": {
                1: "#009E73",  # Green
                2: "#D55E00",  # Orange/red
                3: "grey",  # Grey
                4: "#f0f0f0",
                5: "#f0f0f0",
                6: "#f0f0f0",
                7: "#f0f0f0",
                8: "#f0f0f0",
            },
            "seat_fill": None,  # Will use decision colors
            "seat_edge": "black",
            "bg_color": "white",
            "result_x": 896,
            "result_y": [-5500, -5200, -4900],
            "flip_x": False,
            "flip_y": True,
            "use_polygons": True,
        },
        "poly2": {
            "colors": {
                1: "#009E73",  # Green
                2: "#D55E00",  # Orange/red
                3: "grey",  # Grey
                4: "#f0f0f0",
                5: "#f0f0f0",
                6: "#f0f0f0",
                7: "#f0f0f0",
                8: "#f0f0f0",
            },
            "seat_fill": None,  # Will use decision colors
            "seat_edge": "white",
            "bg_color": "white",
            "result_x": 896,
            "result_y": [-5500, -5200, -4900],
            "flip_x": False,
            "flip_y": True,
            "use_polygons": True,
        },
        "poly3": {
            "colors": {
                1: "#009E73",  # Green
                2: "#D55E00",  # Orange/red
                3: "grey",  # Grey
                4: "#f0f0f0",
                5: "#f0f0f0",
                6: "#f0f0f0",
                7: "#f0f0f0",
                8: "#f0f0f0",
            },
            "seat_fill": None,  # Will use decision colors
            "seat_edge": "none",
            "bg_color": "white",
            "result_x": 896,
            "result_y": [-5500, -5200, -4900],
            "flip_x": False,
            "flip_y": True,
            "use_polygons": True,
        },
    }

    if theme not in configs:
        raise ValueError(
            f"Unknown theme '{theme}'. Choose from: {list(configs.keys())}"
        )

    return configs[theme]


def _plot_point_theme(
    data: "pd.DataFrame",
    ax: "matplotlib.axes.Axes",
    theme_config: dict[str, object],
    point_shape: str,
    point_size: int,
) -> None:
    """Plot visualization using points/markers."""
    import pandas as pd

    # Group by seat to draw seat boundaries
    for seat_num in data["SeatNumber"].unique():
        seat_data = data[data["SeatNumber"] == seat_num]
        if len(seat_data) >= 4:
            # Create polygon for seat boundary
            coords = seat_data[["x", "y"]].values
            polygon = mpatches.Polygon(
                coords,
                closed=True,
                fill=False,
                edgecolor=theme_config["seat_edge"],
                linewidth=1,
            )
            ax.add_patch(polygon)

    # Plot center points with decision colors
    unique_decisions = data.groupby("SeatNumber").first().reset_index()

    for _, row in unique_decisions.iterrows():
        if pd.notna(row["Decision"]):
            decision = int(row["Decision"])
            color = theme_config["colors"].get(decision, "white")  # type: ignore
            alpha = 0.1 if row["highlight"] == 1 else 1.0

            ax.scatter(
                row["center_x"],
                row["center_y"],
                c=color,
                marker=point_shape,
                s=point_size,
                alpha=alpha,
                zorder=2,
            )


def _plot_polygon_theme(
    data: "pd.DataFrame", ax: "matplotlib.axes.Axes", theme_config: dict[str, object]
) -> None:
    """Plot visualization using filled polygons."""
    import pandas as pd

    # Group by seat and plot each seat as a filled polygon
    for seat_num in data["SeatNumber"].unique():
        seat_data = data[data["SeatNumber"] == seat_num].sort_values("order")

        if len(seat_data) >= 4:
            # Get decision for this seat
            decision = seat_data["Decision"].iloc[0]
            if pd.notna(decision):
                decision = int(decision)
                color = theme_config["colors"].get(decision, "#f0f0f0")  # type: ignore

                # Apply alpha based on highlight
                alpha = 0.1 if seat_data["highlight"].iloc[0] == 1 else 1.0

                # Create filled polygon
                coords = seat_data[["x", "y"]].values
                polygon = mpatches.Polygon(
                    coords,
                    closed=True,
                    facecolor=color,
                    edgecolor=theme_config["seat_edge"],
                    linewidth=1 if theme_config["seat_edge"] != "none" else 0,
                    alpha=alpha,
                )
                ax.add_patch(polygon)


def _add_results(
    data: "pd.DataFrame",
    ax: "matplotlib.axes.Axes",
    theme_config: dict[str, object],
    result_size: int,
    has_highlight: bool,
) -> None:
    """Add voting result annotations to the plot."""
    # Get unique persons (one per seat)
    unique_persons = data.groupby("PersonNumber").first().reset_index()

    # Count votes by decision (only for decisions 1-3)
    vote_counts = (
        unique_persons[unique_persons["Decision"].isin([1, 2, 3])]
        .groupby(["Decision", "DecisionText"])
        .size()
        .reset_index(name="count")  # type: ignore[call-overload]
    )

    # If highlighting, also count highlighted votes
    if has_highlight:
        highlighted_counts = (
            unique_persons[
                (unique_persons["Decision"].isin([1, 2, 3]))
                & (unique_persons["highlight"] == 0)
            ]
            .groupby(["Decision", "DecisionText"])
            .size()
            .reset_index(name="highlight_count")  # type: ignore[call-overload]
        )
        vote_counts = vote_counts.merge(
            highlighted_counts, on=["Decision", "DecisionText"], how="left"
        )
        vote_counts["highlight_count"] = (
            vote_counts["highlight_count"].fillna(0).astype(int)
        )

    # Add annotations for each decision type
    result_x = cast(float, theme_config["result_x"])
    result_y = cast(list, theme_config["result_y"])

    for idx, decision in enumerate([1, 2, 3]):
        if decision in vote_counts["Decision"].values:
            row = vote_counts[vote_counts["Decision"] == decision].iloc[0]
            count = row["count"]
            decision_text = row["DecisionText"]
            color = theme_config["colors"][decision]  # type: ignore

            if has_highlight:
                highlight_count = row["highlight_count"]
                label = f"{int(highlight_count)} / {int(count)} {decision_text}"
            else:
                label = f"{int(count)} {decision_text}"

            ax.text(
                result_x,
                result_y[idx],
                label,
                color=color,
                fontsize=result_size,
                fontweight="bold",
                ha="left",
                va="center",
            )
