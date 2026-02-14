"""Tests for the visualization module."""
import pytest
import pandas as pd
import numpy as np

# Check if visualization dependencies are available
try:
    from swissparlpy import plot_voting
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for tests
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


@pytest.mark.skipif(not VISUALIZATION_AVAILABLE, reason="matplotlib not installed")
class TestVisualization:
    """Test cases for plot_voting function."""
    
    def setup_method(self):
        """Set up test data."""
        # Create mock voting data
        np.random.seed(42)
        self.mock_votes = pd.DataFrame({
            'PersonNumber': range(1, 201),
            'Decision': np.random.choice([1, 2, 3], size=200, p=[0.5, 0.3, 0.2]),
            'DecisionText': ['Ja' if d == 1 else 'Nein' if d == 2 else 'Enthaltung' 
                             for d in np.random.choice([1, 2, 3], size=200, p=[0.5, 0.3, 0.2])],
            'ParlGroupNumber': np.random.choice([1, 2, 3, 4], size=200)
        })
        
        self.mock_seats = pd.DataFrame({
            'SeatNumber': range(1, 201),
            'PersonNumber': range(1, 201)
        })
    
    def teardown_method(self):
        """Clean up after each test."""
        plt.close('all')
    
    def test_plot_voting_basic(self):
        """Test basic plot_voting functionality."""
        fig = plot_voting(self.mock_votes, seats=self.mock_seats, theme='scoreboard')
        assert fig is not None
        assert isinstance(fig, plt.Figure)
    
    def test_plot_voting_all_themes(self):
        """Test all available themes."""
        themes = ['scoreboard', 'sym1', 'sym2', 'poly1', 'poly2', 'poly3']
        for theme in themes:
            fig = plot_voting(self.mock_votes, seats=self.mock_seats, theme=theme)
            assert fig is not None, f"Failed to create figure with theme {theme}"
            plt.close(fig)
    
    def test_plot_voting_with_result(self):
        """Test plot_voting with result annotation."""
        fig = plot_voting(self.mock_votes, seats=self.mock_seats, theme='scoreboard', result=True)
        assert fig is not None
    
    def test_plot_voting_with_highlight(self):
        """Test plot_voting with highlighting."""
        fig = plot_voting(
            self.mock_votes, 
            seats=self.mock_seats,
            theme='poly2',
            highlight={'ParlGroupNumber': [2]}
        )
        assert fig is not None
    
    def test_plot_voting_missing_columns(self):
        """Test that missing required columns raise ValueError."""
        # Missing Decision column
        incomplete_votes = self.mock_votes.drop(columns=['Decision'])
        
        with pytest.raises(ValueError, match="Missing required columns"):
            plot_voting(incomplete_votes, seats=self.mock_seats)
    
    def test_plot_voting_invalid_theme(self):
        """Test that invalid theme raises ValueError."""
        with pytest.raises(ValueError, match="Unknown theme"):
            plot_voting(self.mock_votes, seats=self.mock_seats, theme='invalid_theme')
    
    def test_plot_voting_with_list_input(self):
        """Test that list input is converted to DataFrame."""
        votes_list = self.mock_votes.to_dict('records')
        seats_list = self.mock_seats.to_dict('records')
        
        fig = plot_voting(votes_list, seats=seats_list, theme='scoreboard')
        assert fig is not None
    
    def test_plot_voting_custom_point_settings(self):
        """Test custom point shape and size."""
        fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme='scoreboard',
            point_shape='s',  # square
            point_size=100
        )
        assert fig is not None
    
    def test_plot_voting_result_text_size(self):
        """Test custom result text size."""
        fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme='scoreboard',
            result=True,
            result_size=16
        )
        assert fig is not None
    
    def test_plot_voting_with_custom_ax(self):
        """Test providing custom axes."""
        fig, ax = plt.subplots()
        result_fig = plot_voting(
            self.mock_votes,
            seats=self.mock_seats,
            theme='scoreboard',
            ax=ax
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
        required_cols = ['SeatNumber', 'order', 'x', 'y', 'center_x', 'center_y']
        for col in required_cols:
            assert col in seating_plan.columns, f"Missing column: {col}"
        
        # Check data shape (200 seats * 4 corners = 800 rows)
        assert len(seating_plan) == 800, f"Expected 800 rows, got {len(seating_plan)}"
