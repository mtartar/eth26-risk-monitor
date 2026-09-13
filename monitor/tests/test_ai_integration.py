"""Phase 3's exit condition: integration tests against the real Anthropic API.

Excluded from the default `pytest` run (see [tool.pytest.ini_options] in
pyproject.toml) since these cost real API credit. Run with: pytest -m integration
ANTHROPIC_API_KEY comes from eth26-graph-trail/.env by default (see
monitor/config.py) — no separate key setup needed for this repo.
"""

from datetime import datetime, timezone

import pytest

from monitor.ai.decision import recommend_action
from monitor.ai.explanation import explain_transition
from monitor.ai.query import answer_position_query
from monitor.config import settings
from monitor.protocols.aave_risk_model import AaveRiskModel
from monitor.protocols.models import EventKind, NormalizedEvent, PositionState
from monitor.scoring.price_oracle import StaticPriceOracle
from monitor.scoring.risk_state import RiskLevel, RiskTransition
from monitor.scoring.scoring_engine import ScoringEngine

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not settings.anthropic_api_key, reason="ANTHROPIC_API_KEY not set"),
]

_WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
_USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"


def _event(kind, block, reserve, amount_raw, user) -> NormalizedEvent:
    return NormalizedEvent(
        kind=kind,
        protocol="aave-v2",
        chain="ethereum",
        tx_hash=f"0xtx{block}",
        log_index=0,
        block_number=block,
        block_time=datetime.now(timezone.utc),
        user_address=user,
        reserve_address=reserve,
        amount_raw=amount_raw,
    )


def _engine() -> ScoringEngine:
    prices = StaticPriceOracle({_WETH: 3000.0, _USDC: 1.0})
    return ScoringEngine(price_oracle=prices, risk_model=AaveRiskModel())


# --- Decision -----------------------------------------------------------


def test_recommend_action_picks_a_real_precomputed_option():
    """The recommendation's amount and resulting HF are always ours, never the model's."""
    position = PositionState(
        protocol="aave-v2",
        chain="ethereum",
        user_address="0x1111111111111111111111111111111111111111",
        total_collateral_usd=30_000,
        total_debt_usd=20_000,
        liquidation_threshold=0.86,
        as_of_block=1,
        as_of_timestamp=datetime.now(timezone.utc),
    )
    recommendation = recommend_action(position, target_health_factor=1.5)

    assert recommendation.action in ("add_collateral", "repay_debt")
    assert recommendation.resulting_health_factor == 1.5
    if recommendation.action == "add_collateral":
        assert abs(recommendation.amount_usd - (4200 / 0.86)) < 1e-6
    else:
        assert abs(recommendation.amount_usd - 2800) < 1e-6
    assert len(recommendation.rationale) > 0


# --- Explanation: 3 distinct real scenarios ------------------------------


def test_explain_price_crash_scenario():
    """Scenario 1: a price move (no on-chain lending event) pushed a position into danger."""
    transition = RiskTransition(
        user_address="0x1111111111111111111111111111111111111111",
        from_level=RiskLevel.SAFE,
        to_level=RiskLevel.DANGER,
        health_factor=0.91,
        as_of_block=100,
    )
    explanation = explain_transition(
        transition, cause="price_move", context={"collateral_asset": "ETH", "price_change": "-18%"}
    )
    assert len(explanation) > 0


def test_explain_new_large_borrow_scenario():
    """Scenario 2: a real new Borrow event, via the actual scoring engine."""
    engine = _engine()
    engine.process_event(
        _event(
            EventKind.SUPPLY,
            block=1,
            reserve=_WETH,
            amount_raw=str(10 * 10**18),
            user="0x1111111111111111111111111111111111111111",
        )
    )
    transition = engine.process_event(
        _event(
            EventKind.BORROW,
            block=2,
            reserve=_USDC,
            amount_raw=str(20_000 * 10**6),
            user="0x1111111111111111111111111111111111111111",
        )
    )
    assert transition is not None
    explanation = explain_transition(
        transition, cause="new_borrow", context={"borrowed_usd": "$20,000", "asset": "USDC"}
    )
    assert len(explanation) > 0


def test_explain_partial_repayment_scenario():
    """Scenario 3: a real Repay event recovering a position, via the actual scoring engine."""
    engine = _engine()
    user = "0x1111111111111111111111111111111111111111"
    engine.process_event(
        _event(EventKind.SUPPLY, block=1, reserve=_WETH, amount_raw=str(10 * 10**18), user=user)
    )
    engine.process_event(
        _event(EventKind.BORROW, block=2, reserve=_USDC, amount_raw=str(30_000 * 10**6), user=user)
    )
    transition = engine.process_event(
        _event(EventKind.REPAY, block=3, reserve=_USDC, amount_raw=str(15_000 * 10**6), user=user)
    )
    assert transition is not None
    explanation = explain_transition(
        transition, cause="repayment", context={"repaid_usd": "$15,000", "asset": "USDC"}
    )
    assert len(explanation) > 0


# --- NL query over live tracked positions --------------------------------


def test_answer_position_query_identifies_the_riskier_of_two_tracked_users():
    """A real question, answered from the engine's real tracked state, not invented positions."""
    engine = _engine()
    risky_user = "0x1111111111111111111111111111111111111111"
    safe_user = "0x2222222222222222222222222222222222222222"

    engine.process_event(
        _event(
            EventKind.SUPPLY, block=1, reserve=_WETH, amount_raw=str(10 * 10**18), user=risky_user
        )
    )
    engine.process_event(
        _event(
            EventKind.BORROW,
            block=2,
            reserve=_USDC,
            amount_raw=str(30_000 * 10**6),
            user=risky_user,
        )
    )
    engine.process_event(
        _event(
            EventKind.SUPPLY, block=3, reserve=_WETH, amount_raw=str(10 * 10**18), user=safe_user
        )
    )
    engine.process_event(
        _event(
            EventKind.BORROW, block=4, reserve=_USDC, amount_raw=str(1_000 * 10**6), user=safe_user
        )
    )

    answer = answer_position_query(
        "Which tracked position is riskiest right now?",
        engine,
        as_of_block=4,
        as_of_timestamp=datetime.now(timezone.utc),
    )
    assert len(answer) > 0
    assert risky_user in answer or risky_user.lower() in answer.lower()
