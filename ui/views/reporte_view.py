from datetime import datetime
from tkinter import messagebox, filedialog
import customtkinter as ctk
from services.reporte_service import ReporteService
from ui.theme import (
    COLOR_BG_CARD,
    COLOR_SIDEBAR_BTN_HOVER,
    COLOR_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_SUCCESS,
)


class ReporteFrame(ctk.CTkFrame):
    """Vista de exportación de reporte mensual en PDF con costos históricos exactos."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.reporte_service = ReporteService()

        titulo = ctk.CTkLabel(
            self,
            text="Reportes y Corte Mensual",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        )
        titulo.pack(padx=30, pady=(35, 10), anchor="w")

        descripcion = ctk.CTkLabel(
            self,
            text=(
                "Genera un reporte financiero en PDF con todas las ventas del mes actual.\n"
                "Utiliza el costo histórico exacto registrado en cada transacción."
            ),
            justify="left",
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=14),
        )
        descripcion.pack(padx=30, pady=(0, 25), anchor="w")

        frame_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=15)
        frame_card.pack(padx=30, pady=10, fill="x")

        ctk.CTkLabel(frame_card, text="📄", font=ctk.CTkFont(size=56)).pack(
            pady=(25, 5)
        )
        ctk.CTkLabel(
            frame_card,
            text=f"Corte del mes: {datetime.now().strftime('%B %Y')}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_HIGHLIGHT,
        ).pack(pady=(0, 20))

        btn_generar = ctk.CTkButton(
            frame_card,
            text="🖨️ Generar Reporte Mensual (PDF)",
            height=50,
            corner_radius=15,
            fg_color=COLOR_SIDEBAR_BTN_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.generar_reporte,
        )
        btn_generar.pack(padx=20, pady=(0, 25))

        self.lbl_estado = ctk.CTkLabel(self, text="", text_color=COLOR_TEXT_MUTED)
        self.lbl_estado.pack(padx=30, pady=10, anchor="w")

    def generar_reporte(self):
        confirmar = messagebox.askyesno(
            "Confirmar generación",
            "¿Deseas generar el reporte PDF de ventas y ganancias del mes actual?",
        )
        if not confirmar:
            return

        mes_actual = datetime.now().strftime("%m_%Y")
        ruta = filedialog.asksaveasfilename(
            title="Guardar reporte como...",
            defaultextension=".pdf",
            initialfile=f"Corte_Papeleria_{mes_actual}.pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
        )
        if not ruta:
            return

        resultado = self.app.ejecutar_seguro(
            self.reporte_service.generar_reporte_pdf, ruta
        )
        if resultado:
            self.lbl_estado.configure(
                text=f"✅ Reporte guardado en: {resultado}", text_color=COLOR_SUCCESS
            )
            messagebox.showinfo(
                "Éxito", f"El documento se guardó correctamente.\n\nRuta: {resultado}"
            )
