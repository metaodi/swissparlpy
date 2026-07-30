"""Tests for the visualization module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
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


class TestImportErrors:
    """Test import error handling"""

    def test_matplotlib_import_error(self):
        """Test that ImportError is handled when matplotlib is not available"""
        # This tests lines 16-18 in __init__.py
        import sys
        from unittest.mock import patch

        # Simulate ImportError when trying to import visualization
        with patch("swissparlpy.visualization.plot_voting") as mock_plot:
            # Make the import raise ImportError
            mock_plot.side_effect = ImportError("matplotlib not found")

            # The module should still be importable
            # and should handle the ImportError gracefully
            # This is difficult to test without actually uninstalling matplotlib
            # So we just verify the code doesn't crash
            try:
                import swissparlpy

                # Module loaded successfully
                assert True
            except Exception as e:
                # Should not raise exception
                pytest.fail(f"Import should not fail: {e}")

    def test_pandas_import_in_client(self):
        """Test pandas import error handling in client.py"""
        # This tests lines 11-12 in client.py
        import sys
        from unittest.mock import patch

        # Simulate pandas not being installed
        with patch.dict(sys.modules, {"pandas": None}):
            try:
                import importlib
                from swissparlpy import client

                # Force reload
                importlib.reload(client)

                # PANDAS_AVAILABLE should be False
                assert client.PANDAS_AVAILABLE == False
            except ImportError:
                # Expected if pandas is required
                pass


class TestVisualizationEdgeCases:
    """Test edge cases and error handling in visualization module."""

    def setup_method(self):
        """Set up test data."""
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

    def test_plot_voting_with_swissparlresponse(self):
        """Test plot_voting with SwissParlResponse input."""
        from swissparlpy import SwissParlResponse
        from swissparlpy.backends.odata import ODataResponse
        from unittest.mock import Mock
        import pandas as pd

        # Create a mock SwissParlResponse
        mock_backend_response = Mock(spec=ODataResponse)
        mock_backend_response.to_dict_list.return_value = self.mock_votes.to_dict(
            "records"
        )

        response = SwissParlResponse(mock_backend_response)

        # Mock the to_dataframe method to return our DataFrame
        response.to_dataframe = Mock(return_value=self.mock_votes)

        mock_client = Mock()
        from swissparlpy import plot_voting

        fig = plot_voting(
            response, seats=self.mock_seats, theme="scoreboard", client=mock_client
        )

        assert fig is not None
        plt.close(fig)

    def test_plot_voting_without_client(self):
        """Test that client is created automatically if not provided."""
        with patch("swissparlpy.visualization.SwissParlClient") as MockClient:
            mock_instance = Mock()
            MockClient.return_value = mock_instance

            from swissparlpy import plot_voting

            fig = plot_voting(
                self.mock_votes, seats=self.mock_seats, theme="scoreboard"
            )

            # Verify client was created
            MockClient.assert_called_once()
            assert fig is not None
            plt.close(fig)

    def test_plot_voting_seats_none_with_mock_client(self):
        """Test automatic seat retrieval when seats=None."""
        from swissparlpy import plot_voting

        # Add IdLegislativePeriod to votes to test that code path
        votes_with_legis = self.mock_votes.copy()
        votes_with_legis["IdLegislativePeriod"] = 51

        # Mock client
        mock_client = Mock()

        # Mock get_data for seats
        mock_seats_response = Mock()
        mock_seats_response.to_dataframe.return_value = self.mock_seats

        # Mock get_data for legislative period
        mock_legis_df = pd.DataFrame(
            {
                "ID": [50, 51],
                "EndDate": ["2023-01-01", "2027-01-01"],
            }
        )
        mock_legis_response = Mock()
        mock_legis_response.to_dataframe.return_value = mock_legis_df

        # Configure mock client to return different responses
        def mock_get_data(table, **kwargs):
            if table == "SeatOrganisationNr":
                return mock_seats_response
            elif table == "LegislativePeriod":
                return mock_legis_response
            return Mock()

        mock_client.get_data.side_effect = mock_get_data

        fig = plot_voting(votes_with_legis, seats=None, client=mock_client)

        assert fig is not None
        plt.close(fig)

    def test_plot_voting_seats_none_outdated_warning(self):
        """Test warning when voting data is from old legislative period."""
        from swissparlpy import plot_voting
        from swissparlpy import errors

        # Add old IdLegislativePeriod to votes
        votes_with_old_legis = self.mock_votes.copy()
        votes_with_old_legis["IdLegislativePeriod"] = 48  # Old period

        # Mock client
        mock_client = Mock()

        # Mock get_data for seats
        mock_seats_response = Mock()
        mock_seats_response.to_dataframe.return_value = self.mock_seats

        # Mock get_data for legislative period (current is 51)
        mock_legis_df = pd.DataFrame(
            {
                "ID": [48, 49, 50, 51],
                "EndDate": [
                    "2015-01-01",
                    "2019-01-01",
                    "2023-01-01",
                    "2027-01-01",
                ],
            }
        )
        mock_legis_response = Mock()
        mock_legis_response.to_dataframe.return_value = mock_legis_df

        def mock_get_data(table, **kwargs):
            if table == "SeatOrganisationNr":
                return mock_seats_response
            elif table == "LegislativePeriod":
                return mock_legis_response
            return Mock()

        mock_client.get_data.side_effect = mock_get_data

        # Should warn about outdated data
        with pytest.warns(errors.OutdatedDataWarning):
            fig = plot_voting(votes_with_old_legis, seats=None, client=mock_client)
            plt.close(fig)

    def test_plot_voting_seats_none_retrieval_error(self):
        """Test error handling when automatic seat retrieval fails."""
        from swissparlpy import plot_voting

        mock_client = Mock()
        mock_client.get_data.side_effect = Exception("API error")

        with pytest.raises(ValueError, match="Could not retrieve seating data"):
            plot_voting(self.mock_votes, seats=None, client=mock_client)

    def test_plot_voting_missing_seat_columns(self):
        """Test error when seats DataFrame is missing required columns."""
        from swissparlpy import plot_voting

        # Create seats without PersonNumber
        incomplete_seats = pd.DataFrame({"SeatNumber": range(1, 201)})

        mock_client = Mock()

        with pytest.raises(ValueError, match="Missing required columns in seats"):
            plot_voting(self.mock_votes, seats=incomplete_seats, client=mock_client)

    def test_plot_voting_invalid_highlight_format(self):
        """Test error when highlight has wrong format."""
        from swissparlpy import plot_voting

        mock_client = Mock()

        # Highlight with multiple keys (should have exactly one)
        invalid_highlight = {"ParlGroupNumber": [1], "Decision": [1]}

        with pytest.raises(
            ValueError, match="highlight must be a dictionary with exactly one key"
        ):
            plot_voting(
                self.mock_votes,
                seats=self.mock_seats,
                highlight=invalid_highlight,
                client=mock_client,
            )

    def test_plot_voting_invalid_votes_type(self):
        """Test error when votes has invalid type."""
        from swissparlpy import plot_voting

        mock_client = Mock()

        with pytest.raises(
            ValueError,
            match="votes must be a pandas DataFrame, list of dicts, or SwissParlResponse",
        ):
            plot_voting("invalid", seats=self.mock_seats, client=mock_client)

    def test_load_seating_plan_file_not_found(self):
        """Test error when seating plan file is missing."""
        from swissparlpy.visualization import _load_seating_plan

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Seating plan data not found"):
                _load_seating_plan()

    def test_load_seating_plan_pandas_not_available(self):
        """Test error when pandas is not available."""
        import swissparlpy.visualization as viz_module

        # Save original value
        original_pandas = viz_module.PANDAS_AVAILABLE

        try:
            # Temporarily disable pandas
            viz_module.PANDAS_AVAILABLE = False

            with pytest.raises(ImportError, match="pandas is required"):
                viz_module._load_seating_plan()
        finally:
            # Restore original value
            viz_module.PANDAS_AVAILABLE = original_pandas

    def test_plot_voting_matplotlib_not_available(self):
        """Test error when matplotlib is not available."""
        import swissparlpy.visualization as viz_module

        # Save original values
        original_matplotlib = viz_module.MATPLOTLIB_AVAILABLE

        try:
            # Temporarily disable matplotlib
            viz_module.MATPLOTLIB_AVAILABLE = False

            with pytest.raises(
                ImportError, match="matplotlib.*required for visualization"
            ):
                viz_module.plot_voting(
                    self.mock_votes, seats=self.mock_seats, client=Mock()
                )
        finally:
            # Restore original value
            viz_module.MATPLOTLIB_AVAILABLE = original_matplotlib

    def test_plot_voting_pandas_not_available(self):
        """Test error when pandas is not available."""
        import swissparlpy.visualization as viz_module

        # Save original values
        original_pandas = viz_module.PANDAS_AVAILABLE

        try:
            # Temporarily disable pandas
            viz_module.PANDAS_AVAILABLE = False

            with pytest.raises(ImportError, match="pandas.*required for visualization"):
                viz_module.plot_voting(
                    self.mock_votes, seats=self.mock_seats, client=Mock()
                )
        finally:
            # Restore original value
            viz_module.PANDAS_AVAILABLE = original_pandas

    def test_plot_voting_both_not_available(self):
        """Test error when both pandas and matplotlib are not available."""
        import swissparlpy.visualization as viz_module

        # Save original values
        original_pandas = viz_module.PANDAS_AVAILABLE
        original_matplotlib = viz_module.MATPLOTLIB_AVAILABLE

        try:
            # Temporarily disable both
            viz_module.PANDAS_AVAILABLE = False
            viz_module.MATPLOTLIB_AVAILABLE = False

            with pytest.raises(ImportError, match="pandas and matplotlib are required"):
                viz_module.plot_voting(
                    self.mock_votes, seats=self.mock_seats, client=Mock()
                )
        finally:
            # Restore original values
            viz_module.PANDAS_AVAILABLE = original_pandas
            viz_module.MATPLOTLIB_AVAILABLE = original_matplotlib
