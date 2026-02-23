"""Additional tests to improve visualization module coverage."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


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
