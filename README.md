# Sitio web El Cocinerito · versión final

Versión definitiva del sitio corporativo, lista para subir a la web. Son páginas HTML estáticas (carpeta `sitio/`): funcionan en cualquier hosting sin instalar nada. Si luego se elige WordPress, Webflow u otra plataforma, este sitio sirve de base.

## Cómo verlo
Abre `sitio/index.html` en el navegador. `sitio/vista-previa.html` es solo una portada interna con el índice de páginas y no hace falta subirla.

## Cómo subirlo
Sube el contenido de la carpeta `sitio/` a la raíz del hosting. La página de inicio es `index.html`.

## Cambios de la versión final
1. **Foto exterior de la planta** en "Fabricamos tu propia marca", en el inicio y en Para empresas.
2. **Dos productos nuevos:** Adobo 7 Hierbas (bolsa de 60 g) y Ajo Molido en bolsa (15 g). El sitio muestra 21 productos.
3. **Sin sección de Recetas.** Se quitó la página y todos sus enlaces.
4. **Sin WhatsApp dentro del portafolio.** El catálogo, las fichas de producto y la ventana de cada producto ya no tienen botones de cotizar ni el botón flotante. WhatsApp sigue en el menú, en Para empresas, en Contacto y en el resto del sitio, para posibles clientes.
5. **"Acordamos condiciones"** en Para empresas, sin el texto entre paréntesis.
6. **Sin marcadores de pendiente.** Se quitaron los espacios vacíos de fotos de proceso y equipo, y las notas de borrador de los textos legales. Las solicitudes de datos personales las atiende el área comercial y la política rige desde su publicación.

## Antes de publicar
- **Textos legales:** deben ser revisados por un abogado (Ley 1581 de 2012).
- **Formulario de Para empresas:** valida los datos, pero para que llegue a un correo hay que conectarlo en el hosting (por ejemplo, Formspree, Netlify Forms o el formulario de WordPress).
- En la foto de Paprika la etiqueta dice 12 g, pero el Excel dice 15 g. El sitio usa el Excel.
- Tipografías: Bricolage Grotesque y Outfit, porque Banilu y Skandia necesitan licencia para usarse en web.

## Productos
- **Del Excel:** Hierbas, Sazonadores y Tradicionales.
- **Fuera del Excel (a partir de las fotos):** Repostería y la Línea Gourmet, entre ellos Ciruelas pasas, Ajonjolí, Linaza molida, Mix Pimienta y Pimienta Negra Entera. Solo aparecen los productos que tienen foto; los demás siguen en `datos/productos.csv` y aparecen solos en cuanto tengan foto.

## Cómo actualizar
- **Productos:** reemplaza `datos/portafolio.xlsx` y ejecuta `python3 herramientas/importar_excel.py` y luego `python3 herramientas/generar.py`.
- **Fotos de producto:**
  1. Copia la imagen, idealmente PNG o WebP con fondo transparente, a `sitio/img/`.
  2. Añade una fila en `datos/fotos.csv`.
- **Logos de supermercados:**
  1. Copia los archivos a `sitio/img/tiendas/`.
  2. Escribe la ruta en `TIENDAS` dentro de `herramientas/generar.py`.
- **Foto exterior de la planta:** reemplaza `sitio/img/planta-exterior.webp`.

Si prefieres, envíame los archivos y lo regenero yo.
