from rivexis_api.services.evm_decode import (
    decode_verified_abi_calldata,
    function_selector,
)


def word(value: int) -> str:
    return f"{value:064x}"


def address_word(address: str) -> str:
    return "0" * 24 + address[2:].lower()


def test_verified_abi_decodes_canonical_dynamic_bytes():
    signature = "setData(bytes)"
    abi = [
        {
            "type": "function",
            "name": "setData",
            "inputs": [{"name": "data", "type": "bytes"}],
            "outputs": [],
        }
    ]
    payload = word(32) + word(3) + "010203" + ("00" * 29)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "DECODED_VERIFIED_ABI"
    assert result["parameters"][0]["value"] == "0x010203"


def test_verified_abi_decodes_canonical_dynamic_string():
    signature = "setLabel(string)"
    abi = [
        {
            "type": "function",
            "name": "setLabel",
            "inputs": [{"name": "label", "type": "string"}],
            "outputs": [],
        }
    ]
    encoded = "72697665786973"
    payload = word(32) + word(7) + encoded + ("00" * 25)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "DECODED_VERIFIED_ABI"
    assert result["parameters"][0]["value"] == "rivexis"


def test_verified_abi_rejects_dynamic_offset_into_static_head():
    signature = "setData(bytes)"
    abi = [
        {
            "type": "function",
            "name": "setData",
            "inputs": [{"name": "data", "type": "bytes"}],
            "outputs": [],
        }
    ]
    payload = word(0) + word(0)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "MALFORMED_VERIFIED_ABI_CALLDATA"
    assert "static head" in result["malformed_reason"]


def test_verified_abi_rejects_unaligned_dynamic_offset():
    signature = "setData(bytes)"
    abi = [
        {
            "type": "function",
            "name": "setData",
            "inputs": [{"name": "data", "type": "bytes"}],
            "outputs": [],
        }
    ]
    payload = word(33) + word(0)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "MALFORMED_VERIFIED_ABI_CALLDATA"
    assert "aligned" in result["malformed_reason"]


def test_verified_abi_rejects_dynamic_length_past_calldata_tail():
    signature = "setData(bytes)"
    abi = [
        {
            "type": "function",
            "name": "setData",
            "inputs": [{"name": "data", "type": "bytes"}],
            "outputs": [],
        }
    ]
    payload = word(32) + word(33) + ("00" * 32)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "MALFORMED_VERIFIED_ABI_CALLDATA"
    assert "tail bounds" in result["malformed_reason"]


def test_verified_abi_rejects_nonzero_dynamic_bytes_padding():
    signature = "setData(bytes)"
    abi = [
        {
            "type": "function",
            "name": "setData",
            "inputs": [{"name": "data", "type": "bytes"}],
            "outputs": [],
        }
    ]
    padded = "01" + ("00" * 30) + "01"
    payload = word(32) + word(1) + padded

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "MALFORMED_VERIFIED_ABI_CALLDATA"
    assert "padding" in result["malformed_reason"]


def test_verified_abi_decodes_dynamic_array_of_static_addresses():
    signature = "setMembers(address[])"
    abi = [
        {
            "type": "function",
            "name": "setMembers",
            "inputs": [{"name": "members", "type": "address[]"}],
            "outputs": [],
        }
    ]
    first = "0x1111111111111111111111111111111111111111"
    second = "0x2222222222222222222222222222222222222222"
    payload = word(32) + word(2) + address_word(first) + address_word(second)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "DECODED_VERIFIED_ABI"
    assert result["parameters"][0]["value"] == [first, second]


def test_verified_abi_dynamic_array_rejects_noncanonical_bool_element():
    signature = "setFlags(bool[])"
    abi = [
        {
            "type": "function",
            "name": "setFlags",
            "inputs": [{"name": "flags", "type": "bool[]"}],
            "outputs": [],
        }
    ]
    payload = word(32) + word(2) + word(1) + word(2)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "MALFORMED_VERIFIED_ABI_CALLDATA"
    assert "element 1" in result["malformed_reason"]
    assert "bool" in result["malformed_reason"]


def test_verified_abi_does_not_fake_decode_static_tuple():
    signature = "setPair((uint256,address))"
    abi = [
        {
            "type": "function",
            "name": "setPair",
            "inputs": [
                {
                    "name": "pair",
                    "type": "tuple",
                    "components": [
                        {"name": "amount", "type": "uint256"},
                        {"name": "recipient", "type": "address"},
                    ],
                }
            ],
            "outputs": [],
        }
    ]
    recipient = "0x3333333333333333333333333333333333333333"
    payload = word(7) + address_word(recipient)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "UNSUPPORTED_VERIFIED_ABI_TYPE"
    assert result["confidence"] == 0
    assert "tuple" in result["note"]


def test_verified_abi_decodes_fixed_array_of_static_elements():
    signature = "setLevels(uint256[2])"
    abi = [
        {
            "type": "function",
            "name": "setLevels",
            "inputs": [{"name": "levels", "type": "uint256[2]"}],
            "outputs": [],
        }
    ]
    payload = word(1) + word(2)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "DECODED_VERIFIED_ABI"
    assert result["parameters"][0]["value"] == [1, 2]


def test_verified_abi_fixed_array_expands_head_before_dynamic_offset():
    signature = "setLevelsAndNote(uint256[2],string)"
    abi = [
        {
            "type": "function",
            "name": "setLevelsAndNote",
            "inputs": [
                {"name": "levels", "type": "uint256[2]"},
                {"name": "note", "type": "string"},
            ],
            "outputs": [],
        }
    ]
    payload = word(1) + word(2) + word(96) + word(2) + "6f6b" + ("00" * 30)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "DECODED_VERIFIED_ABI"
    assert result["parameters"][0]["value"] == [1, 2]
    assert result["parameters"][1]["value"] == "ok"


def test_verified_abi_fixed_array_rejects_noncanonical_element():
    signature = "setFlags(bool[2])"
    abi = [
        {
            "type": "function",
            "name": "setFlags",
            "inputs": [{"name": "flags", "type": "bool[2]"}],
            "outputs": [],
        }
    ]
    payload = word(1) + word(2)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "MALFORMED_VERIFIED_ABI_CALLDATA"
    assert "element 1" in result["malformed_reason"]
    assert "bool" in result["malformed_reason"]


def test_verified_abi_keeps_nested_fixed_array_unsupported():
    signature = "setMatrix(uint256[2][2])"
    abi = [
        {
            "type": "function",
            "name": "setMatrix",
            "inputs": [{"name": "matrix", "type": "uint256[2][2]"}],
            "outputs": [],
        }
    ]
    payload = word(1) + word(2) + word(3) + word(4)

    result = decode_verified_abi_calldata(function_selector(signature) + payload, abi)

    assert result["status"] == "UNSUPPORTED_VERIFIED_ABI_TYPE"
    assert result["confidence"] == 0
    assert "nested-dynamic" in result["note"]
