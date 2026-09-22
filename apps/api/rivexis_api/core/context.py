from __future__ import annotations
from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("rivexis_request_id", default=None)
_actor_user_id: ContextVar[str | None] = ContextVar("rivexis_actor_user_id", default=None)
_workspace_id: ContextVar[str | None] = ContextVar("rivexis_workspace_id", default=None)
_organization_id: ContextVar[str | None] = ContextVar("rivexis_organization_id", default=None)
_organization_role: ContextVar[str | None] = ContextVar("rivexis_organization_role", default=None)
_trace_id: ContextVar[str | None] = ContextVar("rivexis_trace_id", default=None)
_span_id: ContextVar[str | None] = ContextVar("rivexis_span_id", default=None)
_trace_sampled: ContextVar[bool] = ContextVar("rivexis_trace_sampled", default=True)


def set_request_id(value: str | None):
    return _request_id.set(value)


def reset_request_id(token) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()


def set_actor_user_id(value: str | None):
    return _actor_user_id.set(value)


def reset_actor_user_id(token) -> None:
    _actor_user_id.reset(token)


def get_actor_user_id() -> str | None:
    return _actor_user_id.get()


def set_workspace_id(value: str | None):
    return _workspace_id.set(value)


def reset_workspace_id(token) -> None:
    _workspace_id.reset(token)


def get_workspace_id() -> str | None:
    return _workspace_id.get()


def set_organization_context(organization_id: str | None, role: str | None):
    return (_organization_id.set(organization_id), _organization_role.set(role))

def reset_organization_context(tokens) -> None:
    org_token, role_token = tokens
    _organization_id.reset(org_token)
    _organization_role.reset(role_token)

def get_organization_id() -> str | None:
    return _organization_id.get()

def get_organization_role() -> str | None:
    return _organization_role.get()


def set_trace_context(trace_id: str | None, span_id: str | None):
    return (_trace_id.set(trace_id), _span_id.set(span_id))

def reset_trace_context(tokens) -> None:
    trace_token, span_token = tokens
    _trace_id.reset(trace_token)
    _span_id.reset(span_token)

def get_trace_id() -> str | None:
    return _trace_id.get()

def get_span_id() -> str | None:
    return _span_id.get()


def set_trace_sampled(value: bool):
    return _trace_sampled.set(bool(value))

def reset_trace_sampled(token) -> None:
    _trace_sampled.reset(token)

def get_trace_sampled() -> bool:
    return bool(_trace_sampled.get())
