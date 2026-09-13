"""Aave v3 on Ethereum mainnet.

Status: config only, NOT yet wired to a real Substreams source. Phase 1
searched substreams.dev for a published v3-specific package and found none —
only Aave v2 has a verified, downloadable package (see aave_v2_ethereum.py,
which is what Phase 1's real ingestion pipeline actually runs against). See
docs/phase1_findings.md for the search and the decision to proceed on v2.

What IS confirmed here (against real sources, not assumed):
- The health-factor formula (shared with v2 — see aave_risk_model.py).
- The Aave v3 Pool contract address, via Etherscan.

Revisit this file once a real v3 Substreams package is found or built.
"""

from monitor.protocols.aave_risk_model import AaveRiskModel
from monitor.protocols.models import ProtocolConfig

AAVE_V3_ETHEREUM_CONTRACTS = {
    # Aave v3 Pool, Ethereum mainnet — verified via Etherscan.
    "pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
}


def build_aave_v3_ethereum_config() -> ProtocolConfig:
    """Raise until a real v3 Substreams source is found — see module docstring."""
    raise NotImplementedError(
        "No verified Aave v3 Substreams package found yet (see docs/phase1_findings.md). "
        "aave_v2_ethereum.AAVE_V2_ETHEREUM is the real, working config for now."
    )


AaveV3RiskModel = AaveRiskModel  # same math; kept as an alias for a readable import name
