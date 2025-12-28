from fastapi import APIRouter, Depends
from typing import Dict

from schemas.auth_schema import UserResponse
from core.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/verify", response_model=UserResponse)
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """
    Verifica que el token JWT sea válido y retorna la información del usuario.

    **IMPORTANTE**: Esta API NO genera tokens JWT. Los tokens deben venir
    de la API externa (Laravel) que maneja autenticación.

    Headers:
    ```
    Authorization: Bearer <token_from_external_api>
    ```

    Returns:
        Información del usuario extraída del token

    Raises:
        401: Si el token es inválido, ha expirado o no contiene user_id
    """
    return UserResponse(**current_user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene información del usuario actual (requiere token JWT válido).

    Headers:
    ```
    Authorization: Bearer <token>
    ```

    Returns:
        Información del usuario autenticado
    """
    return UserResponse(**current_user)
