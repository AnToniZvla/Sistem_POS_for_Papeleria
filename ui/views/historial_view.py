from tkinter import ttk
import customtkinter as ctk
from services.reporte_service import ReporteService
from ui.theme import (
    COLOR_BG_CARD,
    COLOR_PRIMARY_BTN,
    COLOR_SIDEBAR_BTN_HOVER,
    COLOR_TEXT_LIGHT,
)


class HistorialFrame(ctk.CTkFrame):
    """Vista de Historial de Ventas con subtotal dinámico en 3NF y cajero responsable."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.reporte_service = ReporteService()
        self.registros_completos = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        titulo = ctk.CTkLabel(
            self,
            text="Registro Histórico de Ventas",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        )
        titulo.grid(row=0, column=0, padx=30, pady=(35, 10), sticky="w")

        frame_filtro = ctk.CTkFrame(self, fg_color="transparent")
        frame_filtro.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")

        self.entry_filtro = ctk.CTkEntry(
            frame_filtro,
            placeholder_text="🔍 Buscar por folio, código de barras, artículo o cajero...",
            corner_radius=15,
            height=36,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_PRIMARY_BTN,
        )
        self.entry_filtro.pack(side="left", padx=(0, 15), fill="x", expand=True)
        self.entry_filtro.bind("<KeyRelease>", lambda e: self._aplicar_filtro())

        btn_refrescar = ctk.CTkButton(
            frame_filtro,
            text="🔄 Refrescar",
            width=120,
            corner_radius=15,
            fg_color=COLOR_SIDEBAR_BTN_HOVER,
            command=self.cargar_historial,
        )
        btn_refrescar.pack(side="left")

        frame_tabla = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=15)
        frame_tabla.grid(row=2, column=0, padx=30, pady=(0, 25), sticky="nsew")
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        columnas = (
            "venta_id",
            "codigo_barras",
            "producto",
            "cantidad",
            "precio_unit",
            "subtotal",
            "cajero",
            "fecha",
        )
        self.tabla = ttk.Treeview(
            frame_tabla, columns=columnas, show="headings", style="Custom.Treeview"
        )
        titulos = {
            "venta_id": "Folio",
            "codigo_barras": "Código",
            "producto": "Artículo",
            "cantidad": "Cant.",
            "precio_unit": "P. Unitario",
            "subtotal": "Subtotal",
            "cajero": "Cajero",
            "fecha": "Fecha y Hora",
        }
        anchos = {
            "venta_id": 60,
            "codigo_barras": 110,
            "producto": 210,
            "cantidad": 60,
            "precio_unit": 90,
            "subtotal": 95,
            "cajero": 95,
            "fecha": 140,
        }
        for col in columnas:
            self.tabla.heading(col, text=titulos[col])
            self.tabla.column(
                col,
                width=anchos[col],
                anchor="w" if col == "producto" else "center",
            )
        self.tabla.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            frame_tabla, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=15, padx=(0, 5))

    def on_show(self):
        self.cargar_historial()

    def cargar_historial(self):
        registros = self.app.ejecutar_seguro(
            self.reporte_service.obtener_historial_ventas
        )
        if registros is None:
            return
        self.registros_completos = registros
        self._aplicar_filtro()

    def _aplicar_filtro(self):
        filtro = self.entry_filtro.get().strip().lower()
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for r in self.registros_completos:
            texto = (
                f"{r['venta_id']} {r['codigo_barras']} {r['producto']} {r['cajero']}".lower()
            )
            if filtro and filtro not in texto:
                continue
            fecha_val = r["fecha"]
            fecha_str = (
                fecha_val.strftime("%Y-%m-%d %H:%M")
                if hasattr(fecha_val, "strftime")
                else str(fecha_val)
            )
            self.tabla.insert(
                "",
                "end",
                values=(
                    f"#{r['venta_id']}",
                    r["codigo_barras"],
                    r["producto"],
                    r["cantidad"],
                    f"${float(r['precio_venta_unitario']):.2f}",
                    f"${float(r['subtotal']):.2f}",
                    r["cajero"],
                    fecha_str,
                ),
            )
