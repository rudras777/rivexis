from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx

from rivexis_api.chains import ChainConfig
from rivexis_api.core.telemetry import trace_headers
from rivexis_api.provider_runtime import RuntimeControlError, execute, safe_provider_endpoint


class ProviderError(RuntimeError):
    _PUBLIC_MESSAGES = {
        "NOT_CONFIGURED": "Provider is not configured",
        "TIMEOUT": "Provider request timed out",
        "TRANSPORT": "Provider transport failure",
        "RATE_LIMIT": "Provider rate limit reached",
        "MALFORMED_RESPONSE": "Provider returned a malformed response",
        "API_ERROR": "Provider API request failed",
        "INVALID_INPUT": "Provider input is invalid",
        "UNSUPPORTED": "Provider operation is unsupported",
        "LOCAL_RATE_LIMIT": "Provider request budget exceeded",
        "CIRCUIT_OPEN": "Provider circuit is temporarily open",
    }

    def __init__(self, message: str, *, provider_id: str, code: str = "PROVIDER_ERROR", retryable: bool = False):
        # Upstream error bodies are untrusted and may echo request URLs, API keys,
        # calldata or tenant inputs. Keep the raw text in-memory only for a debugger;
        # every normal str(exc) surface receives a stable non-secret public message.
        self.internal_message = str(message)
        normalized = str(code or "PROVIDER_ERROR")[:80]
        public = self._PUBLIC_MESSAGES.get(normalized)
        if public is None and normalized.startswith("RPC_"):
            public = "JSON-RPC provider request failed"
        if public is None:
            public = "Provider request failed"
        super().__init__(public)
        self.provider_id = provider_id
        self.code = normalized
        self.retryable = retryable


def _controlled(provider_id: str, operation: str, fn, *, endpoint: str = "", cache_key: str | None = None, cache_ttl_seconds: float = 0.0):
    try:
        return execute(provider_id, operation, fn, endpoint=endpoint, cache_key=cache_key, cache_ttl_seconds=cache_ttl_seconds)
    except RuntimeControlError as exc:
        raise ProviderError(str(exc), provider_id=provider_id, code=exc.code, retryable=exc.retryable) from exc


def _stable_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class ProviderCall:
    provider_id: str
    request_id: str
    endpoint: str
    result: Any
    latency_ms: float


class JsonRpcClient:
    def __init__(self, provider_id: str, url: str, *, timeout_seconds: float = 8.0):
        self.provider_id = provider_id
        self.url = url
        self.timeout_seconds = timeout_seconds

    def call(self, method: str, params: list[Any] | None = None) -> ProviderCall:
        params = params or []
        cache_ttl = {
            "eth_chainId": 30.0,
            "eth_blockNumber": 1.0,
            "eth_getBalance": 3.0,
            "eth_getCode": 60.0,
            "eth_getTransactionByHash": 10.0,
            "eth_call": 2.0,
        }.get(method, 0.0)

        def perform() -> ProviderCall:
            request_id = str(uuid4())
            payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
            started = time.perf_counter()
            try:
                with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                    response = client.post(self.url, json=payload, headers={**trace_headers(), "Content-Type": "application/json"})
                latency = (time.perf_counter() - started) * 1000
                response.raise_for_status()
                body = response.json()
            except httpx.TimeoutException as exc:
                raise ProviderError("Provider request timed out", provider_id=self.provider_id, code="TIMEOUT", retryable=True) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise ProviderError("Provider transport failure", provider_id=self.provider_id, code="TRANSPORT", retryable=True) from exc
            if not isinstance(body, dict):
                raise ProviderError("Malformed JSON-RPC response", provider_id=self.provider_id, code="MALFORMED_RESPONSE")
            if body.get("error"):
                error = body["error"] if isinstance(body["error"], dict) else {"message": str(body["error"])}
                msg = str(error.get("message", "JSON-RPC error"))
                code = str(error.get("code", "RPC_ERROR"))
                retryable = code in {"-32005", "429"} or "rate" in msg.lower() or "limit" in msg.lower()
                raise ProviderError(msg, provider_id=self.provider_id, code=f"RPC_{code}", retryable=retryable)
            if "result" not in body:
                raise ProviderError("JSON-RPC response has no result", provider_id=self.provider_id, code="MALFORMED_RESPONSE")
            return ProviderCall(self.provider_id, request_id, safe_provider_endpoint(self.provider_id, self.url), body["result"], latency)

        return _controlled(
            self.provider_id,
            method,
            perform,
            endpoint=self.url,
            cache_key=_stable_key(params) if cache_ttl else None,
            cache_ttl_seconds=cache_ttl,
        )



class RpcClientFactory:
    @staticmethod
    def url(provider_id: str, chain: ChainConfig) -> str | None:
        if provider_id == "alchemy":
            key = os.getenv("ALCHEMY_API_KEY", "").strip()
            return f"https://{chain.alchemy_network}.g.alchemy.com/v2/{key}" if key else None
        if provider_id == "quicknode":
            # QUICKNODE_URL is intentionally treated as a full endpoint supplied by the operator.
            # For non-Ethereum chains, use chain-specific direct RPC environment variables unless
            # the operator provides a QUICKNODE_URL_TEMPLATE containing {chain} or {chain_id}.
            template = os.getenv("QUICKNODE_URL_TEMPLATE", "").strip()
            if template:
                return template.format(chain=chain.key, chain_id=chain.chain_id)
            if chain.key != "ethereum":
                return None
            return os.getenv("QUICKNODE_URL", "").strip() or None
        if provider_id == "direct_rpc":
            return os.getenv(chain.direct_rpc_env, "").strip() or None
        return None

    @classmethod
    def client(cls, provider_id: str, chain: ChainConfig) -> JsonRpcClient:
        url = cls.url(provider_id, chain)
        if not url:
            raise ProviderError(f"No RPC endpoint configured for {chain.name}", provider_id=provider_id, code="NOT_CONFIGURED")
        timeout = float(os.getenv("RIVEXIS_PROVIDER_TIMEOUT_SECONDS", "8"))
        return JsonRpcClient(provider_id, url, timeout_seconds=timeout)


class TenderlyClient:
    provider_id = "tenderly"

    def __init__(self):
        self.access_key = os.getenv("TENDERLY_ACCESS_KEY", "").strip()
        self.account = os.getenv("TENDERLY_ACCOUNT", "").strip()
        self.project = os.getenv("TENDERLY_PROJECT", "").strip()
        self.timeout_seconds = float(os.getenv("RIVEXIS_PROVIDER_TIMEOUT_SECONDS", "8"))

    @property
    def configured(self) -> bool:
        return bool(self.access_key and self.account and self.project)

    def simulate(self, chain: ChainConfig, transaction: dict[str, Any], *, block_number: int | None = None) -> ProviderCall:
        if not self.configured:
            raise ProviderError("Tenderly credentials are not configured", provider_id=self.provider_id, code="NOT_CONFIGURED")
        endpoint = f"https://api.tenderly.co/api/v1/account/{self.account}/project/{self.project}/simulate"
        payload: dict[str, Any] = {
            "network_id": str(chain.chain_id),
            "from": transaction.get("from"),
            "to": transaction.get("to"),
            "input": transaction.get("data") or transaction.get("input") or "0x",
            "value": _quantity_to_int(transaction.get("value", 0)),
            "save": False,
            "save_if_fails": False,
            "simulation_type": "full",
            "generate_access_list": False,
            "source": "rivexis",
        }
        if transaction.get("gas") is not None:
            payload["gas"] = _quantity_to_int(transaction["gas"])
        gas_price = transaction.get("gasPrice") or transaction.get("gas_price")
        if gas_price is not None:
            payload["gas_price"] = _quantity_to_int(gas_price)
        if block_number is not None and block_number >= 0:
            payload["block_number"] = block_number

        def perform() -> ProviderCall:
            request_id = str(uuid4())
            started = time.perf_counter()
            try:
                with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                    response = client.post(
                        endpoint,
                        json=payload,
                        headers={**trace_headers(), "Content-Type": "application/json", "X-Access-Key": self.access_key, "X-Rivexis-Request-Id": request_id},
                    )
                latency = (time.perf_counter() - started) * 1000
                if response.status_code == 429:
                    raise ProviderError("Tenderly rate limited the request", provider_id=self.provider_id, code="RATE_LIMIT", retryable=True)
                response.raise_for_status()
                body = response.json()
            except ProviderError:
                raise
            except httpx.TimeoutException as exc:
                raise ProviderError("Tenderly request timed out", provider_id=self.provider_id, code="TIMEOUT", retryable=True) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise ProviderError("Tenderly transport failure", provider_id=self.provider_id, code="TRANSPORT", retryable=True) from exc
            if not isinstance(body, dict):
                raise ProviderError("Malformed Tenderly simulation response", provider_id=self.provider_id, code="MALFORMED_RESPONSE")
            if body.get("error") and not body.get("transaction"):
                err = body["error"] if isinstance(body["error"], dict) else {"message": str(body["error"])}
                raise ProviderError(str(err.get("message") or err.get("slug") or "Tenderly simulation error"), provider_id=self.provider_id, code="SIMULATION_ERROR")
            return ProviderCall(self.provider_id, request_id, safe_provider_endpoint(self.provider_id, endpoint), body, latency)

        return _controlled(self.provider_id, "simulate", perform, endpoint=endpoint)



def _quantity_to_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.startswith("0x") else int(value)
    return int(value)


def quantity_to_hex(value: Any) -> str:
    if value is None:
        return "0x0"
    if isinstance(value, str) and value.startswith("0x"):
        return value
    return hex(int(value))


def hex_to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.startswith("0x") else int(value)
    return int(value)


class EtherscanClient:
    provider_id = "etherscan"
    endpoint = "https://api.etherscan.io/v2/api"

    def __init__(self):
        self.api_key = os.getenv("ETHERSCAN_API_KEY", "").strip()
        self.timeout_seconds = float(os.getenv("RIVEXIS_PROVIDER_TIMEOUT_SECONDS", "8"))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _get(self, params: dict[str, Any]) -> ProviderCall:
        if not self.configured:
            raise ProviderError("Etherscan API key is not configured", provider_id=self.provider_id, code="NOT_CONFIGURED")
        query = {**params, "apikey": self.api_key}

        def perform() -> ProviderCall:
            request_id = str(uuid4())
            started = time.perf_counter()
            try:
                with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                    response = client.get(self.endpoint, params=query, headers={**trace_headers(), "X-Rivexis-Request-Id": request_id})
                latency = (time.perf_counter() - started) * 1000
                if response.status_code == 429:
                    raise ProviderError("Etherscan rate limited the request", provider_id=self.provider_id, code="RATE_LIMIT", retryable=True)
                response.raise_for_status()
                body = response.json()
            except ProviderError:
                raise
            except httpx.TimeoutException as exc:
                raise ProviderError("Etherscan request timed out", provider_id=self.provider_id, code="TIMEOUT", retryable=True) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise ProviderError("Etherscan transport failure", provider_id=self.provider_id, code="TRANSPORT", retryable=True) from exc
            if not isinstance(body, dict):
                raise ProviderError("Malformed Etherscan response", provider_id=self.provider_id, code="MALFORMED_RESPONSE")
            if body.get("status") == "0" and str(body.get("message", "")).upper() not in {"OK", "NO TRANSACTIONS FOUND"}:
                message = str(body.get("result") or body.get("message") or "Etherscan API error")
                retryable = "rate limit" in message.lower() or "max rate" in message.lower()
                raise ProviderError(message, provider_id=self.provider_id, code="RATE_LIMIT" if retryable else "API_ERROR", retryable=retryable)
            return ProviderCall(self.provider_id, request_id, safe_provider_endpoint(self.provider_id, self.endpoint), body, latency)

        ttl = float(os.getenv("RIVEXIS_PROVIDER_ETHERSCAN_CACHE_TTL_SECONDS", "15"))
        return _controlled(
            self.provider_id,
            str(params.get("action") or "GET"),
            perform,
            endpoint=self.endpoint,
            cache_key=_stable_key(params),
            cache_ttl_seconds=max(0.0, ttl),
        )


    def get_source_code(self, chain: ChainConfig, address: str) -> ProviderCall:
        return self._get({"chainid": str(chain.chain_id), "module": "contract", "action": "getsourcecode", "address": address})

    def get_abi(self, chain: ChainConfig, address: str) -> ProviderCall:
        return self._get({"chainid": str(chain.chain_id), "module": "contract", "action": "getabi", "address": address})

    def get_contract_creation(self, chain: ChainConfig, address: str) -> ProviderCall:
        return self._get({"chainid": str(chain.chain_id), "module": "contract", "action": "getcontractcreation", "contractaddresses": address})

    def account_transactions(self, chain: ChainConfig, address: str, *, start_block: int = 0, end_block: int = 99999999, page: int = 1, offset: int = 100, sort: str = "desc") -> ProviderCall:
        return self._get({
            "chainid": str(chain.chain_id),
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": min(max(int(offset), 1), 1000),
            "sort": sort,
        })

    def token_transactions(self, chain: ChainConfig, address: str, *, start_block: int = 0, end_block: int = 99999999, page: int = 1, offset: int = 100, sort: str = "desc") -> ProviderCall:
        return self._get({
            "chainid": str(chain.chain_id),
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": min(max(int(offset), 1), 1000),
            "sort": sort,
        })


class RestClient:
    def __init__(self, provider_id: str, *, timeout_seconds: float | None = None):
        self.provider_id = provider_id
        self.timeout_seconds = timeout_seconds or float(os.getenv("RIVEXIS_PROVIDER_TIMEOUT_SECONDS", "8"))

    def get(self, endpoint: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> ProviderCall:
        params = params or {}

        def perform() -> ProviderCall:
            request_id = str(uuid4())
            started = time.perf_counter()
            merged_headers = {**trace_headers(), "Accept": "application/json", "X-Rivexis-Request-Id": request_id, **(headers or {})}
            try:
                with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                    response = client.get(endpoint, params=params, headers=merged_headers)
                latency = (time.perf_counter() - started) * 1000
                if response.status_code == 429:
                    raise ProviderError(f"{self.provider_id} rate limited the request", provider_id=self.provider_id, code="RATE_LIMIT", retryable=True)
                response.raise_for_status()
                body = response.json()
            except ProviderError:
                raise
            except httpx.TimeoutException as exc:
                raise ProviderError(f"{self.provider_id} request timed out", provider_id=self.provider_id, code="TIMEOUT", retryable=True) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise ProviderError(f"{self.provider_id} transport failure", provider_id=self.provider_id, code="TRANSPORT", retryable=True) from exc
            return ProviderCall(self.provider_id, request_id, safe_provider_endpoint(self.provider_id, endpoint), body, latency)

        ttl = float(os.getenv(f"RIVEXIS_PROVIDER_{self.provider_id.upper()}_CACHE_TTL_SECONDS", os.getenv("RIVEXIS_PROVIDER_REST_CACHE_TTL_SECONDS", "15")))
        return _controlled(
            self.provider_id,
            "GET",
            perform,
            endpoint=endpoint,
            cache_key=_stable_key({"endpoint": endpoint, "params": params}),
            cache_ttl_seconds=max(0.0, ttl),
        )

    def post(
        self,
        endpoint: str,
        *,
        json_body: dict[str, Any],
        headers: dict[str, str] | None = None,
        cache_ttl_seconds: float | None = None,
    ) -> ProviderCall:
        if not isinstance(json_body, dict):
            raise ProviderError("REST JSON body must be an object", provider_id=self.provider_id, code="INVALID_INPUT")

        def perform() -> ProviderCall:
            request_id = str(uuid4())
            started = time.perf_counter()
            merged_headers = {
                **trace_headers(),
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Rivexis-Request-Id": request_id,
                **(headers or {}),
            }
            try:
                with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                    response = client.post(endpoint, json=json_body, headers=merged_headers)
                latency = (time.perf_counter() - started) * 1000
                if response.status_code == 429:
                    raise ProviderError(
                        f"{self.provider_id} rate limited the request",
                        provider_id=self.provider_id,
                        code="RATE_LIMIT",
                        retryable=True,
                    )
                if response.status_code >= 500:
                    raise ProviderError(
                        f"{self.provider_id} upstream error HTTP {response.status_code}",
                        provider_id=self.provider_id,
                        code=f"HTTP_{response.status_code}",
                        retryable=True,
                    )
                response.raise_for_status()
                body = response.json()
            except ProviderError:
                raise
            except httpx.TimeoutException as exc:
                raise ProviderError(
                    f"{self.provider_id} request timed out",
                    provider_id=self.provider_id,
                    code="TIMEOUT",
                    retryable=True,
                ) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise ProviderError(
                    f"{self.provider_id} transport failure",
                    provider_id=self.provider_id,
                    code="TRANSPORT",
                    retryable=isinstance(exc, httpx.TransportError),
                ) from exc
            return ProviderCall(self.provider_id, request_id, safe_provider_endpoint(self.provider_id, endpoint), body, latency)

        ttl = (
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else float(
                os.getenv(
                    f"RIVEXIS_PROVIDER_{self.provider_id.upper()}_CACHE_TTL_SECONDS",
                    os.getenv("RIVEXIS_PROVIDER_REST_CACHE_TTL_SECONDS", "15"),
                )
            )
        )
        return _controlled(
            self.provider_id,
            "POST",
            perform,
            endpoint=endpoint,
            cache_key=_stable_key({"endpoint": endpoint, "body": json_body}) if ttl > 0 else None,
            cache_ttl_seconds=max(0.0, ttl),
        )


class BlockaidClient:
    """Credentialed Blockaid EVM scanning adapter.

    The endpoint paths and X-API-Key authentication match Blockaid's current
    generated SDK. Provider output is retained as external evidence; Rivexis
    remains responsible for the final decision.
    """

    provider_id = "blockaid"

    def __init__(self):
        self.api_key = (os.getenv("BLOCKAID_API_KEY", "").strip() or os.getenv("BLOCKAID_CLIENT_API_KEY", "").strip())
        self.base_url = os.getenv("BLOCKAID_BASE_URL", "https://api.blockaid.io").rstrip("/")
        self.client = RestClient(self.provider_id)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise ProviderError("Blockaid API key is not configured", provider_id=self.provider_id, code="NOT_CONFIGURED")
        return {"X-API-Key": self.api_key}

    def scan_address(self, *, chain: str, address: str, domain: str | None = None) -> ProviderCall:
        body: dict[str, Any] = {"chain": chain, "address": address}
        if domain:
            body["metadata"] = {"domain": domain}
        return self.client.post(
            f"{self.base_url}/v0/evm/address/scan",
            json_body=body,
            headers=self._headers(),
            cache_ttl_seconds=float(os.getenv("RIVEXIS_PROVIDER_BLOCKAID_CACHE_TTL_SECONDS", "15")),
        )

    def scan_transaction(
        self,
        *,
        chain: str,
        transaction: dict[str, Any],
        account_address: str | None = None,
        domain: str | None = None,
        block: int | str | None = None,
    ) -> ProviderCall:
        tx = {
            "from": transaction.get("from"),
            "to": transaction.get("to"),
            "data": transaction.get("data") or transaction.get("input") or "0x",
            "value": quantity_to_hex(transaction.get("value", 0)),
        }
        # Blockaid's transaction scan requires a sender. Historical transaction
        # lookup should populate it before this method is called.
        if not tx["from"]:
            raise ProviderError("Blockaid transaction scan requires a from address", provider_id=self.provider_id, code="INVALID_INPUT")
        body: dict[str, Any] = {
            "chain": chain,
            "data": tx,
            "options": ["simulation", "validation"],
        }
        if account_address:
            body["account_address"] = account_address
        if domain:
            body["metadata"] = {"domain": domain}
        if block is not None:
            body["block"] = str(block)
        return self.client.post(
            f"{self.base_url}/v0/evm/transaction/scan",
            json_body=body,
            headers=self._headers(),
            cache_ttl_seconds=float(os.getenv("RIVEXIS_PROVIDER_BLOCKAID_CACHE_TTL_SECONDS", "5")),
        )


class NansenClient:
    provider_id = "nansen"

    def __init__(self):
        self.api_key = os.getenv("NANSEN_API_KEY", "").strip()
        self.base_url = os.getenv("NANSEN_BASE_URL", "https://api.nansen.ai").rstrip("/")
        self.client = RestClient(self.provider_id)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def address_labels(self, *, address: str, chain: str, page: int = 1, per_page: int = 100) -> ProviderCall:
        if not self.configured:
            raise ProviderError("Nansen API key is not configured", provider_id=self.provider_id, code="NOT_CONFIGURED")
        body = {
            "address": address,
            "chain": chain,
            "pagination": {"page": max(1, int(page)), "per_page": min(max(1, int(per_page)), 100)},
        }
        return self.client.post(
            f"{self.base_url}/api/v1/profiler/address/labels",
            json_body=body,
            headers={"apiKey": self.api_key},
            cache_ttl_seconds=float(os.getenv("RIVEXIS_PROVIDER_NANSEN_CACHE_TTL_SECONDS", "60")),
        )


class ArkhamClient:
    provider_id = "arkham"

    def __init__(self):
        self.api_key = os.getenv("ARKHAM_API_KEY", "").strip()
        self.base_url = os.getenv("ARKHAM_BASE_URL", "https://api.arkm.com").rstrip("/")
        self.license_approved = os.getenv("RIVEXIS_ARKHAM_LICENSE_APPROVED", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.client = RestClient(self.provider_id)

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.license_approved)

    @property
    def credentialed(self) -> bool:
        return bool(self.api_key)

    def address_intelligence(self, address: str) -> ProviderCall:
        if not self.api_key:
            raise ProviderError("Arkham API key is not configured", provider_id=self.provider_id, code="NOT_CONFIGURED")
        if not self.license_approved:
            raise ProviderError(
                "Arkham integration is disabled until commercial/API terms are explicitly approved for this deployment",
                provider_id=self.provider_id,
                code="LICENSE_APPROVAL_REQUIRED",
            )
        return self.client.get(
            f"{self.base_url}/intelligence/address/{address}/all",
            headers={"API-Key": self.api_key},
        )

    def counterparties(self, address: str) -> ProviderCall:
        if not self.configured:
            code = "LICENSE_APPROVAL_REQUIRED" if self.api_key else "NOT_CONFIGURED"
            raise ProviderError("Arkham counterparty intelligence is unavailable", provider_id=self.provider_id, code=code)
        return self.client.get(
            f"{self.base_url}/counterparties/address/{address}",
            headers={"API-Key": self.api_key},
        )


class CoinGeckoClient:
    provider_id = "coingecko"

    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY", "").strip()
        self.client = RestClient(self.provider_id)

    def simple_price(self, ids: list[str], vs_currency: str = "usd") -> ProviderCall:
        if not ids:
            raise ProviderError("At least one CoinGecko id is required", provider_id=self.provider_id, code="INVALID_INPUT")
        base = "https://pro-api.coingecko.com/api/v3" if self.api_key else "https://api.coingecko.com/api/v3"
        headers = {"x-cg-pro-api-key": self.api_key} if self.api_key else {}
        return self.client.get(
            f"{base}/simple/price",
            params={
                "ids": ",".join(sorted(set(ids))),
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
            headers=headers,
        )


class DefiLlamaClient:
    provider_id = "defillama"
    base = "https://api.llama.fi"

    def __init__(self):
        self.client = RestClient(self.provider_id)

    def protocol(self, slug: str) -> ProviderCall:
        clean = slug.strip().lower()
        if not clean or "/" in clean or ".." in clean:
            raise ProviderError("Invalid DefiLlama protocol slug", provider_id=self.provider_id, code="INVALID_INPUT")
        return self.client.get(f"{self.base}/protocol/{clean}")

    def protocols(self) -> ProviderCall:
        return self.client.get(f"{self.base}/protocols")


class LifiClient:
    provider_id = "lifi"
    endpoint = "https://li.quest/v1/quote"

    def __init__(self):
        self.api_key = os.getenv("LIFI_API_KEY", "").strip()
        self.client = RestClient(self.provider_id)

    def quote(self, params: dict[str, Any]) -> ProviderCall:
        required = ["fromChain", "toChain", "fromToken", "toToken", "fromAmount", "fromAddress"]
        missing = [k for k in required if params.get(k) in (None, "")]
        if missing:
            raise ProviderError(f"Missing LI.FI quote parameters: {', '.join(missing)}", provider_id=self.provider_id, code="INVALID_INPUT")
        headers = {"x-lifi-api-key": self.api_key} if self.api_key else {}
        clean: dict[str, Any] = {k: v for k, v in params.items() if v is not None and v != ""}
        return self.client.get(self.endpoint, params=clean, headers=headers)

class DefiLlamaYieldClient:
    """Read-only adapter for DefiLlama's public yield-pool surface.

    The adapter intentionally returns provider data only. Yield quality/risk is
    calculated by Rivexis and never inferred from APY alone.
    """

    provider_id = "defillama_yields"
    endpoint = "https://yields.llama.fi/pools"

    def __init__(self):
        self.client = RestClient(self.provider_id)

    def pools(self) -> ProviderCall:
        return self.client.get(self.endpoint)
