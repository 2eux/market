"""
Intraday Margin Monitor — A++ Upgrade
Replaces obsolete PDTGuardrail.

PDT eliminated 4 June 2026 (FINRA Reg Notice 26-10).
Replaced by real-time intraday margin framework.

Capital Tiers:
  <$200   → Cash (T+1 settlement, no leverage)
  $200–$2k → Cash (growing toward margin threshold)
  $2k–$25k → Reg T Margin (25% maintenance, intraday margin)
  $25k+   → Full infrastructure (L2 data, co-location eval)
"""
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AccountType(Enum):
    CASH = "cash"
    MARGIN = "margin"


@dataclass
class MarginStatus:
    """Current margin/cash status."""
    account_type: AccountType
    capital: float
    buying_power: float
    maintenance_margin: float
    margin_excess: float
    cash_available: float
    t1_settlement: float
    can_short: bool
    can_use_leverage: bool


class IntradayMarginMonitor:
    """
    Manages margin/cash constraints per capital tier.
    Replaces PDTGuardrail — FINRA PDT eliminated 4 June 2026.
    """

    REG_T_MAINTENANCE_PCT = 25.0  # 25% maintenance margin
    CASH_TIER_THRESHOLD = 2000.0
    MARGIN_TIER_THRESHOLD = 2000.0
    INFRA_TIER_THRESHOLD = 25000.0

    def __init__(self, capital: float = 200.0):
        self.capital = capital

    @property
    def account_type(self) -> AccountType:
        if self.capital < self.MARGIN_TIER_THRESHOLD:
            return AccountType.CASH
        return AccountType.MARGIN

    @property
    def tier_label(self) -> str:
        if self.capital < 200:
            return "<$200 — Micro (Cash)"
        if self.capital < self.CASH_TIER_THRESHOLD:
            return "$200–$2k — Cash (Growing)"
        if self.capital < self.INFRA_TIER_THRESHOLD:
            return "$2k–$25k — Reg T Margin"
        return "$25k+ — Infrastructure Tier"

    def get_status(self) -> MarginStatus:
        """Calculate current account status."""
        acct = self.account_type

        if acct == AccountType.CASH:
            return MarginStatus(
                account_type=acct,
                capital=self.capital,
                buying_power=self.capital,  # No leverage in cash
                maintenance_margin=0.0,
                margin_excess=0.0,
                cash_available=self.capital,
                t1_settlement=self.capital,  # T+1 settlement
                can_short=False,
                can_use_leverage=False,
            )

        # Margin account (Reg T)
        maintenance = self.capital * (self.REG_T_MAINTENANCE_PCT / 100.0)
        buying_power = self.capital * 2  # Reg T: 2x leverage
        margin_excess = self.capital - maintenance

        return MarginStatus(
            account_type=acct,
            capital=self.capital,
            buying_power=buying_power,
            maintenance_margin=maintenance,
            margin_excess=margin_excess,
            cash_available=self.capital,
            t1_settlement=0.0,
            can_short=True,
            can_use_leverage=True,
        )

    def can_open_position(self, notional: float) -> tuple[bool, str]:
        """Check if a position can be opened within constraints."""
        status = self.get_status()

        if status.account_type == AccountType.CASH:
            if notional > status.cash_available:
                return False, f"Notional ${notional:.2f} exceeds cash available ${status.cash_available:.2f}"
            t1_cost = notional
            if t1_cost > status.capital:
                return False, f"T+1 settlement requires ${t1_cost:.2f} > capital ${status.capital:.2f}"
            return True, "OK (cash account)"

        # Margin
        if notional > status.buying_power:
            return False, f"Notional ${notional:.2f} exceeds buying power ${status.buying_power:.2f}"
        post_trade_excess = status.capital - (notional * (status.REG_T_MAINTENANCE_PCT / 100.0))
        if post_trade_excess < 0:
            return False, f"Post-trade margin excess would be negative"
        return True, "OK (margin account)"

    def capital_tier_info(self) -> dict:
        """Return human-readable tier information."""
        return {
            "tier": self.tier_label,
            "account_type": self.account_type.value,
            "capital": self.capital,
            "pdt_applies": False,
            "pdt_eliminated": True,
            "finra_notice": "26-10",
            "elimination_date": "2026-06-04",
        }
