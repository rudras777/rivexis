from __future__ import annotations

from typing import Any

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
APPROVAL_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
APPROVAL_FOR_ALL_TOPIC = "0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31"
ERC1155_TRANSFER_SINGLE_TOPIC = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
ERC1155_TRANSFER_BATCH_TOPIC = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
MAX_INPUT_LOGS = 1000
MAX_EFFECT_ROWS = 200
MAX_BATCH_ITEMS = 100


def _hex(value: object, *, nibbles: int | None = None) -> str | None:
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    raw = value[2:]
    if nibbles is not None and len(raw) != nibbles:
        return None
    if len(raw) % 2:
        return None
    try:
        int(raw or "0", 16)
    except ValueError:
        return None
    return "0x" + raw.lower()


def _address(value: object) -> str | None:
    return _hex(value, nibbles=40)


def _topic(value: object) -> str | None:
    return _hex(value, nibbles=64)


def _topic_address(value: object) -> str | None:
    normalized = _topic(value)
    if normalized is None:
        return None
    raw = normalized[2:]
    if raw[:24] != "0" * 24:
        return None
    return "0x" + raw[-40:]


def _topic_uint(value: object) -> int | None:
    normalized = _topic(value)
    if normalized is None:
        return None
    return int(normalized, 16)


def _data_words(value: object) -> list[int] | None:
    normalized = _hex(value)
    if normalized is None:
        return None
    raw = normalized[2:]
    if len(raw) % 64:
        return None
    return [int(raw[i : i + 64], 16) for i in range(0, len(raw), 64)]


def _log_index(value: object) -> int | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        result = int(value, 16) if isinstance(value, str) and value.startswith("0x") else int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _raw_log(row: object) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    nested = row.get("raw")
    raw = nested if isinstance(nested, dict) else row
    address = _address(raw.get("address") or row.get("address"))
    topics_value = raw.get("topics") if "topics" in raw else row.get("topics")
    data_value = raw.get("data") if "data" in raw else row.get("data")
    if address is None or not isinstance(topics_value, list) or not topics_value:
        return None
    topics: list[str] = []
    for value in topics_value:
        topic = _topic(value)
        if topic is None:
            return None
        topics.append(topic)
    data = _hex(data_value)
    if data is None:
        return None
    index_value = raw.get("logIndex")
    if index_value is None:
        index_value = raw.get("log_index")
    if index_value is None:
        index_value = row.get("logIndex")
    if index_value is None:
        index_value = row.get("log_index")
    return {
        "address": address,
        "topics": topics,
        "data": data,
        "log_index": _log_index(index_value),
    }


def _movement_kind(from_address: str, to_address: str) -> str:
    if from_address == ZERO_ADDRESS and to_address == ZERO_ADDRESS:
        return "zero_address_supply_signal"
    if from_address == ZERO_ADDRESS:
        return "mint"
    if to_address == ZERO_ADDRESS:
        return "burn"
    return "transfer"


def _base_effect(raw: dict[str, Any], standard: str, event: str) -> dict[str, Any]:
    return {
        "standard": standard,
        "event": event,
        "contract": raw["address"],
        "log_index": raw["log_index"],
    }


def _decode_transfer(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], int] | None:
    topics = raw["topics"]
    if len(topics) == 3:
        words = _data_words(raw["data"])
        from_address = _topic_address(topics[1])
        to_address = _topic_address(topics[2])
        if words is None or len(words) != 1 or from_address is None or to_address is None:
            return None
        return ([{
            **_base_effect(raw, "ERC20", "Transfer"),
            "kind": _movement_kind(from_address, to_address),
            "from": from_address,
            "to": to_address,
            "amount_raw": str(words[0]),
        }], 1)
    if len(topics) == 4:
        from_address = _topic_address(topics[1])
        to_address = _topic_address(topics[2])
        token_id = _topic_uint(topics[3])
        if raw["data"] != "0x" or from_address is None or to_address is None or token_id is None:
            return None
        return ([{
            **_base_effect(raw, "ERC721", "Transfer"),
            "kind": _movement_kind(from_address, to_address),
            "from": from_address,
            "to": to_address,
            "token_id": str(token_id),
        }], 1)
    return None


def _decode_approval(raw: dict[str, Any]) -> dict[str, Any] | None:
    topics = raw["topics"]
    owner = _topic_address(topics[1]) if len(topics) > 1 else None
    spender = _topic_address(topics[2]) if len(topics) > 2 else None
    if owner is None or spender is None:
        return None
    if len(topics) == 3:
        words = _data_words(raw["data"])
        if words is None or len(words) != 1:
            return None
        return {
            **_base_effect(raw, "ERC20", "Approval"),
            "owner": owner,
            "spender": spender,
            "amount_raw": str(words[0]),
        }
    if len(topics) == 4 and raw["data"] == "0x":
        token_id = _topic_uint(topics[3])
        if token_id is None:
            return None
        return {
            **_base_effect(raw, "ERC721", "Approval"),
            "owner": owner,
            "approved": spender,
            "token_id": str(token_id),
        }
    return None


def _decode_approval_for_all(raw: dict[str, Any]) -> dict[str, Any] | None:
    topics = raw["topics"]
    if len(topics) != 3:
        return None
    owner = _topic_address(topics[1])
    operator = _topic_address(topics[2])
    words = _data_words(raw["data"])
    if owner is None or operator is None or words is None or len(words) != 1 or words[0] not in {0, 1}:
        return None
    return {
        **_base_effect(raw, "ERC721_OR_ERC1155", "ApprovalForAll"),
        "owner": owner,
        "operator": operator,
        "approved": bool(words[0]),
    }


def _decode_erc1155_single(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], int] | None:
    topics = raw["topics"]
    words = _data_words(raw["data"])
    if len(topics) != 4 or words is None or len(words) != 2:
        return None
    operator = _topic_address(topics[1])
    from_address = _topic_address(topics[2])
    to_address = _topic_address(topics[3])
    if operator is None or from_address is None or to_address is None:
        return None
    return ([{
        **_base_effect(raw, "ERC1155", "TransferSingle"),
        "kind": _movement_kind(from_address, to_address),
        "operator": operator,
        "from": from_address,
        "to": to_address,
        "token_id": str(words[0]),
        "amount_raw": str(words[1]),
    }], 1)


def _decode_uint_array(raw_hex: str, offset_bytes: int) -> tuple[list[int], int] | None:
    raw = raw_hex[2:]
    byte_length = len(raw) // 2
    if offset_bytes < 0 or offset_bytes % 32 or offset_bytes + 32 > byte_length:
        return None
    start = offset_bytes * 2
    count = int(raw[start : start + 64], 16)
    end_bytes = offset_bytes + 32 + count * 32
    if end_bytes > byte_length:
        return None
    values: list[int] = []
    for index in range(min(count, MAX_BATCH_ITEMS)):
        word_start = start + 64 + index * 64
        values.append(int(raw[word_start : word_start + 64], 16))
    return values, count


def _decode_erc1155_batch(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], int, bool] | None:
    topics = raw["topics"]
    words = _data_words(raw["data"])
    if len(topics) != 4 or words is None or len(words) < 2:
        return None
    operator = _topic_address(topics[1])
    from_address = _topic_address(topics[2])
    to_address = _topic_address(topics[3])
    if operator is None or from_address is None or to_address is None:
        return None

    # TransferBatch(uint256[],uint256[]) has a two-word head followed by two
    # dynamic arrays. Accept only canonical ABI layout so overlapping/aliased
    # offsets cannot be reinterpreted as legitimate token movements.
    ids_offset = words[0]
    amounts_offset = words[1]
    if ids_offset != 64:
        return None
    ids = _decode_uint_array(raw["data"], ids_offset)
    if ids is None:
        return None
    expected_amounts_offset = ids_offset + 32 + ids[1] * 32
    if amounts_offset != expected_amounts_offset:
        return None
    amounts = _decode_uint_array(raw["data"], amounts_offset)
    if amounts is None or ids[1] != amounts[1]:
        return None
    expected_total_bytes = amounts_offset + 32 + amounts[1] * 32
    if expected_total_bytes != len(raw["data"][2:]) // 2:
        return None

    output: list[dict[str, Any]] = []
    for index, (token_id, amount) in enumerate(zip(ids[0], amounts[0], strict=True)):
        output.append({
            **_base_effect(raw, "ERC1155", "TransferBatch"),
            "kind": _movement_kind(from_address, to_address),
            "operator": operator,
            "from": from_address,
            "to": to_address,
            "token_id": str(token_id),
            "amount_raw": str(amount),
            "batch_item_index": index,
            "batch_size": ids[1],
        })
    return output, ids[1], ids[1] > len(output)


def normalize_standard_event_logs(logs: object, *, source: str, outcome: str) -> dict[str, Any]:
    """Normalize only well-known raw ERC event signatures from an available log list.

    Values remain raw integer strings because token decimals/metadata are not proven by
    an event log. Unknown or malformed logs stay explicit instead of being inferred.
    """

    if not isinstance(logs, list):
        return {
            "status": "EVENT_LOGS_UNAVAILABLE",
            "source": source,
            "outcome": outcome,
            "logs_available": False,
            "input_log_count": None,
            "processed_log_count": 0,
            "omitted_log_count": 0,
            "decoded_log_count": 0,
            "asset_change_count": 0,
            "approval_event_count": 0,
            "unknown_log_count": 0,
            "malformed_log_count": 0,
            "asset_changes": [],
            "approval_events": [],
            "truncated": False,
        }

    input_log_count = len(logs)
    processed_logs = logs[:MAX_INPUT_LOGS]
    omitted_log_count = max(0, input_log_count - len(processed_logs))
    asset_changes: list[dict[str, Any]] = []
    approval_events: list[dict[str, Any]] = []
    decoded_log_count = 0
    asset_change_count = 0
    approval_event_count = 0
    unknown_log_count = 0
    malformed_log_count = 0
    truncated = omitted_log_count > 0

    for row in processed_logs:
        raw = _raw_log(row)
        if raw is None:
            malformed_log_count += 1
            continue
        topic0 = raw["topics"][0]
        if topic0 == TRANSFER_TOPIC:
            decoded = _decode_transfer(raw)
            if decoded is None:
                malformed_log_count += 1
                continue
            rows, count = decoded
            decoded_log_count += 1
            asset_change_count += count
            for effect in rows:
                if len(asset_changes) < MAX_EFFECT_ROWS:
                    asset_changes.append(effect)
                else:
                    truncated = True
        elif topic0 == APPROVAL_TOPIC:
            decoded = _decode_approval(raw)
            if decoded is None:
                malformed_log_count += 1
                continue
            decoded_log_count += 1
            approval_event_count += 1
            if len(approval_events) < MAX_EFFECT_ROWS:
                approval_events.append(decoded)
            else:
                truncated = True
        elif topic0 == APPROVAL_FOR_ALL_TOPIC:
            decoded = _decode_approval_for_all(raw)
            if decoded is None:
                malformed_log_count += 1
                continue
            decoded_log_count += 1
            approval_event_count += 1
            if len(approval_events) < MAX_EFFECT_ROWS:
                approval_events.append(decoded)
            else:
                truncated = True
        elif topic0 == ERC1155_TRANSFER_SINGLE_TOPIC:
            decoded = _decode_erc1155_single(raw)
            if decoded is None:
                malformed_log_count += 1
                continue
            rows, count = decoded
            decoded_log_count += 1
            asset_change_count += count
            for effect in rows:
                if len(asset_changes) < MAX_EFFECT_ROWS:
                    asset_changes.append(effect)
                else:
                    truncated = True
        elif topic0 == ERC1155_TRANSFER_BATCH_TOPIC:
            decoded = _decode_erc1155_batch(raw)
            if decoded is None:
                malformed_log_count += 1
                continue
            rows, count, batch_truncated = decoded
            decoded_log_count += 1
            asset_change_count += count
            truncated = truncated or batch_truncated
            for effect in rows:
                if len(asset_changes) < MAX_EFFECT_ROWS:
                    asset_changes.append(effect)
                else:
                    truncated = True
        else:
            unknown_log_count += 1

    return {
        "status": "NORMALIZED_STANDARD_EVENT_LOGS",
        "source": source,
        "outcome": outcome,
        "logs_available": True,
        "input_log_count": input_log_count,
        "processed_log_count": len(processed_logs),
        "omitted_log_count": omitted_log_count,
        "decoded_log_count": decoded_log_count,
        "asset_change_count": asset_change_count,
        "approval_event_count": approval_event_count,
        "unknown_log_count": unknown_log_count,
        "malformed_log_count": malformed_log_count,
        "asset_changes": asset_changes,
        "approval_events": approval_events,
        "truncated": truncated,
        "raw_amounts_unscaled": True,
    }
