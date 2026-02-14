"""
Example script demonstrating the plot_voting visualization function.

This script shows how to visualize voting results from the Swiss National Council
using different themes and options.
"""

import swissparlpy as spp
import pandas as pd

# Note: This example requires matplotlib to be installed
# Install with: pip install matplotlib

try:
    import matplotlib.pyplot as plt
    from swissparlpy import plot_voting
except ImportError:
    print("This example requires matplotlib. Install with: pip install matplotlib")
    exit(1)


def example_basic_visualization():
    """Basic visualization with default scoreboard theme."""
    print("Example 1: Basic visualization with scoreboard theme")
    print("=" * 60)
    
    # Get voting data for a specific vote
    # Note: This will only work if you have access to the Swiss Parliament API
    try:
        votes = spp.get_data("Voting", Language="DE", IdVote=23458)
        votes_df = pd.DataFrame(votes)
        
        # Create visualization
        fig = plot_voting(votes_df, theme='scoreboard', result=True)
        plt.savefig('voting_scoreboard.png', dpi=150, bbox_inches='tight')
        print("✓ Saved visualization as 'voting_scoreboard.png'")
        plt.close()
    except Exception as e:
        print(f"✗ Could not create visualization: {e}")
        print("  (This is expected if you don't have API access)")


def example_different_themes():
    """Demonstrate different visualization themes."""
    print("\nExample 2: Different themes")
    print("=" * 60)
    
    themes = ['scoreboard', 'sym1', 'sym2', 'poly1', 'poly2', 'poly3']
    
    try:
        votes = spp.get_data("Voting", Language="DE", IdVote=23458)
        votes_df = pd.DataFrame(votes)
        
        for theme in themes:
            fig = plot_voting(votes_df, theme=theme, result=True)
            filename = f'voting_{theme}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"✓ Saved {filename}")
            plt.close()
    except Exception as e:
        print(f"✗ Could not create visualizations: {e}")


def example_with_highlighting():
    """Example with parliamentary group highlighting."""
    print("\nExample 3: Highlighting a parliamentary group")
    print("=" * 60)
    
    try:
        votes = spp.get_data("Voting", Language="DE", IdVote=23458)
        votes_df = pd.DataFrame(votes)
        
        # Highlight parliamentary group number 2
        fig = plot_voting(
            votes_df, 
            theme='poly2',
            highlight={'ParlGroupNumber': [2]},
            result=True
        )
        plt.savefig('voting_highlighted.png', dpi=150, bbox_inches='tight')
        print("✓ Saved visualization with highlighting as 'voting_highlighted.png'")
        plt.close()
    except Exception as e:
        print(f"✗ Could not create visualization: {e}")


def example_with_mock_data():
    """Example using mock data (works without API access)."""
    print("\nExample 4: Using mock data (no API required)")
    print("=" * 60)
    
    # Create mock voting data
    import numpy as np
    
    # Create mock data for 200 seats
    mock_votes = pd.DataFrame({
        'PersonNumber': range(1, 201),
        'Decision': np.random.choice([1, 2, 3], size=200, p=[0.5, 0.3, 0.2]),
        'DecisionText': ['Ja' if d == 1 else 'Nein' if d == 2 else 'Enthaltung' 
                         for d in np.random.choice([1, 2, 3], size=200, p=[0.5, 0.3, 0.2])],
        'IdVote': [23458] * 200,
        'ParlGroupNumber': np.random.choice([1, 2, 3, 4], size=200)
    })
    
    # Create mock seats data
    mock_seats = pd.DataFrame({
        'SeatNumber': range(1, 201),
        'PersonNumber': range(1, 201)
    })
    
    try:
        # Create visualizations with different themes
        for theme in ['scoreboard', 'poly2']:
            fig = plot_voting(
                mock_votes, 
                seats=mock_seats,
                theme=theme,
                result=True
            )
            filename = f'voting_mock_{theme}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"✓ Saved {filename}")
            plt.close()
        
        # Create with highlighting
        fig = plot_voting(
            mock_votes,
            seats=mock_seats, 
            theme='poly2',
            highlight={'ParlGroupNumber': [2]},
            result=True
        )
        plt.savefig('voting_mock_highlighted.png', dpi=150, bbox_inches='tight')
        print("✓ Saved voting_mock_highlighted.png")
        plt.close()
        
    except Exception as e:
        print(f"✗ Could not create visualization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("Swiss Parliament Voting Visualization Examples")
    print("=" * 60)
    
    # Try basic visualization (requires API access)
    # example_basic_visualization()
    # example_different_themes()
    # example_with_highlighting()
    
    # This example works without API access
    example_with_mock_data()
    
    print("\n" + "=" * 60)
    print("Done! Check the generated PNG files.")
