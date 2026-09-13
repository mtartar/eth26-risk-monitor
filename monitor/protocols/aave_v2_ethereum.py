"""Aave v2 on Ethereum mainnet — the real, working protocol/chain config.

Everything below is confirmed against a real source, not assumed — see
docs/phase1_findings.md for how each fact was obtained:
- network/output_module/initial_block: extracted directly from the real,
  published "aave-v2-lending-pool" v0.1.4 package (streamingfast), by
  parsing it as the sf.substreams.v1.Package protobuf message it actually
  is (see scripts/generate_protos.sh and substreams_packages/).
- The LendingPool contract address: verified via Etherscan.

This is Phase 0's originally-planned "aave-v3-ethereum" target, redirected
to v2 once Phase 1 found no verified v3 Substreams package exists yet.
"""

from monitor.protocols.aave_risk_model import AaveRiskModel
from monitor.protocols.models import ProtocolConfig, SubstreamsSource

AAVE_V2_ETHEREUM = ProtocolConfig(
    protocol="aave-v2",
    chain="ethereum",
    substreams=SubstreamsSource(
        package_path="substreams_packages/aave-v2-lending-pool-v0.1.4.spkg",
        network="mainnet",
        output_module="map_events",
        initial_block=11367463,
    ),
    contract_addresses={
        # Aave V2 LendingPool, Ethereum mainnet — verified via Etherscan.
        "lending_pool": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
    },
    notes=(
        "Output module 'map_events' emits an already-decoded contract.v1.Events "
        "message (see protos/contract/v1/contract.proto) — no raw EVM log/topic "
        "parsing needed on our side; the Substreams module does that in Rust/WASM."
    ),
)

AaveV2RiskModel = AaveRiskModel  # same math as v3; kept as a readable import name
