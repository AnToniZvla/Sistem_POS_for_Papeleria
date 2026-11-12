from typing import Optional, Dict, Any, List
from database.connection import get_connection


class UsuarioRepository:
    """Acceso a datos para usuarios y roles con consultas parametrizadas."""

    @staticmethod
    def contar_usuarios() -> int:
        with get_connection(commit=False) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM usuarios")
                (total,) = cursor.fetchone()
                return int(total or 0)
            finally:
                cursor.close()

    @staticmethod
    def obtener_por_username(username: str) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT u.id, u.username, u.nombre_completo, u.password_hash,
                   u.rol_id, r.nombre AS rol_nombre, u.activo
            FROM usuarios u
            INNER JOIN roles r ON u.rol_id = r.id
            WHERE u.username = %s
            LIMIT 1
        """
        with get_connection(commit=False) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql, (username.strip(),))
                return cursor.fetchone()
            finally:
                cursor.close()

    @staticmethod
    def obtener_rol_id_por_nombre(nombre_rol: str) -> int:
        with get_connection(commit=False) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM roles WHERE nombre = %s LIMIT 1",
                    (nombre_rol,),
                )
                fila = cursor.fetchone()
                if fila:
                    return int(fila[0])
            finally:
                cursor.close()

        with get_connection(commit=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO roles (nombre) VALUES (%s)",
                    (nombre_rol,),
                )
                return int(cursor.lastrowid)
            finally:
                cursor.close()

    @staticmethod
    def crear_usuario(
        username: str,
        nombre_completo: str,
        password_hash: str,
        rol_id: int,
    ) -> int:
        sql = """
            INSERT INTO usuarios (username, nombre_completo, password_hash, rol_id, activo)
            VALUES (%s, %s, %s, %s, 1)
        """
        with get_connection(commit=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    sql,
                    (username.strip(), nombre_completo.strip(), password_hash, rol_id),
                )
                return int(cursor.lastrowid)
            finally:
                cursor.close()

    @staticmethod
    def actualizar_hash(usuario_id: int, nuevo_hash: str) -> None:
        with get_connection(commit=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                    (nuevo_hash, usuario_id),
                )
            finally:
                cursor.close()

    @staticmethod
    def listar_roles() -> List[Dict[str, Any]]:
        with get_connection(commit=False) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, nombre FROM roles ORDER BY id")
                return cursor.fetchall()
            finally:
                cursor.close()
