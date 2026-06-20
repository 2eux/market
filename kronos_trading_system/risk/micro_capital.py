"""
Micro Capital Engine — A++ Upgrade: $200 Starting Capital Viability

MC-1: IBKR Lite execution (commission-free US stocks/ETFs, 5bps implicit spread)
MC-2: Whole-share, sub-$50 ETF universe (no fractional fees)
MC-3: Cost-aware trade gate (reject if edge < 3x round-trip cost)
MC-4: Swing not scalp (multi-hour/day holds, 10-20x less friction)
MC-5: Validation-first metric (signal accuracy + execution integrity, not $ P&L)
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TradeVerdict:
    """Cost gate result for a potential trade."""
    approved: bool
    reason: str
    round_trip_cost: float
    cost_pct: float
    expected_edge: float
    edge_to_cost_ratio: float
    capital_after: float


# Sub-$50 liquid ETFs suitable for micro capital
MICRO_ETF_UNIVERSE = [
    "SPY", "IVV", "VOO", "QQQ", "IWM", "TLT", "GLD", "SLV",
    "XLF", "XLE", "XLK", "XLV", "XLI", "XLP", "XLU", "XLY",
    "HYG", "LQD", "VNQ", "DIA", "USO", "EWJ", "EWZ",
    "EFA", "EEM", "VTI", "BND", "AGG", "TLH", "MUB",
    "GDX", "GDXJ", "ARKK", "SMH", "IBB", "KRE", "KBE",
]


@dataclass
class MicroCapitalConfig:
    """Configuration for micro capital trading."""
    capital: float = 200.00
    broker_plan: str = "lite"  # lite | tiered | fixed
    implicit_spread_bps: float = 5.0
    cost_edge_ratio: float = 3.0  # MC-3: minimum edge/cost ratio
    max_round_trip_cost_pct: float = 0.5
    universe: list = None

    def __post_init__(self):
        if self.universe is None:
            self.universe = [t for t in MICRO_ETF_UNIVERSE]


class MicroCapitalEngine:
    """
    A++: Makes $200 starting capital economically viable.

    1. IBKR Lite: $0 commissions on US stocks/ETFs
    2. Whole shares only (no fractional fees)
    3. Cost-aware gate: edge/3x round-trip cost or reject
    4. Swing holding (hours-days, not minutes)
    """

    def __init__(self, config: Optional[MicroCapitalConfig] = None):
        self.config = config or MicroCapitalConfig()
        self.capital = self.config.capital
        self.trades_executed = 0
        self.cumulative_cost = 0.0

    def calculate_round_trip_cost(self, price: float, shares: int) -> float:
        """Calculate realistic round-trip cost for IBKR Lite.

        IBKR Lite is commission-free but has implicit spread cost.
        At micro tier, we model 5bps effective spread.
        """
        notional = price * shares
        if self.config.broker_plan == "lite":
            # No commissions, but model implicit spread cost
            spread_cost = notional * (self.config.implicit_spread_bps / 10000)
            return spread_cost * 2  # round trip
        elif self.config.broker_plan == "fixed":
            # $1.00 minimum per order
            return max(1.0, notional * 0.005) * 2
        else:
            # Tiered: ~0.5% on fractional
            return notional * 0.005 * 2

    def evaluate_trade(self, price: float, expected_return_pct: float) -> TradeVerdict:
        """
        MC-3: Cost-aware trade gate.
        Reject any signal where expected edge < 3x round-trip cost.
        """
        # Calculate max affordable shares (whole shares only — MC-2)
        max_shares = int(self.capital / price) if price > 0 else 0
        if max_shares < 1:
            return TradeVerdict(
                approved=False,
                reason="Cannot afford 1 whole share",
                round_trip_cost=0,
                cost_pct=0,
                expected_edge=0,
                edge_to_cost_ratio=0,
                capital_after=self.capital,
            )

        # Trade with 1 share at minimum
        shares = min(max_shares, 1)  # Start with 1 share for validation
        notional = price * shares
        round_trip_cost = self.calculate_round_trip_cost(price, shares)
        cost_pct = (round_trip_cost / notional * 100) if notional > 0 else 0
        expected_edge = notional * (expected_return_pct / 100.0)

        edge_to_cost_ratio = (expected_edge / round_trip_cost) if round_trip_cost > 0 else 0

        if cost_pct > self.config.max_round_trip_cost_pct:
            return TradeVerdict(
                approved=False,
                reason=f"Round-trip cost ({cost_pct:.3f}%) exceeds max ({self.config.max_round_trip_cost_pct}%)",
                round_trip_cost=round_trip_cost,
                cost_pct=cost_pct,
                expected_edge=expected_edge,
                edge_to_cost_ratio=edge_to_cost_ratio,
                capital_after=self.capital,
            )

        if edge_to_cost_ratio < self.config.cost_edge_ratio:
            return TradeVerdict(
                approved=False,
                reason=f"Edge/cost ratio ({edge_to_cost_ratio:.1f}x) < minimum ({self.config.cost_edge_ratio}x)",
                round_trip_cost=round_trip_cost,
                cost_pct=cost_pct,
                expected_edge=expected_edge,
                edge_to_cost_ratio=edge_to_cost_ratio,
                capital_after=self.capital,
            )

        # Trade approved
        capital_after = self.capital - round_trip_cost
        self.trades_executed += 1
        self.cumulative_cost += round_trip_cost

        return TradeVerdict(
            approved=True,
            reason=f"Approved: {edge_to_cost_ratio:.1f}x edge/cost (need ≥{self.config.cost_edge_ratio}x)",
            round_trip_cost=round_trip_cost,
            cost_pct=cost_pct,
            expected_edge=expected_edge,
            edge_to_cost_ratio=edge_to_cost_ratio,
            capital_after=capital_after,
        )

    def viable_trade_example(self) -> dict:
        """
        MC-1 through MC-5: Demonstrate a viable $200 trade.
        1 share of $45 ETF on IBKR Lite, expecting 1.5% move.
        """
        price = 45.0
        expected_return = 1.5
        verdict = self.evaluate_trade(price, expected_return)

        return {
            "instrument": "1 share of ~$45 liquid ETF",
            "price": price,
            "broker_plan": self.config.broker_plan,
            "implicit_spread_bps": self.config.implicit_spread_bps,
            "expected_return_pct": expected_return,
            "round_trip_cost": verdict.round_trip_cost,
            "round_trip_cost_pct": verdict.cost_pct,
            "expected_edge": verdict.expected_edge,
            "edge_to_cost_ratio": verdict.edge_to_cost_ratio,
            "approved": verdict.approved,
            "reason": verdict.reason,
            "capital_at_risk": price,
            "capital_remaining": self.capital - price,
            "verdict": "VIABLE ✅" if verdict.approved else "REJECTED ❌",
        }
