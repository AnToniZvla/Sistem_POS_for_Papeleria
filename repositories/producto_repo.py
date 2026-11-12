from typing import List, Dict, Any, Optional
from database.connection import get_connection


class ProductoRepository:
    """Repositorio 3NF para productos, categorías y movimientos de inventario."""

    @staticmethod
    def listar_categorias() -> List[Dict[str, Any]]:
        with get_connection(commit=False) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, nombre FROM categorias ORDER BY id ASC")
                return cursor.fetchall()
            finally:
                cursor.close()

    @staticmethod
    def crear_categoria_si_no_existe(nombre_categoria: str) -> int:
        nombre_limpio = nombre_categoria.strip()
        with get_connection(commit=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM categorias WHERE LOWER(nombre) = LOWER(%s) LIMIT 1",
                    (nombre_limpio,),
                )
                existente = cursor.fetchone()
                if existente:
                    return int(existente[0])
                cursor.execute(
                    "INSERT INTO categorias (nombre) VALUES (%s)",
                    (nombre_limpio,),
                )
                return int(cursor.lastrowid)
            finally:
                cursor.close()

    @staticmethod
    def listar_productos_activos() -> List[Dict[str, Any]]:
        sql = """
            SELECT p.id,
                   COALESCE(p.codigo_barras, '') AS codigo_barras,
                   p.nombre,
                   p.categoria_id,
                   c.nombre AS categoria_nombre,
                   p.precio_costo,
                   p.precio_venta,
                   p.stock,
                   p.stock_minimo
            FROM productos p
            INNER JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1
            ORDER BY p.nombre ASC
        """
        with get_connection(commit=False) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql)
                filas = cursor.fetchall()
                for f in filas:
                    f["precio_costo"] = float(f["precio_costo"])
                    f["precio_venta"] = float(f["precio_venta"])
                    f["stock"] = int(f["stock"])
                    f["stock_minimo"] = int(f["stock_minimo"])
                return filas
            finally:
                cursor.close()

    @staticmethod
    def buscar_por_codigo_barras(codigo_barras: str) -> Optional[Dict[str, Any]]:
        codigo = codigo_barras.strip()
        if not codigo:
            return None
        sql = """
            SELECT p.id,
                   COALESCE(p.codigo_barras, '') AS codigo_barras,
                   p.nombre,
                   p.categoria_id,
                   c.nombre AS categoria_nombre,
                   p.precio_costo,
                   p.precio_venta,
                   p.stock,
                   p.stock_minimo
            FROM productos p
            INNER JOIN categorias c ON p.categoria_id = c.id
            WHERE p.codigo_barras = %s AND p.activo = 1
            LIMIT 1
        """
        with get_connection(commit=False) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql, (codigo,))
                fila = cursor.fetchone()
                if fila:
                    fila["precio_costo"] = float(fila["precio_costo"])
                    fila["precio_venta"] = float(fila["precio_venta"])
                    fila["stock"] = int(fila["stock"])
                    fila["stock_minimo"] = int(fila["stock_minimo"])
                return fila
            finally:
                cursor.close()

    @staticmethod
    def crear_producto(
        codigo_barras: Optional[str],
        nombre: str,
        categoria_id: int,
        precio_costo: float,
        precio_venta: float,
        stock_inicial: int,
        stock_minimo: int,
        usuario_id: Optional[int],
    ) -> int:
        codigo_db = codigo_barras.strip() if codigo_barras and codigo_barras.strip() else None
        with get_connection(commit=True) as conn:
            cursor = conn.cursor()
            try:
                sql_prod = """
                    INSERT INTO productos
                        (codigo_barras, nombre, categoria_id, precio_costo, precio_venta, stock, stock_minimo, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                """
                cursor.execute(
                    sql_prod,
                    (
                        codigo_db,
                        nombre.strip(),
                        categoria_id,
                        precio_costo,
                        precio_venta,
                        stock_inicial,
                        stock_minimo,
                    ),
                )
                producto_id = int(cursor.lastrowid)

                if stock_inicial > 0:
                    sql_mov = """
                        INSERT INTO movimientos_inventario
                            (producto_id, usuario_id, tipo, cantidad, motivo)
                        VALUES (%s, %s, 'ENTRADA', %s, 'Registro inicial de producto')
                    """
                    cursor.execute(sql_mov, (producto_id, usuario_id, stock_inicial))

                return producto_id
            finally:
                cursor.close()

    @staticmethod
    def actualizar_producto(
        producto_id: int,
        codigo_barras: Optional[str],
        nombre: str,
        categoria_id: int,
        precio_costo: float,
        precio_venta: float,
        nuevo_stock: int,
        stock_minimo: int,
        usuario_id: Optional[int],
    ) -> None:
        codigo_db = codigo_barras.strip() if codigo_barras and codigo_barras.strip() else None
        with get_connection(commit=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT stock FROM productos WHERE id = %s FOR UPDATE",
                    (producto_id,),
                )
                fila = cursor.fetchone()
                if not fila:
                    raise ValueError("El producto seleccionado ya no existe.")
                stock_anterior = int(fila[0])
                diferencia = nuevo_stock - stock_anterior

                sql_upd = """
                    UPDATE productos
                    SET codigo_barras = %s,
                        nombre = %s,
                        categoria_id = %s,
                        precio_costo = %s,
                        precio_venta = %s,
                        stock = %s,
                        stock_minimo = %s
                    WHERE id = %s
                """
                cursor.execute(
                    sql_upd,
                    (
                        codigo_db,
                        nombre.strip(),
                        categoria_id,
                        precio_costo,
                        precio_venta,
                        nuevo_stock,
                        stock_minimo,
                        producto_id,
                    ),
                )

                if diferencia != 0:
                    tipo_mov = "ENTRADA" if diferencia > 0 else "AJUSTE"
                    motivo = (
                        "Entrada de stock en inventario"
                        if diferencia > 0
                        else "Ajuste manual de inventario"
                    )
                    sql_mov = """
                        INSERT INTO movimientos_inventario
                            (producto_id, usuario_id, tipo, cantidad, motivo)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        sql_mov,
                        (producto_id, usuario_id, tipo_mov, abs(diferencia), motivo),
                    )
            finally:
                cursor.close()

    @staticmethod
    def sumar_stock_entrada(
        producto_id: int,
        cantidad_entrada: int,
        usuario_id: Optional[int],
        motivo: str = "Entrada por escaneo en inventario",
    ) -> int:
        with get_connection(commit=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT stock FROM productos WHERE id = %s FOR UPDATE",
                    (producto_id,),
                )
                fila = cursor.fetchone()
                if not fila:
                    raise ValueError("El producto no existe.")
                nuevo_stock = int(fila[0]) + cantidad_entrada

                cursor.execute(
                    "UPDATE productos SET stock = %s WHERE id = %s",
                    (nuevo_stock, producto_id),
                )
                cursor.execute(
                    """
                    INSERT INTO movimientos_inventario
                        (producto_id, usuario_id, tipo, cantidad, motivo)
                    VALUES (%s, %s, 'ENTRADA', %s, %s)
                    """,
                    (producto_id, usuario_id, cantidad_entrada, motivo),
                )
                return nuevo_stock
            finally:
                cursor.close()
