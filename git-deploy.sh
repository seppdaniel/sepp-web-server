#!/bin/bash
git add .
git commit -m "Deploy v1.0 - Upload + Vercel" 2>/dev/null || git commit -m "Update"
git push origin main
echo "✅ Repo atualizado! Vá ao dashboard Vercel e faça deploy."
