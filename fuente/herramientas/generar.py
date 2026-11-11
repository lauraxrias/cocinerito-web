#!/usr/bin/env python3
"""Genera el sitio estático de El Cocinerito en ./site.

Los productos se leen de datos/productos.csv (una fila por producto; varios
gramajes separados por punto y coma, p. ej. "10 g; 25 g; 500 g"). Ese archivo
se puede exportar desde Excel. Si un producto no tiene foto, se muestra un
espacio reservado. En el sitio final estos datos vendrán del panel de
administración del CMS que se elija.
"""
import csv, json, os, html
from urllib.parse import quote

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "sitio")
CSV = os.path.join(BASE, "..", "datos", "productos.csv")

EMPRESA = {
    "nombre": "Industria de Alimentos El Cocinerito",
    "razonSocial": "Industria de Alimentos El Cocinerito S.A.S.",
    "nit": "900.445.789-7",
    "planta": "Zona Industrial El Paraíso, Manzana C8, Lote 13",
    "ciudad": "Santander de Quilichao, Cauca",
    "correo": "jefecomercial@cocinerito.com",
    "whatsapp": "573148870121",  # WhatsApp de la jefa comercial (solo dígitos, con 57)
    "whatsappVisible": "+57 314 887 0121",
}

# Colores tomados de los empaques fotografiados. "acento" es la versión legible
# para textos y "tinte" el fondo claro de la sección de cada línea.
LINEAS = [
    {"id": "hierbas", "nombre": "Hierbas", "color": "#0B4A36", "acento": "#0B4A36", "tinte": "#DFEAE3",
     "texto": "Hierbas secas, enteras y molidas, para sopas, carnes y salsas."},
    {"id": "sazonadores", "nombre": "Sazonadores", "color": "#C1191E", "acento": "#A3151A", "tinte": "#F7E1DC",
     "texto": "Adobos y mezclas listas para darle sazón a cualquier preparación."},
    {"id": "tradicionales", "nombre": "Tradicionales", "color": "#BF8107", "acento": "#7F5604", "tinte": "#F6E8CC",
     "texto": "Canela, clavo, comino, color y las especias de toda la vida."},
    {"id": "reposteria", "nombre": "Repostería", "color": "#2B1E67", "acento": "#2B1E67", "tinte": "#E4E1F0",
     "texto": "Ingredientes para postres, panes y preparaciones dulces."},
    {"id": "saludable", "nombre": "Saludable", "color": "#EAE7DC", "borde": "#3F5815", "acento": "#3F5815", "tinte": "#E9ECD9",
     "texto": "Semillas para sumar a la alimentación diaria."},
    {"id": "gourmet", "nombre": "Línea Gourmet", "color": "#151515", "acento": "#151515", "tinte": "#E7E4DE",
     "texto": "Pimientas en frasco molino para moler en el momento."},
]
L = {l["id"]: l for l in LINEAS}
PRESENTACIONES = [{"id": "bolsa", "nombre": "Bolsa"}, {"id": "frasco", "nombre": "Frasco"}, {"id": "tarro", "nombre": "Tarro"}]
P = {p["id"]: p for p in PRESENTACIONES}

def leer_productos():
    out = []
    with open(CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r = {k: (v or "").strip() for k, v in r.items()}
            if not r.get("nombre"):
                continue
            r["gramajes"] = [g.strip() for g in r["gramajes"].split(";") if g.strip()]
            r["foto"] = r.get("foto") or ""
            out.append(r)
    return out

PRODUCTOS = leer_productos()
PR = {p["id"]: p for p in PRODUCTOS}

# ---------------------------------------------------------------- familias
# En el catálogo se muestra un solo producto por nombre. Las variantes de forma
# (entero, molido, en grano, en hojas, en astilla) y las distintas presentaciones
# (bolsa, frasco, tarro) se agrupan y se consultan al abrir el producto.
FORMAS = {"entero": "Entero", "entera": "Entera", "molido": "Molido", "molida": "Molida",
          "grano": "En grano", "hojas": "En hojas", "astilla": "En astilla"}

def slug(s):
    import unicodedata, re
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def base_y_forma(nombre):
    partes = nombre.split()
    if len(partes) > 1 and partes[-1].lower() in FORMAS:
        return " ".join(partes[:-1]), FORMAS[partes[-1].lower()]
    return nombre, ""

def tipo(presentacion):
    """Bolsas por un lado; frascos y tarros por otro."""
    return "bolsa" if presentacion == "bolsa" else "envase"

def armar_familias():
    # Solo se publican las presentaciones que tienen foto.
    grupos = {}
    for p in PRODUCTOS:
        if not p["foto"]:
            continue
        b, _ = base_y_forma(p["nombre"])
        grupos.setdefault((p["linea"], b, tipo(p["presentacion"])), []).append(p)
    fams = []
    for (linea, b, tp), filas in grupos.items():
        mismo = len({f["nombre"] for f in filas}) == 1
        nombre = filas[0]["nombre"] if mismo else b
        variantes = []
        for f in filas:
            forma = "" if mismo else base_y_forma(f["nombre"])[1]
            variantes.append({"forma": forma, "presentacion": f["presentacion"], "envase": f["envase"],
                              "gramajes": f["gramajes"], "foto": f["foto"], "id": f["id"]})
        foto = next((f["foto"] for f in filas if f["foto"]), "")
        doble = tp != "bolsa" and (linea, b, "bolsa") in grupos
        fid = slug(nombre) + ("-" + filas[0]["presentacion"] if doble else "")
        if any(f["id"] == fid for f in fams):
            fid += "-" + linea
        fams.append({"id": fid, "tipo": tp,
                     "nombre": nombre, "linea": linea, "foto": foto, "variantes": variantes,
                     "presentaciones": sorted({v["presentacion"] for v in variantes}, key=["bolsa", "frasco", "tarro"].index)})
    orden = [l["id"] for l in LINEAS]
    fams.sort(key=lambda f: (orden.index(f["linea"]), 0 if f["foto"] else 1, f["nombre"]))
    return fams

FAMILIAS = armar_familias()
FA = {f["id"]: f for f in FAMILIAS}
FAMILIA_DE = {v["id"]: f for f in FAMILIAS for v in f["variantes"]}

# Supermercados donde se encuentran los productos. "logo": ruta a la imagen
# oficial (PNG o SVG) dentro de sitio/img/tiendas/. Vacío: espacio para cargarlo.
TIENDAS = [
    {"nombre": "Éxito", "logo": "img/tiendas/exito.png"},
    {"nombre": "Supertiendas Cañaveral", "logo": "img/tiendas/canaveral.png"},
    {"nombre": "Jumbo", "logo": "img/tiendas/jumbo.png"},
    {"nombre": "Olímpica", "logo": "img/tiendas/olimpica.png"},
    {"nombre": "La Montaña Agromercados", "logo": "img/tiendas/la-montana.png"},
    {"nombre": "Supermercados Caribe", "logo": "img/tiendas/caribe.png"},
]
# Foto exterior de la nueva planta (vacío hasta recibirla).
PLANTA_EXTERIOR = "img/planta-exterior.webp"

PERFILES = [
    {"id": "distribuidor", "nombre": "Distribuidor", "mensaje": "Hola, soy distribuidor y quiero información para distribuir los productos El Cocinerito."},
    {"id": "supermercado", "nombre": "Supermercado o tienda", "mensaje": "Hola, tengo un supermercado o tienda y quiero información para vender los productos El Cocinerito."},
    {"id": "restaurante", "nombre": "Restaurante u hotel", "mensaje": "Hola, tengo un restaurante u hotel y quiero información sobre los productos El Cocinerito."},
    {"id": "otro", "nombre": "Otro", "mensaje": "Hola, quiero información sobre los productos El Cocinerito."},
]
PF = {p["id"]: p for p in PERFILES}
MSG_MARCA = "Hola, me interesa que El Cocinerito fabrique productos con mi propia marca."

# Inicio: producto protagonista y video de receta (vacío hasta tener el archivo).
HERO = {"producto": "adobo-6-alinos", "video": "", "poster": ""}

e = html.escape

def wa(texto):
    return f"https://wa.me/{EMPRESA['whatsapp']}?text={quote(texto)}"

def gramajes(p):
    return " · ".join(p["gramajes"]) if p["gramajes"] else "Gramajes por confirmar"

ICON_WA = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3Z"/><path d="M9 8.5c0 3.6 2.9 6.5 6.5 6.5l1-1.6-2-1-1 .8a4 4 0 0 1-2.7-2.7l.8-1-1-2Z" fill="currentColor" stroke-width="1"/></svg>'
ICON_FLECHA = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="square"><path d="M6 18 18 6M9 6h9v9"/></svg>'
ICON_MENU = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M3 6h18M3 12h18M3 18h18"/></svg>'

NAV = [
    ("catalogo.html", "Productos"),
    ("linea-gourmet.html", "Línea Gourmet"),
    ("empresas.html", "Para empresas"),
    ("nosotros.html", "Nosotros"),
    ("contacto.html", "Contacto"),
]

def punto(l):
    borde = f";--b:{l['borde']}" if l.get("borde") else ""
    return f'<i class="punto" style="--c:{l["color"]}{borde}" aria-hidden="true"></i>'

def estilo_linea(l):
    return f'--c:{l["color"]};--acento:{l["acento"]};--tinte:{l["tinte"]}'

BOLSA_SVG = ('<svg viewBox="0 0 100 140" aria-hidden="true"><path d="M10 14 15 8l5 6 5-6 5 6 5-6 5 6 5-6 5 6 5-6 5 6 5-6 5 6 5-6 5 6v108c0 6-4 10-10 10H20c-6 0-10-4-10-10Z" '
             'fill="currentColor" fill-opacity=".09" stroke="currentColor" stroke-opacity=".45" stroke-width="1.6" stroke-dasharray="5 4"/>'
             '<path d="M30 52h40M36 62h28" stroke="currentColor" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/></svg>')

def foto(obj, lazy=True, cls="prod-img", nombre=None):
    """obj: producto o familia. Sin foto: silueta de bolsa con 'Foto por cargar'."""
    nombre = nombre or obj["nombre"]
    if not obj.get("foto"):
        return f'<span class="sin-foto">{BOLSA_SVG}<span>Foto por cargar</span></span>'
    alt = f'{nombre} El Cocinerito'
    return f'<img class="{cls}" src="{obj["foto"]}" alt="{e(alt)}"{" loading=\"lazy\"" if lazy else ""} decoding="async">'

def unir(xs):
    xs = [x for x in xs if x]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1] if xs else ""

def resumen(f):
    """Texto corto bajo el nombre del producto en el catálogo."""
    formas = list(dict.fromkeys(v["forma"] for v in f["variantes"] if v["forma"]))
    pres = unir([P[p]["nombre"] for p in f["presentaciones"]])
    if formas:
        return f'{unir(formas).capitalize()} · {pres.lower() if len(formas) else pres}'
    grs = [g for v in f["variantes"] for g in v["gramajes"]]
    return f'{pres} · {", ".join(grs)}' if grs else pres

def tabla_variantes(f):
    filas = []
    for v in f["variantes"]:
        forma = f'<strong>{v["forma"]}</strong> · ' if v["forma"] else ""
        grs = "".join(f"<li>{g}</li>" for g in v["gramajes"]) or '<li><span class="pendiente">Por confirmar</span></li>'
        filas.append(f'<li class="variante"><span class="variante__tipo">{forma}{e(v["envase"])}</span><ul class="gramajes">{grs}</ul></li>')
    return f'<ul class="variantes">{"".join(filas)}</ul>'

def msg_cotizar(f):
    return f"Hola, quiero cotizar {f['nombre']} de El Cocinerito."

def cabecera(actual):
    links = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if h == actual else ""}>{t}</a></li>' for h, t in NAV)
    return f'''<a class="sr saltar" href="#contenido">Saltar al contenido</a>
<header class="cabecera">
  <div class="envoltura">
    <a class="marca" href="index.html" aria-label="El Cocinerito, inicio"><img src="img/logo-crema.webp" width="1200" height="511" alt="Industria de Alimentos El Cocinerito"></a>
    <button class="abrir-menu" aria-expanded="false" aria-controls="menu">Menú {ICON_MENU}</button>
    <ul class="menu" id="menu">{links}</ul>
    <a class="boton boton--crema boton--cab" href="{wa(PF['otro']['mensaje'])}" target="_blank" rel="noopener">{ICON_WA}<span>WhatsApp</span></a>
  </div>
</header>'''

def franja(clase=""):
    """Franja de cuadros y círculos, tomada de la base de los empaques."""
    return f'<div class="franja {clase}" aria-hidden="true"></div>'

def pie(flotante=True):
    nav = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in [("index.html", "Inicio")] + NAV)
    return f'''{franja("franja--pie")}
<footer class="pie">
  <div class="envoltura">
    <div class="pie__rejilla">
      <div class="pie__marca"><img src="img/logo-crema.webp" width="1200" height="511" alt="El Cocinerito" loading="lazy"><p>Sazón colombiana desde 1984.</p></div>
      <div class="pie__col">
        <h2 class="pie__titulo">Planta de producción</h2>
        <p>{e(EMPRESA['planta'])}<br>{e(EMPRESA['ciudad'])}</p>
      </div>
      <div class="pie__col">
        <h2 class="pie__titulo">Área comercial</h2>
        <p><a href="mailto:{EMPRESA['correo']}">{EMPRESA['correo']}</a></p>
        <p><a class="pie__wa" href="{wa(PF['otro']['mensaje'])}" target="_blank" rel="noopener">{ICON_WA} {EMPRESA['whatsappVisible']}</a></p>
      </div>
      <nav class="pie__col" aria-label="Pie de página"><h2 class="pie__titulo">Sitio</h2><ul>{nav}</ul></nav>
    </div>
    <div class="pie__abajo">
      <p>© 2026 {e(EMPRESA['razonSocial'])} · NIT {EMPRESA['nit']}</p>
      <ul>
        <li><a href="legal.html#datos">Política de tratamiento de datos</a></li>
        <li><a href="legal.html#aviso">Aviso de privacidad</a></li>
        <li><a href="legal.html#terminos">Términos de uso</a></li>
        <li><a href="legal.html#cookies">Cookies</a></li>
      </ul>
    </div>
  </div>
</footer>
''' + (f'<a class="wa-flotante" href="{wa(PF["otro"]["mensaje"])}" target="_blank" rel="noopener" aria-label="Escribir por WhatsApp">{ICON_WA}</a>' if flotante else "")

DIALOGO = '''<dialog class="dialogo" id="dialogo" aria-labelledby="dlg-titulo">
  <div class="dialogo__caja">
    <button class="dialogo__cerrar" type="button" data-cerrar aria-label="Cerrar"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
    <div class="dialogo__foto" data-dlg-foto></div>
    <div class="dialogo__info">
      <p class="dialogo__linea" data-dlg-linea></p>
      <h2 id="dlg-titulo" data-dlg-nombre></h2>
      <h3 class="dialogo__sub">Presentaciones y gramajes</h3>
      <div data-dlg-variantes></div>
      <p class="aviso">Imagen de referencia. La información oficial del producto es la que figura en su etiqueta.</p>
    </div>
  </div>
</dialog>'''

def pagina(nombre, titulo, descripcion, cuerpo, actual=None, clase_body="", dialogo=False):
    doc = f'''<!doctype html>
<html lang="es-CO">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<link rel="icon" href="img/logo-verde.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/estilos.css">
<script>document.documentElement.classList.add('js')</script>
</head>
<body{f' class="{clase_body}"' if clase_body else ''}>
{cabecera(actual or nombre)}
<main id="contenido">
{cuerpo}
</main>
{pie(flotante=not (nombre == "catalogo.html" or nombre.startswith("producto-")))}
{DIALOGO if dialogo else ""}
<script src="js/datos.js"></script>
<script src="js/sitio.js"></script>
</body>
</html>
'''
    with open(os.path.join(OUT, nombre), "w", encoding="utf-8") as f:
        f.write(doc)

# ------------------------------------------------------------- bloques comunes
def bloque_whatsapp(titulo="¿Tienes un negocio?", texto="Elige el tipo de negocio y te abrimos WhatsApp con un mensaje listo. Allí nos cuentas qué necesitas.", id_="t-wa", chef=True):
    chips = "".join(f'<label class="chip"><input type="radio" name="perfil" value="{p["id"]}"{" checked" if i == 0 else ""}><span>{p["nombre"]}</span></label>' for i, p in enumerate(PERFILES))
    img = '<img class="wa-bloque__chef" src="img/chef-cuchara.webp" width="576" height="1100" alt="" loading="lazy">' if chef else ""
    return f'''<section class="seccion envoltura" aria-labelledby="{id_}">
  <form class="wa-bloque{" wa-bloque--chef" if chef else ""} aparece" data-wa-form>
    <div class="wa-bloque__texto">
      <h2 id="{id_}">{titulo}</h2>
      <p>{texto}</p>
      {img}
    </div>
    <div class="wa-bloque__accion">
      <fieldset class="campo-grupo"><legend>Mi negocio es</legend><div class="chips">{chips}</div></fieldset>
      <p class="burbuja" aria-live="polite"><span data-wa-texto>{e(PERFILES[0]['mensaje'])}</span></p>
      <a class="boton boton--crema boton--ancho" data-wa-enlace href="{wa(PERFILES[0]['mensaje'])}" target="_blank" rel="noopener">{ICON_WA}Abrir WhatsApp</a>
    </div>
  </form>
</section>'''

SELLOS = [("ISO 22000", "Gestión de inocuidad alimentaria"),
          ("GMP-HACCP", "Análisis de peligros y puntos críticos de control"),
          ("BPM", "Buenas prácticas de manufactura")]

def bloque_marca_propia(titulo_tag="h2", con_enlace=True):
    """Fabricamos tu propia marca: foto exterior de la planta como protagonista."""
    if PLANTA_EXTERIOR:
        fondo = f'<img class="fabrica__foto" src="{PLANTA_EXTERIOR}" alt="Exterior de la nueva planta de producción de El Cocinerito en Santander de Quilichao" loading="lazy">'
    else:
        fondo = '<div class="fabrica__foto fabrica__foto--pend"><span>Espacio para la foto exterior de la nueva planta de producción</span></div>'
    sellos = "".join(f"<li><strong>{a}</strong><span>{b}</span></li>" for a, b in SELLOS)
    enlace = '<a class="enlace enlace--crema" href="empresas.html#marca-propia">Cómo trabajamos con empresas</a>' if con_enlace else ""
    return f'''<section class="fabrica" id="marca-propia" aria-labelledby="t-fabrica">
  <div class="fabrica__escena">
    {fondo}
    <img class="fabrica__chef" src="img/chef-cuchara.webp" width="576" height="1100" alt="El personaje de El Cocinerito con una cuchara de palo, con el pulgar arriba" loading="lazy" data-prof="0.5">
  </div>
  <div class="envoltura fabrica__rejilla">
    <div class="fabrica__texto">
      <{titulo_tag} id="t-fabrica" class="aparece">Fabricamos tu propia marca</{titulo_tag}>
      <p class="fabrica__lead aparece" style="--i:1">Ponemos nuestra planta, nuestros procesos y más de cuarenta años de experiencia al servicio de empresas que quieren su propia línea de condimentos y especias.</p>
      <div class="acciones aparece" style="--i:2"><a class="boton boton--crema" href="{wa(MSG_MARCA)}" target="_blank" rel="noopener">{ICON_WA}Hablemos de tu marca</a>{enlace}</div>
    </div>
    <ol class="fabrica__puntos">
      <li class="aparece"><span class="fabrica__num">01</span><h3>Planta propia</h3><p>Elaboramos y empacamos en {e(EMPRESA['ciudad'])}.</p></li>
      <li class="aparece" style="--i:1"><span class="fabrica__num">02</span><h3>Calidad certificada</h3><ul class="sellos">{sellos}</ul></li>
      <li class="aparece" style="--i:2"><span class="fabrica__num">03</span><h3>Todos los canales</h3><p>Retail, mayoristas, institucional e industrial.</p></li>
    </ol>
  </div>
</section>'''

def bloque_tiendas(titulo_tag="h2"):
    items = []
    for i, t in enumerate(TIENDAS):
        if t["logo"]:
            logo = f'<img src="{t["logo"]}" alt="{e(t["nombre"])}" loading="lazy">'
        else:
            logo = f'<span class="tienda__pend"><strong>{e(t["nombre"])}</strong><span>Logo oficial por cargar</span></span>'
        items.append(f'<li class="tienda aparece" style="--i:{i}">{logo}</li>')
    return f'''<section class="tiendas" aria-labelledby="t-tiendas">
  <div class="envoltura tiendas__rejilla">
    <div class="tiendas__texto">
      <{titulo_tag} id="t-tiendas" class="aparece">Encuéntranos en</{titulo_tag}>
      <p class="aparece" style="--i:1">Nuestros productos están en supermercados y establecimientos comerciales como:</p>
    </div>
    <ul class="tiendas__lista">{"".join(items)}</ul>
  </div>
</section>'''

def bloque_planta(titulo_tag="h2"):
    if PLANTA_EXTERIOR:
        grande = f'<img class="planta__grande" src="{PLANTA_EXTERIOR}" alt="Exterior de la nueva planta de producción" loading="lazy">'
    else:
        grande = '<span class="espacio-foto planta__grande">Espacio para la foto exterior de la planta</span>'
    sellos = "".join(f"<li><strong>{a}</strong><span>{b}</span></li>" for a, b in SELLOS)
    return f'''<section class="planta" id="planta" aria-labelledby="t-planta">
  <div class="envoltura planta__rejilla">
    <div class="planta__fotos">
      {grande}
    </div>
    <div class="planta__texto">
      <{titulo_tag} id="t-planta" class="aparece">Nuestra planta</{titulo_tag}>
      <p class="aparece" style="--i:1">Elaboramos y empacamos en nuestra planta de {e(EMPRESA['ciudad'])}, en {e(EMPRESA['planta'])}.</p>
      <ul class="sellos sellos--claro aparece" style="--i:2">{sellos}</ul>
    </div>
  </div>
</section>'''

TIPOS = [("bolsa", "Bolsas"), ("envase", "Frascos y tarros")]

def tarjeta(f, i=0, lazy=True, linea=False):
    l = L[f["linea"]]
    dato = (f'{punto(l)}{l["nombre"]} · ' if linea else "") + e(resumen(f))
    return (f'<li class="prod aparece" style="--i:{i % 4};{estilo_linea(l)}" data-linea="{f["linea"]}" data-presentaciones="{f["tipo"]}" data-nombre="{e(f["nombre"].lower())}">'
            f'<a class="prod__a" href="producto-{f["id"]}.html" data-familia="{f["id"]}">'
            f'<span class="prod__foto">{foto(f, lazy)}</span>'
            f'<strong class="prod__nombre">{e(f["nombre"])}</strong>'
            f'<span class="prod__dato">{dato}</span>'
            f'<span class="prod__ver" aria-hidden="true">Ver presentaciones</span></a></li>')

# ------------------------------------------------------------- inicio
def inicio():
    adobo, oreg, canela = FA["adobo-6-alinos"], FA["oregano-entero"], FA["canela-molida"]
    hero = f'''<section class="hero" aria-labelledby="t-inicio">
  <div class="envoltura hero__rejilla">
    <div class="hero__texto">
      <h1 id="t-inicio" class="aparece">Sazón colombiana para cada cocina</h1>
      <p class="hero__lead aparece" style="--i:2">Desde 1984 elaboramos en Santander de Quilichao, Cauca, hierbas, sazonadores, especias tradicionales, repostería y línea saludable para hogares, tiendas, restaurantes, mayoristas e industria.</p>
      <div class="acciones aparece" style="--i:3"><a class="boton boton--crema" href="catalogo.html">Ver productos</a><a class="boton boton--fantasma" href="#marca-propia">Fabricamos tu marca</a></div>
    </div>
    <div class="hero__escena" data-escena>
      <span class="hero__disco" aria-hidden="true" data-prof="-0.2"></span>
      <img class="hero__chef" src="img/chef-sarten.webp" width="630" height="1100" alt="El personaje de El Cocinerito salteando verduras y especias en una sartén" data-prof="0.35">
      <a class="hero__bolsa hero__bolsa--1" href="producto-{adobo['id']}.html" data-prof="1.1" aria-label="{e(adobo['nombre'])}">{foto(adobo, False, "")}</a>
      <a class="hero__bolsa hero__bolsa--2" href="producto-{oreg['id']}.html" data-prof="1.6" aria-label="{e(oreg['nombre'])}">{foto(oreg, False, "")}</a>
      <a class="hero__bolsa hero__bolsa--3" href="producto-{canela['id']}.html" data-prof="0.8" aria-label="{e(canela['nombre'])}">{foto(canela, False, "")}</a>
    </div>
  </div>
  {franja("franja--hero")}
</section>'''

    rep = {"hierbas": "oregano-entero", "sazonadores": "adobo-6-alinos", "tradicionales": "paprika", "reposteria": "arandanos", "saludable": "linaza-molida", "gourmet": "mix-pimienta"}
    filas, escenas = [], []
    for i, l in enumerate(LINEAS):
        f = FA[rep[l["id"]]]
        href = "linea-gourmet.html" if l["id"] == "gourmet" else f"catalogo.html#linea-{l['id']}"
        filas.append(f'<li class="aparece" style="--i:{i};{estilo_linea(l)}"><a href="{href}" data-linea-i="{i}">'
                     f'<span class="lineas__nombre">{l["nombre"]}</span>'
                     f'<span class="lineas__desc">{e(l["texto"])}</span>'
                     f'<span class="lineas__movil" aria-hidden="true">{foto(f, True, "")}</span></a></li>')
        escenas.append(f'<figure class="lineas__fig{" ver" if i == 0 else ""}" data-linea-i="{i}" style="{estilo_linea(l)}"><span class="lineas__circulo"></span>{foto(f, True, "")}<figcaption>{e(f["nombre"])}</figcaption></figure>')
    l0 = LINEAS[0]
    lineas = f'''<section class="lineas" aria-labelledby="t-lineas" style="{estilo_linea(l0)}" data-lineas>
  <div class="envoltura lineas__rejilla">
    <div class="lineas__cabeza">
      <h2 id="t-lineas" class="aparece">Seis líneas, un mismo sabor de casa</h2>
      <p class="aparece" style="--i:1">Cada línea lleva el color de su empaque, para que la reconozcas en la góndola y aquí.</p>
    </div>
    <ul class="lineas__lista">{"".join(filas)}</ul>
    <div class="lineas__escena" aria-hidden="true">{"".join(escenas)}</div>
  </div>
</section>'''

    por_linea = [[f for f in FAMILIAS if f["linea"] == l["id"] and f["tipo"] == "bolsa"] for l in LINEAS]
    con_foto = [g[i] for i in range(max(map(len, por_linea))) for g in por_linea if i < len(g)]  # alterna líneas
    riel = "".join(f'<li class="riel__item" style="{estilo_linea(L[f["linea"]])}"><a href="producto-{f["id"]}.html" data-familia="{f["id"]}"><span class="riel__foto">{foto(f)}</span><strong>{e(f["nombre"])}</strong><span>{L[f["linea"]]["nombre"]}</span></a></li>' for f in con_foto)
    portafolio = f'''<section class="portafolio" aria-labelledby="t-port">
  <div class="envoltura portafolio__cabeza">
    <h2 id="t-port" class="aparece">Un amplio portafolio</h2>
    <div class="aparece" style="--i:1"><p>En bolsa, frasco y tarro, para la cocina de la casa y para la de un negocio. Abre cualquier producto para ver sus presentaciones.</p><a class="boton" href="catalogo.html">Ver todo el portafolio</a></div>
  </div>
  <div class="riel" data-riel>
    <ul class="riel__pista">{riel}</ul>
  </div>
</section>'''

    cuerpo = hero + bloque_tiendas() + lineas + portafolio + bloque_marca_propia() + bloque_gourmet() + bloque_whatsapp()
    pagina("index.html", "El Cocinerito · Condimentos, especias y repostería", "Industria de Alimentos El Cocinerito: condimentos, especias, hierbas y sazonadores colombianos desde 1984, con marca propia y fabricación para otras marcas.", cuerpo, actual="index.html", dialogo=True)

def bloque_gourmet(enlace=True):
    pn, mx = FA["pimienta-negra-entera"], FA["mix-pimienta"]
    link = '<p class="aparece" style="--i:2;margin-top:28px"><a class="enlace" href="linea-gourmet.html">Conocer la Línea Gourmet</a></p>' if enlace else ""
    def item(f, i):
        v = f["variantes"][0]
        return f'<a class="gourmet__item aparece" style="--i:{i}" href="producto-{f["id"]}.html" data-familia="{f["id"]}"><span class="gourmet__foto">{foto(f)}</span><strong>{f["nombre"]}</strong><span>{e(v["envase"])} · {", ".join(v["gramajes"])}</span></a>'
    return f'''<section class="gourmet" aria-labelledby="t-gourmet">
  <div class="envoltura gourmet__rejilla">
    <div class="gourmet__texto">
      <h2 id="t-gourmet" class="aparece">Línea Gourmet</h2>
      <p class="aparece" style="--i:1">Pimientas en frasco molino, para moler en el momento en la mesa o en la cocina.</p>
      {link}
    </div>
    {item(pn, 0)}{item(mx, 1)}
  </div>
</section>'''

# ------------------------------------------------------------- catálogo
def catalogo():
    tabs = '<button class="filtro" type="button" data-linea="" aria-pressed="true">Todas</button>' + "".join(
        f'<button class="filtro" type="button" data-linea="{l["id"]}" aria-pressed="false">{punto(l)}{l["nombre"]}</button>' for l in LINEAS)
    fp = '<button class="filtro filtro--chico" type="button" data-presentacion="" aria-pressed="true">Todas</button>' + "".join(
        f'<button class="filtro filtro--chico" type="button" data-presentacion="{k}" aria-pressed="false">{t}</button>' for k, t in TIPOS)
    bloques = []
    # Bolsas: agrupadas por línea, cada línea con su color de fondo
    grupos = []
    for l in LINEAS:
        fs = [f for f in FAMILIAS if f["linea"] == l["id"] and f["tipo"] == "bolsa"]
        if not fs:
            continue
        items = "".join(tarjeta(f, i) for i, f in enumerate(fs))
        grupos.append(f'''<section class="grupo" id="linea-{l['id']}" data-grupo="{l['id']}" style="{estilo_linea(l)}" aria-labelledby="g-{l['id']}">
    <div class="envoltura">
      <div class="grupo__cabeza"><span class="grupo__sello" aria-hidden="true"></span><h3 id="g-{l['id']}">{l['nombre']}</h3><p>{e(l['texto'])}</p></div>
      <ul class="rejilla">{items}</ul>
    </div>
  </section>''')
    bloques.append(f'''<section class="bloque" id="bolsas" data-grupo="bolsas" aria-labelledby="b-bolsas">
  <div class="bloque__cabeza"><div class="envoltura"><h2 id="b-bolsas">Bolsas</h2><p>Hierbas, sazonadores, especias, repostería y línea saludable en bolsa.</p></div></div>
  {"".join(grupos)}
</section>''')
    envases = [f for f in FAMILIAS if f["tipo"] == "envase"]
    items = "".join(tarjeta(f, i, linea=True) for i, f in enumerate(envases))
    bloques.append(f'''<section class="bloque bloque--envases" id="frascos" data-grupo="envases" aria-labelledby="b-envases">
  <div class="bloque__cabeza"><div class="envoltura"><h2 id="b-envases">Frascos y tarros</h2><p>Frascos, frascos molino y tarros para la cocina, la mesa y el negocio.</p></div></div>
  <div class="envoltura"><ul class="rejilla">{items}</ul></div>
</section>''')
    cuerpo = f'''<section class="cabeza-verde" aria-labelledby="t-cat">
  <div class="envoltura cabeza-verde__rejilla">
    <div>
      <h1 id="t-cat">Productos</h1>
      <p class="portada__texto">Un amplio portafolio en bolsas, frascos y tarros. Abre cualquier producto para ver sus presentaciones y gramajes.</p>
    </div>
    <div class="cabeza-verde__bolsas" aria-hidden="true">{foto(FA["canela-molida"], False, "")}{foto(FA["adobo-6-alinos"], False, "")}{foto(FA["oregano-entero"], False, "")}</div>
  </div>
</section>
<div class="filtros" id="filtros">
  <div class="envoltura">
    <div class="filtros__fila filtros__lineas" role="group" aria-label="Línea">{tabs}</div>
    <div class="filtros__fila" role="group" aria-label="Presentación"><span class="filtros__rotulo">Presentación</span>{fp}
      <label class="buscar-caja"><span class="sr">Buscar producto</span><input class="buscar" type="search" id="buscar" placeholder="Buscar producto"></label>
    </div>
  </div>
</div>
<p class="sr" id="contador" aria-live="polite"></p>
<div id="rejilla">{"".join(bloques)}</div>
<div class="envoltura"><p class="vacio" id="vacio" hidden>No encontramos productos con esos filtros. Prueba con otra línea, otra presentación u otra búsqueda.</p></div>
'''
    pagina("catalogo.html", "Productos · El Cocinerito", "Catálogo de condimentos, especias, hierbas, sazonadores, repostería, línea saludable y Línea Gourmet El Cocinerito.", cuerpo, dialogo=True)

# ------------------------------------------------------------- producto (una página por familia)
def productos():
    for f in FAMILIAS:
        l = L[f["linea"]]
        rel = [x for x in FAMILIAS if x["id"] != f["id"] and x["linea"] == f["linea"]]
        rel += [x for x in FAMILIAS if x["id"] != f["id"] and x not in rel and x["foto"]]
        rel_html = "".join(tarjeta(x, i) for i, x in enumerate(rel[:4]))
        linea_href = "linea-gourmet.html" if f["linea"] == "gourmet" else f"catalogo.html#linea-{f['linea']}"
        cuerpo = f'''<section class="detalle" style="{estilo_linea(l)}" aria-labelledby="t-prod">
  <div class="envoltura">
    <nav class="migas" aria-label="Ruta"><a href="catalogo.html">Productos</a> / <a href="{linea_href}">{l['nombre']}</a></nav>
    <div class="detalle__rejilla">
      <div class="detalle__foto"><span class="detalle__circulo" aria-hidden="true"></span>{foto(f, False)}</div>
      <div class="detalle__info">
        <p class="detalle__linea">{punto(l)}{l['nombre']}</p>
        <h1 id="t-prod">{e(f['nombre'])}</h1>
        <h2 class="dialogo__sub">Presentaciones y gramajes</h2>
        {tabla_variantes(f)}
        <div class="acciones"><a class="boton" href="catalogo.html">Ver todo el portafolio</a></div>
        <p class="aviso">Imagen de referencia. La información oficial del producto es la que figura en su etiqueta.</p>
      </div>
    </div>
  </div>
</section>
<section class="seccion envoltura" aria-labelledby="t-rel">
  <h2 id="t-rel" class="titulo-seccion">También te puede interesar</h2>
  <ul class="rejilla">{rel_html}</ul>
</section>'''
        desc = f"{f['nombre']} El Cocinerito, línea {l['nombre']}: " + "; ".join(f"{(v['forma'] + ' ') if v['forma'] else ''}{v['envase'].lower()} {', '.join(v['gramajes'])}" for v in f["variantes"]) + "."
        pagina(f"producto-{f['id']}.html", f"{f['nombre']} · El Cocinerito", desc, cuerpo, actual="catalogo.html", dialogo=True)

# ------------------------------------------------------------- línea gourmet
def linea_gourmet():
    cuerpo = f'''<section class="envoltura portada portada--partida" aria-labelledby="t-lg">
  <div>
    <h1 id="t-lg">Línea Gourmet</h1>
    <div class="acciones"><a class="boton boton--crema" href="{wa('Hola, quiero información sobre la Línea Gourmet de El Cocinerito para mi negocio.')}" target="_blank" rel="noopener">{ICON_WA}Preguntar por WhatsApp</a></div>
  </div>
  <p class="portada__texto">Pimienta negra entera y mezcla de pimientas en frasco molino. Una línea con presentación propia para la mesa, la cocina y el servicio de restaurantes y hoteles.</p>
</section>
{bloque_gourmet(enlace=False)}
<section class="envoltura seccion" aria-labelledby="t-lg-b2b" style="padding-bottom:var(--seccion)">
  <div class="dos">
    <h2 id="t-lg-b2b">Para tiendas, hoteles y restaurantes</h2>
    <div class="prosa"><p>Si quieres la Línea Gourmet en tu negocio o en tu servicio de mesa, escríbenos y te contamos disponibilidad y condiciones.</p></div>
  </div>
</section>'''
    pagina("linea-gourmet.html", "Línea Gourmet · El Cocinerito", "Línea Gourmet El Cocinerito: Pimienta Negra Entera y Mix Pimienta en frasco molino.", cuerpo, clase_body="pagina-oscura", dialogo=True)

# ------------------------------------------------------------- empresas
def empresas():
    tipos = "".join(f'<option value="{p["id"]}">{p["nombre"]}</option>' for p in PERFILES)
    filas = "".join(f'<li class="aparece" style="--i:{i}"><a href="{wa(p["mensaje"])}" target="_blank" rel="noopener"><span>{p["nombre"]}</span><span class="perfiles__accion">{ICON_WA} Escribir {ICON_FLECHA}</span></a></li>' for i, p in enumerate(PERFILES))
    cuerpo = f'''<section class="cabeza-verde" aria-labelledby="t-emp">
  <div class="envoltura cabeza-verde__rejilla">
    <div>
      <h1 id="t-emp">Para empresas</h1>
      <p class="portada__texto">Trabajamos con distribuidores, supermercados, tiendas, restaurantes, hoteles y empresas que quieren su propia marca. Cuéntanos qué necesitas.</p>
      <div class="acciones"><a class="boton boton--crema" href="#formulario">Solicitar información</a><a class="boton boton--fantasma" href="{wa(PF['distribuidor']['mensaje'])}" target="_blank" rel="noopener">{ICON_WA}WhatsApp</a></div>
    </div>
    <div class="cabeza-verde__bolsas" aria-hidden="true">{foto(FA["ajo-molido"], False, "")}{foto(FA["adobo-6-alinos"], False, "")}{foto(FA["oregano-entero"], False, "")}</div>
  </div>
</section>
<section class="seccion envoltura" aria-labelledby="t-perfiles">
  <div class="dos">
    <div>
      <h2 id="t-perfiles" class="aparece">Escríbenos según tu negocio</h2>
      <p class="aparece" style="--i:1;margin-top:18px;max-width:40ch">Cada opción abre WhatsApp con un mensaje listo para que te atienda la persona indicada.</p>
    </div>
    <ul class="perfiles">{filas}</ul>
  </div>
</section>
<div class="seccion">{bloque_marca_propia(con_enlace=False)}</div>
{bloque_tiendas()}
<section class="seccion envoltura" aria-labelledby="t-pasos">
  <div class="dos">
    <h2 id="t-pasos" class="aparece">Cómo empezar</h2>
    <ol class="pasos">
      <li class="aparece"><strong>Escríbenos</strong><span>Por WhatsApp o con el formulario de esta página.</span></li>
      <li class="aparece" style="--i:1"><strong>Recibe el portafolio</strong><span>Te enviamos las referencias, presentaciones y gramajes.</span></li>
      <li class="aparece" style="--i:2"><strong>Acordamos condiciones</strong><span>Definimos contigo las condiciones comerciales según tu negocio.</span></li>
    </ol>
  </div>
</section>
<section class="seccion envoltura" aria-labelledby="t-form" id="formulario">
  <div class="dos">
    <div class="prosa">
      <h2 id="t-form">Solicita información comercial</h2>
      <p>Pedimos solo los datos necesarios para responderte. Los usamos para atender esta solicitud y, si lo autorizas aparte, para enviarte novedades del portafolio.</p>
      <p>Para conocer, actualizar, rectificar o suprimir tus datos, escribe a <a class="enlace" href="mailto:{EMPRESA['correo']}">{EMPRESA['correo']}</a>. Más información en la <a class="enlace" href="legal.html#datos">Política de tratamiento de datos</a>.</p>
    </div>
    <form class="form" id="form-b2b" novalidate>
      <label><span>Nombre</span><input name="nombre" required autocomplete="name"></label>
      <label><span>Empresa</span><input name="empresa" required autocomplete="organization"></label>
      <label><span>Tipo de negocio</span><select name="tipo" required><option value="">Elige una opción</option>{tipos}<option value="marca-propia">Quiero mi propia marca</option></select></label>
      <label><span>Ciudad</span><input name="ciudad" required autocomplete="address-level2"></label>
      <label><span>WhatsApp o teléfono</span><input name="telefono" type="tel" required autocomplete="tel" inputmode="tel"></label>
      <label><span>Correo <span class="opc">(opcional)</span></span><input name="correo" type="email" autocomplete="email"></label>
      <label class="ancho"><span>¿Qué necesitas? <span class="opc">(opcional)</span></span><textarea name="mensaje" maxlength="800"></textarea></label>
      <label class="consentimiento ancho"><input type="checkbox" name="autoriza" required><span>Autorizo a {e(EMPRESA['razonSocial'])} a tratar mis datos personales para responder esta solicitud, según la <a href="legal.html#datos">Política de tratamiento de datos personales</a>. (Obligatorio)</span></label>
      <label class="consentimiento ancho"><input type="checkbox" name="novedades"><span>Quiero recibir novedades del portafolio por WhatsApp o correo. (Opcional)</span></label>
      <p class="error ancho" id="form-error" role="alert"></p>
      <button class="boton" type="submit">Enviar solicitud</button>
      <div class="exito ancho" id="form-exito" hidden tabindex="-1"><strong>Gracias, recibimos tu solicitud.</strong> El área comercial te contactará pronto.</div>
    </form>
  </div>
</section>'''
    pagina("empresas.html", "Para empresas · El Cocinerito", "Distribuidores, supermercados, restaurantes y fabricación de marca propia: solicita información comercial de El Cocinerito.", cuerpo)

# ------------------------------------------------------------- nosotros
def nosotros():
    cuerpo = f'''<section class="cabeza-verde" aria-labelledby="t-nos">
  <div class="envoltura cabeza-verde__rejilla">
    <div>
      <h1 id="t-nos">Quiénes somos</h1>
      <p class="portada__texto">Industria de Alimentos El Cocinerito inició operaciones en mayo de 1984 para elaborar condimentos. Hoy atiende el mercado colombiano con su marca comercial y con marcas propias para otros clientes.</p>
    </div>
    <img class="cabeza-verde__chef" src="img/chef-cuchara.webp" width="576" height="1100" alt="El personaje de El Cocinerito con una cuchara de palo y el pulgar arriba">
  </div>
</section>
<section class="seccion envoltura" aria-labelledby="t-hist">
  <h2 id="t-hist" class="titulo-seccion aparece">Nuestra historia</h2>
  <ol class="historia">
    <li class="aparece"><strong>1984</strong><p>Iniciamos operaciones en mayo, elaborando condimentos con las marcas El Cocinerito, Trisabor y El Condimenterito.</p></li>
    <li class="aparece" style="--i:1"><strong>Después</strong><p>Ampliamos el portafolio con las líneas de repostería, granos y alimentos saludables.</p></li>
    <li class="aparece" style="--i:2"><strong>Hoy</strong><p>Llegamos a almacenes de retail, mayoristas y a los canales institucional e industrial, con nuestra marca y con marcas propias.</p></li>
    <li class="aparece" style="--i:3"><strong>2030</strong><p>Queremos ser reconocidos en Colombia y en el exterior, con énfasis en sostenibilidad y responsabilidad social.</p></li>
  </ol>
</section>
<section class="seccion envoltura" aria-label="Misión y visión">
  <div class="mision">
    <div class="mision__bloque mision__bloque--verde aparece"><h2>Misión</h2><p>Desarrollar productos alimenticios de alta calidad y uso práctico que permitan experimentar en los consumidores nacionales e internacionales nuevas sensaciones de sabor en las comidas, brindando diversas alternativas que generen satisfacción al buen gusto.</p></div>
    <div class="mision__bloque mision__bloque--mostaza aparece" style="--i:1"><h2>Visión</h2><p>Para el año 2030 El Cocinerito espera haber alcanzado el reconocimiento en el mercado nacional e internacional, como empresa colombiana que brinda a sus consumidores diversas sensaciones de sabores y productos de uso confiable, con énfasis en sostenibilidad y responsabilidad social.</p></div>
  </div>
</section>
<div class="seccion">{bloque_planta()}</div>
<section class="seccion envoltura" aria-labelledby="t-datos">
  <div class="dos">
    <h2 id="t-datos">Datos de la empresa</h2>
    <dl class="datos">
      <div><dt>Razón social</dt><dd>{e(EMPRESA['razonSocial'])}</dd></div>
      <div><dt>NIT</dt><dd>{EMPRESA['nit']}</dd></div>
      <div><dt>Planta</dt><dd>{e(EMPRESA['planta'])}, {e(EMPRESA['ciudad'])}</dd></div>
      <div><dt>Comercial</dt><dd><a class="enlace" href="mailto:{EMPRESA['correo']}">{EMPRESA['correo']}</a><br>{EMPRESA['whatsappVisible']}</dd></div>
    </dl>
  </div>
</section>'''
    pagina("nosotros.html", "Nosotros · El Cocinerito", "Industria de Alimentos El Cocinerito S.A.S.: desde 1984, planta en Santander de Quilichao, certificaciones ISO 22000, GMP-HACCP y BPM.", cuerpo)

# ------------------------------------------------------------- contacto
def contacto():
    cuerpo = f'''<section class="cabeza-verde" aria-labelledby="t-con">
  <div class="envoltura">
    <h1 id="t-con">Contacto</h1>
    <p class="portada__texto">La forma más rápida de hablar con nosotros es WhatsApp. Si representas una empresa, también puedes usar el formulario comercial.</p>
  </div>
</section>
{bloque_whatsapp("Escríbenos por WhatsApp", "Elige tu tipo de negocio y te abrimos el chat con un mensaje listo.", "t-wa-con")}
<section class="seccion envoltura" aria-labelledby="t-canales">
  <h2 id="t-canales" class="titulo-seccion">Otros canales</h2>
  <ul class="canales canales--cuatro">
    <li class="aparece"><h3>WhatsApp comercial</h3><p><a class="enlace" href="{wa(PF['otro']['mensaje'])}" target="_blank" rel="noopener">{EMPRESA['whatsappVisible']}</a></p></li>
    <li class="aparece" style="--i:1"><h3>Área comercial</h3><p><a class="enlace" href="mailto:{EMPRESA['correo']}">{EMPRESA['correo']}</a></p></li>
    <li class="aparece" style="--i:2"><h3>Planta de producción</h3><p>{e(EMPRESA['planta'])}<br>{e(EMPRESA['ciudad'])}</p></li>
    <li class="aparece" style="--i:3"><h3>Formulario para empresas</h3><p><a class="enlace" href="empresas.html#formulario">Ir al formulario</a></p></li>
  </ul>
</section>'''
    pagina("contacto.html", "Contacto · El Cocinerito", "Contacta al área comercial de El Cocinerito por WhatsApp o correo.", cuerpo)


# ------------------------------------------------------------- legal
def legal():
    R, N, C, D = e(EMPRESA['razonSocial']), EMPRESA['nit'], EMPRESA['correo'], f"{e(EMPRESA['planta'])}, {e(EMPRESA['ciudad'])}"
    cuerpo = f'''<section class="envoltura portada" aria-labelledby="t-leg">
  <h1 id="t-leg">Información legal</h1>
  <p class="portada__texto">Política de tratamiento de datos, aviso de privacidad, términos de uso y cookies de este sitio.</p>
</section>
<section class="seccion envoltura seccion--corta" aria-label="Documentos legales">
  <div class="dos">
    <nav aria-label="Documentos" class="legal-nav"><ul>
      <li><a class="enlace" href="#datos">Política de tratamiento de datos</a></li>
      <li><a class="enlace" href="#aviso">Aviso de privacidad</a></li>
      <li><a class="enlace" href="#terminos">Términos de uso</a></li>
      <li><a class="enlace" href="#cookies">Cookies</a></li>
    </ul></nav>
    <div class="prosa legal">
      <h2 id="datos">Política de tratamiento de datos personales</h2>
      <p>Esta política se adopta en cumplimiento de la Ley 1581 de 2012 y del Decreto 1074 de 2015 (Capítulo 25, Título 2, Parte 2, Libro 2).</p>
      <h3>Responsable del tratamiento</h3>
      <p>{R}, NIT {N}, con domicilio en {D}. Correo: {C}.</p>
      <h3>Datos que recogemos y para qué</h3>
      <p>A través de este sitio recogemos los datos que la persona entrega voluntariamente en el formulario comercial o al escribirnos por WhatsApp o correo: nombre, empresa, tipo de negocio, ciudad, teléfono y, si lo da, correo y mensaje. Los usamos para:</p>
      <ul>
        <li>Responder la solicitud y gestionar la relación comercial.</li>
        <li>Enviar información de productos y novedades, solo si la persona lo autoriza de forma separada.</li>
        <li>Cumplir obligaciones legales y atender requerimientos de autoridades.</li>
      </ul>
      <p>No recogemos datos sensibles ni datos de niños, niñas o adolescentes a través del sitio. No vendemos ni cedemos los datos a terceros para fines comerciales.</p>
      <h3>Derechos del titular</h3>
      <p>El titular de los datos puede: conocer, actualizar y rectificar sus datos; pedir prueba de la autorización otorgada; ser informado sobre el uso que se ha dado a sus datos; presentar quejas ante la Superintendencia de Industria y Comercio; revocar la autorización o pedir la supresión de sus datos cuando no exista un deber legal o contractual de conservarlos; y acceder gratuitamente a sus datos.</p>
      <h3>Cómo ejercer los derechos</h3>
      <p>El área responsable de atender consultas y reclamos es el área comercial, en el correo {C}. La solicitud debe incluir el nombre del titular, su identificación, la descripción de lo que pide y un dato de contacto.</p>
      <ul>
        <li><strong>Consultas:</strong> se responden en máximo diez (10) días hábiles desde su recibo. Si no es posible, se informarán los motivos y se responderá en máximo cinco (5) días hábiles adicionales.</li>
        <li><strong>Reclamos</strong> (corrección, actualización, supresión o incumplimiento): se responden en máximo quince (15) días hábiles desde el día siguiente a su recibo, prorrogables hasta por ocho (8) días hábiles informando los motivos.</li>
      </ul>
      <h3>Vigencia</h3>
      <p>Esta política rige desde su publicación en este sitio. Los datos se conservarán mientras sean necesarios para las finalidades descritas o mientras exista una obligación legal. Cualquier cambio sustancial se comunicará en este sitio.</p>

      <h2 id="aviso">Aviso de privacidad</h2>
      <p>{R}, NIT {N}, con domicilio en {D}, es responsable del tratamiento de los datos personales que entregues en este sitio. Los usaremos para responder tu solicitud y, solo si lo autorizas, para enviarte información de nuestros productos.</p>
      <p>Como titular puedes conocer, actualizar, rectificar y suprimir tus datos, revocar la autorización y presentar quejas ante la Superintendencia de Industria y Comercio. Para ejercer estos derechos escribe a {C}.</p>
      <p>Puedes consultar la Política de tratamiento de datos personales completa en esta misma página.</p>

      <h2 id="terminos">Términos de uso</h2>
      <h3>Objeto del sitio</h3>
      <p>Este sitio presenta a {R} y su portafolio de productos. Es un sitio informativo: no vende productos en línea ni procesa pagos. Las cotizaciones y pedidos se acuerdan directamente con el área comercial.</p>
      <h3>Información de productos</h3>
      <p>Las imágenes son de referencia. La información oficial de cada producto (ingredientes, contenido neto, registro sanitario, fechas y modo de uso) es la que figura en su etiqueta. La disponibilidad de referencias y presentaciones puede cambiar sin previo aviso.</p>
      <h3>Propiedad intelectual</h3>
      <p>Las marcas, logotipos, diseños de empaque, fotografías y textos de este sitio son de {R} o se usan con autorización. No pueden copiarse, modificarse ni usarse con fines comerciales sin permiso escrito.</p>
      <h3>Enlaces a servicios de terceros</h3>
      <p>Algunos botones abren servicios externos como WhatsApp o redes sociales. Esos servicios tienen sus propios términos y políticas de privacidad, que recomendamos revisar.</p>
      <h3>Responsabilidad</h3>
      <p>Procuramos que la información del sitio sea correcta y esté actualizada, pero puede contener errores u omisiones que corregiremos cuando los detectemos. No respondemos por interrupciones del sitio ajenas a nuestro control.</p>
      <h3>Cambios y ley aplicable</h3>
      <p>Podemos actualizar estos términos; la versión vigente es la publicada en este sitio. Se rigen por las leyes de la República de Colombia. Para preguntas, escribe a {C}.</p>

      <h2 id="cookies">Política de cookies</h2>
      <p>Las cookies son pequeños archivos que un sitio guarda en el navegador para recordar información sobre la visita.</p>
      <p>Por ahora este sitio no usa cookies de analítica, publicidad ni seguimiento. Las fuentes tipográficas se cargan desde Google Fonts, un servicio que puede registrar datos técnicos de la conexión, como la dirección IP.</p>
      <p>Si más adelante incorporamos herramientas de analítica, píxeles de redes sociales o videos incrustados, actualizaremos esta política, explicaremos qué cookies usan y para qué, y pediremos tu aceptación antes de activarlas. Siempre podrás borrar o bloquear las cookies desde la configuración de tu navegador.</p>
    </div>
  </div>
</section>'''
    pagina("legal.html", "Información legal · El Cocinerito", "Política de tratamiento de datos, aviso de privacidad, términos de uso y cookies de El Cocinerito.", cuerpo)

def datos_js():
    data = {"bolsa": BOLSA_SVG, "empresa": EMPRESA, "lineas": LINEAS, "presentaciones": PRESENTACIONES, "perfiles": PERFILES,
            "familias": FAMILIAS}
    with open(os.path.join(OUT, "js", "datos.js"), "w", encoding="utf-8") as f:
        f.write("/* Generado por generar.py a partir de datos/productos.csv. */\n")
        f.write("window.COCINERITO = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")

if __name__ == "__main__":
    for viejo in ["linea-negra.html", "recetas.html"]:
        ruta = os.path.join(OUT, viejo)
        if os.path.exists(ruta):
            os.remove(ruta)
    for n in os.listdir(OUT):
        if n.startswith("producto-") and n.endswith(".html"):
            os.remove(os.path.join(OUT, n))
    datos_js(); inicio(); catalogo(); productos(); linea_gourmet(); empresas(); nosotros(); contacto(); legal()
    print("ok", len(PRODUCTOS), "filas del Excel,", len(FAMILIAS), "productos en el catálogo")
