from tkinter import messagebox
import customtkinter as ctk
from services.auth_service import AuthService
from ui.theme import (
    COLOR_BG_MAIN,
    COLOR_BG_CARD,
    COLOR_PRIMARY_BTN,
    COLOR_SIDEBAR_BTN_HOVER,
    COLOR_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
)


class LoginWindow(ctk.CTkToplevel):
    """
    Ventana modal de inicio de sesión.
    Si la tabla `usuarios` está vacía, activa automáticamente el modo de creación
    del primer usuario Administrador.
    """

    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.auth_service = AuthService()
        self.modo_registro_inicial = False

        self.title("Acceso al Sistema - Papelería POS")
        self.geometry("440x520")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG_MAIN)

        self.protocol("WM_DELETE_WINDOW", self._cerrar_app)

        self.card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=18)
        self.card.pack(fill="both", expand=True, padx=30, pady=30)

        self._construir_interfaz()

    def _construir_interfaz(self):
        for widget in self.card.winfo_children():
            widget.destroy()

        try:
            self.modo_registro_inicial = (
                self.auth_service.requiere_configuracion_inicial()
            )
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", str(e))
            self._cerrar_app()
            return

        icono_lbl = ctk.CTkLabel(
            self.card,
            text="🔐" if not self.modo_registro_inicial else "🛡️",
            font=ctk.CTkFont(size=42),
        )
        icono_lbl.pack(pady=(25, 5))

        titulo_texto = (
            "Iniciar Sesión"
            if not self.modo_registro_inicial
            else "Crear Primer Administrador"
        )
        ctk.CTkLabel(
            self.card,
            text=titulo_texto,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXT_LIGHT,
        ).pack(pady=(0, 4))

        subtitulo = (
            "Ingresa tus credenciales para acceder al POS"
            if not self.modo_registro_inicial
            else "No hay usuarios registrados. Configura la cuenta Admin."
        )
        ctk.CTkLabel(
            self.card,
            text=subtitulo,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_HIGHLIGHT if self.modo_registro_inicial else COLOR_TEXT_MUTED,
            wraplength=340,
        ).pack(pady=(0, 18))

        # Usuario
        ctk.CTkLabel(
            self.card, text="Usuario:", text_color=COLOR_TEXT_LIGHT
        ).pack(padx=30, anchor="w")
        self.entry_user = ctk.CTkEntry(
            self.card,
            placeholder_text="Ej. admin",
            height=38,
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_user.pack(padx=30, pady=(2, 12), fill="x")

        if self.modo_registro_inicial:
            ctk.CTkLabel(
                self.card, text="Nombre Completo:", text_color=COLOR_TEXT_LIGHT
            ).pack(padx=30, anchor="w")
            self.entry_nombre = ctk.CTkEntry(
                self.card,
                placeholder_text="Ej. Administrador General",
                height=38,
                corner_radius=10,
                fg_color=COLOR_BG_MAIN,
                border_width=0,
            )
            self.entry_nombre.pack(padx=30, pady=(2, 12), fill="x")

        # Contraseña
        ctk.CTkLabel(
            self.card, text="Contraseña:", text_color=COLOR_TEXT_LIGHT
        ).pack(padx=30, anchor="w")
        self.entry_pass = ctk.CTkEntry(
            self.card,
            placeholder_text="••••••••",
            show="•",
            height=38,
            corner_radius=10,
            fg_color=COLOR_BG_MAIN,
            border_width=0,
        )
        self.entry_pass.pack(padx=30, pady=(2, 12), fill="x")

        if self.modo_registro_inicial:
            ctk.CTkLabel(
                self.card, text="Confirmar Contraseña:", text_color=COLOR_TEXT_LIGHT
            ).pack(padx=30, anchor="w")
            self.entry_confirm = ctk.CTkEntry(
                self.card,
                placeholder_text="••••••••",
                show="•",
                height=38,
                corner_radius=10,
                fg_color=COLOR_BG_MAIN,
                border_width=0,
            )
            self.entry_confirm.pack(padx=30, pady=(2, 16), fill="x")
            self.entry_confirm.bind("<Return>", lambda e: self._procesar_submit())
        else:
            self.entry_pass.bind("<Return>", lambda e: self._procesar_submit())

        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus_set())

        texto_btn = (
            "Ingresar al Sistema"
            if not self.modo_registro_inicial
            else "Registrar Admin e Iniciar"
        )
        btn_submit = ctk.CTkButton(
            self.card,
            text=texto_btn,
            height=42,
            corner_radius=12,
            fg_color=COLOR_SIDEBAR_BTN_HOVER if self.modo_registro_inicial else COLOR_PRIMARY_BTN,
            hover_color=COLOR_SIDEBAR_BTN_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._procesar_submit,
        )
        btn_submit.pack(padx=30, pady=(10, 20), fill="x")

        self.after(150, self.entry_user.focus_set)

    def _procesar_submit(self):
        try:
            if self.modo_registro_inicial:
                usuario = self.auth_service.registrar_primer_admin(
                    username=self.entry_user.get(),
                    nombre_completo=self.entry_nombre.get(),
                    password=self.entry_pass.get(),
                    confirmar_password=self.entry_confirm.get(),
                )
                messagebox.showinfo(
                    "Administrador Creado",
                    f"Bienvenido, {usuario['nombre_completo']}.\n"
                    "Tu cuenta Admin ha sido protegida con Argon2id.",
                )
            else:
                usuario = self.auth_service.autenticar(
                    username=self.entry_user.get(),
                    password=self.entry_pass.get(),
                )

            self.on_login_success(usuario)
            self.destroy()
        except Exception as e:
            messagebox.showwarning("Autenticación", str(e))

    def _cerrar_app(self):
        self.master.destroy()
