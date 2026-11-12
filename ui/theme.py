from tkinter import ttk
import customtkinter as ctk

# Paleta de Colores Modo Oscuro (Conservada del diseño original)
COLOR_SIDEBAR = "#1D1E33"            # Azul oscuro profundo (Sidebar)
COLOR_BG_MAIN = "#151626"            # Azul noche profundo (Fondo principal)
COLOR_BG_CARD = "#24263E"            # Azul grisáceo oscuro (Tarjetas y tablas)
COLOR_PRIMARY_BTN = "#393B6E"        # Azul medio (Botones primarios y cabeceras)
COLOR_SIDEBAR_BTN_HOVER = "#7A5C96"  # Morado medio (Hover y acciones secundarias)
COLOR_ACCENT = "#AA789F"             # Malva (Selección activa y acentos)
COLOR_HIGHLIGHT = "#F0B4B6"          # Rosa suave (Totales y ganancias)
COLOR_TEXT_LIGHT = "#EBEBEB"         # Blanco suave para lectura cómoda
COLOR_TEXT_MUTED = "#AAB7B8"         # Gris claro para etiquetas secundarias
COLOR_SUCCESS = "#27AE60"            # Verde esmeralda (Cobro y confirmaciones)
COLOR_WARNING = "#D68910"            # Ámbar (Alertas de stock)
COLOR_DANGER = "#A93226"             # Rojo oscuro (Salir / Errores)


def inicializar_tema():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")


def configurar_estilo_treeview():
    """Configura el estilo visual de las tablas ttk.Treeview en modo oscuro."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Custom.Treeview",
        background=COLOR_BG_CARD,
        foreground=COLOR_TEXT_LIGHT,
        fieldbackground=COLOR_BG_CARD,
        rowheight=32,
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Custom.Treeview.Heading",
        background=COLOR_PRIMARY_BTN,
        foreground="#FFFFFF",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        padding=6,
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", COLOR_ACCENT)],
        foreground=[("selected", "#FFFFFF")],
    )
