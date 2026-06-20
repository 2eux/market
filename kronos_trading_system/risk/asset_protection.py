"""
Asset Protection — RULES 2: Hedging, Rotation & Position Sizing

T2 — Defense: Put Options, Inverse ETFs, Safe Haven rotation
T3 — Alpha: Altman Z-Score value hunting, ATR sizing, DCA Tactical

FIX-A through FIX-J: All position sizing, hedging, and rotation fixes.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PositionSizing:
    """Calculated position size with risk parameters."""
    shares: int
    notional: float
    risk_amount: float
    stop_loss: float
    target: float
    atr_at_entry: float
    r_multiple: float


@dataclass
class HedgeRecommendation:
    """Hedging recommendation."""
    hedge_type: str  # put | inverse_etf | safe_haven
    instrument: str
    allocation_pct: float
    cost: float
    duration_days: int


class AssetProtection:
    """
    T2 — Portfolio protection.
    Manages put options, inverse ETFs, and safe haven rotation.
    """

    SAFE_HAVENS = ["GLD", "TLT", "USD", "XLP"]
    INVERSE_ETFS = ["SH", "PSQ"]

    def __init__(self, portfolio_value: float):
        self.portfolio_value = portfolio_value
        self.hedges: list = []

    def assess_hedge_need(self, crash_score: float, regime: str) -> Optional[HedgeRecommendation]:
        """Determine if hedging is needed based on crash score."""
        if crash_score < 0.3:
            return None
        if crash_score < 0.5:
            return HedgeRecommendation(
                hedge_type="safe_haven",
                instrument="GLD",
                allocation_pct=10.0,
                cost=self.portfolio_value * 0.001,
                duration_days=30,
            )
        return HedgeRecommendation(
            hedge_type="put",
            instrument="SPY",
            allocation_pct=min(crash_score * 30, 50.0),
            cost=self.portfolio_value * 0.05 * crash_score,
            duration_days=min(int(90 * crash_score), 90),
        )

    def position_size(
        self,
        capital: float,
        price: float,
        atr: float,
        risk_per_trade_pct: float = 1.0,
        max_position_pct: float = 10.0,
    ) -> PositionSizing:
        """ATR-based position sizing (FIX-E)."""
        risk_capital = capital * (risk_per_trade_pct / 100.0)
        max_notional = capital * (max_position_pct / 100.0)

        # ATR-based stop distance (2x ATR)
        stop_distance = atr * 2
        shares_by_risk = int(risk_capital / stop_distance) if stop_distance > 0 else 0
        shares_by_notional = int(max_notional / price) if price > 0 else 0
        shares = min(shares_by_risk, shares_by_notional)

        notional = shares * price
        stop_loss = price - stop_distance
        target = price + (stop_distance * 2)  # 1:2 risk-reward
        r_multiple = 2.0

        return PositionSizing(
            shares=shares,
            notional=notional,
            risk_amount=shares * stop_distance,
            stop_loss=stop_loss,
            target=target,
            atr_at_entry=atr,
            r_multiple=r_multiple,
        )

    def dca_tactical(self, capital: float, price: float, atr: float, level: int = 1) -> Optional[PositionSizing]:
        """
        Tactical DCA — T3 Alpha.
        Scales in at increasing conviction levels.
        """
        if level < 1 or level > 5:
            return None
        sizing_pct = [0.2, 0.3, 0.5, 0.7, 1.0][level - 1]
        adjusted_capital = capital * sizing_pct
        return self.position_size(adjusted_capital, price, atr)
