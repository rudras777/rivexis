from __future__ import annotations

from rivexis_api.services.evm_events import (
    ERC1155_TRANSFER_BATCH_TOPIC,
    MAX_INPUT_LOGS,
    TRANSFER_TOPIC,
    normalize_standard_event_logs,
)


def address(byte: str) -> str:
    return "0x" + byte * 40


def topic_address(value: str) -> str:
    return "0x" + "0" * 24 + value[2:]


def word(value: int) -> str:
    return f"{value:064x}"


def batch_log(data: str) -> dict:
    return {
        "address": address("a"),
        "topics": [
            ERC1155_TRANSFER_BATCH_TOPIC,
            topic_address(address("1")),
            topic_address(address("2")),
            topic_address(address("3")),
        ],
        "data": data,
        "logIndex": 0,
    }


def test_transfer_batch_rejects_noncanonical_or_overlapping_offsets():
    # ids offset points into the two-word ABI head. The old decoder could reinterpret
    # this as array data when the payload happened to satisfy its loose bounds.
    overlapping = "0x" + "".join(
        [
            word(0),
            word(64),
            word(2),
            word(7),
            word(8),
            word(2),
            word(70),
            word(80),
        ]
    )
    effects = normalize_standard_event_logs(
        [batch_log(overlapping)], source="fixture", outcome="predicted"
    )

    assert effects["decoded_log_count"] == 0
    assert effects["malformed_log_count"] == 1
    assert effects["asset_changes"] == []


def test_transfer_batch_rejects_trailing_noncanonical_abi_words():
    canonical_with_trailing_word = "0x" + "".join(
        [
            word(64),
            word(160),
            word(2),
            word(7),
            word(8),
            word(2),
            word(70),
            word(80),
            word(999),
        ]
    )
    effects = normalize_standard_event_logs(
        [batch_log(canonical_with_trailing_word)], source="fixture", outcome="observed"
    )

    assert effects["decoded_log_count"] == 0
    assert effects["malformed_log_count"] == 1
    assert effects["asset_change_count"] == 0


def test_integer_zero_log_index_is_preserved():
    sender = address("1")
    recipient = address("2")
    log = {
        "address": address("a"),
        "topics": [TRANSFER_TOPIC, topic_address(sender), topic_address(recipient)],
        "data": "0x" + word(42),
        "logIndex": 0,
    }

    effects = normalize_standard_event_logs([log], source="fixture", outcome="observed")

    assert effects["decoded_log_count"] == 1
    assert effects["asset_changes"][0]["log_index"] == 0


def test_event_normalization_bounds_input_logs_and_reports_omitted_coverage():
    unknown = {
        "address": address("a"),
        "topics": ["0x" + "99" * 32],
        "data": "0x",
    }
    logs = [dict(unknown) for _ in range(MAX_INPUT_LOGS + 17)]

    effects = normalize_standard_event_logs(logs, source="fixture", outcome="predicted")

    assert effects["input_log_count"] == MAX_INPUT_LOGS + 17
    assert effects["processed_log_count"] == MAX_INPUT_LOGS
    assert effects["omitted_log_count"] == 17
    assert effects["unknown_log_count"] == MAX_INPUT_LOGS
    assert effects["truncated"] is True
