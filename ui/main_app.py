from tkinter import messagebox
import customtkinter as ctk
from database.connection import verificar_esquema_inicial
from ui.theme import (
    inicializar_tema,
    configurar_estilo_treeview,
    COLOR_SIDEBAR,
    COLOR_BG_MAIN,
    COLOR_SIDEBAR_BTN_HOVER,
    COLOR_ACCENT,
    COLOR_HIGHLIGHT,
    COLOR_TEXT_MUTED,
    COLOR_DANGER,
)
from ui.login_view import LoginWindow
from ui.views.dashboard_view import DashboardFrame
from ui.views.inventario_view import InventarioFrame
from ui.views.pos_view import PosFrame
from ui.views.historial_view import HistorialFrame
from ui.views.reporte_view import ReporteFrame


class MainApp(ctk.CTk):
    """Ventana principal del sistema POS con control de sesión y navegación limpia."""

    def __init__(self):
        super().__init__()
        inicializar_tema()
        configurar_estilo_treeview()

        self.title("Sistema de Gestión - Papelería POS (3NF)")
        self.geometry("1220x720")
        self.minsize(1040, 620)
        self.configure(fg_color=COLOR_BG_MAIN)

        self.usuario_actual = {
            "id": None,
            "username": "Invitado",
            "nombre_completo": "Sin sesión",
            "rol_nombre": "Cajero",
        }
        self.carrito = []
        self.vistas = {}
        self.botones_nav = {}

        # Ocultar ventana principal hasta autenticar
        self.withdraw()

        if not self._verificar_bd():
            self.destroy()
            return

        self._abrir_login()

    def _verificar_bd(self) -> bool:
        try:
            verificar_esquema_inicial()
            return True
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", str(e))
            return False

    def _abrir_login(self):
        LoginWindow(self, on_login_success=self._on_login_exitoso)

    def _on_login_exitoso(self, datos_usuario: dict):
        self.usuario_actual = datos_usuario
        self._inicializar_layout()
        self.deiconify()
        self.mostrar_vista("ventas")

    def _inicializar_layout(self):
        for child in self.winfo_children():
            if not isinstance(child, LoginWindow):
                child.destroy()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._crear_sidebar()
        self._crear_contenedor_vistas()

        # Atajos globales de teclado
        self.bind("<F12>", lambda e: self.vistas["ventas"].procesar_venta())

    def _crear_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0, fg_color=COLOR_SIDEBAR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        titulo = ctk.CTkLabel(
            self.sidebar,
            text="✏️ Papelería POS",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white",
            justify="left",
        )
        titulo.grid(row=0, column=0, padx=20, pady=(30, 5), sticky="w")

        info_usuario = (
            f"👤 {self.usuario_actual['nombre_completo']}\n"
            f"Rol: {self.usuario_actual['rol_nombre']}"
        )
        lbl_user = ctk.CTkLabel(
            self.sidebar,
            text=info_usuario,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_HIGHLIGHT,
            justify="left",
        )
        lbl_user.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        botones = [
            ("📊  Resumen", "dashboard"),
            ("🛒  Punto de Venta", "ventas"),
            ("📓  Inventario", "productos"),
            ("📜  Registro", "historial"),
            ("📎  Reportes", "reporte"),
        ]

        self.botones_nav = {}
        for i, (texto, clave) in enumerate(botones, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=texto,
                anchor="w",
                corner_radius=15,
                fg_color="transparent",
                hover_color=COLOR_SIDEBAR_BTN_HOVER,
                text_color="white",
                font=ctk.CTkFont(size=14),
                height=45,
                command=lambda k=clave: self.mostrar_vista(k),
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.botones_nav[clave] = btn

        btn_salir = ctk.CTkButton(
            self.sidebar,
            text="🚪  Salir del Sistema",
            anchor="w",
            corner_radius=15,
            fg_color=COLOR_DANGER,
            hover_color="#7B241C",
            text_color="white",
            font=ctk.CTkFont(size=14),
            height=45,
            command=self.destroy,
        )
        btn_salir.grid(row=9, column=0, padx=15, pady=(4, 20), sticky="sew")

    def _crear_contenedor_vistas(self):
        self.contenedor = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.contenedor.grid(row=0, column=1, sticky="nsew")
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

        self.vistas = {
            "dashboard": DashboardFrame(self.contenedor, self),
            "productos": InventarioFrame(self.contenedor, self),
            "ventas": PosFrame(self.contenedor, self),
            "historial": HistorialFrame(self.contenedor, self),
            "reporte": ReporteFrame(self.contenedor, self),
        }

        for vista in self.vistas.values():
            vista.grid(row=0, column=0, sticky="nsew")

    def mostrar_vista(self, clave: str):
        for k, btn in self.botones_nav.items():
            btn.configure(fg_color=COLOR_ACCENT if k == clave else "transparent")

        vista = self.vistas[clave]
        vista.tkraise()
        if hasattr(vista, "on_show"):
            vista.on_show()

    def ejecutar_seguro(self, funcion, *args, mensaje_exito=None, **kwargs):
        try:
            resultado = funcion(*args, **kwargs)
            if mensaje_exito:
                messagebox.showinfo("Éxito", mensaje_exito)
            return resultado
        except Exception as e:
            messagebox.showerror("Operación no completada", str(e))
            return None
