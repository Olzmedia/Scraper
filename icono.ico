"""
============================================================
 LEAD SCRAPER — App de escritorio con dashboard HTML
============================================================
Interfaz web moderna dentro de una ventana nativa (PyWebView).
Soporta múltiples PERFILES, panel con gráficas, exportador con ruta
configurable, y modo prudente / sesión persistente (anti-captcha).
"""
import os
import sys
import logging
import threading
import asyncio

import scraper_google_maps as motor
import perfiles as pf
import plantillas

try:
    from version import __version__ as VERSION
except Exception:
    VERSION = "dev"


def recurso(nombre):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


class BufferLog(logging.Handler):
    def __init__(self, buffer):
        super().__init__()
        self.buffer = buffer

    def emit(self, record):
        self.buffer.append(self.format(record))


VISIBLES = ["nombre", "categoria", "score", "telefono", "whatsapp", "email",
            "sitio_web", "direccion", "zona"]


def _stats_de(leads):
    total = len(leads)
    por_nicho, por_zona = {}, {}
    score = {"Alto (≥5)": 0, "Medio (3-5)": 0, "Bajo (<3)": 0}
    cob = {"WhatsApp": 0, "Email válido": 0, "Con web": 0, "Sin web": 0, "Teléfono": 0}
    for l in leads:
        n = l.get("_nicho") or l.get("categoria") or "otros"
        por_nicho[n] = por_nicho.get(n, 0) + 1
        z = l.get("zona") or "—"
        por_zona[z] = por_zona.get(z, 0) + 1
        try:
            sc = float(l.get("score") or 0)
        except Exception:
            sc = 0
        score["Alto (≥5)" if sc >= 5 else "Medio (3-5)" if sc >= 3 else "Bajo (<3)"] += 1
        if l.get("telefono"): cob["Teléfono"] += 1
        if l.get("whatsapp"): cob["WhatsApp"] += 1
        if l.get("email_estado") == "válido": cob["Email válido"] += 1
        if l.get("sin_web"): cob["Sin web"] += 1
        else: cob["Con web"] += 1
    return {"total": total, "por_nicho": por_nicho, "por_zona": por_zona,
            "score": score, "cobertura": cob}


class Api:
    def __init__(self):
        self.log_lines = []
        self.leads = []
        self.corriendo = False
        self.hilo = None
        self.cfg_actual = None
        self._configurar_logging()
        # asegurar al menos un perfil
        if not pf.listar():
            pf.crear("Predeterminado")
        self.perfil = pf.listar()[0]
        self.leads = pf.cargar_leads(self.perfil)

    def _configurar_logging(self):
        h = BufferLog(self.log_lines)
        h.setFormatter(logging.Formatter("%(message)s"))
        lg = logging.getLogger("scraper")
        lg.setLevel(logging.INFO)
        lg.addHandler(h)
        try:
            fh = logging.FileHandler(
                os.path.join(motor.dir_datos(), "scraper.log"), encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
            lg.addHandler(fh)
        except Exception:
            pass

    # ---------- info / perfiles ----------
    def info(self):
        cfg = pf.cargar_config(self.perfil)
        return {
            "version": VERSION,
            "navegador": motor.navegador_instalado(),
            "perfiles": pf.listar(),
            "perfil": self.perfil,
            "config": cfg,
            "export_dir": cfg.get("_export_dir", ""),
            "tema": pf.cargar_tema(self.perfil),
            "foto": pf.cargar_foto(self.perfil),
        }

    def seleccionar_perfil(self, nombre):
        if nombre in pf.listar():
            self.perfil = nombre
            self.leads = pf.cargar_leads(nombre)
        c = pf.cargar_config(self.perfil)
        return {"config": c, "leads": list(self.leads),
                "export_dir": c.get("_export_dir", ""),
                "tema": pf.cargar_tema(self.perfil),
                "foto": pf.cargar_foto(self.perfil)}

    def crear_perfil(self, nombre):
        try:
            n = pf.crear(nombre)
            self.perfil = n
            self.leads = []
            return {"ok": True, "perfiles": pf.listar(), "perfil": n}
        except ValueError as e:
            return {"error": str(e)}

    def renombrar_perfil(self, nuevo):
        try:
            n = pf.renombrar(self.perfil, nuevo)
            self.perfil = n
            return {"ok": True, "perfiles": pf.listar(), "perfil": n}
        except ValueError as e:
            return {"error": str(e)}

    def borrar_perfil(self):
        pf.borrar_perfil(self.perfil)
        if not pf.listar():
            pf.crear("Predeterminado")
        self.perfil = pf.listar()[0]
        self.leads = pf.cargar_leads(self.perfil)
        return {"ok": True, "perfiles": pf.listar(), "perfil": self.perfil}

    def borrar_leads(self):
        pf.borrar_leads(self.perfil)
        self.leads = []
        self.log_lines.append(f"Leads del perfil '{self.perfil}' borrados.")
        return {"ok": True}

    def guardar_config(self, c):
        actual = pf.cargar_config(self.perfil)
        actual.update(c or {})
        pf.guardar_config(self.perfil, actual)
        return {"ok": True}

    # ---------- diálogos ----------
    def elegir_carpeta(self):
        try:
            import webview
            r = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
            if r:
                d = r[0] if isinstance(r, (list, tuple)) else r
                self.guardar_config({"_export_dir": d})
                return d
        except Exception:
            pass
        return None

    # ---------- navegador ----------
    def instalar_navegador(self):
        def tarea():
            try:
                motor.instalar_navegador(self.log_lines.append)
            except Exception as e:
                self.log_lines.append(f"Error instalando navegador: {e}")
        threading.Thread(target=tarea, daemon=True).start()
        return {"ok": True}

    # ---------- construir cfg del motor ----------
    def _construir_cfg(self, c):
        nichos = [n for n in c.get("nichos", []) if n.strip()]
        if not nichos:
            raise ValueError("Agrega al menos un nicho.")
        busqueda = {"nichos": nichos, "zoom": c.get("zoom", "14z"),
                    "target_por_nicho": int(c.get("target", 100))}
        if c.get("usar_grilla"):
            busqueda["grilla"] = {"usar": True,
                                  "centro_lat": float(c["clat"]),
                                  "centro_lng": float(c["clng"]),
                                  "radio_km": float(c["radio"]),
                                  "filas": int(c["malla"]), "columnas": int(c["malla"])}
            busqueda["zonas"] = []
        else:
            zonas = []
            for l in (c.get("zonas_txt") or "").splitlines():
                l = l.strip()
                if not l:
                    continue
                p = [x.strip() for x in l.split(",")]
                if len(p) < 3:
                    raise ValueError(f"Zona mal escrita: '{l}' (usa: Nombre, lat, lng)")
                zonas.append({"nombre": p[0], "lat": float(p[1]), "lng": float(p[2])})
            if not zonas:
                raise ValueError("Agrega al menos una zona o activa la cuadrícula.")
            busqueda["zonas"] = zonas
            busqueda["grilla"] = {"usar": False}

        user_dir = os.path.join(pf.ruta_perfil(self.perfil), "navegador") \
            if c.get("sesion_persistente", True) else None
        return {
            "busqueda": busqueda,
            "rendimiento": {"concurrencia": int(c.get("conc", 2)),
                            "headless": False, "reintentos": 3,
                            "descanso_cada": 25 if c.get("modo_prudente") else 40,
                            "enfriamiento_seg": 180,
                            "modo_prudente": bool(c.get("modo_prudente", False)),
                            "user_data_dir": user_dir},
            "extraccion": {"extraer_email": bool(c.get("email", True)),
                           "extraer_redes": bool(c.get("redes", True)),
                           "timeout_web_seg": 10},
            "salida": {"archivo_excel": pf.ruta_excel(self.perfil),
                       "carpeta_temp": pf.carpeta_temp(self.perfil)},
        }

    def iniciar(self, c):
        if self.corriendo:
            return {"error": "Ya hay un proceso en curso."}
        if not motor.navegador_instalado():
            return {"error": "Primero instala el navegador."}
        try:
            cfg = self._construir_cfg(c)
        except (ValueError, KeyError, TypeError) as e:
            return {"error": str(e)}
        # guardar la config en el perfil
        self.guardar_config(c)
        self.cfg_actual = cfg
        self.leads = pf.cargar_leads(self.perfil)  # conserva lo previo + suma nuevos
        self.log_lines.clear()
        motor.PARAR.clear()
        motor.ON_LEAD = self.leads.append
        self.corriendo = True

        def tarea():
            try:
                asyncio.run(motor.run(cfg))
            except Exception as e:
                self.log_lines.append(f"ERROR: {e}")
            finally:
                self.corriendo = False
                motor.ON_LEAD = None

        self.hilo = threading.Thread(target=tarea, daemon=True)
        self.hilo.start()
        return {"ok": True}

    def detener(self):
        motor.PARAR.set()
        self.log_lines.append("Deteniendo…")
        return {"ok": True}

    def estado(self):
        return {"corriendo": self.corriendo, "log": list(self.log_lines),
                "leads": list(self.leads), "navegador": motor.navegador_instalado()}

    def estado_ligero(self):
        """Solo contadores — mucho más liviano para el refresco cada segundo."""
        return {"corriendo": self.corriendo, "n_leads": len(self.leads),
                "n_log": len(self.log_lines), "navegador": motor.navegador_instalado()}

    def log_desde(self, idx):
        try:
            return list(self.log_lines[int(idx):])
        except Exception:
            return []

    def leads_get(self):
        return list(self.leads)

    def estadisticas(self):
        return _stats_de(self.leads)

    # ---------- plantillas de nichos ----------
    def plantillas_categorias(self):
        return plantillas.categorias()

    def plantilla_nichos(self, categoria):
        return plantillas.nichos_de(categoria)

    # ---------- tema y foto por perfil ----------
    def guardar_tema(self, tema):
        pf.guardar_tema(self.perfil, tema or {})
        return {"ok": True}

    # ---------- hoja editable ----------
    def hoja_get(self):
        h = pf.cargar_hoja(self.perfil)
        return {"ediciones": h["ediciones"], "columnas": h["columnas"],
                "eliminados": h["eliminados"]}

    def hoja_guardar(self, hoja):
        pf.guardar_hoja(self.perfil, hoja or {})
        return {"ok": True}

    def hoja_exportar(self, ruta=None):
        destino = (ruta or pf.cargar_config(self.perfil).get("_export_dir")
                   or pf.ruta_perfil(self.perfil))
        try:
            arch = pf.exportar_hoja(self.perfil, destino, VISIBLES)
            return {"ok": True, "ruta": arch}
        except Exception as e:
            self.log_lines.append(f"Error al exportar hoja: {e}")
            return {"ok": False}

    # ---------- contactados ----------
    def contactados_get(self):
        try:
            return pf.cargar_contactados(self.perfil)
        except Exception:
            return []

    def contactados_set(self, lista):
        try:
            pf.guardar_contactados(self.perfil, lista or [])
        except Exception:
            pass
        return {"ok": True}

    # ---------- plantillas de mensaje ----------
    def mensajes_get(self):
        try:
            return pf.cargar_mensajes(self.perfil)
        except Exception:
            return {}

    def mensajes_set(self, msjs):
        try:
            pf.guardar_mensajes(self.perfil, msjs or {})
        except Exception:
            pass
        return {"ok": True}

    # ---------- estado de contacto por canal ----------
    def enviados_get(self):
        try:
            return pf.cargar_enviados(self.perfil)
        except Exception:
            return {"wa": [], "email": []}

    def enviados_set(self, datos):
        try:
            pf.guardar_enviados(self.perfil, datos or {"wa": [], "email": []})
        except Exception:
            pass
        return {"ok": True}

    def guardar_foto(self, data_url):
        pf.guardar_foto(self.perfil, data_url or "")
        return {"ok": True}

    def quitar_foto(self):
        pf.quitar_foto(self.perfil)
        return {"ok": True}

    # ---------- exportar ----------
    def exportar(self, ruta=None):
        tmp = pf.carpeta_temp(self.perfil)
        if not os.path.isdir(tmp) or not os.listdir(tmp):
            return {"ok": False}
        destino_dir = (ruta or pf.cargar_config(self.perfil).get("_export_dir") or
                       pf.ruta_perfil(self.perfil))
        os.makedirs(destino_dir, exist_ok=True)
        archivo = os.path.join(destino_dir, f"leads_{pf._slug(self.perfil)}.xlsx")
        try:
            motor.construir_excel(tmp, archivo)
            return {"ok": True, "ruta": archivo}
        except Exception as e:
            self.log_lines.append(f"Error al exportar: {e}")
            return {"ok": False}


def main():
    import webview
    api = Api()
    webview.create_window(
        f"Lead Scraper  ·  v{VERSION}",
        url=recurso(os.path.join("web", "index.html")),
        js_api=api, width=1240, height=800, min_size=(1040, 680),
        background_color="#0b0f1a")
    webview.start()


if __name__ == "__main__":
    # IMPORTANTE: evita que el .exe se relance a sí mismo en bucle
    import multiprocessing
    multiprocessing.freeze_support()
    main()
