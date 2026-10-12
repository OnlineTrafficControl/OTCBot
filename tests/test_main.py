import otc_bot.__main__ as main_module


class FakeBot:

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def run(self, token: str) -> None:
        if self.error is not None:
            raise self.error


def test_main_success(monkeypatch) -> None:
    bot = FakeBot()

    monkeypatch.setattr(main_module, "create_bot", lambda: bot)
    monkeypatch.setattr(main_module, "BOT_TOKEN", "test-token")

    monkeypatch.setattr(main_module, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_notice", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_critical", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_exception", lambda *a, **k: None)

    results = []
    monkeypatch.setattr(
        main_module,
        "close_logger",
        lambda **kwargs: results.append(kwargs["result"]),
    )

    main_module.main()

    assert results == ["SUCCESS"]


def test_main_login_failure(monkeypatch) -> None:
    bot = FakeBot(main_module.LoginFailure("invalid token"))

    monkeypatch.setattr(main_module, "create_bot", lambda: bot)
    monkeypatch.setattr(main_module, "BOT_TOKEN", "invalid-token")

    monkeypatch.setattr(main_module, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_notice", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_exception", lambda *a, **k: None)

    critical_logs = []
    monkeypatch.setattr(
        main_module,
        "log_critical",
        lambda message, **kwargs: critical_logs.append(message),
    )

    results = []
    monkeypatch.setattr(
        main_module,
        "close_logger",
        lambda **kwargs: results.append(kwargs["result"]),
    )

    main_module.main()

    assert results == ["FAILURE"]
    assert any("token" in message.lower() for message in critical_logs)


def test_main_keyboard_interrupt(monkeypatch) -> None:
    bot = FakeBot(KeyboardInterrupt())

    monkeypatch.setattr(main_module, "create_bot", lambda: bot)
    monkeypatch.setattr(main_module, "BOT_TOKEN", "test-token")

    monkeypatch.setattr(main_module, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_critical", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_exception", lambda *a, **k: None)

    notices = []
    monkeypatch.setattr(
        main_module,
        "log_notice",
        lambda message, **kwargs: notices.append(message),
    )

    results = []
    monkeypatch.setattr(
        main_module,
        "close_logger",
        lambda **kwargs: results.append(kwargs["result"]),
    )

    main_module.main()

    assert results == ["SUCCESS"]
    assert any("shutdown" in message.lower() for message in notices)


def test_main_unexpected_error(monkeypatch) -> None:
    bot = FakeBot(RuntimeError("unexpected failure"))

    monkeypatch.setattr(main_module, "create_bot", lambda: bot)
    monkeypatch.setattr(main_module, "BOT_TOKEN", "test-token")

    monkeypatch.setattr(main_module, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_notice", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_critical", lambda *a, **k: None)

    exceptions = []
    monkeypatch.setattr(
        main_module,
        "log_exception",
        lambda message, **kwargs: exceptions.append(message),
    )

    results = []
    monkeypatch.setattr(
        main_module,
        "close_logger",
        lambda **kwargs: results.append(kwargs["result"]),
    )

    main_module.main()

    assert results == ["FAILURE"]
    assert len(exceptions) == 1


def test_main_bot_creation_failure(monkeypatch) -> None:
    def fail_creation():
        raise RuntimeError("creation failed")

    monkeypatch.setattr(main_module, "create_bot", fail_creation)
    monkeypatch.setattr(main_module, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_notice", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "log_critical", lambda *a, **k: None)

    exceptions = []
    monkeypatch.setattr(
        main_module,
        "log_exception",
        lambda message, **kwargs: exceptions.append(message),
    )

    results = []
    monkeypatch.setattr(
        main_module,
        "close_logger",
        lambda **kwargs: results.append(kwargs["result"]),
    )

    main_module.main()

    assert results == ["FAILURE"]
    assert len(exceptions) == 1
