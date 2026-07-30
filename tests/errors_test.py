import pytest
from swissparlpy import errors


class TestErrorHandling:
    """Test custom error classes"""

    def test_swissparl_error(self):
        """Test SwissParlError can be raised and caught"""
        with pytest.raises(errors.SwissParlError):
            raise errors.SwissParlError("Test error")

    def test_swissparl_timeout_error(self):
        """Test SwissParlTimeoutError can be raised and caught"""
        with pytest.raises(errors.SwissParlTimeoutError):
            raise errors.SwissParlTimeoutError("Timeout error")

    def test_table_not_found_error(self):
        """Test TableNotFoundError can be raised and caught"""
        with pytest.raises(errors.TableNotFoundError):
            raise errors.TableNotFoundError("Table not found")

    def test_swissparl_http_request_error(self):
        """Test SwissParlHttpRequestError can be raised and caught"""
        with pytest.raises(errors.SwissParlHttpRequestError):
            raise errors.SwissParlHttpRequestError("HTTP request failed")

    def test_no_more_records_error(self):
        """Test NoMoreRecordsError can be raised and caught"""
        with pytest.raises(errors.NoMoreRecordsError):
            raise errors.NoMoreRecordsError("No more records")

    def test_result_very_large_warning(self):
        """Test ResultVeryLargeWarning can be raised"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Large result", errors.ResultVeryLargeWarning)
            assert len(w) == 1
            assert issubclass(w[0].category, errors.ResultVeryLargeWarning)

    def test_pagination_warning(self):
        """Test PaginationWarning can be raised"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Pagination issue", errors.PaginationWarning)
            assert len(w) == 1
            assert issubclass(w[0].category, errors.PaginationWarning)
