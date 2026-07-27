"""
============================================================
 LEAD SCRAPER — Aplicación de escritorio (interfaz gráfica)
============================================================
Envuelve el motor de scraping (scraper_google_maps.py) en una
ventana. Pensada para compilarse a .exe con PyInstaller.

Ejecutar en desarrollo:
    python app.py
"""

import os
import sys
import queue
import logging
import threading
import asyncio

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

import scraper_google_maps as motor

try:
    from version import __version__ as VERSION
except Exception:
    VERSION = "dev"

APP_NOMBRE = "Lead Scraper — Google Maps"


def recurso(nombre):
    """Ruta a un archivo incluido, funciona en desarrollo y dentro del .exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


# ---------- puente entre el logging del motor y la ventana ----------
class ColaLogHandler(logging.Handler):
    def __init__(self, cola):
        super().__init__()
        self.cola = cola

    def emit(self, record):
        self.cola.put(self.format(record))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NOMBRE}  ·  v{VERSION}")
        self.geometry("860x680")
        self.minsize(760, 600)

        # Ícono de la ventana (.ico en Windows, .png como respaldo)
        try:
            self.iconbitmap(recurso("icono.ico"))
        except Exception:
            try:
                self._icono = tk.PhotoImage(file=recurso("icono.png"))
                self.iconphoto(True, self._icono)
            except Exception:
                pass

        self.cola_log = queue.Queue()
        self.hilo = None

        self._construir_ui()
        self._configurar_logging()
        self.after(150, self._vaciar_cola_log)
        self._actualizar_estado_navegador()

    # ---------------- interfaz ----------------
    def _construir_ui(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except Exception:
            pass

        cont = ttk.Frame(self, padding=12)
        cont.pack(fill="both", expand=True)

        cab = ttk.Frame(cont)
        cab.pack(fill="x")
        ttk.Label(cab, text="Lead Scraper — Google Maps",
                  font=("Segoe UI", 15, "bold")).pack(side="left")
        ttk.Label(cab, text=f"v{VERSION}", foreground="#2563EB",
                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=(8, 0))
        ttk.Label(cont, text="Extrae leads de negocios por nichos y zonas.",
                  foreground="#555").pack(anchor="w", pady=(0, 8))

        cols = ttk.Frame(cont)
        cols.pack(fill="both", expand=True)
        izq = ttk.Frame(cols)
        izq.pack(side="left", fill="both", expand=True, padx=(0, 8))
        der = ttk.Frame(cols)
        der.pack(side="left", fill="y")

        # --- Nichos ---
        ttk.Label(izq, text="Nichos  (sinónimos con | para captar más):").pack(
            anchor="w")
        self.txt_nichos = tk.Text(izq, height=6, wrap="none")
        self.txt_nichos.pack(fill="x")
        self.txt_nichos.insert("1.0",
            "gimnasios | gym | crossfit\n"
            "restaurantes | comidas rápidas\n"
            "peluquerías | salón de belleza | barbería\n"
            "ferreterías")

        # --- Zonas ---
        ttk.Label(izq, text="Zonas  (Nombre, lat, lng — una por línea):").pack(
            anchor="w", pady=(8, 0))
        self.txt_zonas = tk.Text(izq, height=5, wrap="none")
        self.txt_zonas.pack(fill="x")
        self.txt_zonas.insert("1.0",
            "Ibagué Centro, 4.4389, -75.2322\n"
            "Ibagué Norte, 4.4650, -75.2100\n"
            "Ibagué Sur, 4.4100, -75.1800")

        # --- Cuadrícula automática ---
        self.var_grilla = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="Usar cuadrícula automática (ignora las zonas de arriba)",
                        variable=self.var_grilla,
                        command=self._toggle_grilla).pack(anchor="w", pady=(6, 0))
        self.frm_grilla = ttk.Frame(izq)
        self.frm_grilla.pack(fill="x")
        ttk.Label(self.frm_grilla, text="Centro lat:").grid(row=0, column=0, sticky="w")
        self.ent_clat = ttk.Entry(self.frm_grilla, width=11)
        self.ent_clat.insert(0, "4.4389"); self.ent_clat.grid(row=0, column=1, padx=2)
        ttk.Label(self.frm_grilla, text="lng:").grid(row=0, column=2, sticky="w")
        self.ent_clng = ttk.Entry(self.frm_grilla, width=11)
        self.ent_clng.insert(0, "-75.2322"); self.ent_clng.grid(row=0, column=3, padx=2)
        ttk.Label(self.frm_grilla, text="Radio km:").grid(row=1, column=0, sticky="w")
        self.ent_radio = ttk.Entry(self.frm_grilla, width=11)
        self.ent_radio.insert(0, "6"); self.ent_radio.grid(row=1, column=1, padx=2)
        ttk.Label(self.frm_grilla, text="Malla:").grid(row=1, column=2, sticky="w")
        self.spn_grid = ttk.Spinbox(self.frm_grilla, from_=2, to=6, width=4)
        self.spn_grid.set(3); self.spn_grid.grid(row=1, column=3, sticky="w", padx=2)
        self._toggle_grilla()

        # --- Parámetros (columna derecha) ---
        cajita = ttk.LabelFrame(der, text="Parámetros", padding=10)
        cajita.pack(fill="x")

        def fila(lbl):
            f = ttk.Frame(cajita)
            f.pack(fill="x", pady=3)
            ttk.Label(f, text=lbl, width=16).pack(side="left")
            return f

        f = fila("Zoom (radio):")
        self.cmb_zoom = ttk.Combobox(f, values=["12z", "13z", "14z", "15z"],
                                     width=8, state="readonly")
        self.cmb_zoom.set("13z")
        self.cmb_zoom.pack(side="left")

        f = fila("Leads por nicho:")
        self.spn_target = ttk.Spinbox(f, from_=5, to=1000, width=8)
        self.spn_target.set(100)
        self.spn_target.pack(side="left")

        f = fila("Concurrencia:")
        self.spn_conc = ttk.Spinbox(f, from_=1, to=6, width=8)
        self.spn_conc.set(2)
        self.spn_conc.pack(side="left")

        self.var_headless = tk.BooleanVar(value=False)
        ttk.Checkbutton(cajita, text="Ocultar navegador (headless)",
                        variable=self.var_headless).pack(anchor="w", pady=(6, 0))

        self.var_email = tk.BooleanVar(value=True)
        ttk.Checkbutton(cajita, text="Extraer email de la web",
                        variable=self.var_email).pack(anchor="w")

        self.var_redes = tk.BooleanVar(value=True)
        ttk.Checkbutton(cajita, text="Extraer WhatsApp / Instagram / Facebook",
                        variable=self.var_redes).pack(anchor="w")

        # --- Carpeta de salida ---
        cajita2 = ttk.LabelFrame(der, text="Guardar resultados en", padding=10)
        cajita2.pack(fill="x", pady=(10, 0))
        self.var_salida = tk.StringVar(
            value=os.path.join(motor.dir_datos(), "resultados"))
        ttk.Entry(cajita2, textvariable=self.var_salida, width=26).pack(
            side="left", fill="x", expand=True)
        ttk.Button(cajita2, text="...", width=3,
                   command=self._elegir_carpeta).pack(side="left", padx=(4, 0))

        # --- Botones de acción ---
        acciones = ttk.Frame(der)
        acciones.pack(fill="x", pady=(12, 0))
        self.btn_navegador = ttk.Button(acciones, text="Instalar navegador",
                                        command=self._instalar_navegador)
        self.btn_navegador.pack(fill="x")
        self.btn_iniciar = ttk.Button(acciones, text="▶  Iniciar",
                                      command=self._iniciar)
        self.btn_iniciar.pack(fill="x", pady=(6, 0))
        self.btn_detener = ttk.Button(acciones, text="■  Detener",
                                      command=self._detener, state="disabled")
        self.btn_detener.pack(fill="x", pady=(6, 0))

        # --- Log ---
        ttk.Label(cont, text="Registro:").pack(anchor="w", pady=(10, 0))
        self.log = scrolledtext.ScrolledText(cont, height=12, state="disabled",
                                             font=("Consolas", 9), bg="#111",
                                             fg="#ddd")
        self.log.pack(fill="both", expand=True)

        self.estado = ttk.Label(cont, text="", foreground="#777")
        self.estado.pack(anchor="w", pady=(4, 0))

    # ---------------- logging ----------------
    def _configurar_logging(self):
        h = ColaLogHandler(self.cola_log)
        h.setFormatter(logging.Formatter("%(message)s"))
        lg = logging.getLogger("scraper")
        lg.setLevel(logging.INFO)
        lg.addHandler(h)
        # también a archivo
        try:
            fh = logging.FileHandler(
                os.path.join(motor.dir_datos(), "scraper.log"), encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
            lg.addHandler(fh)
        except Exception:
            pass

    def _log_ui(self, texto):
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _vaciar_cola_log(self):
        try:
            while True:
                self._log_ui(self.cola_log.get_nowait())
        except queue.Empty:
            pass
        self.after(150, self._vaciar_cola_log)

    # ---------------- acciones ----------------
    def _elegir_carpeta(self):
        d = filedialog.askdirectory()
        if d:
            self.var_salida.set(d)

    def _toggle_grilla(self):
        estado = "normal" if self.var_grilla.get() else "disabled"
        for hijo in self.frm_grilla.winfo_children():
            try:
                hijo.configure(state=estado)
            except Exception:
                pass

    def _actualizar_estado_navegador(self):
        if motor.navegador_instalado():
            self.btn_navegador.configure(text="✓ Navegador listo", state="disabled")
            self.estado.configure(text="Navegador instalado. Listo para usar.")
        else:
            self.btn_navegador.configure(text="Instalar navegador (1ª vez)",
                                         state="normal")
            self.estado.configure(
                text="Falta instalar el navegador. Pulsa 'Instalar navegador'.")

    def _instalar_navegador(self):
        self.btn_navegador.configure(state="disabled")

        def tarea():
            try:
                motor.instalar_navegador(self.cola_log.put)
            except Exception as e:
                self.cola_log.put(f"Error instalando navegador: {e}")
            self.after(0, self._actualizar_estado_navegador)

        threading.Thread(target=tarea, daemon=True).start()

    def _parse_config(self):
        nichos = [l.strip() for l in
                  self.txt_nichos.get("1.0", "end").splitlines() if l.strip()]
        if not nichos:
            raise ValueError("Agrega al menos un nicho.")

        busqueda = {
            "nichos": nichos,
            "zoom": self.cmb_zoom.get(),
            "target_por_nicho": int(self.spn_target.get()),
        }

        if self.var_grilla.get():
            try:
                busqueda["grilla"] = {
                    "usar": True,
                    "centro_lat": float(self.ent_clat.get()),
                    "centro_lng": float(self.ent_clng.get()),
                    "radio_km": float(self.ent_radio.get()),
                    "filas": int(self.spn_grid.get()),
                    "columnas": int(self.spn_grid.get()),
                }
            except ValueError:
                raise ValueError("Revisa los valores de la cuadrícula "
                                 "(centro, radio y malla deben ser números).")
            busqueda["zonas"] = []
        else:
            zonas = []
            for l in self.txt_zonas.get("1.0", "end").splitlines():
                l = l.strip()
                if not l:
                    continue
                partes = [p.strip() for p in l.split(",")]
                if len(partes) < 3:
                    raise ValueError(f"Zona mal escrita: '{l}'  "
                                     f"(usa: Nombre, lat, lng)")
                zonas.append({"nombre": partes[0],
                              "lat": float(partes[1]), "lng": float(partes[2])})
            if not zonas:
                raise ValueError("Agrega al menos una zona o activa la cuadrícula.")
            busqueda["zonas"] = zonas
            busqueda["grilla"] = {"usar": False}

        carpeta = self.var_salida.get().strip() or motor.dir_datos()
        os.makedirs(carpeta, exist_ok=True)
        return {
            "busqueda": busqueda,
            "rendimiento": {
                "concurrencia": int(self.spn_conc.get()),
                "headless": self.var_headless.get(),
                "reintentos": 3, "descanso_cada": 40, "enfriamiento_seg": 180,
            },
            "extraccion": {
                "extraer_email": self.var_email.get(),
                "extraer_redes": self.var_redes.get(),
                "timeout_web_seg": 10,
            },
            "salida": {
                "archivo_excel": os.path.join(carpeta, "leads.xlsx"),
                "carpeta_temp": os.path.join(carpeta, "temp_csv"),
            },
        }

    def _iniciar(self):
        if not motor.navegador_instalado():
            messagebox.showwarning(
                APP_NOMBRE,
                "Primero instala el navegador (botón 'Instalar navegador').")
            return
        try:
            cfg = self._parse_config()
        except ValueError as e:
            messagebox.showerror(APP_NOMBRE, str(e))
            return

        motor.PARAR.clear()
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self.estado.configure(text="Ejecutando...")
        self._salida_excel = cfg["salida"]["archivo_excel"]

        def tarea():
            try:
                asyncio.run(motor.run(cfg))
            except Exception as e:
                self.cola_log.put(f"ERROR: {e}")
            self.after(0, self._al_terminar)

        self.hilo = threading.Thread(target=tarea, daemon=True)
        self.hilo.start()

    def _detener(self):
        motor.PARAR.set()
        self.cola_log.put("Deteniendo... (terminando tareas en curso)")
        self.btn_detener.configure(state="disabled")

    def _al_terminar(self):
        self.btn_iniciar.configure(state="normal")
        self.btn_detener.configure(state="disabled")
        self.estado.configure(text="Terminado.")
        if getattr(self, "_salida_excel", None) and os.path.exists(self._salida_excel):
            if messagebox.askyesno(APP_NOMBRE,
                                   "Proceso terminado.\n¿Abrir el archivo Excel?"):
                try:
                    if sys.platform.startswith("win"):
                        os.startfile(self._salida_excel)  # noqa
                    elif sys.platform == "darwin":
                        os.system(f'open "{self._salida_excel}"')
                    else:
                        os.system(f'xdg-open "{self._salida_excel}"')
                except Exception:
                    pass


if __name__ == "__main__":
    App().mainloop()
