from types import SimpleNamespace
from unittest.mock import Mock

from app import main


def test_main_starts_streamable_http_server(monkeypatch) -> None:
    settings = SimpleNamespace(host="127.0.0.1", port=9001)
    run_mock = Mock()

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main.mcp, "run", run_mock)

    main.main()

    run_mock.assert_called_once_with(
        transport="streamable-http",
        host="127.0.0.1",
        port=9001,
    )
