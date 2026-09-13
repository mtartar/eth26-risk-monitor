"""Generic, protocol-agnostic domain model for the risk monitor.

New to DeFi lending or this codebase's patterns? Read docs/glossary.md first —
it explains "health factor," "liquidation threshold," and why RiskModel is a
typing.Protocol rather than a base class, all in plain English.

Every lending protocol (Aave, Compound, Morpho, ...) plugs in behind the same
two shapes: a ProtocolConfig describing where its data comes from, and a
RiskModel describing how to turn a position snapshot into a health factor.
Adding a new protocol or chain should mean adding one new module and one
registry entry (see registry.py) — never touching this file or any file
that already works.
"""

from datetime import datetime
from enum import Enum
from typing import Protocol

from pydantic import BaseModel


class EventKind(str, Enum):
    """Canonical lending-lifecycle event categories, shared across all protocols.

    Each protocol's config maps its own raw event names onto these — the
    scoring engine only ever reasons in terms of this enum, never a
    protocol-specific event name.
    """

    SUPPLY = "supply"
    WITHDRAW = "withdraw"
    BORROW = "borrow"
    REPAY = "repay"
    LIQUIDATION = "liquidation"
    ORACLE_UPDATE = "oracle_update"


class SubstreamsSource(BaseModel):
    """Where to get one protocol/chain's real-time event stream."""

    package: str
    version: str
    endpoint: str
    module: str
    event_topics: dict[EventKind, str]


class ProtocolConfig(BaseModel):
    """Everything specific to one protocol deployment on one chain.

    An instance of this plus a RiskModel is the entire integration surface
    for a new protocol/chain pair.
    """

    protocol: str
    chain: str
    substreams: SubstreamsSource
    contract_addresses: dict[str, str]
    notes: str = ""


class PositionState(BaseModel):
    """A protocol-agnostic snapshot of one user's aggregate lending position.

    liquidation_threshold is a fraction (0.8 = 80%): only that share of
    total_collateral_usd counts toward safety, as the protocol's own buffer
    against price swings between the last update and the next one.
    """

    protocol: str
    chain: str
    user_address: str
    total_collateral_usd: float
    total_debt_usd: float
    liquidation_threshold: float
    as_of_block: int
    as_of_timestamp: datetime


class RiskModel(Protocol):
    """Protocol-specific health-factor logic behind one generic interface.

    A Protocol class (unlike a normal base class) needs no explicit
    inheritance — any class with a matching compute_health_factor method
    satisfies this automatically. See docs/glossary.md if that's unfamiliar.
    """

    def compute_health_factor(self, position: PositionState) -> float:
        """Return the health factor for a position; below 1.0 means eligible for liquidation."""
        ...
