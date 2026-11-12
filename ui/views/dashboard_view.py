import customtkinter as ctk
from services.reporte_service import ReporteService
from ui.theme import (
    COLOR_BG_CARD,
    COLOR_PRIMARY_BTN,
    COLOR_SIDEBAR_BTN_HOVER,
    COLOR_ACCENT,
    COLOR_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_SUCCESS,
    COLOR_WARNING,
)


class DashboardFrame(ctk.CTkFrame):
    """Vista de Resumen con métricas calculadas sobre costos históricos."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.reporte_service = ReporteService()

        titulo = ctk.CTkLabel(
            self,
            text="Resumen de la Papelería",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        )
        titulo.grid(row=0, column=0, columnspan=3, padx=30, pady=(35, 20), sticky="w")

        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.tarjetas = {}
        info_tarjetas = [
            ("total_productos", "📓 Productos activos", COLOR_PRIMARY_BTN),
            ("total_stock", "📦 Unidades en stock", COLOR_SIDEBAR_BTN_HOVER),
            ("bajo_stock", "⚠️ Productos por agotarse", COLOR_WARNING),
            ("ventas_mes", "🛒 Ventas este mes", COLOR_ACCENT),
            ("total_ventas_mes", "💰 Ingresos del mes", COLOR_SUCCESS),
            ("ganancia_mes", "📈 Ganancia neta (Costo Hist.)", COLOR_HIGHLIGHT),
        ]

        for i, (clave, etiqueta, color) in enumerate(info_tarjetas):
            fila = 1 + (i // 3)
            columna = i % 3
            tarjeta = ctk.CTkFrame(self, corner_radius=15, fg_color=COLOR_BG_CARD)
            tarjeta.grid(row=fila, column=columna, padx=15, pady=15, sticky="nsew")

            barra = ctk.CTkFrame(tarjeta, width=8, fg_color=color, corner_radius=15)
            barra.pack(side="left", fill="y", pady=12, padx=(12, 0))

            contenido = ctk.CTkFrame(tarjeta, fg_color="transparent")
            contenido.pack(side="left", fill="both", expand=True, padx=15, pady=18)

            lbl_valor = ctk.CTkLabel(
                contenido,
                text="--",
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=COLOR_TEXT_LIGHT,
            )
            lbl_valor.pack(anchor="w")

            lbl_desc = ctk.CTkLabel(
                contenido,
                text=etiqueta,
                font=ctk.CTkFont(size=14),
                text_color=COLOR_TEXT_MUTED,
            )
            lbl_desc.pack(anchor="w")

            self.tarjetas[clave] = lbl_valor

        btn_actualizar = ctk.CTkButton(
            self,
            text="🔄 Actualizar métricas",
            corner_radius=15,
            height=40,
            fg_color=COLOR_SIDEBAR_BTN_HOVER,
            command=self.cargar_metricas,
        )
        btn_actualizar.grid(row=3, column=0, padx=30, pady=20, sticky="w")

    def on_show(self):
        self.cargar_metricas()

    def cargar_metricas(self):
        metricas = self.app.ejecutar_seguro(
            self.reporte_service.obtener_metricas_dashboard
        )
        if not metricas:
            return
        self.tarjetas["total_productos"].configure(text=str(metricas["total_productos"]))
        self.tarjetas["total_stock"].configure(text=str(metricas["total_stock"]))
        self.tarjetas["bajo_stock"].configure(text=str(metricas["bajo_stock"]))
        self.tarjetas["ventas_mes"].configure(text=str(metricas["ventas_mes"]))
        self.tarjetas["total_ventas_mes"].configure(
            text=f"${metricas['total_ventas_mes']:.2f}"
        )
        self.tarjetas["ganancia_mes"].configure(
            text=f"${metricas['ganancia_mes']:.2f}"
        )
