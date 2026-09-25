"""Behaviors (plan 008, tech debt 29):
- Given LOG_LEVEL unset, when the app is created, then rizalai loggers emit
  INFO and above through a stream handler, with the logger name in the line.
- Given LOG_LEVEL=WARNING, then INFO records are not emitted.
- Given the setup runs twice, then there is still one handler.
"""

import logging

import pytest

from rizalai.config import get_settings


@pytest.fixture
def fresh_logging(monkeypatch):
    """Start without our handler, with clean settings; restore afterwards."""
    from rizalai.logging_setup import HANDLER_NAME

    logger = logging.getLogger("rizalai")
    saved = (logger.level, list(logger.handlers))
    logger.handlers = [h for h in logger.handlers if h.get_name() != HANDLER_NAME]
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    get_settings.cache_clear()
    yield logger
    logger.setLevel(saved[0])
    logger.handlers = saved[1]
    monkeypatch.undo()
    get_settings.cache_clear()


def test_info_is_emitted_with_the_logger_name(fresh_logging, capsys):
    from rizalai.main import create_app

    create_app()
    logging.getLogger("rizalai.x").info("reflection fell back")
    err = capsys.readouterr().err
    assert "INFO rizalai.x: reflection fell back" in err


def test_log_level_warning_silences_info(fresh_logging, capsys, monkeypatch):
    from rizalai.main import create_app

    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    get_settings.cache_clear()
    create_app()
    logging.getLogger("rizalai.x").info("quiet")
    logging.getLogger("rizalai.x").warning("loud")
    err = capsys.readouterr().err
    assert "quiet" not in err
    assert "WARNING rizalai.x: loud" in err


def test_configure_logging_is_idempotent(fresh_logging):
    from rizalai.logging_setup import HANDLER_NAME, configure_logging

    configure_logging("INFO")
    configure_logging("INFO")
    ours = [h for h in fresh_logging.handlers if h.get_name() == HANDLER_NAME]
    assert len(ours) == 1
