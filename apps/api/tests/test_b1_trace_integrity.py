from rivexis_api.services.evm_decode import UINT256_MAX, normalize_call_trace


def address(byte: str) -> str:
    return "0x" + byte * 40


def word(value: int) -> str:
    return f"{value:064x}"


def address_word(value: str) -> str:
    return "0" * 24 + value[2:]


def test_trace_rejects_malformed_quantities_instead_of_coercing_zero():
    trace = {
        "type": "CALL",
        "from": address("1"),
        "to": address("2"),
        "value": "0x00",
        "gas": True,
        "gasUsed": -1,
        "input": "0x",
    }

    result = normalize_call_trace(trace)

    assert result["status"] == "PARTIAL_CALL_TRACE"
    assert result["malformed_node_count"] == 1
    assert result["calls"][0]["value_wei"] is None
    assert result["calls"][0]["gas"] is None
    assert result["calls"][0]["gas_used"] is None
    assert result["native_value_transfers"] == []
    assert result["calls"][0]["integrity_issues"] == [
        "invalid_value",
        "invalid_gas",
        "invalid_gas_used",
    ]


def test_trace_rejects_quantity_above_uint256():
    trace = {
        "type": "CALL",
        "from": address("1"),
        "to": address("2"),
        "value": hex(UINT256_MAX + 1),
        "input": "0x",
    }

    result = normalize_call_trace(trace)

    assert result["status"] == "PARTIAL_CALL_TRACE"
    assert result["calls"][0]["value_wei"] is None
    assert result["native_value_transfers"] == []


def test_trace_invalid_addresses_cannot_become_transfer_or_approval_evidence():
    spender = address("4")
    approval = "0x095ea7b3" + address_word(spender) + word(UINT256_MAX)
    trace = {
        "type": "CALL",
        "from": "not-an-address",
        "to": "0x1234",
        "value": "0x10",
        "input": approval,
    }

    result = normalize_call_trace(trace)

    assert result["status"] == "PARTIAL_CALL_TRACE"
    assert result["calls"][0]["from"] is None
    assert result["calls"][0]["to"] is None
    assert result["native_value_transfers"] == []
    assert result["approval_candidates"] == []


def test_trace_rejects_noncanonical_calldata_and_child_collection():
    trace = {
        "type": "CALL",
        "from": address("1"),
        "to": address("2"),
        "value": "0x0",
        "input": "0xabc",
        "calls": {"type": "CALL"},
    }

    result = normalize_call_trace(trace)

    assert result["status"] == "PARTIAL_CALL_TRACE"
    assert result["call_count"] == 1
    assert result["calls"][0]["calldata_decode"]["status"] == "NO_CALLDATA"
    assert result["calls"][0]["integrity_issues"] == [
        "invalid_input",
        "invalid_calls",
    ]


def test_trace_discards_non_object_child_without_promoting_evidence():
    trace = {
        "type": "CALL",
        "from": address("1"),
        "to": address("2"),
        "value": "0x0",
        "input": "0x",
        "calls": ["bad-child"],
    }

    result = normalize_call_trace(trace)

    assert result["status"] == "PARTIAL_CALL_TRACE"
    assert result["call_count"] == 1
    assert result["discarded_node_count"] == 1


def test_trace_depth_is_bounded_and_reported():
    root = {
        "type": "CALL",
        "from": address("1"),
        "to": address("2"),
        "value": "0x0",
        "input": "0x",
    }
    current = root
    for _ in range(130):
        child = {
            "type": "CALL",
            "from": address("1"),
            "to": address("2"),
            "value": "0x0",
            "input": "0x",
        }
        current["calls"] = [child]
        current = child

    result = normalize_call_trace(root)

    assert result["status"] == "PARTIAL_CALL_TRACE"
    assert result["call_count"] == 129
    assert result["truncated"] is True
    assert result["truncation_reasons"] == ["depth_limit"]


def test_trace_cycle_is_bounded_and_reported():
    trace = {
        "type": "CALL",
        "from": address("1"),
        "to": address("2"),
        "value": "0x0",
        "input": "0x",
    }
    trace["calls"] = [trace]

    result = normalize_call_trace(trace)

    assert result["status"] == "PARTIAL_CALL_TRACE"
    assert result["call_count"] == 1
    assert result["discarded_node_count"] == 1
    assert result["truncation_reasons"] == ["cycle_detected"]


def test_trace_non_object_root_is_unavailable():
    result = normalize_call_trace("not-a-trace")

    assert result["status"] == "UNAVAILABLE_CALL_TRACE"
    assert result["call_count"] == 0
    assert result["valid_call_count"] == 0
    assert result["discarded_node_count"] == 1
