from __future__ import annotations

from typing import Any

UINT256_MAX = 2**256 - 1


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
    # Canonical ABI address encoding left-pads a 20-byte address with exactly
    # 12 zero bytes. Do not silently discard non-zero high bits.
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
    # Solidity ABI bool values are canonically encoded as exactly 0 or 1.
    return None


def _malformed_standard(selector: str, signature: str) -> dict[str, Any]:
    return {
        "status": "MALFORMED_STANDARD_CALLDATA",
        "selector": selector,
        "signature": signature,
        "confidence": 0,
        "note": "One or more static ABI words were not canonically encoded; Rivexis did not normalize them into plausible parameters.",
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
            "parameters": {"spender_or_approved": spender, "amount_or_token_id": amount},
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
        "note": "No ABI or verified signature evidence was used; Rivexis will not guess the method.",
    }


# Pure-Python Keccak-256 is kept here to avoid requiring a full web3 dependency merely to
# resolve verified ABI function selectors. Ethereum uses Keccak padding (0x01), not SHA3-256.
_KECCAK_RC = [
    0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
    0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
    0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
    0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
    0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
    0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008,
]
_KECCAK_ROT = [
    [0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]
]
_MASK64=(1<<64)-1

def _rol64(value:int,shift:int)->int:
    shift%=64
    return ((value<<shift)|(value>>(64-shift if shift else 64)))&_MASK64

def _keccak_f(state:list[int])->None:
    for rc in _KECCAK_RC:
        c=[state[x]^state[x+5]^state[x+10]^state[x+15]^state[x+20] for x in range(5)]
        d=[c[(x-1)%5]^_rol64(c[(x+1)%5],1) for x in range(5)]
        for x in range(5):
            for y in range(5):state[x+5*y]^=d[x]
        b=[0]*25
        for x in range(5):
            for y in range(5):b[y+5*((2*x+3*y)%5)]=_rol64(state[x+5*y],_KECCAK_ROT[x][y])
        for x in range(5):
            for y in range(5):state[x+5*y]=b[x+5*y]^((~b[(x+1)%5+5*y])&b[(x+2)%5+5*y])
        state[0]^=rc

def keccak256(data:bytes)->bytes:
    rate=136;state=[0]*25
    padded=bytearray(data);padded.append(0x01)
    while len(padded)%rate != rate-1:padded.append(0)
    padded.append(0x80)
    for offset in range(0,len(padded),rate):
        block=padded[offset:offset+rate]
        for i in range(rate//8):state[i]^=int.from_bytes(block[i*8:(i+1)*8],"little")
        _keccak_f(state)
    out=bytearray()
    while len(out)<32:
        for i in range(rate//8):
            out.extend(state[i].to_bytes(8,"little"))
            if len(out)>=32:return bytes(out[:32])
        _keccak_f(state)
    return bytes(out[:32])

def function_selector(signature:str)->str:
    return "0x"+keccak256(signature.encode()).hex()[:8]

def _canonical_abi_type(param:dict[str,Any])->str:
    typ=str(param.get("type") or "")
    if typ.startswith("tuple"):
        suffix=typ[5:]
        inner=",".join(_canonical_abi_type(x) for x in (param.get("components") or []))
        return f"({inner}){suffix}"
    return typ

def _decode_abi_static(typ:str,word:str)->Any:
    if typ=="address":return _address(word)
    if typ=="bool":return _bool(word)
    if typ.startswith("uint"):return _uint(word)
    if typ.startswith("int"):
        raw=_uint(word)
        if raw is None:return None
        bits=int(typ[3:] or "256");return raw-(1<<bits) if raw >= (1<<(bits-1)) else raw
    if typ=="bytes32":return "0x"+word
    if typ.startswith("bytes") and typ[5:].isdigit():
        size=int(typ[5:]);return "0x"+word[:size*2]
    return "0x"+word

def _is_dynamic_type(typ:str)->bool:
    return typ in {"bytes","string"} or typ.endswith("[]") or typ.startswith("tuple")

def decode_verified_abi_calldata(calldata:str|None,abi:Any)->dict[str,Any]:
    if not isinstance(calldata,str) or not calldata.startswith("0x") or len(calldata)<10:
        return {"status":"NO_SELECTOR"}
    if isinstance(abi,str):
        import json
        try:abi=json.loads(abi)
        except Exception:return {"status":"INVALID_ABI"}
    if not isinstance(abi,list):return {"status":"INVALID_ABI"}
    selector=calldata[:10].lower();payload=calldata[10:]
    for item in abi:
        if not isinstance(item,dict) or item.get("type")!="function" or not item.get("name"):continue
        inputs=item.get("inputs") or []
        signature=f"{item['name']}({','.join(_canonical_abi_type(x) for x in inputs)})"
        if function_selector(signature)!=selector:continue
        decoded=[];malformed_static=False
        for index,param in enumerate(inputs):
            typ=_canonical_abi_type(param);word=payload[index*64:(index+1)*64]
            value=None
            if len(word)==64:
                if _is_dynamic_type(typ):
                    offset=_uint(word)
                    if offset is not None:
                        pos=offset*2
                        length_word=payload[pos:pos+64]
                        length=_uint(length_word)
                        if length is not None and typ in {"bytes","string"}:
                            raw=payload[pos+64:pos+64+length*2]
                            if typ=="string":
                                try:value=bytes.fromhex(raw).decode("utf-8")
                                except Exception:value={"hex":"0x"+raw,"length":length}
                            else:value="0x"+raw
                        else:value={"dynamic_offset":offset,"length":length}
                else:
                    value=_decode_abi_static(typ,word)
                    if value is None:malformed_static=True
            elif not _is_dynamic_type(typ):
                malformed_static=True
            decoded.append({"name":param.get("name") or f"arg{index}","type":typ,"value":value})
        if malformed_static:
            return {
                "status":"MALFORMED_VERIFIED_ABI_CALLDATA",
                "selector":selector,
                "signature":signature,
                "function":item.get("name"),
                "parameters":decoded,
                "confidence":0,
                "note":"One or more static ABI parameters were not canonically encoded; Rivexis did not coerce them into valid values.",
            }
        return {"status":"DECODED_VERIFIED_ABI","selector":selector,"signature":signature,"function":item.get("name"),"parameters":decoded,"confidence":99}
    return {"status":"SELECTOR_NOT_FOUND_IN_VERIFIED_ABI","selector":selector,"confidence":0}

def normalize_call_trace(trace:Any)->dict[str,Any]:
    calls=[];native_transfers=[];approval_candidates=[]
    def walk(node:Any,parent:int|None=None,depth:int=0):
        if not isinstance(node,dict):return
        idx=len(calls);data=node.get("input") or "0x";decoded=decode_common_calldata(data)
        value_raw=node.get("value") or "0x0"
        try:value=int(value_raw,16) if isinstance(value_raw,str) and value_raw.startswith("0x") else int(value_raw or 0)
        except Exception:value=0
        item={"trace_index":idx,"parent_trace_index":parent,"depth":depth,"call_type":str(node.get("type") or "CALL").upper(),"from":node.get("from"),"to":node.get("to"),"value_wei":value,"gas":_uint_hex(node.get("gas")),"gas_used":_uint_hex(node.get("gasUsed")),"error":node.get("error"),"selector":decoded.get("selector"),"calldata_decode":decoded}
        calls.append(item)
        if value>0:native_transfers.append({"trace_index":idx,"from":node.get("from"),"to":node.get("to"),"amount_wei":value})
        if decoded.get("status") in {"DECODED_STANDARD_SELECTOR","PARTIALLY_DECODED_STANDARD_SELECTOR"} and decoded.get("signature") in {"approve(address,uint256)","setApprovalForAll(address,bool)"}:
            approval_candidates.append({"trace_index":idx,"contract":node.get("to"),"decode":decoded})
        for child in node.get("calls") or []:walk(child,idx,depth+1)
    walk(trace)
    return {"calls":calls,"native_value_transfers":native_transfers,"approval_candidates":approval_candidates,"call_count":len(calls),"error_count":sum(1 for x in calls if x.get("error"))}

def _uint_hex(value:Any)->int|None:
    if value is None:return None
    try:return int(value,16) if isinstance(value,str) and value.startswith("0x") else int(value)
    except Exception:return None

def summarize_prestate_diff(value:Any)->dict[str,Any]:
    if not isinstance(value,dict):return {"status":"UNAVAILABLE"}
    pre=value.get("pre") if isinstance(value.get("pre"),dict) else {}
    post=value.get("post") if isinstance(value.get("post"),dict) else {}
    addresses=sorted(set(pre)|set(post));changes=[]
    for address in addresses:
        before=pre.get(address) or {};after=post.get(address) or {};fields=[]
        for field in ("balance","nonce","code"):
            if before.get(field)!=after.get(field):fields.append(field)
        bstore=before.get("storage") if isinstance(before.get("storage"),dict) else {}
        astore=after.get("storage") if isinstance(after.get("storage"),dict) else {}
        changed_slots=sum(1 for slot in set(bstore)|set(astore) if bstore.get(slot)!=astore.get(slot))
        if fields or changed_slots:changes.append({"address":address,"changed_fields":fields,"changed_storage_slots":changed_slots})
    return {"status":"NORMALIZED_PRESTATE_DIFF","addresses_touched":len(addresses),"addresses_changed":len(changes),"changes":changes[:200],"truncated":len(changes)>200}
