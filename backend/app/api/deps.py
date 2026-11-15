"""
FastAPI route dependency injectors for Authentication and Role-Based Access Control (RBAC).
"""

from typing import Any, Callable, Dict, List, Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.app.core.security import decode_access_token
from src.database.models import get_user_by_id, get_user_by_username


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """
    Validates the JWT bearer token and returns the corresponding active user record.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("user_id")
    username = payload.get("sub")

    user = None
    if user_id:
        user = get_user_by_id(int(user_id))
    elif username:
        user = get_user_by_username(str(username))

    if not user:
        raise credentials_exception

    return user


def require_role(allowed_roles: Union[str, List[str]]) -> Callable:
    """
    Role-based access control dependency factory. Accepts single role string or list of roles.
    """
    roles_list = [allowed_roles] if isinstance(allowed_roles, str) else allowed_roles

    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "").lower()
        if user_role not in [r.lower() for r in roles_list]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the following roles: {', '.join(roles_list)}.",
            )
        return current_user

    return role_checker


# Role convenience shortcuts
get_current_teacher = require_role(["teacher"])
get_current_student = require_role(["student"])
