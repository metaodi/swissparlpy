import mock
import os
from conftest import fixture_content

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class SwissParlTestCase:
    def setUp(self):
        self.session_mock = mock.MagicMock()
        self._setup_session_mock(self.session_mock)

    def _setup_session_mock(self, session_mock, filename=None):
        if not filename:
            filename = self._testMethodName + ".json"

        content = fixture_content(filename)
        session_mock.return_value.get.return_value = mock.MagicMock(content=content)  # noqa
