from rivexis_api.services.evm_decode import summarize_prestate_diff


def address(byte: str) -> str:
    return "0x" + byte * 40


def word(value: int) -> str:
    return f"0x{value:064x}"


def test_state_diff_rejects_non_object_and_missing_sections():
    for value in (None, [], {}, {"unrelated": {}}):
        result = summarize_prestate_diff(value)
        assert result["status"] == "UNAVAILABLE_PRESTATE_DIFF"
        assert result["changes"] == []


def test_state_diff_normalizes_canonical_fields_and_storage():
    account = address("a")
    result = summarize_prestate_diff(
        {
            "pre": {
                account.upper().replace("0X", "0x"): {
                    "balance": "0x10",
                    "nonce": 1,
                    "code": "0x6000",
                    "storage": {word(1): word(2)},
                }
            },
            "post": {
                account: {
                    "balance": "0xf",
                    "nonce": 1,
                    "code": "0x6000",
                    "storage": {word(1): word(3)},
                }
            },
        }
    )

    assert result["status"] == "NORMALIZED_PRESTATE_DIFF"
    assert result["addresses_touched"] == 1
    assert result["addresses_changed"] == 1
    assert result["changes"] == [
        {
            "address": account,
            "change_type": "MODIFIED",
            "changed_fields": ["balance"],
            "changed_storage_slots": 1,
        }
    ]


def test_state_diff_malformed_fields_cannot_become_changes():
    account = address("1")
    result = summarize_prestate_diff(
        {
            "pre": {
                account: {
                    "balance": "0x00",
                    "nonce": "0x1",
                    "code": "0xabc",
                    "storage": {"0x01": word(1)},
                }
            },
            "post": {
                account: {
                    "balance": "0x1",
                    "nonce": "0x2",
                    "code": "0x6000",
                    "storage": {word(1): word(2)},
                }
            },
        }
    )

    assert result["status"] == "PARTIAL_PRESTATE_DIFF"
    assert result["addresses_changed"] == 0
    assert result["changes"] == []
    assert result["malformed_field_count"] == 3
    assert result["malformed_storage_entry_count"] == 1


def test_state_diff_keeps_valid_address_changes_but_reports_invalid_address():
    account = address("2")
    result = summarize_prestate_diff(
        {
            "pre": {
                "not-an-address": {"balance": "0x1"},
                account: {"balance": "0x1"},
            },
            "post": {account: {"balance": "0x2"}},
        }
    )

    assert result["status"] == "PARTIAL_PRESTATE_DIFF"
    assert result["addresses_touched"] == 1
    assert result["addresses_changed"] == 1
    assert result["malformed_address_count"] == 1
    assert result["discarded_address_count"] == 1


def test_state_diff_omitted_post_fields_are_unchanged_per_geth_diff_contract():
    account = address("3")
    result = summarize_prestate_diff(
        {
            "pre": {
                account: {
                    "balance": "0x10",
                    "nonce": 7,
                    "code": "0x6000",
                    "storage": {word(1): word(2)},
                }
            },
            "post": {account: {"nonce": 8, "storage": {word(1): word(3)}}},
        }
    )

    assert result["status"] == "NORMALIZED_PRESTATE_DIFF"
    assert result["changes"] == [
        {
            "address": account,
            "change_type": "MODIFIED",
            "changed_fields": ["nonce"],
            "changed_storage_slots": 1,
        }
    ]


def test_state_diff_labels_created_and_deleted_accounts():
    deleted = address("4")
    created = address("5")
    result = summarize_prestate_diff(
        {
            "pre": {deleted: {"balance": "0x1", "nonce": 1, "code": "0x"}},
            "post": {created: {"balance": "0x2", "nonce": 1, "code": "0x6000"}},
        }
    )

    assert result["status"] == "NORMALIZED_PRESTATE_DIFF"
    assert [change["change_type"] for change in result["changes"]] == [
        "ACCOUNT_DELETED",
        "ACCOUNT_CREATED",
    ]


def test_state_diff_with_only_invalid_addresses_is_unavailable():
    result = summarize_prestate_diff(
        {"pre": {"not-an-address": {"balance": "0x1"}}, "post": {}}
    )

    assert result["status"] == "UNAVAILABLE_PRESTATE_DIFF"
    assert result["addresses_touched"] == 0
    assert result["changes"] == []


def test_state_diff_duplicate_case_alias_is_discarded():
    account = address("a")
    upper = account.upper().replace("0X", "0x")
    result = summarize_prestate_diff(
        {
            "pre": {
                account: {"balance": "0x1"},
                upper: {"balance": "0x2"},
            },
            "post": {account: {"balance": "0x3"}},
        }
    )

    assert result["status"] == "UNAVAILABLE_PRESTATE_DIFF"
    assert result["changes"] == []
    assert result["malformed_address_count"] == 1


def test_state_diff_change_output_is_bounded_and_reported():
    pre = {
        f"0x{index:040x}": {"balance": "0x1"}
        for index in range(1, 202)
    }
    post = {
        f"0x{index:040x}": {"balance": "0x2"}
        for index in range(1, 202)
    }

    result = summarize_prestate_diff({"pre": pre, "post": post})

    assert result["status"] == "PARTIAL_PRESTATE_DIFF"
    assert result["addresses_changed"] == 201
    assert len(result["changes"]) == 200
    assert result["truncated"] is True
    assert result["truncation_reasons"] == ["change_output_limit"]
