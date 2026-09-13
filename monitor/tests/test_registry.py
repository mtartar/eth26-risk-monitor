"""Tests for the protocol/chain registry lookup."""

import pytest

from monitor.protocols.registry import get_protocol_config, get_risk_model


def test_get_protocol_config_returns_aave_v3_ethereum():
    """The one registered protocol/chain resolves to its config."""
    config = get_protocol_config("aave-v3-ethereum")
    assert config.protocol == "aave-v3"
    assert config.chain == "ethereum"


def test_get_risk_model_returns_aave_v3_ethereum():
    """The one registered protocol/chain resolves to its risk model."""
    model = get_risk_model("aave-v3-ethereum")
    assert model is not None


def test_unknown_protocol_key_raises_with_known_keys_listed():
    """An unregistered key fails loudly rather than returning None."""
    with pytest.raises(KeyError, match="aave-v3-ethereum"):
        get_protocol_config("compound-v2-ethereum")
