from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from rivexis_api.core.security import decode_token
from rivexis_api.core.context import set_actor_user_id
from rivexis_api.core.config import settings
from rivexis_api.services.store import get_user
bearer=HTTPBearer(auto_error=False)

def current_user(request: Request, creds: HTTPAuthorizationCredentials|None=Depends(bearer)):
    token = creds.credentials if creds else request.cookies.get(settings.session_cookie_name, "")
    if not token: raise HTTPException(401,"Authentication required")
    try: payload=decode_token(token)
    except ValueError as exc: raise HTTPException(401,str(exc)) from exc
    request.state.auth_source = "bearer" if creds else "cookie"
    request.state.session_token = token
    user=get_user(payload["sub"])
    if not user: raise HTTPException(401,"User no longer exists")
    if int(payload.get("ver",-1)) != int(user.token_version or 0): raise HTTPException(401,"Session has been revoked")
    set_actor_user_id(user.id)
    return user
