from tkinter import ttk, messagebox
import customtkinter as ctk
from services.inventario_service import InventarioService
from services.pos_service import PosService
from ui.theme import (
    COLOR_BG_MAIN,
    COLOR_BG_CARD,
    COLOR_PRIMARY_BTN,
    COLOR_ACCENT,
    COLOR_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_SUCCESS,
    COLOR_WARNING,
)


class PosFrame(ctk.CTkFrame):
    """
    Vista de Punto de Venta (Caja Rápida):
    - Oculta el `Precio Costo` para evitar ruido visual en caja.
    - Buscador unificado con foco automático:
      * Si se escanea un `codigo_barras` + <Return>: agrega +1 al carrito con su
        `precio_venta` registrado, limpia el buscador y muestra notificación sin popups.
      * Si se escribe texto parcial: filtra en tiempo real y autocompleta `precio_venta`.
    """

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.inventario_service = InventarioService()
        self.pos_service = PosService()
        self.todos_los_productos = []

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(2, weight=1)

        # Cabecera y notificación discreta de escaneo
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.grid(
            row=0, column=0, columnspan=2, padx=30, pady=(30, 10), sticky="ew"
        )
        frame_header.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            frame_header,
            text="Punto de Venta",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        )
        titulo.grid(row=0, column=0, sticky="w")

        self.lbl_notificacion_pos = ctk.CTkLabel(
            frame_header,
            text="📌 Listo para escanear código de barras o buscar por nombre",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_notificacion_pos.grid(row=0, column=1, padx=20, sticky="e")

        # Buscador dual (Escáner HID + Filtro de nombre)
        frame_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        frame_busqueda.grid(row=1, column=0, padx=(30, 15), pady=(0, 10), sticky="ew")

        self.entry_buscar_caja = ctk.CTkEntry(
            frame_busqueda,
            placeholder_text="🔫 Escanea código de barras (Enter) o escribe nombre del artículo...",
            corner_radius=15,
            height=40,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_ACCENT,
            border_width=2,
            font=ctk.CTkFont(size=14),
        )
        self.entry_buscar_caja.pack(side="left", fill="x", expand=True)
        self.entry_buscar_caja.bind("<Return>", self._on_enter_buscador_caja)
        self.entry_buscar_caja.bind("<KeyRelease>", self._filtrar_caja)

        # Panel Izquierdo: Catálogo de Caja (Sin Precio Costo)
        frame_productos = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=15)
        frame_productos.grid(
            row=2, column=0, padx=(30, 15), pady=(0, 25), sticky="nsew"
        )
        frame_productos.grid_rowconfigure(1, weight=1)
        frame_productos.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_productos,
            text="Artículos Disponibles",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        columnas = ("codigo_barras", "nombre", "precio_venta", "stock")
        self.tabla_productos = ttk.Treeview(
            frame_productos, columns=columnas, show="headings", style="Custom.Treeview"
        )
        self.tabla_productos.heading("codigo_barras", text="Código")
        self.tabla_productos.heading("nombre", text="Artículo")
        self.tabla_productos.heading("precio_venta", text="Precio Venta")
        self.tabla_productos.heading("stock", text="Stock")

        self.tabla_productos.column("codigo_barras", width=110, anchor="center")
        self.tabla_productos.column("nombre", width=210, anchor="w")
        self.tabla_productos.column("precio_venta", width=100, anchor="e")
        self.tabla_productos.column("stock", width=70, anchor="center")
        self.tabla_productos.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        self.tabla_productos.bind(
            "<<TreeviewSelect>>", self._on_seleccionar_producto_manual
        )
        self.tabla_productos.bind(
            "<Double-1>", lambda e: self.agregar_seleccionado_al_carrito()
        )

        scrollbar1 = ttk.Scrollbar(
            frame_productos, orient="vertical", command=self.tabla_productos.yview
        )
        self.tabla_productos.configure(yscrollcommand=scrollbar1.set)
        scrollbar1.grid(row=1, column=1, sticky="ns", pady=5, padx=(0, 5))

        # Controles de adición manual (con precio autocompletado)
        frame_agregar = ctk.CTkFrame(frame_productos, fg_color="transparent")
        frame_agregar.grid(
            row=2, column=0, columnspan=2, padx=15, pady=15, sticky="ew"
        )
        frame_agregar.grid_columnconfigure(0, weight=1)
        frame_agregar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_agregar, text="Cantidad:").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        frame_cant = ctk.CTkFrame(frame_agregar, fg_color="transparent")
        frame_cant.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        btn_menos_v = ctk.CTkButton(
            frame_cant,
            text="-",
            width=32,
            corner_radius=10,
            fg_color=COLOR_ACCENT,
            command=lambda: self._ajustar_cant_venta(-1),
        )
        btn_menos_v.pack(side="left", padx=(0, 5))

        self.entry_cant_venta = ctk.CTkEntry(
            frame_cant,
            placeholder_text="1",
            justify="center",
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_cant_venta.pack(side="left", fill="x", expand=True)
        self.entry_cant_venta.insert(0, "1")

        btn_mas_v = ctk.CTkButton(
            frame_cant,
            text="+",
            width=32,
            corner_radius=10,
            fg_color=COLOR_ACCENT,
            command=lambda: self._ajustar_cant_venta(1),
        )
        btn_mas_v.pack(side="left", padx=(5, 0))

        ctk.CTkLabel(frame_agregar, text="Precio Unitario ($):").grid(
            row=0, column=1, sticky="w"
        )
        self.entry_precio_venta = ctk.CTkEntry(
            frame_agregar,
            placeholder_text="Autocompletado",
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_precio_venta.grid(row=1, column=1, sticky="ew")

        btn_agregar = ctk.CTkButton(
            frame_agregar,
            text="➡️ Agregar al Carrito",
            corner_radius=15,
            height=38,
            fg_color=COLOR_PRIMARY_BTN,
            command=self.agregar_seleccionado_al_carrito,
        )
        btn_agregar.grid(row=2, column=0, columnspan=2, pady=(12, 0), sticky="ew")

        # Panel Derecho: Carrito de Compras
        frame_carrito = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=15)
        frame_carrito.grid(
            row=1, column=1, rowspan=2, padx=(0, 30), pady=(0, 25), sticky="nsew"
        )
        frame_carrito.grid_rowconfigure(1, weight=1)
        frame_carrito.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_carrito,
            text="🛒 Carrito de Venta",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        columnas_carrito = ("producto", "cantidad", "precio_venta", "subtotal")
        self.tabla_carrito = ttk.Treeview(
            frame_carrito,
            columns=columnas_carrito,
            show="headings",
            style="Custom.Treeview",
        )
        self.tabla_carrito.heading("producto", text="Artículo")
        self.tabla_carrito.heading("cantidad", text="Cant.")
        self.tabla_carrito.heading("precio_venta", text="P. Unit.")
        self.tabla_carrito.heading("subtotal", text="Subtotal")

        self.tabla_carrito.column("producto", width=165, anchor="w")
        self.tabla_carrito.column("cantidad", width=55, anchor="center")
        self.tabla_carrito.column("precio_venta", width=80, anchor="e")
        self.tabla_carrito.column("subtotal", width=85, anchor="e")
        self.tabla_carrito.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")

        frame_acciones_carrito = ctk.CTkFrame(frame_carrito, fg_color="transparent")
        frame_acciones_carrito.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        frame_acciones_carrito.grid_columnconfigure((0, 1), weight=1)

        btn_quitar = ctk.CTkButton(
            frame_acciones_carrito,
            text="🗑️ Quitar seleccionado",
            corner_radius=12,
            fg_color="#34495E",
            command=self.quitar_del_carrito,
        )
        btn_quitar.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        btn_vaciar = ctk.CTkButton(
            frame_acciones_carrito,
            text="🧹 Vaciar carrito",
            corner_radius=12,
            fg_color="#34495E",
            command=self.vaciar_carrito,
        )
        btn_vaciar.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.lbl_total = ctk.CTkLabel(
            frame_carrito,
            text="Total: $0.00",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_HIGHLIGHT,
        )
        self.lbl_total.grid(row=3, column=0, padx=18, pady=10, sticky="e")

        btn_procesar = ctk.CTkButton(
            frame_carrito,
            text="✅ Cobrar Venta (F12)",
            corner_radius=15,
            fg_color=COLOR_SUCCESS,
            hover_color="#1E8449",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.procesar_venta,
        )
        btn_procesar.grid(row=4, column=0, padx=15, pady=(0, 18), sticky="ew")

    def on_show(self):
        self.cargar_productos()
        self.after(100, self.entry_buscar_caja.focus_set)

    def _mostrar_notificacion(self, texto: str, color: str = COLOR_SUCCESS):
        self.lbl_notificacion_pos.configure(text=texto, text_color=color)

    def cargar_productos(self):
        productos = self.app.ejecutar_seguro(self.inventario_service.obtener_productos)
        if productos is None:
            return
        self.todos_los_productos = productos
        self._filtrar_caja()

    def _filtrar_caja(self, event=None):
        if event and event.keysym == "Return":
            return
        filtro = self.entry_buscar_caja.get().strip().lower()
        for item in self.tabla_productos.get_children():
            self.tabla_productos.delete(item)

        for p in self.todos_los_productos:
            codigo_str = p["codigo_barras"] or "-"
            texto_busqueda = f"{codigo_str} {p['nombre']}".lower()
            if not filtro or filtro in texto_busqueda:
                self.tabla_productos.insert(
                    "",
                    "end",
                    iid=str(p["id"]),
                    values=(
                        codigo_str,
                        p["nombre"],
                        f"${p['precio_venta']:.2f}",
                        p["stock"],
                    ),
                )

    def _on_enter_buscador_caja(self, event=None):
        """
        Escaneo directo en Punto de Venta (<Return>):
        Si coincide con un `codigo_barras`, agrega 1 unidad inmediatamente al carrito
        con su `precio_venta`, limpia el buscador y notifica visualmente sin popups.
        """
        texto = self.entry_buscar_caja.get().strip()
        if not texto:
            return

        # 1. Buscar coincidencia exacta por código de barras en caché local o BD
        prod_exacto = next(
            (
                p
                for p in self.todos_los_productos
                if p["codigo_barras"] and p["codigo_barras"].lower() == texto.lower()
            ),
            None,
        )

        if not prod_exacto:
            prod_exacto = self.inventario_service.buscar_por_codigo(texto)

        if prod_exacto:
            try:
                item = self.pos_service.agregar_o_incrementar_en_carrito(
                    carrito=self.app.carrito,
                    producto=prod_exacto,
                    cantidad_agregar=1,
                )
                self._refrescar_tabla_carrito()
                self.entry_buscar_caja.delete(0, "end")
                self._filtrar_caja()
                self._mostrar_notificacion(
                    f"✅ +1 {item['nombre']} agregado (${item['precio_venta']:.2f})",
                    COLOR_SUCCESS,
                )
            except ValueError as err:
                self.entry_buscar_caja.delete(0, "end")
                self._mostrar_notificacion(f"⚠️ {err}", COLOR_WARNING)
            return

        # 2. Si no es código de barras pero el filtro dejó un único producto en la tabla, seleccionarlo
        hijos = self.tabla_productos.get_children()
        if len(hijos) == 1:
            self.tabla_productos.selection_set(hijos[0])
            self._on_seleccionar_producto_manual()
            self.agregar_seleccionado_al_carrito()
            self.entry_buscar_caja.delete(0, "end")
            self._filtrar_caja()
        else:
            self._mostrar_notificacion(
                f"🔍 Sin coincidencia de código exacto para '{texto}'. Selecciona de la lista.",
                COLOR_WARNING,
            )

    def _on_seleccionar_producto_manual(self, event=None):
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            return
        prod_id = int(seleccion[0])
        prod = next(
            (p for p in self.todos_los_productos if int(p["id"]) == prod_id), None
        )
        if prod:
            self.entry_precio_venta.delete(0, "end")
            self.entry_precio_venta.insert(0, f"{prod['precio_venta']:.2f}")
            if not self.entry_cant_venta.get().strip():
                self.entry_cant_venta.insert(0, "1")

    def _ajustar_cant_venta(self, delta: int):
        try:
            actual = int(self.entry_cant_venta.get())
        except ValueError:
            actual = 1
        nuevo = max(1, actual + delta)
        self.entry_cant_venta.delete(0, "end")
        self.entry_cant_venta.insert(0, str(nuevo))

    def agregar_seleccionado_al_carrito(self):
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning(
                "Sin selección",
                "Escanea un código de barras o selecciona un artículo de la tabla.",
            )
            return

        prod_id = int(seleccion[0])
        prod = next(
            (p for p in self.todos_los_productos if int(p["id"]) == prod_id), None
        )
        if not prod:
            return

        try:
            cantidad = int(self.entry_cant_venta.get())
            precio_override = float(self.entry_precio_venta.get())
        except ValueError:
            messagebox.showwarning(
                "Datos inválidos",
                "Verifica que la cantidad y el precio unitario sean números válidos.",
            )
            return

        try:
            item = self.pos_service.agregar_o_incrementar_en_carrito(
                carrito=self.app.carrito,
                producto=prod,
                cantidad_agregar=cantidad,
                precio_venta_override=precio_override,
            )
            self._refrescar_tabla_carrito()
            self.entry_cant_venta.delete(0, "end")
            self.entry_cant_venta.insert(0, "1")
            self._mostrar_notificacion(
                f"✅ +{cantidad} {item['nombre']} en carrito", COLOR_SUCCESS
            )
            self.entry_buscar_caja.focus_set()
        except ValueError as err:
            messagebox.showwarning("Stock / Validación", str(err))

    def _refrescar_tabla_carrito(self):
        for row in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(row)

        for idx, item in enumerate(self.app.carrito):
            self.tabla_carrito.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    item["nombre"],
                    item["cantidad"],
                    f"${item['precio_venta']:.2f}",
                    f"${item['subtotal']:.2f}",
                ),
            )
        total = sum(i["subtotal"] for i in self.app.carrito)
        self.lbl_total.configure(text=f"Total: ${total:.2f}")

    def quitar_del_carrito(self):
        seleccion = self.tabla_carrito.selection()
        if not seleccion:
            return
        idx = int(seleccion[0])
        if 0 <= idx < len(self.app.carrito):
            eliminado = self.app.carrito.pop(idx)
            self._refrescar_tabla_carrito()
            self._mostrar_notificacion(
                f"🗑️ '{eliminado['nombre']}' retirado del carrito", COLOR_TEXT_MUTED
            )
        self.entry_buscar_caja.focus_set()

    def vaciar_carrito(self):
        self.app.carrito.clear()
        self._refrescar_tabla_carrito()
        self._mostrar_notificacion("🧹 Carrito vaciado", COLOR_TEXT_MUTED)
        self.entry_buscar_caja.focus_set()

    def procesar_venta(self):
        if not self.app.carrito:
            messagebox.showwarning(
                "Carrito vacío",
                "Agrega o escanea al menos un artículo antes de cobrar.",
            )
            return

        total_previo = sum(i["subtotal"] for i in self.app.carrito)
        confirmar = messagebox.askyesno(
            "Confirmar Cobro",
            f"¿Confirmas el cobro de {len(self.app.carrito)} línea(s) "
            f"por un total de ${total_previo:.2f}?",
        )
        if not confirmar:
            self.entry_buscar_caja.focus_set()
            return

        resultado = self.app.ejecutar_seguro(
            self.pos_service.cobrar_venta,
            self.app.usuario_actual["id"],
            self.app.carrito,
        )
        if resultado is None:
            return

        venta_id, total_cobrado = resultado
        self.app.carrito.clear()
        self._refrescar_tabla_carrito()
        self.cargar_productos()
        self._mostrar_notificacion(
            f"✅ Venta #{venta_id} cobrada con éxito (${total_cobrado:.2f})",
            COLOR_SUCCESS,
        )
        messagebox.showinfo(
            "Venta Exitosa",
            f"Folio de Venta #{venta_id} registrado.\nTotal cobrado: ${total_cobrado:.2f}",
        )
        self.entry_buscar_caja.focus_set()
