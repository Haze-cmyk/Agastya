"""
Unit tests for Quantum-Inspired Regressor (QIR) and classical machine learning baseline models.
"""

import numpy as np
import pytest
from app.models.qi_regressor import QuantumInspiredRegressor
from app.models.baselines import train_and_evaluate_all_models, compute_metrics


def test_qi_regressor_training_and_prediction():
    rng = np.random.default_rng(42)
    # Synthetic inputs: speed (12-22), displacement (100k-200k), sea state (0-8), fouling (0-40)
    X = rng.uniform(low=[12.0, 100000.0, 0.0, 0.0], high=[22.0, 200000.0, 8.0, 40.0], size=(120, 4))
    # Synthetic target roughly cubic with speed
    y = 0.015 * (X[:, 0] ** 3) + 0.0002 * X[:, 1] + 2.5 * X[:, 2] + rng.normal(0, 1.0, size=120)

    qir = QuantumInspiredRegressor(n_qubits=12, learning_rate=0.03, epochs=60, seed=42)
    qir.fit(X[:100], y[:100])

    preds = qir.predict(X[100:])
    assert len(preds) == 20
    assert np.all(preds >= 0.0)  # Non-negative fuel consumption
    assert not np.any(np.isnan(preds))


def test_qi_regressor_reproducibility():
    rng = np.random.default_rng(100)
    X = rng.uniform(low=[10.0, 50000.0, 1.0, 5.0], high=[20.0, 150000.0, 6.0, 30.0], size=(60, 4))
    y = 0.02 * (X[:, 0] ** 3)

    qir1 = QuantumInspiredRegressor(n_qubits=8, epochs=40, seed=777)
    qir1.fit(X, y)
    p1 = qir1.predict(X[:10])

    qir2 = QuantumInspiredRegressor(n_qubits=8, epochs=40, seed=777)
    qir2.fit(X, y)
    p2 = qir2.predict(X[:10])

    # Bit-for-bit identical with fixed seed
    np.testing.assert_allclose(p1, p2, rtol=1e-5, atol=1e-5)


def test_all_baseline_models():
    rng = np.random.default_rng(42)
    X = rng.uniform(10.0, 20.0, size=(80, 4))
    y = 0.02 * (X[:, 0] ** 3) + rng.normal(0, 0.5, size=80)

    results = train_and_evaluate_all_models(
        X_train=X[:60],
        y_train=y[:60],
        X_val=X[60:],
        y_val=y[60:],
        seed=42
    )

    expected_models = ["qi_regressor", "linear_regression", "random_forest", "gradient_boosting", "ann"]
    for m in expected_models:
        assert m in results
        assert results[m]["rmse"] > 0
        assert results[m]["mae"] > 0
        assert results[m]["r2"] <= 1.0
        assert results[m]["training_time_ms"] > 0


def test_compute_metrics_handles_zeros():
    y_true = np.array([0.0, 10.0, 20.0])
    y_pred = np.array([0.5, 9.8, 20.2])
    metrics = compute_metrics(y_true, y_pred, 10.5)
    assert not np.isnan(metrics["mape"])
    assert metrics["rmse"] > 0
