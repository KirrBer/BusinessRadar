import pytest

from ml_core import startup


def test_startup_uses_real_data_by_default(monkeypatch):
    calls = []
    monkeypatch.delenv("BUSINESSRADAR_DEMO", raising=False)
    monkeypatch.setenv("BUSINESSRADAR_DATA_DIR", "/real/business-data")
    monkeypatch.setattr(startup, "train_rf", lambda **kwargs: calls.append(("rf", kwargs)))
    monkeypatch.setattr(startup, "train_kmeans", lambda **kwargs: calls.append(("kmeans", kwargs)))

    startup.train_models()

    assert calls == [
        ("rf", {"data_dir": "/real/business-data", "demo": False}),
        ("kmeans", {"data_dir": "/real/business-data", "demo": False}),
    ]


def test_synthetic_training_requires_explicit_demo_flag(monkeypatch):
    calls = []
    monkeypatch.setenv("BUSINESSRADAR_DEMO", "true")
    monkeypatch.setattr(startup, "train_rf", lambda **kwargs: calls.append(("rf", kwargs)))
    monkeypatch.setattr(startup, "train_kmeans", lambda **kwargs: calls.append(("kmeans", kwargs)))

    startup.train_models()

    assert [kwargs["demo"] for _, kwargs in calls] == [True, True]


def test_real_startup_fails_when_training_data_is_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("BUSINESSRADAR_DEMO", raising=False)
    monkeypatch.setenv("BUSINESSRADAR_DATA_DIR", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="addresses.csv"):
        startup.train_models()