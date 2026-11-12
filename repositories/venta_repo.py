from typing import List, Dict, Any, Tuple, Optional
from database.connection import get_connection


class VentaRepository:
    """
    Repositorio transaccional de ventas y consultas analíticas en 3NF.
    Garantiza atomicidad ACID total en el proceso de cobro.
    """

    @staticmethod
    def procesar_venta_acid(
        usuario_id: Optional[int],
        carrito: List[Dict[str, Any]],
    ) -> Tuple[int, float]:
        """
        Ejecuta toda la venta dentro de una ÚNICA transacción ACID.
        Si cualquier producto no tiene stock suficiente o falla un INSERT,
        el context manager realiza rollback() de toda la operación.
        """
        if not carrito:
            raise ValueError("El carrito de compras está vacío.")

        with get_connection(commit=True) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                total_calculado = 0.0
                lineas_validadas = []

                # 1. Bloquear filas de productos (FOR UPDATE) y validar stock real
                for item in carrito:
                    producto_id = int(item["producto_id"])
                    cantidad_solicitada = int(item["cantidad"])
                    precio_venta_unit = round(float(item["precio_venta"]), 2)

                    if cantidad_solicitada <= 0:
                        raise ValueError("La cantidad de venta debe ser mayor a cero.")
                    if precio_venta_unit <= 0:
                        raise ValueError("El precio de venta debe ser mayor a cero.")

                    cursor.execute(
                        """
                        SELECT id, nombre, stock, precio_costo
                        FROM productos
                        WHERE id = %s AND activo = 1
                        FOR UPDATE
                        """,
                        (producto_id,),
                    )
                    prod_db = cursor.fetchone()
                    if not prod_db:
                        raise ValueError(
                            f"El producto ID #{producto_id} no existe o está inactivo."
                        )

                    stock_actual = int(prod_db["stock"])
                    if stock_actual < cantidad_solicitada:
                        raise ValueError(
                            f"Stock insuficiente para '{prod_db['nombre']}'. "
                            f"Disponible: {stock_actual}, solicitado: {cantidad_solicitada}."
                        )

                    costo_historico = round(float(prod_db["precio_costo"]), 2)
                    subtotal_linea = round(cantidad_solicitada * precio_venta_unit, 2)
                    total_calculado = round(total_calculado + subtotal_linea, 2)

                    lineas_validadas.append(
                        {
                            "producto_id": producto_id,
                            "cantidad": cantidad_solicitada,
                            "precio_costo_historico": costo_historico,
                            "precio_venta_unitario": precio_venta_unit,
                        }
                    )

                # 2. Insertar cabecera de venta con el total definitivo
                cursor.execute(
                    """
                    INSERT INTO ventas (usuario_id, total_venta)
                    VALUES (%s, %s)
                    """,
                    (usuario_id, total_calculado),
                )
                venta_id = int(cursor.lastrowid)

                # 3. Insertar detalles (sin columna redundante), descontar stock y registrar Kardex
                sql_detalle = """
                    INSERT INTO detalles_ventas
                        (venta_id, producto_id, cantidad, precio_costo_historico, precio_venta_unitario)
                    VALUES (%s, %s, %s, %s, %s)
                """
                sql_descuento = """
                    UPDATE productos
                    SET stock = stock - %s
                    WHERE id = %s
                """
                sql_kardex = """
                    INSERT INTO movimientos_inventario
                        (producto_id, usuario_id, tipo, cantidad, motivo)
                    VALUES (%s, %s, 'SALIDA_VENTA', %s, %s)
                """

                for linea in lineas_validadas:
                    cursor.execute(
                        sql_detalle,
                        (
                            venta_id,
                            linea["producto_id"],
                            linea["cantidad"],
                            linea["precio_costo_historico"],
                            linea["precio_venta_unitario"],
                        ),
                    )
                    cursor.execute(
                        sql_descuento,
                        (linea["cantidad"], linea["producto_id"]),
                    )
                    cursor.execute(
                        sql_kardex,
                        (
                            linea["producto_id"],
                            usuario_id,
                            linea["cantidad"],
                            f"Venta folio #{venta_id}",
                        ),
                    )

                return venta_id, total_calculado
            finally:
                cursor.close()

    @staticmethod
    def obtener_historial_ventas() -> List[Dict[str, Any]]:
        """
        Calcula dinámicamente el subtotal (cantidad * precio_venta_unitario)
        respetando la Tercera Forma Normal (3NF).
        """
        sql = """
            SELECT v.id AS venta_id,
                   COALESCE(p.codigo_barras, '-') AS codigo_barras,
                   p.nombre AS producto,
                   dv.cantidad,
                   dv.precio_venta_unitario,
                   ROUND(dv.cantidad * dv.precio_venta_unitario, 2) AS subtotal,
                   COALESCE(u.username, 'Sistema') AS cajero,
                   v.fecha
            FROM ventas v
            INNER JOIN detalles_ventas dv ON v.id = dv.venta_id
            INNER JOIN productos p ON dv.producto_id = p.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            ORDER BY v.fecha DESC, dv.id ASC
        """
        with get_connection(commit=False) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql)
                return cursor.fetchall()
            finally:
                cursor.close()

    @staticmethod
    def obtener_metricas_dashboard() -> Dict[str, Any]:
        """
        Calcula métricas exactas usando `dv.precio_costo_historico` para que
        cambios futuros en `productos.precio_costo` no alteren ganancias pasadas.
        """
        with get_connection(commit=False) as conn:
            cursor = conn.cursor()
            try:
                metricas: Dict[str, Any] = {}

                cursor.execute(
                    "SELECT COUNT(*), COALESCE(SUM(stock), 0) FROM productos WHERE activo = 1"
                )
                total_productos, total_stock = cursor.fetchone()
                metricas["total_productos"] = int(total_productos or 0)
                metricas["total_stock"] = int(total_stock or 0)

                cursor.execute(
                    "SELECT COUNT(*) FROM productos WHERE activo = 1 AND stock <= stock_minimo"
                )
                (bajo_stock,) = cursor.fetchone()
                metricas["bajo_stock"] = int(bajo_stock or 0)

                sql_ventas_mes = """
                    SELECT COUNT(DISTINCT v.id),
                           COALESCE(SUM(dv.cantidad * dv.precio_venta_unitario), 0),
                           COALESCE(SUM(dv.cantidad * dv.precio_costo_historico), 0)
                    FROM ventas v
                    INNER JOIN detalles_ventas dv ON v.id = dv.venta_id
                    WHERE MONTH(v.fecha) = MONTH(CURRENT_DATE())
                      AND YEAR(v.fecha) = YEAR(CURRENT_DATE())
                """
                cursor.execute(sql_ventas_mes)
                ventas_mes, ingresos_mes, costo_historico_mes = cursor.fetchone()

                ingresos_f = float(ingresos_mes or 0.0)
                costo_f = float(costo_historico_mes or 0.0)

                metricas["ventas_mes"] = int(ventas_mes or 0)
                metricas["total_ventas_mes"] = round(ingresos_f, 2)
                metricas["ganancia_mes"] = round(ingresos_f - costo_f, 2)

                return metricas
            finally:
                cursor.close()

    @staticmethod
    def obtener_registros_reporte_mensual() -> List[Dict[str, Any]]:
        """
        Devuelve los detalles vendidos del mes actual con su costo histórico exacto.
        """
        sql = """
            SELECT v.id AS venta_id,
                   p.nombre AS producto,
                   dv.cantidad,
                   dv.precio_costo_historico,
                   dv.precio_venta_unitario,
                   ROUND(dv.cantidad * dv.precio_costo_historico, 2) AS subtotal_costo,
                   ROUND(dv.cantidad * dv.precio_venta_unitario, 2) AS subtotal_venta,
                   v.fecha
            FROM ventas v
            INNER JOIN detalles_ventas dv ON v.id = dv.venta_id
            INNER JOIN productos p ON dv.producto_id = p.id
            WHERE MONTH(v.fecha) = MONTH(CURRENT_DATE())
              AND YEAR(v.fecha) = YEAR(CURRENT_DATE())
            ORDER BY v.fecha ASC, dv.id ASC
        """
        with get_connection(commit=False) as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql)
                return cursor.fetchall()
            finally:
                cursor.close()
