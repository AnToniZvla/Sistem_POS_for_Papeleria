import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fpdf import FPDF
from repositories.venta_repo import VentaRepository


class ReporteService:
    """Servicio de métricas de negocio, historial y exportación de PDF mensual."""

    def __init__(self):
        self._venta_repo = VentaRepository()

    def obtener_metricas_dashboard(self) -> Dict[str, Any]:
        return self._venta_repo.obtener_metricas_dashboard()

    def obtener_historial_ventas(self) -> List[Dict[str, Any]]:
        return self._venta_repo.obtener_historial_ventas()

    def generar_reporte_pdf(self, ruta_destino: Optional[str] = None) -> str:
        registros = self._venta_repo.obtener_registros_reporte_mensual()
        if not registros:
            raise ValueError(
                "No hay ventas registradas en el mes actual para generar el reporte."
            )

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        pdf.set_font("Arial", "B", 14)
        pdf.cell(
            190,
            8,
            txt="Reporte Mensual de Ventas y Ganancias (Costos Historicos 3NF)",
            ln=True,
            align="C",
        )
        pdf.set_font("Arial", size=9)
        pdf.cell(
            190,
            5,
            txt=f"Fecha de generacion: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ln=True,
            align="C",
        )
        pdf.ln(3)

        pdf.set_font("Arial", "B", 8)
        pdf.cell(15, 6, "ID Vta", border=1, align="C")
        pdf.cell(45, 6, "Producto", border=1, align="C")
        pdf.cell(12, 6, "Cant.", border=1, align="C")
        pdf.cell(20, 6, "Costo Hist.", border=1, align="C")
        pdf.cell(20, 6, "P. Venta", border=1, align="C")
        pdf.cell(24, 6, "Subt. Costo", border=1, align="C")
        pdf.cell(24, 6, "Subt. Venta", border=1, align="C")
        pdf.cell(30, 6, "Fecha", border=1, align="C")
        pdf.ln()

        pdf.set_font("Arial", size=8)
        total_costo_mes = 0.0
        total_venta_mes = 0.0

        for row in registros:
            id_venta = str(row["venta_id"])
            nombre = (
                str(row["producto"])[:22]
                .encode("latin-1", "replace")
                .decode("latin-1")
            )
            cantidad = int(row["cantidad"])
            costo_hist = float(row["precio_costo_historico"])
            precio_venta = float(row["precio_venta_unitario"])
            subt_costo = float(row["subtotal_costo"])
            subt_venta = float(row["subtotal_venta"])
            fecha_val = row["fecha"]
            fecha_str = (
                fecha_val.strftime("%Y-%m-%d %H:%M")
                if hasattr(fecha_val, "strftime")
                else str(fecha_val)[:16]
            )

            pdf.cell(15, 6, id_venta, border=1, align="C")
            pdf.cell(45, 6, nombre, border=1)
            pdf.cell(12, 6, str(cantidad), border=1, align="C")
            pdf.cell(20, 6, f"${costo_hist:.2f}", border=1, align="R")
            pdf.cell(20, 6, f"${precio_venta:.2f}", border=1, align="R")
            pdf.cell(24, 6, f"${subt_costo:.2f}", border=1, align="R")
            pdf.cell(24, 6, f"${subt_venta:.2f}", border=1, align="R")
            pdf.cell(30, 6, fecha_str, border=1, align="C")
            pdf.ln()

            total_costo_mes += subt_costo
            total_venta_mes += subt_venta

        ganancia_total = round(total_venta_mes - total_costo_mes, 2)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(130, 6, "COSTO HISTORICO TOTAL DE LO VENDIDO:", border=1, align="R")
        pdf.cell(60, 6, f"${total_costo_mes:.2f}", border=1, align="C")
        pdf.ln()
        pdf.cell(130, 6, "INGRESO BRUTO POR VENTAS DEL MES:", border=1, align="R")
        pdf.cell(60, 6, f"${total_venta_mes:.2f}", border=1, align="C")
        pdf.ln()

        pdf.set_fill_color(220, 235, 255)
        pdf.cell(130, 6, "GANANCIA NETA DEL MES:", border=1, align="R", fill=True)
        pdf.cell(60, 6, f"${ganancia_total:.2f}", border=1, align="C", fill=True)

        if ruta_destino:
            nombre_archivo = ruta_destino
        else:
            mes_actual = datetime.now().strftime("%m_%Y")
            nombre_archivo = os.path.join(
                os.getcwd(), f"reporte_ventas_{mes_actual}.pdf"
            )

        pdf.output(nombre_archivo)
        return nombre_archivo
