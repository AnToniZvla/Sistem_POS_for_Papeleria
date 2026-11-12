# Sistema de Gestión - Papelería ✏️📊

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-1F6AA5?style=for-the-badge)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![ReportLab](https://img.shields.io/badge/PDF-ReportLab-D9383A?style=for-the-badge)

Aplicación de escritorio moderna desarrollada en Python para la administración integral de una papelería. Centraliza el control de inventario, agiliza el cobro en mostrador mediante un **Punto de Venta (POS)** compatible con lectores de códigos de barras, presenta métricas clave en tiempo real y exporta reportes ejecutivos en formato PDF.

---

## ✨ Características Principales

- **🛒 Punto de Venta (POS) Dinámico:**
  - Soporte nativo *plug-and-play* para **lectores de códigos de barras (USB / Bluetooth en modo teclado HID)**.
  - Búsqueda rápida por código de barras o nombre del producto.
  - Cálculo automático de subtotales, totales, cambio y descuento inmediato de existencias al confirmar cada venta.
- **📦 Gestión Visual de Inventario:**
  - Registro único por producto vinculando su código de barras, nombre, precio de compra, precio de venta y stock inicial.
  - Resurtido ágil de mercancía: basta con escanear un artículo existente para sumar nuevas unidades al inventario sin volver a darlo de alta.
  - Visualización clara de existencias disponibles y alertas de stock bajo.
- **📈 Métricas y Dashboard en Tiempo Real:**
  - Consulta instantánea de ingresos, volumen de ventas, productos con mayor rotación y valoración general del inventario.
- **📄 Reportes Ejecutivos en PDF:**
  - Generación automatizada de reportes de ventas, movimientos e inventario listos para imprimir o archivar mediante **ReportLab**.
- **🎨 Interfaz Moderna en Modo Oscuro:**
  - Diseñada con **CustomTkinter** para ofrecer una experiencia fluida, limpia y cómoda durante jornadas prolongadas en mostrador.

---

## 🛠️ Tecnologías y Librerías

- **[Python 3.10+](https://www.python.org/):** Lenguaje principal de desarrollo.
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter):** Framework gráfico moderno basado en Tkinter con soporte nativo para temas oscuros.
- **[SQLite](https://www.sqlite.org/):** Motor de base de datos relacional local, ligero y autocontenido (no requiere instalar servidores externos).
- **[ReportLab](https://www.reportlab.com/):** Librería para la maquetación y exportación programática de documentos y reportes en PDF.

---

## 🚀 Guía de Instalación y Ejecución (Windows)

### 1. Requisitos Previos
Asegúrate de tener instalado **Python 3.10 o superior** en tu equipo. Durante la instalación, marca obligatoriamente la casilla **"Add Python to PATH"**.

### 2. Clonar el Repositorio
Abre una terminal (**CMD** o **PowerShell**), ubícate en la carpeta donde deseas guardar el proyecto y ejecuta:

```cmd
git clone [https://github.com/AnToniZvla/Database.git](https://github.com/AnToniZvla/Database.git)
cd Database