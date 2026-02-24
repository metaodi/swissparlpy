import pytest


class TestBaseBackendAbstractMethods:
    """Test that BaseBackend and BaseResponse are properly abstract"""

    def test_base_backend_cannot_be_instantiated(self):
        """Test that BaseBackend cannot be instantiated directly"""
        from swissparlpy.backends.base import BaseBackend

        with pytest.raises(TypeError):
            BaseBackend()  # type: ignore

    def test_base_response_cannot_be_instantiated(self):
        """Test that BaseResponse cannot be instantiated directly"""
        from swissparlpy.backends.base import BaseResponse

        with pytest.raises(TypeError):
            BaseResponse()  # type: ignore

    def test_base_response_to_dataframe_without_pandas(self):
        """Test BaseResponse.to_dataframe() without pandas"""
        from swissparlpy.backends.base import BaseResponse
        import swissparlpy.backends.base as base_module

        # Create a mock concrete implementation
        class MockResponse(BaseResponse):
            def __len__(self):
                return 1

            @property
            def _records_loaded_count(self):
                return 1

            def __iter__(self):
                return iter([{"id": 1}])

            def __getitem__(self, key):
                return {"id": 1}

            def to_dict_list(self):
                return [{"id": 1}]

            @property
            def variables(self):
                return ["id"]

            @property
            def table(self):
                return "test"

        mock_response = MockResponse()

        # Temporarily disable pandas
        original_pandas = base_module.PANDAS_AVAILABLE
        try:
            base_module.PANDAS_AVAILABLE = False

            with pytest.raises(ImportError, match="pandas is not installed"):
                mock_response.to_dataframe()
        finally:
            base_module.PANDAS_AVAILABLE = original_pandas
