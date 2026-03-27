from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pathlib import Path
import time
import os

app = FastAPI(title="Sepp Web Server")

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
IMAGES_DIR = PUBLIC_DIR / "images"

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_images():
    images = []
    if not PUBLIC_DIR.exists():
        return []
    
    for fp in PUBLIC_DIR.rglob("*"):
        if fp.is_file() and fp.suffix.lower() in VALID_EXTENSIONS:
            rel = fp.relative_to(PUBLIC_DIR)
            url = "/" + str(rel).replace("\\", "/")
            name = fp.stem.replace("-", " ").replace("_", " ").title()
            images.append({"url": url, "name": name, "mtime": fp.stat().st_mtime})
    
    images.sort(key=lambda x: x["mtime"], reverse=True)
    return images


def render_template(images):
    template = (BASE_DIR / "app" / "templates" / "index.html").read_text()
    
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
    return render_template(get_images())


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


@app.get("/{path:path}")
async def serve(path: str):
    fp = PUBLIC_DIR / path
    if fp.is_file():
        return FileResponse(fp)
    return FileResponse(PUBLIC_DIR / "index.html")
