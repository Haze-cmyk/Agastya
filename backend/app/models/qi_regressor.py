"""
Agastya Quantum-Inspired Regressor (QIR)
Qubit probability-amplitude encoding with rotation-gate updates
tuning quantum-inspired neural activation layers for non-linear fuel prediction.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import numpy as np


class QuantumInspiredRegressor:
    """
    Quantum-Inspired Regressor using Qubit angle state encoding:
      |psi_j> = cos(theta_j)|0> + sin(theta_j)|1>
    with unitary quantum rotation gate updates U(Delta theta):
      [cos(Delta theta) -sin(Delta theta); sin(Delta theta) cos(Delta theta)]
    """

    def __init__(
        self,
        n_qubits: int = 16,
        learning_rate: float = 0.03,
        epochs: int = 120,
        batch_size: int = 32,
        seed: int = 42
    ):
        self.n_qubits = n_qubits
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed

        # Model parameters
        self.W_in: Optional[np.ndarray] = None  # (n_features, n_qubits)
        self.theta_bias: Optional[np.ndarray] = None  # (n_qubits,)
        self.W_out: Optional[np.ndarray] = None  # (n_qubits * 2, 1)
        self.b_out: float = 0.0

        # Normalization statistics
        self.x_mean: Optional[np.ndarray] = None
        self.x_std: Optional[np.ndarray] = None
        self.y_mean: float = 0.0
        self.y_std: float = 1.0

        self.fitted_: bool = False

    def _init_weights(self, n_features: int, rng: np.random.Generator) -> None:
        # Initialize input projection into quantum phase space [-pi/2, pi/2]
        self.W_in = rng.normal(0.0, 0.5, size=(n_features, self.n_qubits))
        self.theta_bias = rng.uniform(-np.pi / 4.0, np.pi / 4.0, size=(self.n_qubits,))
        # Hidden features: [sin^2(theta), cos(2*theta)] -> dimension is n_qubits * 2
        self.W_out = rng.normal(0.0, 0.2, size=(self.n_qubits * 2, 1))
        self.b_out = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> QuantumInspiredRegressor:
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).reshape(-1, 1)

        rng = np.random.default_rng(self.seed)
        n_samples, n_features = X.shape

        # Normalize features
        self.x_mean = np.mean(X, axis=0)
        self.x_std = np.std(X, axis=0) + 1e-8
        X_norm = (X - self.x_mean) / self.x_std

        self.y_mean = float(np.mean(y))
        self.y_std = float(np.std(y)) + 1e-8
        y_norm = (y - self.y_mean) / self.y_std

        self._init_weights(n_features, rng)

        # Quantum rotation velocity momentum
        v_W_in = np.zeros_like(self.W_in)
        v_bias = np.zeros_like(self.theta_bias)
        v_W_out = np.zeros_like(self.W_out)
        momentum = 0.85

        # Training loop with mini-batches
        indices = np.arange(n_samples)
        for epoch in range(self.epochs):
            rng.shuffle(indices)
            for start_idx in range(0, n_samples, self.batch_size):
                end_idx = min(start_idx + self.batch_size, n_samples)
                batch_idx = indices[start_idx:end_idx]
                X_b = X_norm[batch_idx]
                y_b = y_norm[batch_idx]
                b_size = len(batch_idx)

                # Forward pass:
                # 1. Compute qubit phase angles theta in [-pi, pi]
                theta = np.dot(X_b, self.W_in) + self.theta_bias  # (b_size, n_qubits)

                # 2. Quantum probability-amplitude representations
                # p_amplitude = sin^2(theta), harmonic = cos(2*theta)
                p_amp = np.sin(theta) ** 2
                harmonic = np.cos(2.0 * theta)
                phi = np.hstack([p_amp, harmonic])  # (b_size, n_qubits * 2)

                # 3. Output prediction
                y_pred = np.dot(phi, self.W_out) + self.b_out  # (b_size, 1)

                # Loss: Mean Squared Error
                error = y_pred - y_b  # (b_size, 1)

                # Backward pass (Quantum rotation gate updates):
                grad_W_out = np.dot(phi.T, error) / b_size
                grad_b_out = float(np.mean(error))

                # Gradient through quantum state representation
                grad_phi = np.dot(error, self.W_out.T)  # (b_size, n_qubits * 2)
                grad_p_amp = grad_phi[:, :self.n_qubits]
                grad_harmonic = grad_phi[:, self.n_qubits:]

                # d(sin^2(theta))/d(theta) = 2*sin(theta)*cos(theta) = sin(2*theta)
                # d(cos(2*theta))/d(theta) = -2*sin(2*theta)
                sin_2theta = np.sin(2.0 * theta)
                d_theta = grad_p_amp * sin_2theta - 2.0 * grad_harmonic * sin_2theta  # (b_size, n_qubits)

                grad_W_in = np.dot(X_b.T, d_theta) / b_size
                grad_bias = np.mean(d_theta, axis=0)

                # Unitary rotation update with momentum
                v_W_in = momentum * v_W_in - self.learning_rate * grad_W_in
                v_bias = momentum * v_bias - self.learning_rate * grad_bias
                v_W_out = momentum * v_W_out - self.learning_rate * grad_W_out

                self.W_in += v_W_in
                self.theta_bias += v_bias
                self.W_out += v_W_out
                self.b_out -= self.learning_rate * grad_b_out

        self.fitted_ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.fitted_:
            raise ValueError("Model is not fitted yet.")

        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        X_norm = (X - self.x_mean) / self.x_std
        theta = np.dot(X_norm, self.W_in) + self.theta_bias
        p_amp = np.sin(theta) ** 2
        harmonic = np.cos(2.0 * theta)
        phi = np.hstack([p_amp, harmonic])

        y_norm_pred = np.dot(phi, self.W_out) + self.b_out
        y_pred = y_norm_pred * self.y_std + self.y_mean
        # Fuel consumption cannot be negative
        return np.maximum(y_pred.flatten(), 0.0)
