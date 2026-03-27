from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import time

app = FastAPI(title="Sepp Web Server")

BASE_DIR = Path(__file__).resolve().parent.parent

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

public_dir = BASE_DIR / "public"
images_dir = public_dir / "images"


def get_images_from_public():
    """List all valid images from public/ folder, sorted by modification time."""
    images = []
    
    if not public_dir.exists():
        return []
    
    for file_path in public_dir.rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in VALID_EXTENSIONS:
                rel_path = file_path.relative_to(public_dir)
                url_path = "/" + str(rel_path).replace("\\", "/")
                name = file_path.stem.replace("-", " ").replace("_", " ")
                name = name.title()
                images.append({
                    "url": url_path,
                    "name": name,
                    "mtime": file_path.stat().st_mtime
                })
    
    images.sort(key=lambda x: x["mtime"], reverse=True)
    return images


@app.get("/", response_class=HTMLResponse)
async def root():
    images = get_images_from_public()
    
    template_path = BASE_DIR / "app" / "templates" / "index.html"
    html_content = template_path.read_text()
    
    start_marker = '{% for image in images %}'
    end_marker = '{% endfor %}'
    
    if images:
        items_html = ""
        for img in images:
            items_html += f'''
            <div class="gallery-item" data-src="{img["url"]}">
                <img src="{img["url"]}" alt="{img["name"]}">
                <div class="gallery-item-info">
                    <span>{img["name"]}</span>
                </div>
            </div>'''
        
        start_idx = html_content.find(start_marker)
        end_idx = html_content.find(end_marker) + len(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            html_content = html_content[:start_idx] + items_html + html_content[end_idx:]
        
        no_images_start = html_content.find('{% if not images %}')
        no_images_end = html_content.find('{% endif %}', no_images_start)
        if no_images_start != -1 and no_images_end != -1:
            html_content = html_content[:no_images_start] + html_content[no_images_end + len('{% endif %}'):]
    else:
        no_images_start = html_content.find('{% if not images %}')
        no_images_end = html_content.find('{% endif %}', no_images_start)
        if no_images_start != -1 and no_images_end != -1:
            for_start = html_content.find(start_marker)
            for_end = html_content.find(end_marker) + len(end_marker)
            if for_start != -1 and for_end != -1:
                before_loop = html_content[:for_start]
                after_endif = html_content[no_images_end + len('{% endif %}'):]
                no_images_msg = html_content[no_images_start:no_images_end + len('{% endif %}')]
                html_content = before_loop + no_images_msg + after_endif
    
    return html_content


@app.post("/upload", response_class=JSONResponse)
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload with validation."""
    
    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return JSONResponse(
            {"success": False, "error": "Arquivo muito grande. Máximo 10MB."},
            status_code=400
        )
    
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in VALID_EXTENSIONS:
        return JSONResponse(
            {"success": False, "error": f"Extensão inválida. Use: {', '.join(VALID_EXTENSIONS)}"},
            status_code=400
        )
    
    # Create images directory if not exists
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = int(time.time() * 1000)
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = images_dir / safe_filename
    
    # Save file
    content = await file.read()
    file_path.write_bytes(content)
    
    return {
        "success": True,
        "filename": safe_filename,
        "url": f"/images/{safe_filename}"
    }


@app.get("/api/images")
async def list_images():
    """API endpoint to list images."""
    return get_images_from_public()


@app.get("/{file_path:path}")
async def serve_file(file_path: str):
    full_path = BASE_DIR / "public" / file_path
    if full_path.is_file():
        return FileResponse(full_path)
    return FileResponse(BASE_DIR / "public" / "index.html")
