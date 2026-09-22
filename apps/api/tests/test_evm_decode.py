from rivexis_api.services.evm_decode import UINT256_MAX, decode_common_calldata


def word(value: int) -> str:
    return f"{value:064x}"


def address_word(address: str) -> str:
    return "0" * 24 + address[2:].lower()


def test_decodes_erc20_transfer():
    to="0x1111111111111111111111111111111111111111"
    data="0xa9059cbb"+address_word(to)+word(12345)
    out=decode_common_calldata(data)
    assert out["signature"]=="transfer(address,uint256)"
    assert out["parameters"]=={"to":to,"amount_raw":12345}


def test_flags_uint256_max_approval_without_overclaiming_standard():
    spender="0x2222222222222222222222222222222222222222"
    data="0x095ea7b3"+address_word(spender)+word(UINT256_MAX)
    out=decode_common_calldata(data)
    assert out["unlimited_approval_candidate"] is True
    assert "AMBIGUOUS" in out["standard"]


def test_unknown_selector_is_not_guessed():
    out=decode_common_calldata("0xdeadbeef"+word(1))
    assert out["status"]=="UNKNOWN_SELECTOR"
    assert out["confidence"]==0


def test_keccak_selector_matches_ethereum_standard():
    from rivexis_api.services.evm_decode import function_selector
    assert function_selector("transfer(address,uint256)")=="0xa9059cbb"
    assert function_selector("approve(address,uint256)")=="0x095ea7b3"


def test_verified_abi_decodes_nonstandard_static_function():
    from rivexis_api.services.evm_decode import decode_verified_abi_calldata, function_selector
    target="0x3333333333333333333333333333333333333333"
    signature="allocate(address,uint256)"
    calldata=function_selector(signature)+address_word(target)+word(777)
    abi=[{"type":"function","name":"allocate","inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[]}]
    out=decode_verified_abi_calldata(calldata,abi)
    assert out["status"]=="DECODED_VERIFIED_ABI"
    assert out["signature"]==signature
    assert out["parameters"][0]["value"]==target
    assert out["parameters"][1]["value"]==777


def test_call_trace_normalization_extracts_nested_value_and_approval():
    from rivexis_api.services.evm_decode import normalize_call_trace
    spender="0x4444444444444444444444444444444444444444"
    approval="0x095ea7b3"+address_word(spender)+word(UINT256_MAX)
    trace={"type":"CALL","from":"0x"+"11"*20,"to":"0x"+"22"*20,"value":"0x0","input":"0x","calls":[
        {"type":"CALL","from":"0x"+"22"*20,"to":"0x"+"33"*20,"value":"0x10","gas":"0x100","gasUsed":"0x80","input":approval}
    ]}
    out=normalize_call_trace(trace)
    assert out["call_count"]==2
    assert out["native_value_transfers"][0]["amount_wei"]==16
    assert out["approval_candidates"][0]["decode"]["unlimited_approval_candidate"] is True
