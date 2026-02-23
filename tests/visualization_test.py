"""Tests for the visualization module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock
from swissparlpy import plot_voting
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for tests
import matplotlib.pyplot as plt


@pytest.fixture
def mock_client():
    """Create a mock SwissParlClient for tests."""
    return Mock()


class TestVisualization:
    """Test cases for plot_voting function."""

    def setup_method(self):
        """Set up test data."""
        # Create mock voting data
        np.random.seed(42)
        decisions = np.random.choice([1, 2, 3], size=200, p=[0.5, 0.3, 0.2])
        decision_text_map = {1: "Ja", 2: "Nein", 3: "Enthaltung"}

        self.mock_votes = pd.DataFrame(
            {
                "PersonNumber": range(1, 201),
                "Decision": decisions,
                "DecisionText": [decision_text_map[d] for d in decisions],
                "ParlGroupNumber": np.random.choice([1, 2, 3, 4], size=200),
            }
        )

        self.mock_seats = pd.DataFrame(
            {"SeatNumber": range(1, 201), "PersonNumber": range(1, 201)}
        )

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_plot_voting_basic(self, mock_client):
        """Test basic plot_voting functionality."""
        fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme="scoreboard",
            client=mock_client,
        )
        assert fig is not None
        assert isinstance(fig, plt.Figure)

    def test_plot_voting_all_themes(self, mock_client):
        """Test all available themes."""
        themes = ["scoreboard", "sym1", "sym2", "poly1", "poly2", "poly3"]
        for theme in themes:
            fig = plot_voting(
                self.mock_votes, seats=self.mock_seats, theme=theme, client=mock_client
            )
            assert fig is not None, f"Failed to create figure with theme {theme}"
            plt.close(fig)

    def test_plot_voting_with_result(self, mock_client):
        """Test plot_voting with result annotation."""
        fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme="scoreboard",
            result=True,
            client=mock_client,
        )
        assert fig is not None

    def test_plot_voting_with_highlight(self, mock_client):
        """Test plot_voting with highlighting."""
        fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme="poly2",
            highlight={"ParlGroupNumber": [2]},
            client=mock_client,
        )
        assert fig is not None

    def test_plot_voting_missing_columns(self, mock_client):
        """Test that missing required columns raise ValueError."""
        # Missing Decision column
        incomplete_votes = self.mock_votes.drop(columns=["Decision"])

        with pytest.raises(ValueError, match="Missing required columns"):
            plot_voting(incomplete_votes, seats=self.mock_seats, client=mock_client)

    def test_plot_voting_invalid_theme(self, mock_client):
        """Test that invalid theme raises ValueError."""
        with pytest.raises(ValueError, match="Unknown theme"):
            plot_voting(
                self.mock_votes,
                seats=self.mock_seats,
                theme="invalid_theme",
                client=mock_client,
            )

    def test_plot_voting_with_list_input(self, mock_client):
        """Test that list input is converted to DataFrame."""
        votes_list = self.mock_votes.to_dict("records")
        seats_list = self.mock_seats.to_dict("records")

        fig = plot_voting(
            votes_list, seats=seats_list, theme="scoreboard", client=mock_client
        )
        assert fig is not None

    def test_plot_voting_custom_point_settings(self, mock_client):
        """Test custom point shape and size."""
        fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme="scoreboard",
            point_shape="s",  # square
            point_size=100,
            client=mock_client,
        )
        assert fig is not None

    def test_plot_voting_result_text_size(self, mock_client):
        """Test custom result text size."""
        fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme="scoreboard",
            result=True,
            result_size=16,
            client=mock_client,
        )
        assert fig is not None

    def test_plot_voting_with_custom_ax(self, mock_client):
        """Test providing custom axes."""
        fig, ax = plt.subplots()
        result_fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme="scoreboard",
            ax=ax,
            client=mock_client,
        )
        assert result_fig is fig

    def test_seating_plan_data_exists(self):
        """Test that seating plan data file exists."""
        from pathlib import Path
        import swissparlpy.visualization

        module_path = Path(swissparlpy.visualization.__file__).parent
        seating_plan_path = module_path / "data" / "seating_plan.csv"

        assert seating_plan_path.exists(), "Seating plan data file not found"

    def test_seating_plan_data_format(self):
        """Test that seating plan data has correct format."""
        from swissparlpy.visualization import _load_seating_plan

        seating_plan = _load_seating_plan()

        # Check it's a DataFrame
        assert isinstance(seating_plan, pd.DataFrame)

        # Check required columns exist
        required_cols = ["SeatNumber", "order", "x", "y", "center_x", "center_y"]
        for col in required_cols:
            assert col in seating_plan.columns, f"Missing column: {col}"

        # Check data shape (200 seats * 4 corners = 800 rows)
        assert len(seating_plan) == 800, f"Expected 800 rows, got {len(seating_plan)}"
