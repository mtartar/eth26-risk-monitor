import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Events(_message.Message):
    __slots__ = ("borrows", "deposits", "flash_loans", "liquidation_calls", "pauseds", "rebalance_stable_borrow_rates", "repays", "reserve_data_updateds", "reserve_used_as_collateral_disableds", "reserve_used_as_collateral_enableds", "swaps", "tokens_rescueds", "unpauseds", "upgradeds", "withdraws")
    BORROWS_FIELD_NUMBER: _ClassVar[int]
    DEPOSITS_FIELD_NUMBER: _ClassVar[int]
    FLASH_LOANS_FIELD_NUMBER: _ClassVar[int]
    LIQUIDATION_CALLS_FIELD_NUMBER: _ClassVar[int]
    PAUSEDS_FIELD_NUMBER: _ClassVar[int]
    REBALANCE_STABLE_BORROW_RATES_FIELD_NUMBER: _ClassVar[int]
    REPAYS_FIELD_NUMBER: _ClassVar[int]
    RESERVE_DATA_UPDATEDS_FIELD_NUMBER: _ClassVar[int]
    RESERVE_USED_AS_COLLATERAL_DISABLEDS_FIELD_NUMBER: _ClassVar[int]
    RESERVE_USED_AS_COLLATERAL_ENABLEDS_FIELD_NUMBER: _ClassVar[int]
    SWAPS_FIELD_NUMBER: _ClassVar[int]
    TOKENS_RESCUEDS_FIELD_NUMBER: _ClassVar[int]
    UNPAUSEDS_FIELD_NUMBER: _ClassVar[int]
    UPGRADEDS_FIELD_NUMBER: _ClassVar[int]
    WITHDRAWS_FIELD_NUMBER: _ClassVar[int]
    borrows: _containers.RepeatedCompositeFieldContainer[Borrow]
    deposits: _containers.RepeatedCompositeFieldContainer[Deposit]
    flash_loans: _containers.RepeatedCompositeFieldContainer[FlashLoan]
    liquidation_calls: _containers.RepeatedCompositeFieldContainer[LiquidationCall]
    pauseds: _containers.RepeatedCompositeFieldContainer[Paused]
    rebalance_stable_borrow_rates: _containers.RepeatedCompositeFieldContainer[RebalanceStableBorrowRate]
    repays: _containers.RepeatedCompositeFieldContainer[Repay]
    reserve_data_updateds: _containers.RepeatedCompositeFieldContainer[ReserveDataUpdated]
    reserve_used_as_collateral_disableds: _containers.RepeatedCompositeFieldContainer[ReserveUsedAsCollateralDisabled]
    reserve_used_as_collateral_enableds: _containers.RepeatedCompositeFieldContainer[ReserveUsedAsCollateralEnabled]
    swaps: _containers.RepeatedCompositeFieldContainer[Swap]
    tokens_rescueds: _containers.RepeatedCompositeFieldContainer[TokensRescued]
    unpauseds: _containers.RepeatedCompositeFieldContainer[Unpaused]
    upgradeds: _containers.RepeatedCompositeFieldContainer[Upgraded]
    withdraws: _containers.RepeatedCompositeFieldContainer[Withdraw]
    def __init__(self, borrows: _Optional[_Iterable[_Union[Borrow, _Mapping]]] = ..., deposits: _Optional[_Iterable[_Union[Deposit, _Mapping]]] = ..., flash_loans: _Optional[_Iterable[_Union[FlashLoan, _Mapping]]] = ..., liquidation_calls: _Optional[_Iterable[_Union[LiquidationCall, _Mapping]]] = ..., pauseds: _Optional[_Iterable[_Union[Paused, _Mapping]]] = ..., rebalance_stable_borrow_rates: _Optional[_Iterable[_Union[RebalanceStableBorrowRate, _Mapping]]] = ..., repays: _Optional[_Iterable[_Union[Repay, _Mapping]]] = ..., reserve_data_updateds: _Optional[_Iterable[_Union[ReserveDataUpdated, _Mapping]]] = ..., reserve_used_as_collateral_disableds: _Optional[_Iterable[_Union[ReserveUsedAsCollateralDisabled, _Mapping]]] = ..., reserve_used_as_collateral_enableds: _Optional[_Iterable[_Union[ReserveUsedAsCollateralEnabled, _Mapping]]] = ..., swaps: _Optional[_Iterable[_Union[Swap, _Mapping]]] = ..., tokens_rescueds: _Optional[_Iterable[_Union[TokensRescued, _Mapping]]] = ..., unpauseds: _Optional[_Iterable[_Union[Unpaused, _Mapping]]] = ..., upgradeds: _Optional[_Iterable[_Union[Upgraded, _Mapping]]] = ..., withdraws: _Optional[_Iterable[_Union[Withdraw, _Mapping]]] = ...) -> None: ...

class Borrow(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user", "on_behalf_of", "amount", "borrow_rate_mode", "borrow_rate", "referral")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ON_BEHALF_OF_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    BORROW_RATE_MODE_FIELD_NUMBER: _ClassVar[int]
    BORROW_RATE_FIELD_NUMBER: _ClassVar[int]
    REFERRAL_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    on_behalf_of: bytes
    amount: str
    borrow_rate_mode: str
    borrow_rate: str
    referral: int
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ..., on_behalf_of: _Optional[bytes] = ..., amount: _Optional[str] = ..., borrow_rate_mode: _Optional[str] = ..., borrow_rate: _Optional[str] = ..., referral: _Optional[int] = ...) -> None: ...

class Deposit(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user", "on_behalf_of", "amount", "referral")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ON_BEHALF_OF_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    REFERRAL_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    on_behalf_of: bytes
    amount: str
    referral: int
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ..., on_behalf_of: _Optional[bytes] = ..., amount: _Optional[str] = ..., referral: _Optional[int] = ...) -> None: ...

class FlashLoan(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "target", "initiator", "asset", "amount", "premium", "referral_code")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_FIELD_NUMBER: _ClassVar[int]
    ASSET_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    PREMIUM_FIELD_NUMBER: _ClassVar[int]
    REFERRAL_CODE_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    target: bytes
    initiator: bytes
    asset: bytes
    amount: str
    premium: str
    referral_code: int
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., target: _Optional[bytes] = ..., initiator: _Optional[bytes] = ..., asset: _Optional[bytes] = ..., amount: _Optional[str] = ..., premium: _Optional[str] = ..., referral_code: _Optional[int] = ...) -> None: ...

class LiquidationCall(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "collateral_asset", "debt_asset", "user", "debt_to_cover", "liquidated_collateral_amount", "liquidator", "receive_a_token")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    COLLATERAL_ASSET_FIELD_NUMBER: _ClassVar[int]
    DEBT_ASSET_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    DEBT_TO_COVER_FIELD_NUMBER: _ClassVar[int]
    LIQUIDATED_COLLATERAL_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    LIQUIDATOR_FIELD_NUMBER: _ClassVar[int]
    RECEIVE_A_TOKEN_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    collateral_asset: bytes
    debt_asset: bytes
    user: bytes
    debt_to_cover: str
    liquidated_collateral_amount: str
    liquidator: bytes
    receive_a_token: bool
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., collateral_asset: _Optional[bytes] = ..., debt_asset: _Optional[bytes] = ..., user: _Optional[bytes] = ..., debt_to_cover: _Optional[str] = ..., liquidated_collateral_amount: _Optional[str] = ..., liquidator: _Optional[bytes] = ..., receive_a_token: _Optional[bool] = ...) -> None: ...

class Paused(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ...) -> None: ...

class RebalanceStableBorrowRate(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ...) -> None: ...

class Repay(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user", "repayer", "amount")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    REPAYER_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    repayer: bytes
    amount: str
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ..., repayer: _Optional[bytes] = ..., amount: _Optional[str] = ...) -> None: ...

class ReserveDataUpdated(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "liquidity_rate", "stable_borrow_rate", "variable_borrow_rate", "liquidity_index", "variable_borrow_index")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    LIQUIDITY_RATE_FIELD_NUMBER: _ClassVar[int]
    STABLE_BORROW_RATE_FIELD_NUMBER: _ClassVar[int]
    VARIABLE_BORROW_RATE_FIELD_NUMBER: _ClassVar[int]
    LIQUIDITY_INDEX_FIELD_NUMBER: _ClassVar[int]
    VARIABLE_BORROW_INDEX_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    liquidity_rate: str
    stable_borrow_rate: str
    variable_borrow_rate: str
    liquidity_index: str
    variable_borrow_index: str
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., liquidity_rate: _Optional[str] = ..., stable_borrow_rate: _Optional[str] = ..., variable_borrow_rate: _Optional[str] = ..., liquidity_index: _Optional[str] = ..., variable_borrow_index: _Optional[str] = ...) -> None: ...

class ReserveUsedAsCollateralDisabled(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ...) -> None: ...

class ReserveUsedAsCollateralEnabled(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ...) -> None: ...

class Swap(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user", "rate_mode")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    RATE_MODE_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    rate_mode: str
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ..., rate_mode: _Optional[str] = ...) -> None: ...

class TokensRescued(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "token_rescued", "receiver", "amount_rescued")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TOKEN_RESCUED_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_RESCUED_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    token_rescued: bytes
    receiver: bytes
    amount_rescued: str
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., token_rescued: _Optional[bytes] = ..., receiver: _Optional[bytes] = ..., amount_rescued: _Optional[str] = ...) -> None: ...

class Unpaused(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ...) -> None: ...

class Upgraded(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "implementation")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    IMPLEMENTATION_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    implementation: bytes
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., implementation: _Optional[bytes] = ...) -> None: ...

class Withdraw(_message.Message):
    __slots__ = ("evt_tx_hash", "evt_index", "evt_block_time", "evt_block_number", "reserve", "user", "to", "amount")
    EVT_TX_HASH_FIELD_NUMBER: _ClassVar[int]
    EVT_INDEX_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    EVT_BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RESERVE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    evt_tx_hash: str
    evt_index: int
    evt_block_time: _timestamp_pb2.Timestamp
    evt_block_number: int
    reserve: bytes
    user: bytes
    to: bytes
    amount: str
    def __init__(self, evt_tx_hash: _Optional[str] = ..., evt_index: _Optional[int] = ..., evt_block_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evt_block_number: _Optional[int] = ..., reserve: _Optional[bytes] = ..., user: _Optional[bytes] = ..., to: _Optional[bytes] = ..., amount: _Optional[str] = ...) -> None: ...
