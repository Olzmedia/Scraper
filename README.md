# Lead Scraper · Google Maps

Aplicación de escritorio con **dashboard moderno** que extrae leads de negocios
desde Google Maps, los **verifica** y los muestra en una tabla interactiva
priorizada por calidad. Se compila a un `.exe` para Windows.

No usa la API de Google Places.

![interfaz: dashboard oscuro con panel de configuración, KPIs y tabla de leads]

---

## Qué hace

Por cada negocio obtiene y **verifica**: nombre, categoría, teléfono (+57),
**WhatsApp** (validado), email (**con verificación MX**), Instagram, Facebook,
sitio web (marca si está **activo o caído**), estado de **actividad** del
negocio (según reseñas), calificación, dirección, horario y coordenadas.

Cada lead recibe un **score** y la tabla queda ordenada del mejor al peor.

Funciones de captación:
- **Sinónimos por nicho** (`gimnasios | gym | crossfit`) para captar más.
- **WhatsApp e Instagram/Facebook** además de email.
- **Cuadrícula automática** (centro + radio) para cobertura sistemática.
- **Verificación de contactos** (email con registro MX, WhatsApp con formato).
- **Dashboard en vivo**: KPIs, tabla con filtros (por nicho, con WhatsApp,
  email válido, sin web, pendientes), marcar contactados, exportar a Excel.

---

## Archivos del proyecto

| Archivo | Para qué sirve |
|---------|----------------|
| `app_web.py` | La aplicación (dashboard) — **entrada principal** |
| `web/index.html` | La interfaz visual (HTML/CSS/JS) |
| `scraper_google_maps.py` | Motor de scraping |
| `verificacion.py` | Verificación y enriquecimiento de leads |
| `version.py` | Número de versión (una sola fuente) |
| `LeadScraper.spec` | Receta de compilación PyInstaller |
| `.github/workflows/build.yml` | Compila el `.exe` en GitHub |
| `config.yaml` | Config para uso por consola (opcional) |
| `requirements.txt`, `icono.ico`, `icono.png`, `.gitignore` | Apoyo |

---

## Opción A — Compilar el `.exe` en GitHub (recomendado)

1. Crea un repositorio y sube **todos** los archivos (respeta la carpeta
   `.github/workflows/` y la carpeta `web/`).
2. Pestaña **Actions** → *Compilar EXE* → **Run workflow**.
   (O sube un tag `v2.0.0` para crear además un *Release* con el `.exe`.)
3. Descarga el `.exe` desde **Actions → Artifacts** (o **Releases**).

El navegador Chromium **se descarga solo la primera vez** desde la app, así que
el `.exe` queda liviano.

## Opción B — Compilar en tu PC (Windows)

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller LeadScraper.spec
```
El ejecutable queda en `dist/LeadScraper.exe`.

## Opción C — Correr sin compilar (desarrollo)

```bash
pip install -r requirements.txt
playwright install chromium
python app_web.py
```

---

## Uso de la app

1. Ábrela. La primera vez pulsa **Instalar navegador** (descarga ~150 MB, una vez).
2. Escribe **nichos** (sinónimos con `|`) y **zonas** (o activa la cuadrícula).
3. Pulsa **Iniciar**. Verás los leads aparecer en la tabla en tiempo real,
   con sus KPIs. Filtra, ordena por score y marca los que ya contactaste.
4. **Exportar Excel** genera el archivo con Dashboard y hoja por nicho.

---

## Notas técnicas

- **Windows 10/11** traen el runtime *WebView2* que usa la interfaz. En equipos
  muy antiguos podría pedir instalarlo (Microsoft lo ofrece gratis).
- Empieza con **concurrencia 2**. Si aparece captcha, el scraper **pausa** para
  que lo resuelvas; si te cortan, al reiniciar **retoma** donde iba.
- La verificación MX usa `dnspython`; si falta, degrada a una comprobación básica.

---

## Aviso legal

Extraer datos de Google Maps va contra sus Términos de Servicio y Google puede
bloquear el acceso. Úsalo con datos públicos de negocios y cumpliendo la ley de
protección de datos aplicable (en Colombia, Ley 1581 de 2012 / Habeas Data).
La venta de la herramienta o de los datos es responsabilidad de quien la opera.
