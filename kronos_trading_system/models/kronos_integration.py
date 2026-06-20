"""
ML Integration — Kronos, RankIC, Anomaly Detection, Probability Cones

FIX-M3: RankIC evaluator (deploy gate: >0.05)
FIX-M4: Log-normal probability cone
FIX-M5: Z-score anomaly detection for bid-ask spread
A++: Student-t fat-tail option in probability cone
"""
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ProbabilityCone:
    """Price probability cone."""
    lower_68: float
    upper_68: float
    lower_95: float
    upper_95: float
    median: float
    distribution: str  # lognormal | student_t
    volatility: float


@dataclass
class RankIC:
    """Information coefficient evaluation."""
    ic_value: float
    rank_ic: float
    significant: bool
    deploy_ready: bool


@dataclass
class AnomalyScore:
    """Anomaly detection result."""
    z_score: float
    is_anomaly: bool
    severity: str  # none | low | medium | high
    feature: str


class KronosModels:
    """
    ML model integration for the KRONOS AI system.
    Probability cones, RankIC evaluation, anomaly detection.
    """

    def __init__(self):
        self.rankic_threshold = 0.05  # FIX-M3: deploy gate

    def probability_cone(
        self,
        current_price: float,
        volatility: float,
        days_ahead: int = 21,
        distribution: str = "lognormal",
        use_student_t: bool = True,
    ) -> ProbabilityCone:
        """
        Generate price probability cone.

        FIX-M4: Log-normal base implementation
        A++: Student-t fat-tail option
        """
        if distribution == "lognormal":
            mu = 0.0  # drift (assume zero for short-term)
            sigma = volatility * np.sqrt(days_ahead / 252.0)

            median = current_price * np.exp(mu * days_ahead / 365.0)

            if use_student_t:
                # Student-t with fat tails
                dof = 3  # degrees of freedom
                t_68 = self._student_t_quantile(0.84, dof)
                t_95 = self._student_t_quantile(0.975, dof)
                lower_68 = current_price * np.exp(mu * days_ahead / 365.0 - t_68 * sigma)
                upper_68 = current_price * np.exp(mu * days_ahead / 365.0 + t_68 * sigma)
                lower_95 = current_price * np.exp(mu * days_ahead / 365.0 - t_95 * sigma)
                upper_95 = current_price * np.exp(mu * days_ahead / 365.0 + t_95 * sigma)
            else:
                lower_68 = current_price * np.exp(-sigma)
                upper_68 = current_price * np.exp(sigma)
                lower_95 = current_price * np.exp(-2 * sigma)
                upper_95 = current_price * np.exp(2 * sigma)

            return ProbabilityCone(
                lower_68=round(lower_68, 2),
                upper_68=round(upper_68, 2),
                lower_95=round(lower_95, 2),
                upper_95=round(upper_95, 2),
                median=round(median, 2),
                distribution="student_t" if use_student_t else "lognormal",
                volatility=volatility,
            )

        raise ValueError(f"Unknown distribution: {distribution}")

    def _student_t_quantile(self, p: float, dof: int) -> float:
        """Approximate Student-t quantile using normal approximation for dof=3."""
        # Simple approximation for critical values
        if dof == 3:
            if p >= 0.975:
                return 3.182
            if p >= 0.84:
                return 1.25
        return 1.0

    def evaluate_rankic(self, predictions: np.ndarray, actuals: np.ndarray) -> RankIC:
        """
        FIX-M3: RankIC evaluator.
        Deploy gate: RankIC > 0.05 for production.
        """
        if len(predictions) != len(actuals) or len(predictions) < 10:
            return RankIC(ic_value=0.0, rank_ic=0.0, significant=False, deploy_ready=False)

        # Pearson correlation
        pred_rank = np.argsort(predictions)
        actual_rank = np.argsort(actuals)
        rank_diff = pred_rank - actual_rank
        n = len(predictions)
        rank_ic = 1.0 - (6 * np.sum(rank_diff ** 2)) / (n * (n ** 2 - 1))

        return RankIC(
            ic_value=float(np.corrcoef(predictions, actuals)[0, 1]),
            rank_ic=float(rank_ic),
            significant=abs(rank_ic) > self.rankic_threshold,
            deploy_ready=rank_ic > self.rankic_threshold,
        )

    def anomaly_detection(self, values: np.ndarray, feature: str = "spread") -> AnomalyScore:
        """
        FIX-M5: Z-score anomaly detection.
        Detects anomalous bid-ask spreads, volumes, etc.
        """
        if len(values) < 3:
            return AnomalyScore(z_score=0.0, is_anomaly=False, severity="none", feature=feature)

        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return AnomalyScore(z_score=0.0, is_anomaly=False, severity="none", feature=feature)

        latest = values[-1]
        z = (latest - mean) / std

        if abs(z) < 2:
            severity = "none"
            is_anomaly = False
        elif abs(z) < 3:
            severity = "low"
            is_anomaly = True
        elif abs(z) < 4:
            severity = "medium"
            is_anomaly = True
        else:
            severity = "high"
            is_anomaly = True

        return AnomalyScore(
            z_score=round(z, 2),
            is_anomaly=is_anomaly,
            severity=severity,
            feature=feature,
        )
