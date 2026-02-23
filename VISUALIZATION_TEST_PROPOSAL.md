# Proposed Tests for Visualization Module

## Overview

The visualization module currently has only **13% coverage** (21 lines covered out of 161 lines). This is the biggest gap in the test coverage. The existing visualization tests are failing due to network connectivity issues in the test environment.

## Current Issues

The existing tests in `tests/visualization_test.py` are all failing because:
1. They attempt to connect to `ws.parlament.ch` which is blocked in the sandbox
2. They don't properly mock the HTTP requests for seat data
3. They rely on external data that isn't available in the test environment

## Proposed Test Strategy

### 1. Fix Existing Tests with Proper Mocking

All existing visualization tests need to be updated to use `@responses.activate` decorator and mock all HTTP requests.

**Example Fix**:
```python
@responses.activate
def test_plot_voting_basic(self, metadata, voting_data, seats_data):
    """Test basic plot_voting functionality with mocked data"""
    # Mock metadata request
    responses.add(
        responses.GET,
        f"{SERVICE_URL}/$metadata",
        content_type="text/xml",
        body=metadata,
        status=200,
    )

    # Mock voting data request
    responses.add(
        responses.GET,
        f"{SERVICE_URL}/Voting?...",
        content_type="text/xml",
        body=voting_data,
        status=200,
    )

    # Mock seat mapping request
    responses.add(
        responses.GET,
        f"{SERVICE_URL}/SeatOrganisationNr?...",
        content_type="text/xml",
        body=seats_data,
        status=200,
    )

    # Now test plot_voting
    import swissparlpy as spp
    votes = spp.get_data("Voting", Language="DE", IdVote=23458)
    fig = spp.plot_voting(votes, theme='scoreboard')

    assert fig is not None
```

### 2. New Test Cases for Uncovered Functionality

#### Theme Testing
```python
@pytest.mark.parametrize("theme", [
    "scoreboard", "sym1", "sym2", "poly1", "poly2", "poly3"
])
def test_plot_voting_all_themes(votes_df, theme):
    """Test all available themes"""
    fig = plot_voting(votes_df, theme=theme)
    assert fig is not None

def test_plot_voting_invalid_theme():
    """Test error handling for invalid theme"""
    votes_df = pd.DataFrame([...])
    with pytest.raises(ValueError, match="Invalid theme"):
        plot_voting(votes_df, theme="invalid_theme")
```

#### Highlight Functionality
```python
def test_plot_voting_highlight_by_parl_group():
    """Test highlighting specific parliamentary groups"""
    votes_df = pd.DataFrame([...])
    fig = plot_voting(
        votes_df,
        highlight={"ParlGroupCode": ["S", "V"]},
        theme="poly1"
    )
    assert fig is not None

def test_plot_voting_highlight_by_vote():
    """Test highlighting by vote decision"""
    votes_df = pd.DataFrame([...])
    fig = plot_voting(
        votes_df,
        highlight={"DecisionText": ["Ja"]},
        theme="scoreboard"
    )
    assert fig is not None
```

#### Result Display
```python
def test_plot_voting_with_result_display():
    """Test displaying voting results on plot"""
    votes_df = pd.DataFrame([...])
    fig = plot_voting(votes_df, result=True, theme="scoreboard")
    assert fig is not None

def test_plot_voting_result_text_size():
    """Test custom result text size"""
    votes_df = pd.DataFrame([...])
    fig = plot_voting(
        votes_df,
        result=True,
        result_text_size=20,
        theme="scoreboard"
    )
    assert fig is not None
```

#### Input Validation
```python
def test_plot_voting_missing_required_columns():
    """Test error handling for missing required columns"""
    incomplete_df = pd.DataFrame([
        {"IdVote": 1, "PersonNumber": 101}
        # Missing DecisionText, ParlGroupCode, etc.
    ])
    with pytest.raises(ValueError, match="Missing required columns"):
        plot_voting(incomplete_df)

def test_plot_voting_with_list_input():
    """Test plot_voting accepts list of dicts"""
    votes_list = [
        {
            "IdVote": 23458,
            "PersonNumber": 101,
            "DecisionText": "Ja",
            "ParlGroupCode": "S"
        }
    ]
    fig = plot_voting(votes_list)
    assert fig is not None

def test_plot_voting_with_swissparlresponse():
    """Test plot_voting accepts SwissParlResponse"""
    # Mock response
    response = Mock(spec=SwissParlResponse)
    # Set up mock to behave like a response
    fig = plot_voting(response)
    assert fig is not None
```

#### Seat Mapping
```python
def test_get_seat_mapping():
    """Test seat mapping retrieval"""
    from swissparlpy.visualization import _get_seat_mapping

    seats = _get_seat_mapping()
    assert isinstance(seats, dict)
    assert len(seats) > 0

def test_get_seat_mapping_caching():
    """Test that seat mapping is cached"""
    from swissparlpy.visualization import _get_seat_mapping

    # First call
    seats1 = _get_seat_mapping()

    # Second call should use cache
    seats2 = _get_seat_mapping()

    assert seats1 == seats2

def test_custom_seat_mapping():
    """Test providing custom seat mapping"""
    custom_seats = {
        101: (0, 0),
        102: (0, 1),
        # ...
    }
    votes_df = pd.DataFrame([...])
    fig = plot_voting(votes_df, seats=custom_seats)
    assert fig is not None
```

#### Point Settings
```python
def test_plot_voting_custom_point_settings():
    """Test custom point marker settings"""
    votes_df = pd.DataFrame([...])
    fig = plot_voting(
        votes_df,
        theme="sym1",
        point_size=15,
        point_marker="s",  # square
        point_edge_width=2
    )
    assert fig is not None
```

#### Matplotlib Integration
```python
def test_plot_voting_custom_axes():
    """Test plotting on custom matplotlib axes"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 8))
    votes_df = pd.DataFrame([...])

    result_fig = plot_voting(votes_df, ax=ax)

    assert result_fig == fig
    plt.close(fig)

def test_plot_voting_returns_figure():
    """Test that plot_voting returns a Figure object"""
    import matplotlib.pyplot as plt

    votes_df = pd.DataFrame([...])
    fig = plot_voting(votes_df)

    assert isinstance(fig, plt.Figure)
    plt.close(fig)
```

### 3. Test Fixtures for Visualization

Create comprehensive fixtures in `conftest.py`:

```python
@pytest.fixture
def sample_voting_data():
    """Sample voting data for testing"""
    return [
        {
            "IdVote": 23458,
            "PersonNumber": 101,
            "FirstName": "Maya",
            "LastName": "Graf",
            "DecisionText": "Ja",
            "ParlGroupCode": "G",
            "ParlGroupName": "Grüne",
            "Canton": "BL"
        },
        {
            "IdVote": 23458,
            "PersonNumber": 102,
            "FirstName": "Thomas",
            "LastName": "Aeschi",
            "DecisionText": "Nein",
            "ParlGroupCode": "V",
            "ParlGroupName": "SVP",
            "Canton": "ZG"
        },
        # Add more sample data...
    ]

@pytest.fixture
def sample_votes_df(sample_voting_data):
    """Sample voting DataFrame for testing"""
    import pandas as pd
    return pd.DataFrame(sample_voting_data)

@pytest.fixture
def sample_seat_mapping():
    """Sample seat mapping for testing"""
    return {
        101: (5, 3),
        102: (2, 7),
        # Add more seat mappings...
    }
```

## Implementation Priority

### High Priority (Should be implemented immediately)
1. ✅ Fix all existing tests to properly mock HTTP requests
2. ✅ Add tests for all theme configurations
3. ✅ Add tests for result display functionality
4. ✅ Add input validation tests

### Medium Priority (Important but not critical)
5. ✅ Add tests for highlight functionality
6. ✅ Add tests for custom point settings
7. ✅ Add tests for seat mapping

### Low Priority (Nice to have)
8. ✅ Add integration tests with matplotlib
9. ✅ Add performance tests for large datasets

## Expected Coverage Improvement

If all proposed tests are implemented:
- **Current**: 13% (21/161 lines)
- **Expected**: 80-90% (130-145/161 lines)
- **Overall project coverage**: 66% → 78-80%

## Lines Currently Uncovered

### Critical Uncovered Lines (Core Functionality)
- Lines 37-52: Theme configuration setup
- Lines 134-290: Main plotting logic
- Lines 295-423: Vote processing and data preparation
- Lines 434-460: Seat mapping retrieval
- Lines 475-501: Result text rendering
- Lines 513-558: Helper functions

### Less Critical (Import/Setup)
- Lines 21-22: Optional import handling
- Lines 31-32: Import error handling

## Testing Best Practices for Visualization

1. **Use Mock Data**: Never rely on external API calls
2. **Close Figures**: Always close matplotlib figures after tests to avoid memory leaks
3. **Use Temporary Files**: If testing figure saving, use temporary files
4. **Test Visual Properties**: Verify figure size, axes, labels, etc.
5. **Parameterize Tests**: Use `pytest.mark.parametrize` for testing multiple themes/options

## Example Complete Test

```python
import pytest
import pandas as pd
import matplotlib.pyplot as plt
from swissparlpy.visualization import plot_voting


class TestPlotVoting:
    @pytest.fixture
    def sample_votes_df(self):
        """Create sample voting data"""
        return pd.DataFrame([
            {
                "IdVote": 23458,
                "PersonNumber": i,
                "FirstName": f"Person{i}",
                "LastName": f"Last{i}",
                "DecisionText": "Ja" if i % 2 == 0 else "Nein",
                "ParlGroupCode": ["S", "V", "G", "M"][i % 4],
                "ParlGroupName": ["SP", "SVP", "Grüne", "Mitte"][i % 4],
                "Canton": "ZH"
            }
            for i in range(100, 200)
        ])

    @pytest.fixture
    def sample_seats(self):
        """Create sample seat mapping"""
        return {i: (i % 10, i // 10) for i in range(100, 200)}

    def test_basic_plot(self, sample_votes_df, sample_seats):
        """Test basic plotting functionality"""
        fig = plot_voting(
            sample_votes_df,
            seats=sample_seats,
            theme='scoreboard'
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)

        # Verify figure has axes
        assert len(fig.axes) > 0

        plt.close(fig)

    @pytest.mark.parametrize("theme", [
        "scoreboard", "sym1", "sym2", "poly1", "poly2", "poly3"
    ])
    def test_all_themes(self, sample_votes_df, sample_seats, theme):
        """Test all available themes"""
        fig = plot_voting(
            sample_votes_df,
            seats=sample_seats,
            theme=theme
        )

        assert fig is not None
        plt.close(fig)

    def test_with_result_display(self, sample_votes_df, sample_seats):
        """Test result display"""
        fig = plot_voting(
            sample_votes_df,
            seats=sample_seats,
            result=True,
            theme='scoreboard'
        )

        assert fig is not None

        # Check that text was added to the figure
        # (result counts should be displayed)

        plt.close(fig)

    def test_highlight_groups(self, sample_votes_df, sample_seats):
        """Test highlighting functionality"""
        fig = plot_voting(
            sample_votes_df,
            seats=sample_seats,
            highlight={"ParlGroupCode": ["S"]},
            theme='poly1'
        )

        assert fig is not None
        plt.close(fig)
```

## Conclusion

Implementing these tests will:
1. ✅ Increase visualization module coverage from 13% to 80-90%
2. ✅ Increase overall project coverage from 66% to ~78-80%
3. ✅ Ensure visualization functionality is properly tested
4. ✅ Make the codebase more maintainable and reliable

The key to success is proper mocking of all external dependencies (HTTP requests, seat data) so tests can run in isolation.
