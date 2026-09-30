"""
Agastya Machine Learning Model Benchmark Engine
Trains and validates Quantum-Inspired Regressor against classical baselines:
Linear Regression, Random Forest, Gradient Boosting, and Multi-Layer Perceptron (ANN).
"""

from __future__ import annotations
import time
from typing import Dict, Any, Tuple
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from app.models.qi_regressor import QuantumInspiredRegressor


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, train_time_ms: float) -> Dict[str, float]:
    """Computes standardized regression evaluation metrics."""
    y_true = np.asarray(y_true, dtype=np.float64).flatten()
    y_pred = np.asarray(y_pred, dtype=np.float64).flatten()

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))

    # Guard against division by zero in MAPE
    denom = np.where(np.abs(y_true) < 1e-4, 1e-4, np.abs(y_true))
    mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)

    r2 = float(r2_score(y_true, y_pred))

    return {
        "rmse": round(rmse, 3),
        "mae": round(mae, 3),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
        "training_time_ms": round(train_time_ms, 2)
    }


def train_and_evaluate_all_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    seed: int = 42
) -> Dict[str, Dict[str, float]]:
    """
    Fits and validates all 5 prediction architectures on train/validation splits.
    """
    results: Dict[str, Dict[str, float]] = {}

    # Standardize inputs for linear and neural models
    scaler_x = StandardScaler()
    X_train_scaled = scaler_x.fit_transform(X_train)
    X_val_scaled = scaler_x.transform(X_val)

    # 1. Quantum-Inspired Regressor
    t0 = time.perf_counter()
    qir = QuantumInspiredRegressor(n_qubits=16, learning_rate=0.03, epochs=100, seed=seed)
    qir.fit(X_train, y_train)
    t_qir = (time.perf_counter() - t0) * 1000.0
    preds_qir = qir.predict(X_val)
    results["qi_regressor"] = compute_metrics(y_val, preds_qir, t_qir)

    # 2. Linear Regression (Ridge)
    t0 = time.perf_counter()
    linear = Ridge(alpha=1.0, random_state=seed)
    linear.fit(X_train_scaled, y_train)
    t_linear = (time.perf_counter() - t0) * 1000.0
    preds_linear = linear.predict(X_val_scaled)
    results["linear_regression"] = compute_metrics(y_val, preds_linear, t_linear)

    # 3. Random Forest
    t0 = time.perf_counter()
    rf = RandomForestRegressor(n_estimators=60, max_depth=8, random_state=seed)
    rf.fit(X_train, y_train)
    t_rf = (time.perf_counter() - t0) * 1000.0
    preds_rf = rf.predict(X_val)
    results["random_forest"] = compute_metrics(y_val, preds_rf, t_rf)

    # 4. Gradient Boosting
    t0 = time.perf_counter()
    gb = GradientBoostingRegressor(n_estimators=80, learning_rate=0.08, max_depth=4, random_state=seed)
    gb.fit(X_train, y_train)
    t_gb = (time.perf_counter() - t0) * 1000.0
    preds_gb = gb.predict(X_val)
    results["gradient_boosting"] = compute_metrics(y_val, preds_gb, t_gb)

    # 5. Plain Multi-Layer Perceptron (ANN)
    t0 = time.perf_counter()
    mlp = MLPRegressor(hidden_layer_sizes=(32, 16), max_iter=250, random_state=seed, early_stopping=True)
    mlp.fit(X_train_scaled, y_train)
    t_mlp = (time.perf_counter() - t0) * 1000.0
    preds_mlp = mlp.predict(X_val_scaled)
    results["ann"] = compute_metrics(y_val, preds_mlp, t_mlp)

    return results
