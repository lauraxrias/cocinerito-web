#!/usr/bin/env python3
"""Convierte datos/portafolio.xlsx (columnas DESCRIPCION, CATEGORIA, COLOR) en
datos/productos.csv, agrupando los gramajes de un mismo producto y presentación.
Suma las filas de datos/otras-lineas.csv (repostería, saludable, gourmet).
Las fotos se asignan con datos/fotos.csv (id,foto) si existe."""
import csv, os, re, unicodedata
import openpyxl

BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, "..", "datos")
COLOR_LINEA = {"VERDE": "hierbas", "ROJO": "sazonadores", "AMARILLO": "tradicionales",
               "MORADO": "reposteria", "CREMA": "saludable", "BLANCO": "saludable", "NEGRO": "gourmet"}
TILDES = {"OREGANO": "Orégano", "ANIS": "Anís", "ESTRAGON": "Estragón", "RAIZ": "Raíz", "ALIÑOS": "Aliños",
          "AJONJOLI": "Ajonjolí", "SIETE": "7"}
MINUS = {"de", "con", "y"}

def bonito(t):
    pal = []
    for i, w in enumerate(t.split()):
        if w in TILDES: pal.append(TILDES[w]); continue
        lw = w.lower()
        pal.append(lw if (lw in MINUS and i) else lw.capitalize())
    return " ".join(pal)

def slug(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")

def analizar(desc):
    d = re.sub(r"\s+", " ", desc.upper()).strip()
    d = d.replace("EL COCINERITO", "").replace("COCINERITO", "").replace("DOCENA", "").strip()
    m = re.search(r"(\d+)\s*(G|GR|GRS|GRAMOS)\b", d)
    gram = f"{m.group(1)} g" if m else ""
    pres, envase = "bolsa", "Bolsa"
    if "FRASCO" in d: pres, envase = "frasco", "Frasco"
    if "TARRO" in d: pres, envase = "tarro", "Tarro"
    nombre = re.sub(r"\b(X\s*)?\d+\s*(G|GR|GRS|GRAMOS)\b", "", d)
    nombre = re.sub(r"\b(FRASCO|TARRO|X)\b", "", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    nombre = nombre.replace("COLOR ACHIOTE", "COLOR CON ACHIOTE").replace("ADOBO SIETE HIERBAS", "ADOBO 7 HIERBAS")
    return bonito(nombre), pres, envase, gram

def gnum(g):
    return int(re.sub(r"\D", "", g) or 0)

def main():
    wb = openpyxl.load_workbook(os.path.join(D, "portafolio.xlsx"), data_only=True)
    ws = wb.active
    cab = [str(c.value or "").strip().upper() for c in ws[1]]
    iD, iC = cab.index("DESCRIPCION"), cab.index("COLOR")
    fotos = {}
    rf = os.path.join(D, "fotos.csv")
    if os.path.exists(rf):
        with open(rf, encoding="utf-8") as f:
            fotos = {r["id"]: r["foto"] for r in csv.DictReader(f)}
    grupos = {}
    for fila in ws.iter_rows(min_row=2, values_only=True):
        if not fila[iD]: continue
        nombre, pres, envase, gram = analizar(str(fila[iD]))
        linea = COLOR_LINEA.get(str(fila[iC] or "").strip().upper(), "tradicionales")
        id_ = slug(nombre) + ("" if pres == "bolsa" else "-" + pres)
        g = grupos.setdefault(id_, {"id": id_, "nombre": nombre, "linea": linea, "presentacion": pres, "envase": envase, "gramajes": []})
        if gram and gram not in g["gramajes"]: g["gramajes"].append(gram)
    filas = []
    for g in grupos.values():
        g["gramajes"] = "; ".join(sorted(g["gramajes"], key=gnum))
        g["foto"] = fotos.get(g["id"], "")
        filas.append(g)
    with open(os.path.join(D, "otras-lineas.csv"), encoding="utf-8") as f:
        filas += list(csv.DictReader(f))
    orden = ["hierbas", "sazonadores", "tradicionales", "reposteria", "saludable", "gourmet"]
    filas.sort(key=lambda r: (orden.index(r["linea"]), r["nombre"], r["presentacion"]))
    with open(os.path.join(D, "productos.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "nombre", "linea", "presentacion", "envase", "gramajes", "foto"])
        w.writeheader(); w.writerows(filas)
    print(len(filas), "productos")

if __name__ == "__main__":
    main()
