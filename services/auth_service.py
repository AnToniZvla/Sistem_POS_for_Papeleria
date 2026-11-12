from typing import Dict, Any
from repositories.usuario_repo import UsuarioRepository
from security.password_hasher import PasswordSecurity


class AuthService:
    """Servicio de autenticación, verificación de sesión y alta del primer Admin."""

    def __init__(self):
        self._repo = UsuarioRepository()
        self._security = PasswordSecurity()

    def requiere_configuracion_inicial(self) -> bool:
        return self._repo.contar_usuarios() == 0

    def registrar_primer_admin(
        self,
        username: str,
        nombre_completo: str,
        password: str,
        confirmar_password: str,
    ) -> Dict[str, Any]:
        if not self.requiere_configuracion_inicial():
            raise ValueError("Ya existe al menos un usuario registrado en el sistema.")

        username_clean = username.strip()
        nombre_clean = nombre_completo.strip()

        if len(username_clean) < 3:
            raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
        if not nombre_clean:
            raise ValueError("El nombre completo es obligatorio.")
        if len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        if password != confirmar_password:
            raise ValueError("Las contraseñas no coinciden.")

        rol_admin_id = self._repo.obtener_rol_id_por_nombre("Admin")
        pwd_hash = self._security.hash_password(password)
        user_id = self._repo.crear_usuario(
            username=username_clean,
            nombre_completo=nombre_clean,
            password_hash=pwd_hash,
            rol_id=rol_admin_id,
        )

        return {
            "id": user_id,
            "username": username_clean,
            "nombre_completo": nombre_clean,
            "rol_id": rol_admin_id,
            "rol_nombre": "Admin",
        }

    def autenticar(self, username: str, password: str) -> Dict[str, Any]:
        username_clean = username.strip()
        if not username_clean or not password:
            raise ValueError("Ingresa tu usuario y contraseña.")

        usuario = self._repo.obtener_por_username(username_clean)
        if not usuario:
            raise ValueError("Usuario o contraseña incorrectos.")

        if not int(usuario.get("activo", 0)):
            raise ValueError("Esta cuenta de usuario se encuentra desactivada.")

        if not self._security.verify_password(usuario["password_hash"], password):
            raise ValueError("Usuario o contraseña incorrectos.")

        if self._security.needs_rehash(usuario["password_hash"]):
            nuevo_hash = self._security.hash_password(password)
            self._repo.actualizar_hash(int(usuario["id"]), nuevo_hash)

        return {
            "id": int(usuario["id"]),
            "username": usuario["username"],
            "nombre_completo": usuario["nombre_completo"],
            "rol_id": int(usuario["rol_id"]),
            "rol_nombre": usuario["rol_nombre"],
        }
