import src.trading_bot.config as config


def test_intraday_preset_applies_defaults(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("TRADING_PRESET", "intraday")
    monkeypatch.delenv("SCAN_INTERVAL_MIN", raising=False)
    monkeypatch.delenv("MIN_SCORE", raising=False)
    monkeypatch.delenv("SIGNAL_EVAL_WINDOW_MIN", raising=False)

    settings = config.load_settings()

    assert settings.trading_preset == "intraday"
    assert settings.scan_interval_min == 5
    assert settings.min_score == 50
    assert settings.signal_eval_window_min == 180


def test_env_has_priority_over_preset(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("TRADING_PRESET", "intraday")
    monkeypatch.setenv("SCAN_INTERVAL_MIN", "7")

    settings = config.load_settings()

    assert settings.scan_interval_min == 7


def test_unknown_preset_falls_back_to_mvp(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("TRADING_PRESET", "unknown")
    monkeypatch.delenv("SCAN_INTERVAL_MIN", raising=False)

    settings = config.load_settings()

    assert settings.trading_preset == "mvp"
    assert settings.scan_interval_min == 15
