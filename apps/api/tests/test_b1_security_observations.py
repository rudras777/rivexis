from rivexis_api.engines import _b1_transaction_effects_summary
from rivexis_api.services.evm_decode import (
    UINT256_MAX,
    decode_common_calldata,
    normalize_call_trace,
)


def address(byte: str) -> str:
    return "0x" + byte * 40


def word(value: int) -> str:
    return f"{value:064x}"


def address_word(value: str) -> str:
    return "0" * 24 + value[2:]


def call(call_type: str, byte: str, **extra):
    return {
        "type": call_type,
        "from": address("1"),
        "to": address(byte),
        "value": "0x0",
        "input": "0x",
        **extra,
    }


def test_security_observations_are_grounded_and_not_a_verdict():
    spender = address("9")
    unlimited_approval = "0x095ea7b3" + address_word(spender) + word(UINT256_MAX)
    trace = call(
        "CALL",
        "2",
        calls=[
            call("DELEGATECALL", "3"),
            call("CREATE2", "4"),
            call("SELFDESTRUCT", "5"),
            call("CALL", "6", error="execution reverted"),
            call("CALL", "7", input=unlimited_approval),
        ],
    )
    state_diff = {
        "status": "NORMALIZED_PRESTATE_DIFF",
        "addresses_touched": 3,
        "addresses_changed": 3,
        "changes": [
            {
                "address": address("a"),
                "change_type": "ACCOUNT_CREATED",
                "changed_fields": ["code"],
                "changed_storage_slots": 0,
            },
            {
                "address": address("b"),
                "change_type": "ACCOUNT_DELETED",
                "changed_fields": ["code"],
                "changed_storage_slots": 0,
            },
            {
                "address": address("c"),
                "change_type": "MODIFIED",
                "changed_fields": ["code"],
                "changed_storage_slots": 0,
            },
        ],
    }

    effects = _b1_transaction_effects_summary(
        {
            "to": address("8"),
            "calldata_decode": decode_common_calldata(unlimited_approval),
            "call_trace": normalize_call_trace(trace),
            "state_diff": state_diff,
        }
    )

    observations = effects["security_observations"]
    signal_types = {signal["type"] for signal in observations["signals"]}
    assert observations["status"] == "OBSERVATIONS_PRESENT"
    assert observations["is_security_verdict"] is False
    assert signal_types == {
        "DELEGATECALL_OBSERVED",
        "DETERMINISTIC_CONTRACT_CREATION_OBSERVED",
        "SELFDESTRUCT_OPCODE_PATH_OBSERVED",
        "INTERNAL_CALL_FAILURE_OBSERVED",
        "UNLIMITED_APPROVAL_CANDIDATE",
        "ACCOUNT_CREATION_OBSERVED",
        "ACCOUNT_DELETION_OBSERVED",
        "RUNTIME_CODE_CHANGE_OBSERVED",
    }
    assert effects["approval_candidates"][0]["scope"] == "UINT256_MAX_CANDIDATE"
    assert effects["approval_candidates"][1]["scope"] == "UINT256_MAX_CANDIDATE"
    unlimited = next(
        signal
        for signal in observations["signals"]
        if signal["type"] == "UNLIMITED_APPROVAL_CANDIDATE"
    )
    assert unlimited["count"] == 2
    assert len(unlimited["candidates"]) == 2


def test_malformed_trace_node_cannot_create_structural_security_signal():
    trace = normalize_call_trace(
        {
            "type": "DELEGATECALL",
            "from": "not-an-address",
            "to": address("2"),
            "value": "0x0",
            "input": "0x",
        }
    )

    effects = _b1_transaction_effects_summary(
        {"calldata_decode": {"status": "NO_CALLDATA"}, "call_trace": trace}
    )

    observations = effects["security_observations"]
    assert observations["status"] == "INSUFFICIENT_COVERAGE"
    assert observations["signals"] == []
    assert observations["coverage"]["canonical_internal_call_trace"] is False


def test_bounded_approval_is_scoped_without_becoming_security_signal():
    spender = address("9")
    approval = "0x095ea7b3" + address_word(spender) + word(25)
    effects = _b1_transaction_effects_summary(
        {
            "to": address("8"),
            "calldata_decode": decode_common_calldata(approval),
        }
    )

    assert effects["approval_candidates"][0]["scope"] == "BOUNDED_AMOUNT_OR_TOKEN_ID"
    observations = effects["security_observations"]
    assert observations["status"] == "NO_STRUCTURAL_OBSERVATION"
    assert observations["signals"] == []


def test_operator_enablement_is_explicit_but_revocation_is_not_a_warning_signal():
    operator = address("7")
    enabled = "0xa22cb465" + address_word(operator) + word(1)
    revoked = "0xa22cb465" + address_word(operator) + word(0)

    enabled_effects = _b1_transaction_effects_summary(
        {"to": address("8"), "calldata_decode": decode_common_calldata(enabled)}
    )
    revoked_effects = _b1_transaction_effects_summary(
        {"to": address("8"), "calldata_decode": decode_common_calldata(revoked)}
    )

    assert enabled_effects["approval_candidates"][0]["scope"] == "ALL_ASSETS_OPERATOR"
    assert enabled_effects["security_observations"]["signals"][0]["type"] == (
        "ALL_ASSETS_OPERATOR_APPROVAL_CANDIDATE"
    )
    assert revoked_effects["approval_candidates"][0]["scope"] == "OPERATOR_REVOCATION"
    assert revoked_effects["security_observations"]["signals"] == []


def test_invalid_target_is_not_promoted_into_permission_observation():
    spender = address("9")
    approval = "0x095ea7b3" + address_word(spender) + word(UINT256_MAX)
    effects = _b1_transaction_effects_summary(
        {"to": "not-an-address", "calldata_decode": decode_common_calldata(approval)}
    )

    assert effects["approval_candidates"][0]["contract"] is None
    assert effects["security_observations"]["signals"] == []
