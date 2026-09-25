from __future__ import annotations

from typing import Any

UINT256_MAX = 2**256 - 1
_MAX_DYNAMIC_ARRAY_ITEMS = 4096
_MAX_FIXED_ARRAY_ITEMS = 4096
_MAX_STATIC_TUPLE_ITEMS = 4096
_MAX_CALL_TRACE_NODES = 4096
_MAX_CALL_TRACE_DEPTH = 128
_TRACE_CALL_TYPES = {
    "CALL",
    "CALLCODE",
    "CREATE",
    "CREATE2",
    "DELEGATECALL",
    "SELFDESTRUCT",
    "STATICCALL",
}


def _word(data: str, index: int) -> str | None:
    start = 8 + index * 64
    end = start + 64
    if len(data) < end:
        return None
    return data[start:end]


def _address(word: str | None) -> str | None:
    if not isinstance(word, str) or len(word) != 64:
        return None
    try:
        int(word, 16)
    except ValueError:
        return None
    if word[:24] != "0" * 24:
        return None
    return f"0x{word[-40:].lower()}"


def _uint(word: str | None) -> int | None:
    if not word:
        return None
    try:
        return int(word, 16)
    except ValueError:
        return None


def _bool(word: str | None) -> bool | None:
    value = _uint(word)
    if value == 0:
        return False
    if value == 1:
        return True
    return None


def _malformed_standard(selector: str, signature: str) -> dict[str, Any]:
    return {
        "status": "MALFORMED_STANDARD_CALLDATA",
        "selector": selector,
        "signature": signature,
        "confidence": 0,
        "note": (
            "One or more static ABI words were not canonically encoded; "
            "Rivexis did not normalize them into plausible parameters."
        ),
    }


def decode_common_calldata(calldata: str | None) -> dict[str, Any]:
    """Decode a conservative set of standard EVM token methods without an ABI.

    This is deterministic selector/word decoding, not contract identity inference. Where a
    selector is shared by standards (notably approve(address,uint256)), Rivexis preserves
    that ambiguity instead of inventing whether the target is ERC-20 or ERC-721.
    """
    if not isinstance(calldata, str) or not calldata.startswith("0x"):
        return {"status": "NO_CALLDATA"}
    data = calldata[2:].lower()
    if len(data) < 8:
        return {"status": "NO_SELECTOR"}
    selector = f"0x{data[:8]}"

    if selector == "0xa9059cbb":
        signature = "transfer(address,uint256)"
        to = _address(_word(data, 0))
        amount = _uint(_word(data, 1))
        if to is None or amount is None:
            return _malformed_standard(selector, signature)
        return {
            "status": "DECODED_STANDARD_SELECTOR",
            "selector": selector,
            "signature": signature,
            "standard": "ERC20",
            "parameters": {"to": to, "amount_raw": amount},
            "confidence": 95,
        }
    if selector == "0x095ea7b3":
        signature = "approve(address,uint256)"
        spender = _address(_word(data, 0))
        amount = _uint(_word(data, 1))
        if spender is None or amount is None:
            return _malformed_standard(selector, signature)
        return {
            "status": "DECODED_STANDARD_SELECTOR",
            "selector": selector,
            "signature": signature,
            "standard": "ERC20_OR_ERC721_AMBIGUOUS_WITHOUT_CONTRACT_INTERFACE",
            "parameters": {
                "spender_or_approved": spender,
                "amount_or_token_id": amount,
            },
            "unlimited_approval_candidate": amount == UINT256_MAX,
            "confidence": 88,
        }
    if selector == "0x23b872dd":
        signature = "transferFrom(address,address,uint256)"
        sender = _address(_word(data, 0))
        recipient = _address(_word(data, 1))
        amount = _uint(_word(data, 2))
        if sender is None or recipient is None or amount is None:
            return _malformed_standard(selector, signature)
        return {
            "status": "DECODED_STANDARD_SELECTOR",
            "selector": selector,
            "signature": signature,
            "standard": "ERC20_OR_ERC721_AMBIGUOUS_WITHOUT_CONTRACT_INTERFACE",
            "parameters": {
                "from": sender,
                "to": recipient,
                "amount_or_token_id": amount,
            },
            "confidence": 88,
        }
    if selector == "0x42842e0e":
        signature = "safeTransferFrom(address,address,uint256)"
        sender = _address(_word(data, 0))
        recipient = _address(_word(data, 1))
        token_id = _uint(_word(data, 2))
        if sender is None or recipient is None or token_id is None:
            return _malformed_standard(selector, signature)
        return {
            "status": "DECODED_STANDARD_SELECTOR",
            "selector": selector,
            "signature": signature,
            "standard": "ERC721",
            "parameters": {
                "from": sender,
                "to": recipient,
                "token_id": token_id,
            },
            "confidence": 94,
        }
    if selector == "0xb88d4fde":
        signature = "safeTransferFrom(address,address,uint256,bytes)"
        sender = _address(_word(data, 0))
        recipient = _address(_word(data, 1))
        token_id = _uint(_word(data, 2))
        if sender is None or recipient is None or token_id is None:
            return _malformed_standard(selector, signature)
        return {
            "status": "PARTIALLY_DECODED_STANDARD_SELECTOR",
            "selector": selector,
            "signature": signature,
            "standard": "ERC721",
            "parameters": {
                "from": sender,
                "to": recipient,
                "token_id": token_id,
            },
            "note": "Dynamic bytes argument intentionally not decoded by the ABI-free fallback.",
            "confidence": 90,
        }
    if selector == "0xa22cb465":
        signature = "setApprovalForAll(address,bool)"
        operator = _address(_word(data, 0))
        approved = _bool(_word(data, 1))
        if operator is None or approved is None:
            return _malformed_standard(selector, signature)
        return {
            "status": "DECODED_STANDARD_SELECTOR",
            "selector": selector,
            "signature": signature,
            "standard": "ERC721_OR_ERC1155",
            "parameters": {"operator": operator, "approved": approved},
            "confidence": 94,
        }
    if selector == "0xd0e30db0":
        return {
            "status": "DECODED_KNOWN_SELECTOR",
            "selector": selector,
            "signature": "deposit()",
            "standard": "WRAPPED_NATIVE_COMMON_PATTERN",
            "parameters": {},
            "confidence": 82,
        }
    if selector == "0x2e1a7d4d":
        signature = "withdraw(uint256)"
        amount = _uint(_word(data, 0))
        if amount is None:
            return _malformed_standard(selector, signature)
        return {
            "status": "DECODED_KNOWN_SELECTOR",
            "selector": selector,
            "signature": signature,
            "standard": "WRAPPED_NATIVE_COMMON_PATTERN",
            "parameters": {"amount_raw": amount},
            "confidence": 82,
        }
    return {
        "status": "UNKNOWN_SELECTOR",
        "selector": selector,
        "confidence": 0,
        "note": (
            "No ABI or verified signature evidence was used; "
            "Rivexis will not guess the method."
        ),
    }


_KECCAK_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_KECCAK_ROT = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]
_MASK64 = (1 << 64) - 1


def _rol64(value: int, shift: int) -> int:
    shift %= 64
    return (
        (value << shift) | (value >> (64 - shift if shift else 64))
    ) & _MASK64


def _keccak_f(state: list[int]) -> None:
    for rc in _KECCAK_RC:
        c = [
            state[x]
            ^ state[x + 5]
            ^ state[x + 10]
            ^ state[x + 15]
            ^ state[x + 20]
            for x in range(5)
        ]
        d = [c[(x - 1) % 5] ^ _rol64(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= d[x]
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rol64(
                    state[x + 5 * y], _KECCAK_ROT[x][y]
                )
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = b[x + 5 * y] ^ (
                    (~b[(x + 1) % 5 + 5 * y]) & b[(x + 2) % 5 + 5 * y]
                )
        state[0] ^= rc


def keccak256(data: bytes) -> bytes:
    rate = 136
    state = [0] * 25
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != rate - 1:
        padded.append(0)
    padded.append(0x80)
    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(block[i * 8 : (i + 1) * 8], "little")
        _keccak_f(state)
    out = bytearray()
    while len(out) < 32:
        for i in range(rate // 8):
            out.extend(state[i].to_bytes(8, "little"))
            if len(out) >= 32:
                return bytes(out[:32])
        _keccak_f(state)
    return bytes(out[:32])


def function_selector(signature: str) -> str:
    return "0x" + keccak256(signature.encode()).hex()[:8]


def _canonical_abi_type(param: Any) -> str:
    if not isinstance(param, dict):
        return ""
    typ = str(param.get("type") or "")
    if typ.startswith("tuple"):
        components = param.get("components")
        if not isinstance(components, list) or not all(
            isinstance(component, dict) for component in components
        ):
            return typ
        suffix = typ[5:]
        inner = ",".join(
            _canonical_abi_type(component) for component in components
        )
        return f"({inner}){suffix}"
    return typ


def _abi_int_width(typ: str, prefix: str) -> int | None:
    suffix = typ[len(prefix) :]
    if suffix == "":
        return 256
    if not suffix.isdigit():
        return None
    bits = int(suffix)
    return bits if 8 <= bits <= 256 and bits % 8 == 0 else None


def _decode_abi_static(typ: str, word: str) -> Any:
    if len(word) != 64:
        return None
    if typ == "address":
        return _address(word)
    if typ == "bool":
        return _bool(word)
    if typ.startswith("uint"):
        raw = _uint(word)
        bits = _abi_int_width(typ, "uint")
        if raw is None or bits is None or raw >= (1 << bits):
            return None
        return raw
    if typ.startswith("int"):
        raw = _uint(word)
        bits = _abi_int_width(typ, "int")
        if raw is None or bits is None:
            return None
        low_mask = (1 << bits) - 1
        low = raw & low_mask
        negative = bool(low & (1 << (bits - 1)))
        expected = low
        if negative and bits < 256:
            expected |= ((1 << (256 - bits)) - 1) << bits
        if raw != expected:
            return None
        return low - (1 << bits) if negative else low
    if typ.startswith("bytes") and typ[5:].isdigit():
        size = int(typ[5:])
        if not 1 <= size <= 32:
            return None
        used = size * 2
        if any(ch != "0" for ch in word[used:]):
            return None
        return "0x" + word[:used]
    return None


def _supported_static_type(typ: str) -> bool:
    if typ in {"address", "bool"}:
        return True
    if typ.startswith("uint"):
        return _abi_int_width(typ, "uint") is not None
    if typ.startswith("int"):
        return _abi_int_width(typ, "int") is not None
    if typ.startswith("bytes") and typ[5:].isdigit():
        size = int(typ[5:])
        return 1 <= size <= 32
    return False


def _dynamic_array_element_type(typ: str) -> str | None:
    if not typ.endswith("[]"):
        return None
    element_type = typ[:-2]
    return element_type if _supported_static_type(element_type) else None


def _fixed_array_spec(typ: str) -> tuple[str, int] | None:
    if not typ.endswith("]") or "[" not in typ:
        return None
    element_type, separator, length_text = typ.rpartition("[")
    if not separator or "[" in element_type or not length_text.endswith("]"):
        return None
    length_text = length_text[:-1]
    if not length_text.isdigit() or not _supported_static_type(element_type):
        return None
    length = int(length_text)
    if not 1 <= length <= _MAX_FIXED_ARRAY_ITEMS:
        return None
    return element_type, length


def _static_head_words(typ: str) -> int | None:
    if _supported_static_type(typ):
        return 1
    fixed_array = _fixed_array_spec(typ)
    return fixed_array[1] if fixed_array is not None else None


def _static_tuple_components(param: dict[str, Any]) -> list[tuple[str, str]] | None:
    if param.get("type") != "tuple":
        return None
    components = param.get("components")
    if (
        not isinstance(components, list)
        or not 1 <= len(components) <= _MAX_STATIC_TUPLE_ITEMS
        or not all(isinstance(component, dict) for component in components)
    ):
        return None
    normalized = []
    for index, component in enumerate(components):
        typ = _canonical_abi_type(component)
        if not _supported_static_type(typ):
            return None
        normalized.append((component.get("name") or f"item{index}", typ))
    return normalized


def _static_param_words(param: dict[str, Any], typ: str) -> int | None:
    words = _static_head_words(typ)
    if words is not None:
        return words
    tuple_components = _static_tuple_components(param)
    return len(tuple_components) if tuple_components is not None else None


def _is_supported_dynamic_type(typ: str) -> bool:
    return typ in {"bytes", "string"} or _dynamic_array_element_type(typ) is not None


def _is_composite_or_dynamic_type(typ: str) -> bool:
    return (
        typ in {"bytes", "string"}
        or "[" in typ
        or "]" in typ
        or typ.startswith("(")
    )


def _padded_bytes(length: int) -> int:
    return ((length + 31) // 32) * 32


def _decode_dynamic_value(
    *,
    typ: str,
    payload: str,
    offset: int,
    head_size_bytes: int,
) -> tuple[Any, str | None]:
    payload_bytes = len(payload) // 2

    if offset % 32 != 0:
        return None, "dynamic ABI offset is not 32-byte aligned"
    if offset < head_size_bytes:
        return None, "dynamic ABI offset points into the static head"
    if offset + 32 > payload_bytes:
        return None, "dynamic ABI offset does not contain a complete length word"

    start = offset * 2
    length = _uint(payload[start : start + 64])
    if length is None:
        return None, "dynamic ABI length word is malformed"

    data_start_bytes = offset + 32
    data_start = start + 64

    if typ in {"bytes", "string"}:
        padded = _padded_bytes(length)
        padded_end_bytes = data_start_bytes + padded
        if padded_end_bytes > payload_bytes:
            return None, "dynamic bytes/string length exceeds calldata tail bounds"
        raw = payload[data_start : data_start + length * 2]
        if len(raw) != length * 2:
            return None, "dynamic bytes/string payload is truncated"
        padding = payload[data_start + length * 2 : padded_end_bytes * 2]
        if any(ch != "0" for ch in padding):
            return None, "dynamic bytes/string padding is non-zero"
        if typ == "bytes":
            return "0x" + raw, None
        try:
            return bytes.fromhex(raw).decode("utf-8"), None
        except UnicodeDecodeError:
            return {"hex": "0x" + raw, "length": length}, None
        except ValueError:
            return None, "dynamic string payload is not hexadecimal"

    element_type = _dynamic_array_element_type(typ)
    if element_type is not None:
        if length > _MAX_DYNAMIC_ARRAY_ITEMS:
            return None, "dynamic array exceeds the bounded decoder item limit"
        array_end_bytes = data_start_bytes + length * 32
        if array_end_bytes > payload_bytes:
            return None, "dynamic array length exceeds calldata tail bounds"
        values = []
        for index in range(length):
            word_start = data_start + index * 64
            word = payload[word_start : word_start + 64]
            value = _decode_abi_static(element_type, word)
            if value is None:
                return None, (
                    f"dynamic array element {index} is not canonically encoded "
                    f"as {element_type}"
                )
            values.append(value)
        return values, None

    return None, f"verified ABI dynamic type {typ} is not supported by the bounded decoder"


def _malformed_verified_abi(
    *,
    selector: str,
    signature: str,
    function_name: Any,
    parameters: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    return {
        "status": "MALFORMED_VERIFIED_ABI_CALLDATA",
        "selector": selector,
        "signature": signature,
        "function": function_name,
        "parameters": parameters,
        "confidence": 0,
        "note": (
            "Verified ABI calldata failed canonical bounds/encoding validation; "
            "Rivexis did not coerce it into valid parameters."
        ),
        "malformed_reason": reason,
    }


def decode_verified_abi_calldata(
    calldata: str | None, abi: Any
) -> dict[str, Any]:
    if not isinstance(calldata, str) or not calldata.startswith("0x") or len(calldata) < 10:
        return {"status": "NO_SELECTOR"}

    if isinstance(abi, str):
        import json

        try:
            abi = json.loads(abi)
        except Exception:
            return {"status": "INVALID_ABI"}
    if not isinstance(abi, list):
        return {"status": "INVALID_ABI"}

    selector = calldata[:10].lower()
    payload = calldata[10:].lower()

    for item in abi:
        if (
            not isinstance(item, dict)
            or item.get("type") != "function"
            or not item.get("name")
        ):
            continue
        inputs = item.get("inputs") or []
        if not isinstance(inputs, list) or not all(isinstance(x, dict) for x in inputs):
            continue

        signature = (
            f"{item['name']}({','.join(_canonical_abi_type(x) for x in inputs)})"
        )
        if function_selector(signature) != selector:
            continue

        abi_types = [_canonical_abi_type(param) for param in inputs]
        unsupported = next(
            (
                typ
                for param, typ in zip(inputs, abi_types, strict=True)
                if _static_param_words(param, typ) is None
                and not _is_supported_dynamic_type(typ)
            ),
            None,
        )
        if unsupported is not None:
            note = (
                f"Verified ABI type {unsupported} requires tuple/fixed-array/"
                "nested-dynamic decoding that Rivexis does not currently claim."
                if _is_composite_or_dynamic_type(unsupported)
                else f"Verified ABI type {unsupported} is not supported by the bounded decoder."
            )
            return {
                "status": "UNSUPPORTED_VERIFIED_ABI_TYPE",
                "selector": selector,
                "signature": signature,
                "function": item.get("name"),
                "parameters": [
                    {
                        "name": param.get("name") or f"arg{index}",
                        "type": abi_types[index],
                        "value": None,
                    }
                    for index, param in enumerate(inputs)
                ],
                "confidence": 0,
                "note": note,
            }

        decoded: list[dict[str, Any]] = []
        if len(payload) % 64 != 0:
            return _malformed_verified_abi(
                selector=selector,
                signature=signature,
                function_name=item.get("name"),
                parameters=decoded,
                reason="ABI argument payload is not a whole number of 32-byte words",
            )
        try:
            int(payload or "0", 16)
        except ValueError:
            return _malformed_verified_abi(
                selector=selector,
                signature=signature,
                function_name=item.get("name"),
                parameters=decoded,
                reason="ABI argument payload contains non-hexadecimal characters",
            )

        head_size_bytes = sum(
            _static_param_words(param, typ) or 1
            for param, typ in zip(inputs, abi_types, strict=True)
        ) * 32
        head_word_index = 0

        for index, param in enumerate(inputs):
            typ = abi_types[index]
            entry = {
                "name": param.get("name") or f"arg{index}",
                "type": typ,
                "value": None,
            }
            word = payload[head_word_index * 64 : (head_word_index + 1) * 64]
            if len(word) != 64:
                decoded.append(entry)
                return _malformed_verified_abi(
                    selector=selector,
                    signature=signature,
                    function_name=item.get("name"),
                    parameters=decoded,
                    reason=f"ABI head word {index} is missing or truncated",
                )

            if _supported_static_type(typ):
                value = _decode_abi_static(typ, word)
                entry["value"] = value
                decoded.append(entry)
                head_word_index += 1
                if value is None:
                    return _malformed_verified_abi(
                        selector=selector,
                        signature=signature,
                        function_name=item.get("name"),
                        parameters=decoded,
                        reason=f"static ABI parameter {index} is not canonically encoded as {typ}",
                    )
                continue

            fixed_array = _fixed_array_spec(typ)
            if fixed_array is not None:
                element_type, length = fixed_array
                values = []
                error = None
                for element_index in range(length):
                    element_word_index = head_word_index + element_index
                    element_word = payload[
                        element_word_index * 64 : (element_word_index + 1) * 64
                    ]
                    if len(element_word) != 64:
                        error = f"fixed array element {element_index} is missing or truncated"
                        break
                    value = _decode_abi_static(element_type, element_word)
                    if value is None:
                        error = (
                            f"fixed array element {element_index} is not canonically "
                            f"encoded as {element_type}"
                        )
                        break
                    values.append(value)
                entry["value"] = values if error is None else None
                decoded.append(entry)
                head_word_index += length
                if error is not None:
                    return _malformed_verified_abi(
                        selector=selector,
                        signature=signature,
                        function_name=item.get("name"),
                        parameters=decoded,
                        reason=error,
                    )
                continue

            tuple_components = _static_tuple_components(param)
            if tuple_components is not None:
                values = []
                error = None
                for component_index, (component_name, component_type) in enumerate(
                    tuple_components
                ):
                    component_word_index = head_word_index + component_index
                    component_word = payload[
                        component_word_index * 64 : (component_word_index + 1) * 64
                    ]
                    if len(component_word) != 64:
                        error = (
                            f"static tuple component {component_index} is missing or truncated"
                        )
                        break
                    value = _decode_abi_static(component_type, component_word)
                    if value is None:
                        error = (
                            f"static tuple component {component_index} is not canonically "
                            f"encoded as {component_type}"
                        )
                        break
                    values.append(
                        {
                            "name": component_name,
                            "type": component_type,
                            "value": value,
                        }
                    )
                entry["value"] = values if error is None else None
                decoded.append(entry)
                head_word_index += len(tuple_components)
                if error is not None:
                    return _malformed_verified_abi(
                        selector=selector,
                        signature=signature,
                        function_name=item.get("name"),
                        parameters=decoded,
                        reason=error,
                    )
                continue

            if _is_supported_dynamic_type(typ):
                offset = _uint(word)
                if offset is None:
                    decoded.append(entry)
                    return _malformed_verified_abi(
                        selector=selector,
                        signature=signature,
                        function_name=item.get("name"),
                        parameters=decoded,
                        reason=f"dynamic ABI offset word {index} is malformed",
                    )
                value, error = _decode_dynamic_value(
                    typ=typ,
                    payload=payload,
                    offset=offset,
                    head_size_bytes=head_size_bytes,
                )
                entry["value"] = value
                decoded.append(entry)
                head_word_index += 1
                if error is not None:
                    return _malformed_verified_abi(
                        selector=selector,
                        signature=signature,
                        function_name=item.get("name"),
                        parameters=decoded,
                        reason=error,
                    )
                continue

        return {
            "status": "DECODED_VERIFIED_ABI",
            "selector": selector,
            "signature": signature,
            "function": item.get("name"),
            "parameters": decoded,
            "confidence": 99,
        }

    return {
        "status": "SELECTOR_NOT_FOUND_IN_VERIFIED_ABI",
        "selector": selector,
        "confidence": 0,
    }


def normalize_call_trace(trace: Any) -> dict[str, Any]:
    calls: list[dict[str, Any]] = []
    native_transfers: list[dict[str, Any]] = []
    approval_candidates: list[dict[str, Any]] = []
    malformed_node_count = 0
    discarded_node_count = 0
    truncation_reasons: set[str] = set()
    active_nodes: set[int] = set()

    def walk(node: Any, parent: int | None = None, depth: int = 0):
        nonlocal malformed_node_count, discarded_node_count
        if not isinstance(node, dict):
            discarded_node_count += 1
            return
        if depth > _MAX_CALL_TRACE_DEPTH:
            discarded_node_count += 1
            truncation_reasons.add("depth_limit")
            return
        if len(calls) >= _MAX_CALL_TRACE_NODES:
            discarded_node_count += 1
            truncation_reasons.add("node_limit")
            return
        node_id = id(node)
        if node_id in active_nodes:
            discarded_node_count += 1
            truncation_reasons.add("cycle_detected")
            return
        active_nodes.add(node_id)

        idx = len(calls)
        issues = []
        data = node.get("input", "0x")
        if not _is_trace_calldata(data):
            data = None
            issues.append("invalid_input")
        decoded = decode_common_calldata(data)
        value = _trace_quantity(node.get("value"))
        gas = _trace_quantity(node.get("gas"))
        gas_used = _trace_quantity(node.get("gasUsed"))
        if node.get("value") is not None and value is None:
            issues.append("invalid_value")
        if node.get("gas") is not None and gas is None:
            issues.append("invalid_gas")
        if node.get("gasUsed") is not None and gas_used is None:
            issues.append("invalid_gas_used")

        from_address = _trace_address(node.get("from"))
        to_address = _trace_address(node.get("to"))
        if node.get("from") is not None and from_address is None:
            issues.append("invalid_from")
        if node.get("to") is not None and to_address is None:
            issues.append("invalid_to")

        raw_call_type = node.get("type")
        call_type = raw_call_type.upper() if isinstance(raw_call_type, str) else None
        if call_type not in _TRACE_CALL_TYPES:
            call_type = "UNKNOWN"
            issues.append("invalid_call_type")

        raw_error = node.get("error")
        error = raw_error[:512] if isinstance(raw_error, str) and raw_error else None
        if raw_error is not None and not isinstance(raw_error, str):
            issues.append("invalid_error")

        children = node.get("calls")
        if children is None:
            children = []
        elif not isinstance(children, list):
            children = []
            issues.append("invalid_calls")

        if issues:
            malformed_node_count += 1
        item = {
            "trace_index": idx,
            "parent_trace_index": parent,
            "depth": depth,
            "call_type": call_type,
            "from": from_address,
            "to": to_address,
            "value_wei": value,
            "gas": gas,
            "gas_used": gas_used,
            "error": error,
            "selector": decoded.get("selector"),
            "calldata_decode": decoded,
            "integrity": "MALFORMED" if issues else "VALID",
            "integrity_issues": issues,
        }
        calls.append(item)
        if isinstance(value, int) and value > 0 and from_address and to_address:
            native_transfers.append(
                {
                    "trace_index": idx,
                    "from": from_address,
                    "to": to_address,
                    "amount_wei": value,
                }
            )
        if (
            decoded.get("status")
            in {"DECODED_STANDARD_SELECTOR", "PARTIALLY_DECODED_STANDARD_SELECTOR"}
            and decoded.get("signature")
            in {"approve(address,uint256)", "setApprovalForAll(address,bool)"}
            and to_address is not None
        ):
            approval_candidates.append(
                {
                    "trace_index": idx,
                    "contract": to_address,
                    "decode": decoded,
                }
            )
        for child in children:
            walk(child, idx, depth + 1)
        active_nodes.remove(node_id)

    walk(trace)
    partial = bool(malformed_node_count or discarded_node_count or truncation_reasons)
    status = (
        "UNAVAILABLE_CALL_TRACE"
        if not calls
        else "PARTIAL_CALL_TRACE"
        if partial
        else "NORMALIZED_CALL_TRACE"
    )
    return {
        "status": status,
        "calls": calls,
        "native_value_transfers": native_transfers,
        "approval_candidates": approval_candidates,
        "call_count": len(calls),
        "valid_call_count": sum(1 for x in calls if x.get("integrity") == "VALID"),
        "error_count": sum(1 for x in calls if x.get("error")),
        "malformed_node_count": malformed_node_count,
        "discarded_node_count": discarded_node_count,
        "truncated": bool(truncation_reasons),
        "truncation_reasons": sorted(truncation_reasons),
    }


def _trace_address(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return None
    try:
        int(value[2:], 16)
    except ValueError:
        return None
    return value.lower()


def _is_trace_calldata(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("0x"):
        return False
    digits = value[2:]
    if len(digits) % 2 != 0:
        return False
    try:
        int(digits or "0", 16)
    except ValueError:
        return False
    return True


def _trace_quantity(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= UINT256_MAX else None
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    digits = value[2:]
    if not digits or (len(digits) > 1 and digits[0] == "0"):
        return None
    try:
        parsed = int(digits, 16)
    except ValueError:
        return None
    return parsed if parsed <= UINT256_MAX else None


def summarize_prestate_diff(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": "UNAVAILABLE"}
    pre = value.get("pre") if isinstance(value.get("pre"), dict) else {}
    post = value.get("post") if isinstance(value.get("post"), dict) else {}
    addresses = sorted(set(pre) | set(post))
    changes = []
    for address in addresses:
        before = pre.get(address) or {}
        after = post.get(address) or {}
        fields = []
        for field in ("balance", "nonce", "code"):
            if before.get(field) != after.get(field):
                fields.append(field)
        bstore = before.get("storage") if isinstance(before.get("storage"), dict) else {}
        astore = after.get("storage") if isinstance(after.get("storage"), dict) else {}
        changed_slots = sum(
            1
            for slot in set(bstore) | set(astore)
            if bstore.get(slot) != astore.get(slot)
        )
        if fields or changed_slots:
            changes.append(
                {
                    "address": address,
                    "changed_fields": fields,
                    "changed_storage_slots": changed_slots,
                }
            )
    return {
        "status": "NORMALIZED_PRESTATE_DIFF",
        "addresses_touched": len(addresses),
        "addresses_changed": len(changes),
        "changes": changes[:200],
        "truncated": len(changes) > 200,
    }
