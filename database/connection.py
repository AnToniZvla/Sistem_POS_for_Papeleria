from contextlib import contextmanager
import mysql.connector
from mysql.connector import errorcode
from config.settings import Settings


@contextmanager
def get_connection(commit: bool = False):
    """
    Context Manager para conexiones a MySQL con soporte ACID.
    Si commit=True, confirma la transacción al terminar el bloque sin errores;
    si ocurre cualquier excepción, ejecuta rollback() automáticamente.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**Settings.get_db_config())
        yield conn
        if commit:
            conn.commit()
    except mysql.connector.Error as err:
        if conn is not None and conn.is_connected():
            conn.rollback()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise RuntimeError(
                "Acceso denegado a MySQL. Verifica DB_USER y DB_PASSWORD en tu archivo .env."
            ) from err
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            raise RuntimeError(
                f"La base de datos '{Settings.DB_NAME}' no existe en MySQL. "
                "Importa primero schema_y_migracion_3nf.sql en phpMyAdmin."
            ) from err
        raise RuntimeError(f"Error de base de datos MySQL: {err.msg}") from err
    except Exception:
        if conn is not None and conn.is_connected():
            conn.rollback()
        raise
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def verificar_esquema_inicial():
    """
    Verifica que las tablas del esquema 3NF existan al arrancar la aplicación.
    Si la base de datos no ha sido migrada aún, lanza un mensaje descriptivo.
    """
    tablas_requeridas = {
        "roles",
        "usuarios",
        "categorias",
        "productos",
        "ventas",
        "detalles_ventas",
        "movimientos_inventario",
    }
    with get_connection(commit=False) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SHOW TABLES")
            existentes = {fila[0].lower() for fila in cursor.fetchall()}
            faltantes = tablas_requeridas - existentes
            if faltantes:
                raise RuntimeError(
                    "Faltan tablas del esquema 3NF en la base de datos: "
                    f"{', '.join(sorted(faltantes))}.\n\n"
                    "Por favor importa el archivo 'schema_y_migracion_3nf.sql' en phpMyAdmin."
                )
        finally:
            cursor.close()
