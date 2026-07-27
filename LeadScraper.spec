# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — compila el dashboard (app_web.py) a un único .exe
# Uso:  pyinstaller LeadScraper.spec
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# Empaqueta Playwright y PyWebView completos (incluyen archivos internos)
for paquete in ["playwright", "webview", "openpyxl"]:
    d, b, h = collect_all(paquete)
    datas += d
    binaries += b
    hiddenimports += h

# Dependencias que PyInstaller a veces no detecta solo
hiddenimports += [
    "httpx", "h11", "anyio", "sniffio", "certifi", "idna",
    "yaml", "openpyxl", "greenlet", "pyee",
    "dns", "dns.resolver", "dns.rdatatype",
    "clr", "bottle", "proxy_tools",
    "webview.platforms.edgechromium", "webview.platforms.winforms",
    "scraper_google_maps", "verificacion", "version", "perfiles", "plantillas",
]

# Interfaz HTML, gráficas, fuentes e íconos dentro del ejecutable
datas += [
    ("web/index.html", "web"),
    ("web/chart.umd.min.js", "web"),
    ("web/inter-latin-400-normal.woff2", "web"),
    ("web/inter-latin-500-normal.woff2", "web"),
    ("web/inter-latin-600-normal.woff2", "web"),
    ("web/inter-latin-700-normal.woff2", "web"),
    ("web/inter-latin-800-normal.woff2", "web"),
    ("icono.ico", "."),
    ("icono.png", "."),
]

a = Analysis(
    ["app_web.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="LeadScraper",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=True,
    upx_exclude=[], runtime_tmpdir=None,
    console=False,  # sin ventana de consola
    disable_windowed_traceback=False, argv_emulation=False, target_arch=None,
    codesign_identity=None, entitlements_file=None,
    icon="icono.ico",
)
