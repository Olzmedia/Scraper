"""
Verificación y enriquecimiento de leads.
  · Email: valida formato + existencia de registros MX del dominio.
  · WhatsApp: normaliza y valida que el número tenga forma usable.
  · Negocio activo: estima actividad según reseñas.
  · Web: marca si el sitio responde o está caído.
Sin dependencias externas pesadas (usa dnspython si está; si no, degrada bien).
"""
import re
import socket
import asyncio

try:
    import dns.resolver
    _TIENE_DNS = True
except Exception:
    _TIENE_DNS = False

_CACHE_MX = {}


def validar_formato_email(email):
    if not email:
        return False
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
                         email.strip()))


def dominio_tiene_mx(dominio):
    """True si el dominio tiene registros MX (puede recibir correo)."""
    if dominio in _CACHE_MX:
        return _CACHE_MX[dominio]
    ok = False
    try:
        if _TIENE_DNS:
            resolver = dns.resolver.Resolver()
            resolver.lifetime = 5
            resp = resolver.resolve(dominio, "MX")
            ok = len(resp) > 0
        else:
            # Sin dnspython: al menos comprobamos que el dominio resuelva
            socket.gethostbyname(dominio)
            ok = True
    except Exception:
        ok = False
    _CACHE_MX[dominio] = ok
    return ok


def verificar_email(email):
    """Devuelve 'válido', 'formato', 'sin_mx' o ''."""
    primero = (email or "").split(";")[0].strip()
    if not primero:
        return ""
    if not validar_formato_email(primero):
        return "formato"
    dominio = primero.split("@")[1].lower()
    return "válido" if dominio_tiene_mx(dominio) else "sin_mx"


def verificar_whatsapp(numero):
    """Valida que el número tenga forma usable para WhatsApp."""
    if not numero:
        return ""
    d = re.sub(r"[^\d]", "", numero)
    # Colombia: celular 10 díg. empezando en 3, o con 57 delante
    if d.startswith("57"):
        d = d[2:]
    if len(d) == 10 and d.startswith("3"):
        return "válido"
    return "revisar"


def estimar_actividad(resenas, calificacion):
    """Heurística simple de negocio activo según señales disponibles."""
    try:
        rev = int(re.sub(r"[^\d]", "", str(resenas or "0")) or 0)
    except Exception:
        rev = 0
    if rev >= 30:
        return "activo"
    if rev >= 5:
        return "moderado"
    if rev >= 1:
        return "bajo"
    return "sin señales"


async def web_responde(cliente, url, timeout=8):
    """True si el sitio web responde (no está caído)."""
    if not url:
        return None
    u = url if url.startswith("http") else "https://" + url
    try:
        r = await cliente.get(u, timeout=timeout, follow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False


def enriquecer(fila):
    """Agrega campos de verificación/actividad a un lead (parte síncrona)."""
    fila["email_estado"] = verificar_email(fila.get("email", ""))
    fila["whatsapp_estado"] = verificar_whatsapp(fila.get("whatsapp", ""))
    fila["actividad"] = estimar_actividad(fila.get("resenas"),
                                          fila.get("calificacion"))
    return fila
