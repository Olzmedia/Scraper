"""
Plantillas de nichos por categoría, para cargarlas con un clic en la app.
Cada categoría es una lista de líneas (nicho | sinónimos).
"""

PLANTILLAS = {
    "Salud y bienestar": [
        "gimnasios | gym | crossfit | centro de acondicionamiento físico",
        "peluquerías | salón de belleza | barbería | estética",
        "spa | centro de masajes | sauna",
        "odontología | consultorio dental | clínica dental",
        "médicos | consultorio médico | centro médico",
        "óptica | optometría",
        "veterinaria | clínica veterinaria",
        "farmacia | droguería",
        "laboratorio clínico",
        "psicólogo | consultorio psicológico",
        "fisioterapia | terapia física",
    ],
    "Comida y bebida": [
        "restaurantes | comidas rápidas | asadero",
        "cafeterías | café | panadería | repostería",
        "pizzería | comida italiana",
        "bar | discoteca | cervecería",
        "heladería | postres",
        "comida china | comida oriental",
    ],
    "Comercio y retail": [
        "ferreterías | ferretería",
        "supermercados | minimercado | tienda de barrio",
        "ropa | boutique | almacén de ropa",
        "zapatería | calzado",
        "papelería | librería",
        "tienda de mascotas",
        "floristería",
        "joyería | relojería",
        "mueblería | muebles",
        "electrodomésticos | tecnología",
    ],
    "Automotriz": [
        "talleres mecánicos | mecánica automotriz",
        "lavadero de carros | autolavado",
        "llantas | montallantas",
        "repuestos | autopartes",
        "motos | taller de motos",
        "concesionario de autos",
    ],
    "Servicios profesionales": [
        "abogados | oficina jurídica",
        "contadores | contaduría",
        "inmobiliaria | finca raíz",
        "agencia de viajes",
        "imprenta | publicidad | diseño gráfico",
        "notaría",
        "seguros | aseguradora",
    ],
    "Educación": [
        "colegios | institución educativa",
        "jardín infantil | guardería",
        "academia | instituto | centro de idiomas",
        "universidad",
        "autoescuela | escuela de conducción",
    ],
    "Hogar y construcción": [
        "constructora | construcción",
        "carpintería | ebanistería",
        "cerrajería",
        "vidriería",
        "plomería | fontanería",
        "electricista",
    ],
    "Belleza y cuidado personal": [
        "uñas | manicure | spa de uñas",
        "tatuajes | estudio de tatuajes",
        "yoga | pilates",
    ],
    "Hospedaje y eventos": [
        "hoteles | hostal | hospedaje",
        "salón de eventos | eventos",
        "fotografía | fotógrafo",
    ],
}


def categorias():
    return list(PLANTILLAS.keys())


def nichos_de(categoria):
    return PLANTILLAS.get(categoria, [])
