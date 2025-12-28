from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Request para login de usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")


class TokenResponse(BaseModel):
    """Respuesta con el token JWT"""
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    user_id: str = Field(..., description="ID del usuario")
    email: Optional[str] = Field(None, description="Email del usuario")
    name: Optional[str] = Field(None, description="Nombre del usuario")


class UserResponse(BaseModel):
    """Información del usuario actual"""
    user_id: str = Field(..., description="ID del usuario (UUID)")
    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre del usuario")
    apellidos: str = Field(..., description="Apellidos del usuario")
    name: str = Field(..., description="Nombre completo (nombre + apellidos)")
    email_verificado: bool = Field(..., description="Si el email está verificado")
    avatar: Optional[str] = Field(None, description="URL del avatar")
    auth_provider: Optional[str] = Field(None, description="Proveedor de autenticación (local/google)")
    is_admin: bool = Field(default=False, description="Si es administrador")
    created_at: Optional[str] = Field(None, description="Fecha de creación")
    updated_at: Optional[str] = Field(None, description="Fecha de actualización")
