from typing import List, Dict, Any, Optional
from repositories.producto_repo import ProductoRepository


class InventarioService:
    """Lógica de negocio de inventario, códigos de barras y validación de precios."""

    def __init__(self):
        self._repo = ProductoRepository()

    def obtener_categorias(self) -> List[Dict[str, Any]]:
        categorias = self._repo.listar_categorias()
        if not categorias:
            cat_id = self._repo.crear_categoria_si_no_existe("General")
            return [{"id": cat_id, "nombre": "General"}]
        return categorias

    def obtener_productos(self) -> List[Dict[str, Any]]:
        return self._repo.listar_productos_activos()

    def buscar_por_codigo(self, codigo_barras: str) -> Optional[Dict[str, Any]]:
        return self._repo.buscar_por_codigo_barras(codigo_barras)

    def registrar_producto(
        self,
        codigo_barras: Optional[str],
        nombre: str,
        categoria_id: int,
        precio_costo: float,
        precio_venta: float,
        stock: int,
        stock_minimo: int = 5,
        usuario_id: Optional[int] = None,
    ) -> int:
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del artículo es obligatorio.")
        if precio_costo <= 0:
            raise ValueError("El precio de costo debe ser mayor a $0.00.")
        if precio_venta <= 0:
            raise ValueError("El precio de venta al público debe ser mayor a $0.00.")
        if precio_venta < precio_costo:
            raise ValueError(
                "El precio de venta no puede ser menor al precio de costo."
            )
        if stock < 0:
            raise ValueError("El stock inicial no puede ser negativo.")
        if stock_minimo < 0:
            raise ValueError("El stock mínimo no puede ser negativo.")

        return self._repo.crear_producto(
            codigo_barras=codigo_barras,
            nombre=nombre,
            categoria_id=categoria_id,
            precio_costo=round(precio_costo, 2),
            precio_venta=round(precio_venta, 2),
            stock_inicial=int(stock),
            stock_minimo=int(stock_minimo),
            usuario_id=usuario_id,
        )

    def actualizar_producto(
        self,
        producto_id: int,
        codigo_barras: Optional[str],
        nombre: str,
        categoria_id: int,
        precio_costo: float,
        precio_venta: float,
        stock: int,
        stock_minimo: int = 5,
        usuario_id: Optional[int] = None,
    ) -> None:
        if not producto_id:
            raise ValueError("Debes seleccionar un producto válido para actualizar.")
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del artículo es obligatorio.")
        if precio_costo <= 0:
            raise ValueError("El precio de costo debe ser mayor a $0.00.")
        if precio_venta <= 0:
            raise ValueError("El precio de venta al público debe ser mayor a $0.00.")
        if precio_venta < precio_costo:
            raise ValueError(
                "El precio de venta no puede ser menor al precio de costo."
            )
        if stock < 0:
            raise ValueError("El stock no puede ser negativo.")

        self._repo.actualizar_producto(
            producto_id=int(producto_id),
            codigo_barras=codigo_barras,
            nombre=nombre,
            categoria_id=int(categoria_id),
            precio_costo=round(precio_costo, 2),
            precio_venta=round(precio_venta, 2),
            nuevo_stock=int(stock),
            stock_minimo=int(stock_minimo),
            usuario_id=usuario_id,
        )

    def sumar_entrada_rapida(
        self,
        producto_id: int,
        unidades_a_sumar: int,
        usuario_id: Optional[int] = None,
    ) -> int:
        if unidades_a_sumar <= 0:
            raise ValueError("La cantidad a sumar debe ser un entero mayor a 0.")
        return self._repo.sumar_stock_entrada(
            producto_id=int(producto_id),
            cantidad_entrada=int(unidades_a_sumar),
            usuario_id=usuario_id,
            motivo="Entrada rápida de stock por código de barras",
        )
