from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk
from services.inventario_service import InventarioService
from ui.theme import (
    COLOR_BG_MAIN,
    COLOR_BG_CARD,
    COLOR_PRIMARY_BTN,
    COLOR_SIDEBAR_BTN_HOVER,
    COLOR_ACCENT,
    COLOR_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_SUCCESS,
)


class InventarioFrame(ctk.CTkFrame):
    """
    Vista de Inventario en 3NF con soporte nativo para Lector de Código de Barras (HID):
    - Al escanear un código nuevo (<Return>): salta el foco a Nombre para darlo de alta.
    - Al escanear un código existente (<Return>): selecciona el producto y permite sumar
      stock de entrada inmediatamente sin duplicar registros.
    """

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.inventario_service = InventarioService()

        self.producto_seleccionado_id = None
        self.todos_los_productos = []
        self.categorias_map = {}  # nombre -> id

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)

        titulo = ctk.CTkLabel(
            self,
            text="Inventario de Productos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        )
        titulo.grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 10), sticky="w")

        # Barra de búsqueda superior
        frame_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        frame_busqueda.grid(row=1, column=0, padx=(30, 15), pady=(0, 10), sticky="ew")

        self.entry_buscar = ctk.CTkEntry(
            frame_busqueda,
            placeholder_text="🔍 Filtrar inventario por código, artículo o categoría...",
            corner_radius=15,
            height=36,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_PRIMARY_BTN,
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", self._filtrar_productos)

        btn_foco_escaner = ctk.CTkButton(
            frame_busqueda,
            text="🏷️ Escanear en Ficha",
            width=150,
            height=36,
            corner_radius=15,
            fg_color=COLOR_PRIMARY_BTN,
            command=lambda: self.entry_codigo.focus_set(),
        )
        btn_foco_escaner.pack(side="left")

        # Tabla de Inventario
        frame_tabla = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=15)
        frame_tabla.grid(row=2, column=0, padx=(30, 15), pady=(0, 25), sticky="nsew")
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        columnas = (
            "id",
            "codigo_barras",
            "nombre",
            "categoria",
            "precio_costo",
            "precio_venta",
            "stock",
        )
        self.tabla = ttk.Treeview(
            frame_tabla, columns=columnas, show="headings", style="Custom.Treeview"
        )
        self.tabla.heading("id", text="ID")
        self.tabla.heading("codigo_barras", text="Código Barras")
        self.tabla.heading("nombre", text="Artículo")
        self.tabla.heading("categoria", text="Categoría")
        self.tabla.heading("precio_costo", text="Costo")
        self.tabla.heading("precio_venta", text="P. Venta")
        self.tabla.heading("stock", text="Stock")

        self.tabla.column("id", width=45, anchor="center")
        self.tabla.column("codigo_barras", width=115, anchor="center")
        self.tabla.column("nombre", width=185, anchor="w")
        self.tabla.column("categoria", width=110, anchor="center")
        self.tabla.column("precio_costo", width=80, anchor="e")
        self.tabla.column("precio_venta", width=80, anchor="e")
        self.tabla.column("stock", width=65, anchor="center")

        self.tabla.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self._on_seleccionar_tabla)

        scrollbar = ttk.Scrollbar(
            frame_tabla, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=15, padx=(0, 5))

        btn_refrescar = ctk.CTkButton(
            frame_tabla,
            text="🔄 Refrescar",
            width=120,
            corner_radius=15,
            fg_color=COLOR_SIDEBAR_BTN_HOVER,
            command=self.cargar_datos,
        )
        btn_refrescar.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

        # Panel Derecho: Ficha del Producto
        frame_form = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=15)
        frame_form.grid(row=1, column=1, rowspan=2, padx=(0, 30), pady=(0, 25), sticky="nsew")

        lbl_form = ctk.CTkLabel(
            frame_form,
            text="Ficha del Producto",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        )
        lbl_form.pack(padx=20, pady=(18, 4), anchor="w")

        self.lbl_estado_escaner = ctk.CTkLabel(
            frame_form,
            text="Escanea el código de barras y presiona Enter",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_HIGHLIGHT,
            wraplength=280,
            justify="left",
        )
        self.lbl_estado_escaner.pack(padx=20, pady=(0, 10), anchor="w")

        # Código de Barras (Escáner HID)
        ctk.CTkLabel(frame_form, text="Código de Barras (Enter para buscar/validar):").pack(
            padx=20, anchor="w"
        )
        self.entry_codigo = ctk.CTkEntry(
            frame_form,
            placeholder_text="Escanea o escribe código...",
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=1,
            border_color=COLOR_ACCENT,
        )
        self.entry_codigo.pack(padx=20, pady=(2, 10), fill="x")
        self.entry_codigo.bind("<Return>", self._on_escanear_codigo_ficha)

        # Nombre
        ctk.CTkLabel(frame_form, text="Nombre del artículo:").pack(padx=20, anchor="w")
        self.entry_nombre = ctk.CTkEntry(
            frame_form,
            placeholder_text="Ej. Cuaderno Profesional 100h",
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_nombre.pack(padx=20, pady=(2, 10), fill="x")

        # Categoría
        ctk.CTkLabel(frame_form, text="Categoría:").pack(padx=20, anchor="w")
        self.combo_categoria = ctk.CTkOptionMenu(
            frame_form,
            values=["General"],
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            button_color=COLOR_PRIMARY_BTN,
        )
        self.combo_categoria.pack(padx=20, pady=(2, 10), fill="x")

        # Precios (Costo y Venta en una fila limpia)
        frame_precios = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_precios.pack(padx=20, pady=(0, 10), fill="x")
        frame_precios.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(frame_precios, text="Costo ($):").grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.entry_costo = ctk.CTkEntry(
            frame_precios,
            placeholder_text="0.00",
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_costo.grid(row=1, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkLabel(frame_precios, text="Precio Venta ($):").grid(
            row=0, column=1, sticky="w", padx=(5, 0)
        )
        self.entry_venta = ctk.CTkEntry(
            frame_precios,
            placeholder_text="0.00",
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_venta.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        # Stock actual y botones +/-
        ctk.CTkLabel(frame_form, text="Stock disponible:").pack(padx=20, anchor="w")
        frame_cant = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_cant.pack(padx=20, pady=(2, 10), fill="x")

        btn_menos = ctk.CTkButton(
            frame_cant,
            text="-",
            width=35,
            corner_radius=10,
            fg_color=COLOR_ACCENT,
            command=lambda: self._ajustar_cant(-1),
        )
        btn_menos.pack(side="left", padx=(0, 5))

        self.entry_stock = ctk.CTkEntry(
            frame_cant,
            placeholder_text="0",
            corner_radius=10,
            justify="center",
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_stock.pack(side="left", fill="x", expand=True)

        btn_mas = ctk.CTkButton(
            frame_cant,
            text="+",
            width=35,
            corner_radius=10,
            fg_color=COLOR_ACCENT,
            command=lambda: self._ajustar_cant(1),
        )
        btn_mas.pack(side="left", padx=(5, 0))

        self.lbl_id_seleccionado = ctk.CTkLabel(
            frame_form,
            text="📝 Modo: Nuevo Registro",
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_id_seleccionado.pack(padx=20, pady=(2, 8), anchor="w")

        # Botones de acción
        btn_guardar = ctk.CTkButton(
            frame_form,
            text="➕ Registrar Nuevo",
            corner_radius=15,
            fg_color=COLOR_PRIMARY_BTN,
            command=self.registrar_producto,
        )
        btn_guardar.pack(padx=20, pady=4, fill="x")

        btn_actualizar = ctk.CTkButton(
            frame_form,
            text="✏️ Actualizar Seleccionado",
            corner_radius=15,
            fg_color=COLOR_SIDEBAR_BTN_HOVER,
            command=self.actualizar_producto,
        )
        btn_actualizar.pack(padx=20, pady=4, fill="x")

        self.btn_sumar_entrada = ctk.CTkButton(
            frame_form,
            text="📦 Resurtir Stock",
            corner_radius=15,
            fg_color=COLOR_SUCCESS,
            command=self.sumar_stock_seleccionado,
        )
        self.btn_sumar_entrada.pack(padx=20, pady=4, fill="x")

        btn_limpiar = ctk.CTkButton(
            frame_form,
            text="🧹 Nuevo Escaneo",
            corner_radius=15,
            fg_color="#34495E",
            command=self.limpiar_formulario,
        )
        btn_limpiar.pack(padx=20, pady=(4, 15), fill="x")

    def on_show(self):
        self.cargar_datos()
        self.after(100, self.entry_codigo.focus_set)

    def cargar_datos(self):
        categorias = self.app.ejecutar_seguro(
            self.inventario_service.obtener_categorias
        )
        if categorias:
            self.categorias_map = {c["nombre"]: int(c["id"]) for c in categorias}
            nombres_cat = list(self.categorias_map.keys())
            self.combo_categoria.configure(values=nombres_cat)
            if self.combo_categoria.get() not in self.categorias_map:
                self.combo_categoria.set(nombres_cat[0])

        productos = self.app.ejecutar_seguro(self.inventario_service.obtener_productos)
        if productos is not None:
            self.todos_los_productos = productos
            self._filtrar_productos()

    def _filtrar_productos(self, event=None):
        filtro = self.entry_buscar.get().strip().lower()
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for p in self.todos_los_productos:
            texto_busqueda = (
                f"{p['codigo_barras']} {p['nombre']} {p['categoria_nombre']}".lower()
            )
            if not filtro or filtro in texto_busqueda:
                self.tabla.insert(
                    "",
                    "end",
                    iid=str(p["id"]),
                    values=(
                        p["id"],
                        p["codigo_barras"] or "-",
                        p["nombre"],
                        p["categoria_nombre"],
                        f"{p['precio_costo']:.2f}",
                        f"{p['precio_venta']:.2f}",
                        p["stock"],
                    ),
                )

    def _on_escanear_codigo_ficha(self, event=None):
        """
        Comportamiento dual al escanear código de barras en Inventario (<Return>):
        - Si no existe: mantiene el código y salta automáticamente al campo Nombre.
        - Si ya existe: carga el producto y abre/enfoca la entrada de stock sin duplicar.
        """
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            return

        existente = self.app.ejecutar_seguro(
            self.inventario_service.buscar_por_codigo, codigo
        )
        if existente:
            self._cargar_producto_en_formulario(existente)
            if self.tabla.exists(str(existente["id"])):
                self.tabla.selection_set(str(existente["id"]))
                self.tabla.see(str(existente["id"]))
            self.lbl_estado_escaner.configure(
                text=f"✅ Código registrado: '{existente['nombre']}' (Stock: {existente['stock']}).",
                text_color=COLOR_SUCCESS,
            )
            self.sumar_stock_seleccionado()
        else:
            self.producto_seleccionado_id = None
            self.entry_nombre.delete(0, "end")
            self.entry_costo.delete(0, "end")
            self.entry_venta.delete(0, "end")
            self.entry_stock.delete(0, "end")
            self.entry_stock.insert(0, "1")
            self.lbl_id_seleccionado.configure(
                text=f"✨ Nuevo código: {codigo}", text_color=COLOR_HIGHLIGHT
            )
            self.lbl_estado_escaner.configure(
                text="✨ Código nuevo detectado. Completa nombre y precios.",
                text_color=COLOR_HIGHLIGHT,
            )
            self.entry_nombre.focus_set()

    def _on_seleccionar_tabla(self, event=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        prod_id = int(seleccion[0])
        prod = next(
            (p for p in self.todos_los_productos if int(p["id"]) == prod_id), None
        )
        if prod:
            self._cargar_producto_en_formulario(prod)

    def _cargar_producto_en_formulario(self, prod: dict):
        self.producto_seleccionado_id = int(prod["id"])
        self.entry_codigo.delete(0, "end")
        self.entry_codigo.insert(0, prod["codigo_barras"] or "")

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, prod["nombre"])

        if prod["categoria_nombre"] in self.categorias_map:
            self.combo_categoria.set(prod["categoria_nombre"])

        self.entry_costo.delete(0, "end")
        self.entry_costo.insert(0, f"{prod['precio_costo']:.2f}")

        self.entry_venta.delete(0, "end")
        self.entry_venta.insert(0, f"{prod['precio_venta']:.2f}")

        self.entry_stock.delete(0, "end")
        self.entry_stock.insert(0, str(prod["stock"]))

        self.lbl_id_seleccionado.configure(
            text=f"📝 Editando ID: #{prod['id']} ({prod['nombre'][:18]})",
            text_color=COLOR_TEXT_LIGHT,
        )

    def _ajustar_cant(self, delta: int):
        try:
            actual = int(self.entry_stock.get())
        except ValueError:
            actual = 0
        nuevo = max(0, actual + delta)
        self.entry_stock.delete(0, "end")
        self.entry_stock.insert(0, str(nuevo))

    def limpiar_formulario(self):
        self.producto_seleccionado_id = None
        self.entry_codigo.delete(0, "end")
        self.entry_nombre.delete(0, "end")
        self.entry_costo.delete(0, "end")
        self.entry_venta.delete(0, "end")
        self.entry_stock.delete(0, "end")
        self.lbl_id_seleccionado.configure(
            text="📝 Modo: Nuevo Registro", text_color=COLOR_TEXT_MUTED
        )
        self.lbl_estado_escaner.configure(
            text="Escanea el código de barras y presiona Enter",
            text_color=COLOR_HIGHLIGHT,
        )
        if self.tabla.selection():
            self.tabla.selection_remove(self.tabla.selection())
        self.entry_codigo.focus_set()

    def _leer_campos(self):
        codigo = self.entry_codigo.get().strip() or None
        nombre = self.entry_nombre.get().strip()
        cat_nombre = self.combo_categoria.get()
        categoria_id = self.categorias_map.get(cat_nombre, 1)

        try:
            costo = float(self.entry_costo.get())
            venta = float(self.entry_venta.get())
        except ValueError:
            raise ValueError("Costo y Precio de Venta deben ser números válidos.")

        try:
            stock = int(self.entry_stock.get())
        except ValueError:
            raise ValueError("El stock debe ser un número entero.")

        return codigo, nombre, categoria_id, costo, venta, stock

    def registrar_producto(self):
        try:
            codigo, nombre, categoria_id, costo, venta, stock = self._leer_campos()
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
            return

        res = self.app.ejecutar_seguro(
            self.inventario_service.registrar_producto,
            codigo,
            nombre,
            categoria_id,
            costo,
            venta,
            stock,
            5,
            self.app.usuario_actual["id"],
            mensaje_exito=f"Artículo '{nombre}' registrado correctamente.",
        )
        if res is not None:
            self.limpiar_formulario()
            self.cargar_datos()

    def actualizar_producto(self):
        if not self.producto_seleccionado_id:
            messagebox.showwarning(
                "Sin selección",
                "Selecciona o escanea un producto existente para actualizarlo.",
            )
            return
        try:
            codigo, nombre, categoria_id, costo, venta, stock = self._leer_campos()
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
            return

        self.app.ejecutar_seguro(
            self.inventario_service.actualizar_producto,
            self.producto_seleccionado_id,
            codigo,
            nombre,
            categoria_id,
            costo,
            venta,
            stock,
            5,
            self.app.usuario_actual["id"],
            mensaje_exito=f"Artículo '{nombre}' actualizado.",
        )
        self.limpiar_formulario()
        self.cargar_datos()

    def sumar_stock_seleccionado(self):
        if not self.producto_seleccionado_id:
            messagebox.showwarning(
                "Sin selección",
                "Escanea o selecciona primero un producto de la tabla.",
            )
            return

        unidades = simpledialog.askinteger(
            "Entrada de Mercancía",
            "¿Cuántas unidades nuevas ingresaron al almacén?",
            parent=self,
            minvalue=1,
            initialvalue=1,
        )
        if not unidades:
            return

        nuevo_stock = self.app.ejecutar_seguro(
            self.inventario_service.sumar_entrada_rapida,
            self.producto_seleccionado_id,
            unidades,
            self.app.usuario_actual["id"],
        )
        if nuevo_stock is not None:
            self.lbl_estado_escaner.configure(
                text=f"📦 +{unidades} unidades sumadas. Nuevo stock: {nuevo_stock}.",
                text_color=COLOR_SUCCESS,
            )
            self.cargar_datos()
            self.limpiar_formulario()
