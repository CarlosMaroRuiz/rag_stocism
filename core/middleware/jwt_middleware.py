from typing import Optional, Dict
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from core.enviroment import env
import mysql.connector

# Security scheme
security = HTTPBearer()


def get_user_from_db(user_id: str) -> Optional[Dict]:
    """
    Busca un usuario en la base de datos MySQL por su ID.

    Args:
        user_id: UUID del usuario

    Returns:
        Diccionario con los datos del usuario o None si no existe
    """
    try:
        connection = mysql.connector.connect(
            host=env.MYSQL_HOST,
            port=env.MYSQL_PORT,
            user=env.MYSQL_USER,
            password=env.MYSQL_PASSWORD,
            database=env.MYSQL_DATABASE
        )

        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, apellidos, email, email_verificado, avatar, auth_provider, is_admin, created_at, updated_at FROM users WHERE id = %s",
            (user_id,)
        )

        user = cursor.fetchone()
        cursor.close()
        connection.close()

        return user

    except mysql.connector.Error as e:
        print(f"Error de MySQL al buscar usuario: {e}")
        return None


def verify_token(token: str) -> Dict:
    """
    Verifica y decodifica un token JWT generado por Laravel.

    IMPORTANTE: Esta función solo VALIDA tokens, no los genera.
    Los tokens deben venir de la API externa (Laravel) que maneja autenticación.

    Args:
        token: Token JWT a verificar

    Returns:
        Payload del token decodificado

    Raises:
        HTTPException 401: Si el token es inválido o ha expirado
    """
    try:
        payload = jwt.decode(
            token,
            env.JWT_SECRET,
            algorithms=[env.JWT_ALGORITHM]
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependency para obtener usuario actual desde JWT.

    Proceso de validación:
    1. Valida el token JWT (firma y expiración)
    2. Extrae el user_id del payload
    3. Busca el usuario en MySQL
    4. Verifica que el email esté verificado
    5. Retorna los datos completos del usuario

    Args:
        credentials: Credenciales HTTP Bearer

    Returns:
        Diccionario con los datos del usuario

    Raises:
        HTTPException 401: Si el token es inválido, expirado o el usuario no existe
        HTTPException 403: Si el email no está verificado
    """
    # 1️⃣ Validar token JWT
    token = credentials.credentials
    payload = verify_token(token)

    # 2️⃣ Extraer user_id del payload
    user_id: Optional[str] = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido: falta user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3️⃣ Buscar usuario en MySQL
    user = get_user_from_db(str(user_id))

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4️⃣ Verificar que el email esté verificado (igual que Laravel)
    if not user['email_verificado']:
        raise HTTPException(
            status_code=403,
            detail="Email no verificado. Por favor verifica tu email antes de continuar."
        )

    # 5️⃣ Determinar el rol basado en is_admin
    is_admin = user.get('is_admin', False)
    role = "ADMIN" if is_admin else "USER"

    # 6️⃣ Retornar datos del usuario (de la BD, no del token)
    return {
        "user_id": str(user['id']),
        "email": user['email'],
        "nombre": user['nombre'],
        "apellidos": user['apellidos'],
        "name": f"{user['nombre']} {user['apellidos']}".strip(),  # Nombre completo
        "email_verificado": user['email_verificado'],
        "avatar": user.get('avatar'),
        "auth_provider": user.get('auth_provider'),
        "is_admin": is_admin,
        "role": role,  # 🔑 Rol del usuario: ADMIN o USER
        "created_at": str(user['created_at']) if user['created_at'] else None,
        "updated_at": str(user['updated_at']) if user['updated_at'] else None,
        **payload  # Incluir cualquier otro dato del token
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict]:
    """
    Dependency opcional para rutas que pueden funcionar con o sin autenticación.

    Args:
        credentials: Credenciales HTTP Bearer opcionales

    Returns:
        Diccionario con los datos del usuario si hay token válido, None si no hay token
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)

        user_id: Optional[str] = payload.get("user_id")
        if user_id is None:
            return None

        user = get_user_from_db(str(user_id))
        if not user or not user['email_verificado']:
            return None

        is_admin = user.get('is_admin', False)
        role = "ADMIN" if is_admin else "USER"

        return {
            "user_id": str(user['id']),
            "email": user['email'],
            "nombre": user['nombre'],
            "apellidos": user['apellidos'],
            "name": f"{user['nombre']} {user['apellidos']}".strip(),
            "email_verificado": user['email_verificado'],
            "avatar": user.get('avatar'),
            "auth_provider": user.get('auth_provider'),
            "is_admin": is_admin,
            "role": role,  # 🔑 Rol del usuario: ADMIN o USER
            "created_at": str(user['created_at']) if user['created_at'] else None,
            "updated_at": str(user['updated_at']) if user['updated_at'] else None,
            **payload
        }
    except (HTTPException, Exception):
        return None


# ==================== ROLE-BASED ACCESS CONTROL ====================

async def require_user_role(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    if current_user.get("role") != "USER":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Solo usuarios con rol USER pueden acceder a este recurso."
        )

    return current_user


async def require_admin_role(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Solo administradores pueden acceder a este recurso."
        )

    return current_user
