from typing import List, Dict, Any, Tuple, Optional
from repositories.venta_repo import VentaRepository


class PosService:
    """Servicio de Punto de Venta (gestión de carrito en memoria y cobro ACID)."""

    def __init__(self):
        self._venta_repo = VentaRepository()

    @staticmethod
    def agregar_o_incrementar_en_carrito(
        carrito: List[Dict[str, Any]],
        producto: Dict[str, Any],
        cantidad_agregar: int = 1,
        precio_venta_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Agrega un producto al carrito o incrementa su cantidad si ya existe,
        validando el stock disponible en tiempo real.
        """
        if cantidad_agregar <= 0:
            raise ValueError("La cantidad a vender debe ser mayor a 0.")

        prod_id = int(producto["id"])
        nombre = str(producto["nombre"])
        codigo = str(producto.get("codigo_barras") or "-")
        stock_disp = int(producto["stock"])
        precio_unit = round(
            float(
                precio_venta_override
                if precio_venta_override is not None
                else producto["precio_venta"]
            ),
            2,
        )

        if precio_unit <= 0:
            raise ValueError(
                f"El producto '{nombre}' no tiene un precio de venta válido (> $0.00)."
            )

        existente = next(
            (item for item in carrito if int(item["producto_id"]) == prod_id),
            None,
        )
        cantidad_en_carrito = int(existente["cantidad"]) if existente else 0

        if cantidad_en_carrito + cantidad_agregar > stock_disp:
            raise ValueError(
                f"Stock insuficiente para '{nombre}' (Disponible: {stock_disp}, "
                f"en carrito: {cantidad_en_carrito})."
            )

        if existente:
            existente["cantidad"] = cantidad_en_carrito + cantidad_agregar
            existente["precio_venta"] = precio_unit
            existente["subtotal"] = round(
                existente["cantidad"] * existente["precio_venta"], 2
            )
            return existente

        nuevo_item = {
            "producto_id": prod_id,
            "codigo_barras": codigo,
            "nombre": nombre,
            "cantidad": cantidad_agregar,
            "precio_venta": precio_unit,
            "subtotal": round(cantidad_agregar * precio_unit, 2),
        }
        carrito.append(nuevo_item)
        return nuevo_item

    def cobrar_venta(
        self,
        usuario_id: Optional[int],
        carrito: List[Dict[str, Any]],
    ) -> Tuple[int, float]:
        return self._venta_repo.procesar_venta_acid(
            usuario_id=usuario_id,
            carrito=carrito,
        )
