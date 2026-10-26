"""Copia corregida del plan de trabajo v2 → Plan_de_Trabajo_v3.pdf (apellido y estado de los objetivos).

Uso:  python generar_plan_v3.py "D:/2.Tesina/tesis version 2.0/pipeline_productivo/01_business_understanding/plan_de_trabajo_v2.pdf" ../09_entrega_final/Plan_de_Trabajo_v3.pdf
No modifica el original: lo lee y escribe la copia corregida.
"""
import sys
import pymupdf

ORIGEN, DESTINO = sys.argv[1], sys.argv[2]
ARIAL, ARIAL_B = "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"
doc = pymupdf.open(ORIGEN)
f_arial = pymupdf.Font(fontfile=ARIAL)

# (página, texto del span original, texto nuevo, alineación)
CAMBIOS = [(0, "Nicolas Didi", "Nicolás Diego Diddi", "centro"),
           (3, "BETO sobre noticias financieras argentinas. [En proceso]", "BETO sobre noticias financieras argentinas. [Completado]", "izq"),
           (3, "para la detección y validación de shocks informativos. [Completado]", "para la detección y validación de shocks informativos. [No realizado]", "izq"),
           (3, "noticioso. [En revisión]", "noticioso. [Completado]", "izq"),
           (3, "flujo informativo. [En revisión]", "flujo informativo. [Completado]", "izq"),
           (3, "del flujo de noticias. [Constituye el núcleo de la tesina]", "del flujo de noticias. [Completado]", "izq")]
CAMBIOS += [(i, f"Frigoni – Didi  |  {i + 1}", f"Frigoni – Diddi  |  {i + 1}", "der") for i in range(doc.page_count)]

hechos = 0
for pag, viejo, nuevo, alin in CAMBIOS:
    page = doc[pag]
    spans = [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"] if s["text"].strip() == viejo]
    assert len(spans) == 1, (pag, viejo, len(spans))
    s = spans[0]
    x0, y0, x1, y1 = s["bbox"]
    page.add_redact_annot(pymupdf.Rect(x0 - 0.5, y0 + 1, x1 + 0.5, y1 - 1), fill=(1, 1, 1))
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    ancho = f_arial.text_length(nuevo, fontsize=s["size"])
    ancho_viejo = f_arial.text_length(viejo, fontsize=s["size"])
    x = {"izq": s["origin"][0], "centro": s["origin"][0] + (ancho_viejo - ancho) / 2, "der": s["origin"][0] + ancho_viejo - ancho}[alin]
    color = tuple(((s["color"] >> k) & 255) / 255 for k in (16, 8, 0))
    page.insert_text((x, s["origin"][1]), nuevo, fontsize=s["size"], fontname="arial", fontfile=ARIAL, color=color)
    hechos += 1

# Nota de versión en la portada y nota de estado en la página de objetivos.
p1 = doc[0]
nota1 = "Versión 3 · octubre de 2026: actualiza el estado de los objetivos y corrige el apellido de un autor."
w = f_arial.text_length(nota1, fontsize=9)
p1.insert_text(((p1.rect.width - w) / 2, 400), nota1, fontsize=9, fontname="arial", fontfile=ARIAL, color=(0.36, 0.42, 0.48))

p4 = doc[3]
caja = pymupdf.Rect(90, 505, 520, 640)
p4.insert_text((90, 510), "Estado de los objetivos (actualizado en octubre de 2026)", fontsize=11, fontname="arialbd", fontfile=ARIAL_B)
texto = ("Objetivo 3: no se realizó. Los datos de X/Twitter no llegaron a integrarse al análisis y quedan como trabajo futuro. "
         "Objetivo 6: se cumplió con un modelo VAR, pruebas de causalidad de Granger, funciones de impulso-respuesta, event studies "
         "y el análisis por régimen del HMM. El modelo de rezagos distribuidos (DLM) queda como trabajo futuro: el VAR ya mide "
         "los efectos con rezagos. El detalle de cada objetivo y de los resultados está en el documento de entrega final "
         "(Unión/09_entrega_final).")
sobra = p4.insert_textbox(pymupdf.Rect(90, 518, 520, 640), texto, fontsize=10.5, fontname="arial", fontfile=ARIAL, align=pymupdf.TEXT_ALIGN_JUSTIFY)
assert sobra >= 0, sobra
doc.set_metadata({**doc.metadata, "title": "Plan de trabajo v3", "modDate": pymupdf.get_pdf_now()})
doc.save(DESTINO, garbage=3, deflate=True)
print("cambios:", hechos, "· guardado en", DESTINO)
