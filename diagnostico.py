"""
============================================================
 DIAGNÓSTICO  ·  prueba rápida del scraper
============================================================
Corre UNA sola búsqueda en Google Maps y reporta, paso a paso,
dónde está el problema si el scraper no entrega contenido:

  1) ¿El navegador de Playwright está instalado y abre?
  2) ¿Aparece la pantalla de consentimiento? ¿Se aceptó?
  3) ¿Hay bloqueo / captcha?
  4) ¿Cargó la lista de resultados? ¿Cuántas fichas encontró?
  5) ¿Se extraen los datos de una ficha (nombre, dirección, teléfono)?

Uso:
    python diagnostico.py                         # usa valores por defecto (Ibagué)
    python diagnostico.py "veterinaria"           # cambia el término
    python diagnostico.py "veterinaria" 4.4389 -75.2322   # término + coords
    python diagnostico.py "peluquería canina" 4.60 -74.08 --oculto

Al terminar deja una captura en <carpeta de datos>/debug/diagnostico_*.png
para ver exactamente qué mostró Google.
"""
import os
import sys
import time
import asyncio

from playwright.async_api import async_playwright

import scraper_google_maps as motor


def _arg(i, defecto):
    return sys.argv[i] if len(sys.argv) > i and not sys.argv[i].startswith("--") else defecto


async def diagnosticar(termino, lat, lng, oculto=False):
    ok = lambda m: print(f"  ✅ {m}")
    warn = lambda m: print(f"  ⚠  {m}")
    err = lambda m: print(f"  ❌ {m}")

    print("=" * 56)
    print(f" DIAGNÓSTICO  ·  '{termino}'  @ {lat},{lng}")
    print("=" * 56)

    # ---- Paso 0: navegador instalado ----
    print("\n[0] Navegador de Playwright…")
    if not motor.navegador_instalado():
        err("No está instalado. Corre:  python -m playwright install chromium")
        return False
    ok("Instalado.")

    dbg = os.path.join(motor.dir_datos(), "debug")
    os.makedirs(dbg, exist_ok=True)
    captura = os.path.join(dbg, f"diagnostico_{int(time.time())}.png")

    async with async_playwright() as p:
        # ---- Paso 1: abrir navegador ----
        print("\n[1] Abriendo navegador…")
        try:
            navegador = await p.chromium.launch(
                headless=oculto,
                args=["--disable-blink-features=AutomationControlled"])
            contexto = await navegador.new_context(
                locale="es-ES", user_agent=motor.USER_AGENT)
            # cookie que evita la pantalla de consentimiento
            try:
                await contexto.add_cookies([{
                    "name": "CONSENT",
                    "value": "YES+cb.20210328-17-p0.es+FX+100",
                    "domain": ".google.com", "path": "/"}])
            except Exception:
                pass
            await contexto.add_init_script(motor.STEALTH_JS)
            page = await contexto.new_page()
            ok("Navegador abierto.")
        except Exception as e:
            err(f"No abrió el navegador: {e}")
            return False

        exito = False
        try:
            # ---- Paso 2: navegar a la búsqueda ----
            query = termino.replace(" ", "+")
            url = (f"https://www.google.com/maps/search/{query}/"
                   f"@{lat},{lng},14z?hl=es")
            print(f"\n[2] Navegando a la búsqueda…\n    {url}")
            t0 = time.time()
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            ok(f"Página cargada en {time.time()-t0:.1f}s. URL: {page.url}")

            # ---- Paso 3: consentimiento ----
            print("\n[3] Pantalla de consentimiento…")
            if await motor.aceptar_consentimiento(page):
                ok("Apareció y se aceptó automáticamente.")
            else:
                ok("No apareció (o ya estaba aceptada).")

            # ---- Paso 4: bloqueo / captcha ----
            print("\n[4] Bloqueo / captcha…")
            if await motor.detectar_bloqueo(page):
                err(f"Google está mostrando captcha o bloqueo. URL: {page.url}")
                await page.screenshot(path=captura)
                print(f"    📸 Captura: {captura}")
                return False
            ok("Sin bloqueo.")

            # ---- Paso 5: lista de resultados ----
            print("\n[5] Lista de resultados…")
            await page.wait_for_timeout(2000)
            try:
                await page.wait_for_selector('div[role="feed"]', timeout=15000)
                feed_ok = True
            except Exception:
                feed_ok = False

            if not feed_ok and "/maps/place/" in page.url:
                warn("No hubo lista, pero Google abrió una ficha única directa.")
                feed_ok = True

            if not feed_ok:
                err("No cargó la lista de resultados 'div[role=\"feed\"]'.")
                await page.screenshot(path=captura)
                print(f"    📸 Captura: {captura}  (revísala para ver qué mostró Google)")
                return False
            ok("Lista cargada.")

            # ---- Paso 6: contar fichas ----
            print("\n[6] Contando fichas (con scroll)…")
            enlaces = set()
            for _ in range(4):
                for c in await page.query_selector_all('a.hfpxzc'):
                    href = await c.get_attribute("href")
                    if href:
                        enlaces.add(href)
                if not enlaces:
                    for c in await page.query_selector_all(
                            'div[role="feed"] a[href*="/maps/place/"]'):
                        href = await c.get_attribute("href")
                        if href:
                            enlaces.add(href)
                feed = await page.query_selector('div[role="feed"]')
                if feed:
                    await page.evaluate("(el)=>el.scrollBy(0,1200)", feed)
                await page.wait_for_timeout(1200)
            if "/maps/place/" in page.url:
                enlaces.add(page.url)

            if not enlaces:
                err("La lista cargó pero no se encontró ninguna ficha (posible cambio de selector).")
                await page.screenshot(path=captura)
                print(f"    📸 Captura: {captura}")
                return False
            ok(f"Encontradas {len(enlaces)} fichas.")

            # ---- Paso 7: extraer una ficha ----
            print("\n[7] Extrayendo datos de la primera ficha…")
            primero = next(iter(enlaces))
            datos = await motor.extraer_negocio(page, primero, termino, "diagnóstico")
            if not datos or not datos.get("nombre"):
                err("Abrió la ficha pero no extrajo el nombre (revisar selectores de detalle).")
                await page.screenshot(path=captura)
                print(f"    📸 Captura: {captura}")
                return False
            ok("Extracción correcta:")
            print(f"       Nombre    : {datos.get('nombre')}")
            print(f"       Categoría : {datos.get('categoria')}")
            print(f"       Dirección : {datos.get('direccion') or '—'}")
            print(f"       Teléfono  : {datos.get('telefono') or '—'}")
            print(f"       Sitio web : {datos.get('sitio_web') or '—'}")

            await page.screenshot(path=captura)
            exito = True
        except Exception as e:
            err(f"Error inesperado: {e}")
            try:
                await page.screenshot(path=captura)
                print(f"    📸 Captura: {captura}")
            except Exception:
                pass
        finally:
            try:
                await contexto.close()
                await navegador.close()
            except Exception:
                pass

        print("\n" + "=" * 56)
        if exito:
            print(" ✅ TODO FUNCIONA. El scraper puede entregar contenido.")
            print(f"    📸 Captura de referencia: {captura}")
        else:
            print(" ❌ Se encontró el punto de falla arriba.")
        print("=" * 56)
        return exito


def main():
    termino = _arg(1, "veterinaria")
    lat = _arg(2, "4.4389")
    lng = _arg(3, "-75.2322")
    oculto = "--oculto" in sys.argv or "--headless" in sys.argv
    try:
        lat, lng = float(lat), float(lng)
    except ValueError:
        print("lat/lng inválidos. Ej: python diagnostico.py \"veterinaria\" 4.4389 -75.2322")
        sys.exit(2)
    ok = asyncio.run(diagnosticar(termino, lat, lng, oculto))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
