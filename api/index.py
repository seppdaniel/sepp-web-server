import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pathlib import Path
import time

app = FastAPI(title="Sepp Web Server")

# Detect base directory - Vercel uses /vercel/path1
if os.path.exists('/vercel/path1'):
    BASE_DIR = Path('/vercel/path1')
else:
    BASE_DIR = Path(os.environ.get('VERCEL_PATH', os.getcwd()))

PUBLIC_DIR = BASE_DIR / "public"
IMAGES_DIR = PUBLIC_DIR / "images"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_images():
    images = []
    if not PUBLIC_DIR.exists():
        return []
    
    for fp in PUBLIC_DIR.rglob("*"):
        if fp.is_file() and fp.suffix.lower() in VALID_EXTENSIONS:
            # Skip background image from gallery
            if "background" in fp.name.lower():
                continue
            rel = fp.relative_to(PUBLIC_DIR)
            url = "/" + str(rel).replace("\\", "/")
            name = fp.stem.replace("-", " ").replace("_", " ").title()
            images.append({"url": url, "name": name, "mtime": fp.stat().st_mtime})
    
    images.sort(key=lambda x: x["mtime"], reverse=True)
    return images


def render_template(images):
    # Debug: check if template file exists
    template_file = TEMPLATES_DIR / "index.html"
    if not template_file.exists():
        return f"<h1>Template not found at {template_file}</h1><p>BASE_DIR: {BASE_DIR}</p>"
    
    template = template_file.read_text()
    
    start = '{% for image in images %}'
    end = '{% endfor %}'
    
    if images:
        items = "".join(f'''
        <div class="gallery-item" data-src="{i["url"]}">
            <img src="{i["url"]}" alt="{i["name"]}">
            <div class="gallery-item-info"><span>{i["name"]}</span></div>
        </div>''' for i in images)
        
        idx_start = template.find(start)
        idx_end = template.find(end) + len(end)
        if idx_start != -1 and idx_end != -1:
            template = template[:idx_start] + items + template[idx_end:]
        
        # Remove no-images message
        no_img = template.find('{% if not images %}')
        no_img_end = template.find('{% endif %}', no_img)
        if no_img != -1 and no_img_end != -1:
            template = template[:no_img] + template[no_img_end + len('{% endif %}'):]
    
    return template


@app.get("/", response_class=HTMLResponse)
async def root():
    images = get_images()
    
    # Build gallery items HTML
    items_html = ""
    for img in images:
        items_html += f'''
        <div class="gallery-item" data-src="{img["url"]}">
            <img src="{img["url"]}" alt="{img["name"]}">
            <div class="gallery-item-info">
                <span>{img["name"]}</span>
            </div>
        </div>'''
    
    if not items_html:
        items_html = '<p class="no-images">Nenhuma imagem encontrada.</p>'
    
    # DEBUG: unique marker
    debug = "<!-- RENDERED_AT_2026 -->"
    
    # Inline complete HTML template
    template = debug + f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sepp Web Server</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/css/styles.css">
    <script src="/js/gallery.js" defer></script>
</head>
<body>
    <div class="overlay"></div>
    <header>
        <h1>✦ Sepp Web Server</h1>
        <p>Galeria de imagens criadas por Daniel Sepp</p>
    </header>
    <main>
        <section class="hero">
            <div class="glass-card">
                <h2>Bem-vindo ao Sepp Web Server</h2>
                <p>Seu espaço para imagens e criações</p>
            </div>
        </section>
    </main>
    <button class="fab" id="galleryBtn" aria-label="Abrir galeria">✨ Galeria Sepp</button>
    <aside class="gallery-panel" id="galleryPanel">
        <button class="gallery-close" id="galleryClose" aria-label="Fechar galeria">×</button>
        <h3>Galeria de Imagens</h3>
        <div class="upload-section">
            <form id="uploadForm" class="upload-form">
                <div class="upload-dropzone" id="dropzone">
                    <span class="upload-icon">📤</span>
                    <span>Arraste imagem ou clique</span>
                    <input type="file" id="fileInput" accept=".jpg,.jpeg,.png,.webp,.gif" hidden>
                </div>
                <div class="upload-preview" id="uploadPreview" hidden>
                    <img id="previewImg" src="" alt="Preview">
                    <button type="button" id="cancelUpload">✕</button>
                </div>
                <button type="submit" class="upload-btn" id="uploadBtn" hidden>Enviar</button>
                <div class="upload-progress" id="uploadProgress" hidden>
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                    <span>Enviando...</span>
                </div>
            </form>
        </div>
        <div class="trash-zone" id="trashZone">
            <span class="trash-icon">🗑️</span>
            <span>Arraste aqui para excluir</span>
        </div>
        <div class="gallery-grid" id="galleryGrid">{items_html}</div>
    </aside>
    <div class="lightbox" id="lightbox">
        <button class="lightbox-close" id="lightboxClose" aria-label="Fechar">×</button>
        <img src="" alt="Imagem ampliada" id="lightboxImg">
    </div>
</body>
</html>'''
    
    return HTMLResponse(template)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return JSONResponse({"success": False, "error": "Máx 10MB"}, status_code=400)
    
    ext = Path(file.filename).suffix.lower()
    if ext not in VALID_EXTENSIONS:
        return JSONResponse({"success": False, "error": "Extensão inválida"}, status_code=400)
    
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time() * 1000)
    filename = f"{timestamp}_{file.filename}"
    filepath = IMAGES_DIR / filename
    
    content = await file.read()
    filepath.write_bytes(content)
    
    return {"success": True, "filename": filename, "url": f"/images/{filename}"}


@app.get("/api/images")
async def list_images():
    return get_images()


@app.delete("/api/images")
async def delete_image(data: dict):
    url = data.get("url", "")
    
    if not url:
        return JSONResponse({"success": False, "error": "URL requerida"}, status_code=400)
    
    filename = url.lstrip("/")
    file_path = BASE_DIR / "public" / filename
    
    if not file_path.exists() or not file_path.is_file():
        return JSONResponse({"success": False, "error": "Arquivo não encontrado"}, status_code=404)
    
    try:
        file_path.unlink()
        return {"success": True, "message": "Imagem excluída"}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/css/{filename}")
async def serve_css(filename: str):
    print(f"CSS request: {filename}")
    print(f"PUBLIC_DIR: {PUBLIC_DIR}")
    fp = PUBLIC_DIR / "css" / filename
    print(f"Trying: {fp}, exists: {fp.is_file()}")
    if fp.is_file():
        return FileResponse(fp, media_type="text/css")
    return JSONResponse({"error": "Not found", "tried": str(fp)}, status_code=404)


@app.get("/js/{filename}")
async def serve_js(filename: str):
    fp = PUBLIC_DIR / "js" / filename
    if fp.is_file():
        return FileResponse(fp, media_type="application/javascript")
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/images/{filename}")
async def serve_images(filename: str):
    fp = PUBLIC_DIR / "images" / filename
    if fp.is_file():
        return FileResponse(fp)
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/{path:path}")
async def serve(path: str):
    # Try to serve static files from public directory
    fp = PUBLIC_DIR / path
    if fp.is_file():
        return FileResponse(fp)
    
    # Fallback to index.html
    return HTMLResponse(template)
