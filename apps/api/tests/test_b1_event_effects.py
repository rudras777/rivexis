from __future__ import annotations

from dataclasses import dataclass

from rivexis_api.engines import ENGINES
from rivexis_api.models.enums import AnalysisStatus, EngineId
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.providers import Resolution
from rivexis_api.services import live_b1
from rivexis_api.services.evm_events import (
    APPROVAL_FOR_ALL_TOPIC,
    APPROVAL_TOPIC,
    ERC1155_TRANSFER_BATCH_TOPIC,
    ERC1155_TRANSFER_SINGLE_TOPIC,
    TRANSFER_TOPIC,
    normalize_standard_event_logs,
)


def _address(byte: str) -> str:
    return "0x" + byte * 40


def _topic_address(address: str) -> str:
    return "0x" + "0" * 24 + address[2:].lower()


def _topic_uint(value: int) -> str:
    return "0x" + f"{value:064x}"


def _word(value: int) -> str:
    return f"{value:064x}"


def _data_word(value: int) -> str:
    return "0x" + _word(value)


def test_standard_event_normalizer_decodes_erc20_transfer_and_approval():
    token = _address("2")
    sender = _address("1")
    recipient = _address("3")
    spender = _address("4")
    effects = normalize_standard_event_logs(
        [
            {
                "address": token,
                "topics": [TRANSFER_TOPIC, _topic_address(sender), _topic_address(recipient)],
                "data": _data_word(1_250_000),
                "logIndex": "0x7",
            },
            {
                "address": token,
                "topics": [APPROVAL_TOPIC, _topic_address(sender), _topic_address(spender)],
                "data": _data_word(2**256 - 1),
                "logIndex": "0x8",
            },
        ],
        source="fixture",
        outcome="predicted",
    )

    assert effects["status"] == "NORMALIZED_STANDARD_EVENT_LOGS"
    assert effects["source"] == "fixture"
    assert effects["outcome"] == "predicted"
    assert effects["decoded_log_count"] == 2
    assert effects["asset_change_count"] == 1
    assert effects["approval_event_count"] == 1
    transfer = effects["asset_changes"][0]
    assert transfer == {
        "standard": "ERC20",
        "event": "Transfer",
        "contract": token,
        "log_index": 7,
        "kind": "transfer",
        "from": sender,
        "to": recipient,
        "amount_raw": "1250000",
    }
    approval = effects["approval_events"][0]
    assert approval["standard"] == "ERC20"
    assert approval["owner"] == sender
    assert approval["spender"] == spender
    assert approval["amount_raw"] == str(2**256 - 1)
    assert effects["raw_amounts_unscaled"] is True


def test_standard_event_normalizer_decodes_erc721_and_approval_for_all():
    nft = _address("a")
    sender = _address("1")
    recipient = _address("2")
    operator = _address("3")
    effects = normalize_standard_event_logs(
        [
            {
                "address": nft,
                "topics": [TRANSFER_TOPIC, _topic_address(sender), _topic_address(recipient), _topic_uint(42)],
                "data": "0x",
            },
            {
                "address": nft,
                "topics": [APPROVAL_FOR_ALL_TOPIC, _topic_address(sender), _topic_address(operator)],
                "data": _data_word(1),
            },
        ],
        source="fixture",
        outcome="observed",
    )

    transfer = effects["asset_changes"][0]
    assert transfer["standard"] == "ERC721"
    assert transfer["token_id"] == "42"
    approval = effects["approval_events"][0]
    assert approval["standard"] == "ERC721_OR_ERC1155"
    assert approval["approved"] is True
    assert approval["operator"] == operator


def test_standard_event_normalizer_decodes_erc1155_single_and_batch():
    token = _address("b")
    operator = _address("1")
    sender = _address("2")
    recipient = _address("3")
    batch_data = "0x" + "".join(
        [
            _word(64),
            _word(160),
            _word(2),
            _word(7),
            _word(8),
            _word(2),
            _word(70),
            _word(80),
        ]
    )
    effects = normalize_standard_event_logs(
        [
            {
                "address": token,
                "topics": [
                    ERC1155_TRANSFER_SINGLE_TOPIC,
                    _topic_address(operator),
                    _topic_address(sender),
                    _topic_address(recipient),
                ],
                "data": "0x" + _word(5) + _word(50),
            },
            {
                "address": token,
                "topics": [
                    ERC1155_TRANSFER_BATCH_TOPIC,
                    _topic_address(operator),
                    _topic_address(sender),
                    _topic_address(recipient),
                ],
                "data": batch_data,
            },
        ],
        source="fixture",
        outcome="predicted",
    )

    assert effects["decoded_log_count"] == 2
    assert effects["asset_change_count"] == 3
    assert effects["truncated"] is False
    single, first_batch, second_batch = effects["asset_changes"]
    assert single["event"] == "TransferSingle"
    assert single["token_id"] == "5"
    assert single["amount_raw"] == "50"
    assert first_batch["event"] == "TransferBatch"
    assert first_batch["token_id"] == "7"
    assert first_batch["amount_raw"] == "70"
    assert first_batch["batch_item_index"] == 0
    assert first_batch["batch_size"] == 2
    assert second_batch["token_id"] == "8"
    assert second_batch["amount_raw"] == "80"


def test_unknown_and_malformed_logs_remain_explicit_without_invented_effects():
    token = _address("c")
    recipient = _address("3")
    effects = normalize_standard_event_logs(
        [
            {
                "address": token,
                "topics": ["0x" + "99" * 32],
                "data": "0x",
            },
            {
                "address": token,
                "topics": [TRANSFER_TOPIC, "0x" + "11" * 32, _topic_address(recipient)],
                "data": _data_word(1),
            },
            {
                "name": "Transfer",
                "raw": {
                    "address": token,
                    "topics": [TRANSFER_TOPIC, _topic_address(_address("1")), _topic_address(recipient)],
                    "data": _data_word(9),
                },
            },
        ],
        source="fixture",
        outcome="predicted",
    )

    assert effects["unknown_log_count"] == 1
    assert effects["malformed_log_count"] == 1
    assert effects["decoded_log_count"] == 1
    assert effects["asset_change_count"] == 1
    assert effects["asset_changes"][0]["amount_raw"] == "9"


@dataclass
class ProspectiveRpc:
    def call(self, method, params=None):
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "http://rpc.test", "0x1", 1.0)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", "0x100", 1.0)
        raise AssertionError((method, params))


def _select(rpc):
    probe = rpc.call("eth_chainId")
    return "direct_rpc", rpc, probe, []


def test_tenderly_predicted_standard_events_flow_into_canonical_transaction_effects(monkeypatch):
    token = _address("2")
    sender = _address("1")
    recipient = _address("3")
    rpc = ProspectiveRpc()
    monkeypatch.setattr(live_b1, "select_rpc_client", lambda chain: _select(rpc))
    monkeypatch.setattr(
        live_b1,
        "resolve_provider",
        lambda *a, **k: Resolution("simulation", "tenderly", "RESOLVED", ["tenderly"]),
    )

    class FakeTenderly:
        def simulate(self, chain, transaction, block_number=None):
            return ProviderCall(
                "tenderly",
                "sim",
                "https://api.tenderly.co/simulate",
                {
                    "simulation": {"id": "sim-1", "network_id": "1", "block_number": 256},
                    "transaction": {
                        "status": True,
                        "gas_used": 45_000,
                        "logs": [
                            {
                                "address": token,
                                "topics": [TRANSFER_TOPIC, _topic_address(sender), _topic_address(recipient)],
                                "data": _data_word(123),
                            }
                        ],
                    },
                },
                8.0,
            )

    monkeypatch.setattr(live_b1, "TenderlyClient", FakeTenderly)
    result = ENGINES[EngineId.B1](
        {
            "chain": "ethereum",
            "from": sender,
            "to": token,
            "data": "0x",
        },
        False,
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert result.engine_version == "1.3.0"
    assert result.metrics["to"] == token
    assert result.metrics["event_effects"]["source"] == "tenderly_simulation"
    assert result.metrics["event_effects"]["outcome"] == "predicted"
    effects = result.metrics["transaction_effects"]
    assert effects["coverage"]["canonical_token_nft_event_changes"] is True
    assert effects["asset_changes"][0]["amount_raw"] == "123"
    assert effects["event_logs"]["source"] == "tenderly_simulation"
    assert "canonical standard token/NFT event-log effects" not in result.missing_data
    assert any(e.source_type == "simulation_event_logs" for e in result.evidence)


@dataclass
class HistoricalRpc:
    token: str
    sender: str
    recipient: str

    def call(self, method, params=None):
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "http://rpc.test", "0x1", 1.0)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", "0x120", 1.0)
        if method == "eth_getTransactionByHash":
            return ProviderCall(
                "direct_rpc",
                "tx",
                "http://rpc.test",
                {
                    "hash": params[0],
                    "from": self.sender,
                    "to": self.token,
                    "value": "0x0",
                    "input": "0x",
                    "blockNumber": "0x100",
                },
                1.0,
            )
        if method == "eth_getTransactionReceipt":
            return ProviderCall(
                "direct_rpc",
                "receipt",
                "http://rpc.test",
                {
                    "status": "0x1",
                    "blockNumber": "0x100",
                    "logs": [
                        {
                            "address": self.token,
                            "topics": [TRANSFER_TOPIC, _topic_address(self.sender), _topic_address(self.recipient)],
                            "data": _data_word(77),
                            "logIndex": "0x1",
                        }
                    ],
                },
                1.0,
            )
        if method == "eth_call":
            return ProviderCall("direct_rpc", "call", "http://rpc.test", "0x", 1.0)
        if method == "eth_estimateGas":
            return ProviderCall("direct_rpc", "gas", "http://rpc.test", "0x5208", 1.0)
        raise AssertionError((method, params))


def test_mined_receipt_events_are_canonical_observed_effects_for_transaction_hash(monkeypatch):
    token = _address("2")
    sender = _address("1")
    recipient = _address("3")
    rpc = HistoricalRpc(token=token, sender=sender, recipient=recipient)
    monkeypatch.setattr(live_b1, "select_rpc_client", lambda chain: _select(rpc))
    monkeypatch.setattr(
        live_b1,
        "resolve_provider",
        lambda *a, **k: Resolution("simulation", None, "PROVIDER_UNAVAILABLE", ["tenderly"]),
    )

    result = ENGINES[EngineId.B1](
        {"chain": "ethereum", "transaction_hash": "0x" + "aa" * 32},
        False,
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert result.engine_version == "1.3.0"
    assert result.metrics["event_effects_precedence"] == "mined_transaction_receipt"
    effects = result.metrics["transaction_effects"]
    assert effects["event_logs"]["source"] == "mined_transaction_receipt"
    assert effects["event_logs"]["outcome"] == "observed"
    assert effects["coverage"]["canonical_token_nft_event_changes"] is True
    assert effects["asset_changes"][0]["amount_raw"] == "77"
    assert any(e.source_type == "observed_transaction_receipt_events" for e in result.evidence)
