# Sepp Web Server

Serviço de hospedagem de imagens criadas por Daniel Sepp.

## Como rodar localmente

```bash
cd ~/dev/projects/sepp-web-server
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-multipart

uvicorn app.main:app --reload
```

Acesse http://127.0.0.1:8000

### Teste de Upload

```bash
curl -F "file=@imagem.jpg" http://localhost:8000/upload
```

## Imagens

Coloque suas imagens em `public/images/`. O arquivo `server-background.JPG` já está configurado como wallpaper.

---

## 🚀 Deploy Vercel Manual

### Passo 1: Push para GitHub

```bash
./git-deploy.sh
```

### Passo 2: Importar no Vercel

1. Acesse [vercel.com/dashboard](https://vercel.com/dashboard)
2. Clique em **"New Project"**
3. Clique em **"Import Git Repository"**
4. Selecione `seppdaniel/sepp-web-server`
5. Configure:
   - Framework Preset: **Other**
   - Build Command: `pip install -r requirements.txt` (ou deixe vazio)
   - Output Directory: `public`
6. Clique **Deploy**

### Passo 3: Copie a URL

Após o deploy, copie a URL gerada (ex: `https://sepp-web-server.vercel.app`)

---

## Estrutura do Projeto

```
sepp-web-server/
├── api/
│   └── index.py          # FastAPI app (Vercel)
├── app/
│   ├── main.py           # FastAPI app (local)
│   └── templates/
│       └── index.html    # Template Jinja2
├── public/
│   ├── css/styles.css    # Estilos
│   ├── js/gallery.js     # JavaScript galeria + upload
│   ├── images/           # Imagens (upload)
│   ├── index.html
│   └── server-background.JPG
├── pyproject.toml
├── runtime.txt
├── vercel.json
└── git-deploy.sh
```

---

## API Endpoints

- `GET /` - Página principal com galeria
- `POST /upload` - Upload de imagem (multipart/form-data)
- `GET /api/images` - Lista de imagens (JSON)
- `GET /{path}` - Servir arquivos estáticos

---

*The heavens declare the glory of God* ✦
