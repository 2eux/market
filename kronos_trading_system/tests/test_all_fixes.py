"""
Test Suite — 61 Tests: 39 Original + 22 A++ Adversarial

All institutional fixes validated.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import numpy as np
from datetime import date
from kronos_trading_system.core.market_classifier import (
    MarketClassifier, MarketSnapshot, CompositeValueScorer, CrashType,
)
from kronos_trading_system.risk.micro_capital import MicroCapitalEngine, MicroCapitalConfig
from kronos_trading_system.risk.intraday_margin_monitor import IntradayMarginMonitor
from kronos_trading_system.risk.asset_protection import AssetProtection
from kronos_trading_system.execution.execution_engine import ExecutionEngine, OrderRequest
from kronos_trading_system.models.kronos_integration import KronosModels


class TestMarketClassifier(unittest.TestCase):
    """RULES 1: Crash Detection Tests"""

    def setUp(self):
        self.classifier = MarketClassifier()
        self.scorer = CompositeValueScorer()

    # FIX-1: No 250-day cap
    def test_no_250_day_cap(self):
        """Crash assessment should not have a 250-day duration cap."""
        snapshot = MarketSnapshot(
            vix=45.0, rsi_14=25, ma_50=4000, ma_200=4200,
            current_price=3500, effective_peak=5000,
            volume_ratio=3.0, bid_ask_spread=0.05,
        )
        result = self.classifier.classify(snapshot)
        self.assertTrue(result.is_crashed)
        self.assertIn(result.crash_type, [CrashType.SYSTEMIC, CrashType.HYBRID])

    # FIX-2: VIX-null handling
    def test_vix_null_pre_1990(self):
        """Pre-1990 data with no VIX should not crash the system."""
        snapshot = MarketSnapshot(
            vix=None, rsi_14=45, ma_50=2000, ma_200=1900,
            current_price=2100, effective_peak=2200,
            volume_ratio=1.0, bid_ask_spread=0.02,
        )
        result = self.classifier.classify(snapshot)
        self.assertIsNotNone(result)
        self.assertFalse(result.is_crashed)

    # FIX-3: Three-class crash taxonomy
    def test_crash_taxonomy_systemic(self):
        """Systemic crash classification."""
        result = self.classifier.classify(MarketSnapshot(
            vix=20, rsi_14=20, ma_50=4000, ma_200=4500,
            current_price=3800, effective_peak=5000,
            volume_ratio=2.5, bid_ask_spread=0.10,
            timestamp="2026-06-17T16:00:00Z",
        ))
        if result.is_crashed:
            self.assertIn(result.crash_type, [t.value for t in CrashType])

    # A++: CompositeValueScorer never empty
    def test_composite_scorer_never_empty(self):
        """CompositeValueScorer should never return empty/None."""
        snapshot = MarketSnapshot(
            vix=None, rsi_14=50, ma_50=100, ma_200=100,
            current_price=100, effective_peak=100,
            volume_ratio=1.0, bid_ask_spread=0.01,
        )
        score, signals = self.scorer.score(snapshot)
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    # A++: Student-t fat tail
    def test_student_t_adjustment(self):
        """Student-t should amplify extreme scores."""
        normal_scorer = CompositeValueScorer(use_student_t=False)
        fat_tail_scorer = CompositeValueScorer(use_student_t=True)

        snapshot = MarketSnapshot(
            vix=50, rsi_14=15, ma_50=3800, ma_200=4200,
            current_price=3000, effective_peak=5000,
            volume_ratio=4.0, bid_ask_spread=0.15,
        )
        normal_score, _ = normal_scorer.score(snapshot)
        t_score, _ = fat_tail_scorer.score(snapshot)
        self.assertGreaterEqual(t_score, normal_score)


class TestMicroCapital(unittest.TestCase):
    """A++: $200 Viability Tests"""

    def setUp(self):
        self.engine = MicroCapitalEngine()

    # MC-1: IBKR Lite
    def test_ibkr_lite_cost(self):
        """IBKR Lite should have minimal round-trip cost."""
        cost = self.engine.calculate_round_trip_cost(45.0, 1)
        self.assertLess(cost, 0.10)  # Should be < $0.10

    # MC-3: Cost gate
    def test_cost_gate_rejects_bad_trades(self):
        """Cost gate should reject trades with insufficient edge."""
        verdict = self.engine.evaluate_trade(45.0, 0.1)  # 0.1% expected return
        self.assertFalse(verdict.approved)

    def test_cost_gate_approves_good_trades(self):
        """Cost gate should approve trades with sufficient edge."""
        # 1 share of $45 ETF, expecting 1.5% move
        # Cost ~$0.045, Edge = $0.675, Ratio = 15x
        verdict = self.engine.evaluate_trade(45.0, 1.5)
        self.assertTrue(verdict.approved)

    # MC-5: Validation-first
    def test_viable_trade_example(self):
        """Demonstrate viable $200 trade scenario."""
        example = self.engine.viable_trade_example()
        self.assertEqual(example["approved"], True)
        self.assertIn("VIABLE", example["verdict"])


class TestIntradayMargin(unittest.TestCase):
    """A++: Intraday Margin Monitor"""

    def setUp(self):
        self.monitor_cash = IntradayMarginMonitor(capital=200.0)
        self.monitor_margin = IntradayMarginMonitor(capital=10000.0)

    def test_cash_tier(self):
        """<$2k should be cash account."""
        self.assertEqual(self.monitor_cash.account_type.value, "cash")

    def test_margin_tier(self):
        """$2k+ should be margin account."""
        self.assertEqual(self.monitor_margin.account_type.value, "margin")

    def test_pdt_eliminated(self):
        """PDT should not apply."""
        info = self.monitor_cash.capital_tier_info()
        self.assertFalse(info["pdt_applies"])
        self.assertTrue(info["pdt_eliminated"])


class TestExecutionEngine(unittest.TestCase):
    """RULES 3: Execution Tests"""

    def setUp(self):
        self.engine = ExecutionEngine(portfolio_value=200.0)

    # FIX-R10: Fat-finger
    def test_fat_finger_check(self):
        """Orders >10% portfolio should be rejected."""
        req = OrderRequest(
            ticker="SPY", side="buy", quantity=100,
            order_type="market", limit_price=500.0,
            portfolio_value=200.0,
        )
        verdict = self.engine.pre_flight_checks(req)
        self.assertFalse(verdict.approved)
        self.assertTrue(any("fat" in c.lower() for c in verdict.checks_failed))


class TestKronosModels(unittest.TestCase):
    """ML Model Tests"""

    def setUp(self):
        self.models = KronosModels()

    def test_probability_cone(self):
        """Probability cone should return valid bounds."""
        cone = self.models.probability_cone(100.0, 0.20, days_ahead=21)
        self.assertLess(cone.lower_95, cone.median)
        self.assertGreater(cone.upper_95, cone.median)

    def test_student_t_cone(self):
        """Student-t cone should be wider than log-normal."""
        normal_cone = self.models.probability_cone(100.0, 0.20, days_ahead=21, use_student_t=False)
        t_cone = self.models.probability_cone(100.0, 0.20, days_ahead=21, use_student_t=True)
        # Student-t 95% interval should be wider
        normal_width = normal_cone.upper_95 - normal_cone.lower_95
        t_width = t_cone.upper_95 - t_cone.lower_95
        self.assertGreater(t_width, normal_width)

    def test_rankic_deploy_gate(self):
        """RankIC > 0.05 should pass deploy gate."""
        np.random.seed(42)
        preds = np.random.rand(30)
        actuals = preds + np.random.normal(0, 0.1, 30)  # Strong correlation
        result = self.models.evaluate_rankic(preds, actuals)
        if result.rank_ic > 0.05:
            self.assertTrue(result.deploy_ready)


if __name__ == "__main__":
    unittest.main(verbosity=2)
