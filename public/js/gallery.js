document.addEventListener('DOMContentLoaded', () => {
    const galleryBtn = document.getElementById('galleryBtn');
    const galleryPanel = document.getElementById('galleryPanel');
    const galleryClose = document.getElementById('galleryClose');
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightboxImg');
    const lightboxClose = document.getElementById('lightboxClose');
    const trashZone = document.getElementById('trashZone');
    
    // Upload elements
    const uploadForm = document.getElementById('uploadForm');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const uploadPreview = document.getElementById('uploadPreview');
    const previewImg = document.getElementById('previewImg');
    const cancelUpload = document.getElementById('cancelUpload');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadProgress = document.getElementById('uploadProgress');

    let galleryOpen = false;
    let selectedFile = null;
    let draggedItem = null;

    // Toggle gallery
    galleryBtn.addEventListener('click', () => {
        galleryOpen = !galleryOpen;
        galleryPanel.classList.toggle('active', galleryOpen);
        const items = document.querySelectorAll('.gallery-item');
        if (galleryOpen && items.length > 0) animateGalleryItems();
    });

    galleryClose.addEventListener('click', () => {
        galleryOpen = false;
        galleryPanel.classList.remove('active');
    });

    // Stagger animation
    function animateGalleryItems() {
        const items = document.querySelectorAll('.gallery-item');
        items.forEach((item, index) => {
            item.classList.remove('visible');
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    setTimeout(() => item.classList.add('visible'), index * 80);
                });
            });
        });
    }

    // Lightbox
    function setupGalleryItems() {
        const items = document.querySelectorAll('.gallery-item');
        items.forEach(item => {
            // Click to open lightbox (only if not dragging)
            item.addEventListener('click', (e) => {
                if (!item.classList.contains('dragging')) {
                    openLightbox(item.dataset.src);
                }
            });

            // Drag events for delete
            item.setAttribute('draggable', 'true');
            item.addEventListener('dragstart', (e) => {
                draggedItem = item;
                item.classList.add('dragging');
                e.dataTransfer.setData('text/plain', item.dataset.src);
                e.dataTransfer.effectAllowed = 'move';
            });
            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
                draggedItem = null;
            });
            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                item.classList.add('drag-over');
            });
            item.addEventListener('dragleave', () => {
                item.classList.remove('drag-over');
            });
            item.addEventListener('drop', (e) => {
                e.preventDefault();
                item.classList.remove('drag-over');
            });
        });
    }

    function openLightbox(src) {
        lightboxImg.src = src;
        lightbox.classList.add('active');
    }

    function closeLightbox() {
        lightbox.classList.remove('active');
        setTimeout(() => lightboxImg.src = '', 300);
    }

    lightboxClose.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            if (lightbox.classList.contains('active')) closeLightbox();
            if (galleryOpen) { galleryOpen = false; galleryPanel.classList.remove('active'); }
        }
        if (!lightbox.classList.contains('active')) return;
        const items = document.querySelectorAll('.gallery-item');
        const images = Array.from(items).map(i => i.dataset.src);
        const idx = images.indexOf(lightboxImg.src);
        if (e.key === 'ArrowRight' && idx < images.length - 1) openLightbox(images[idx + 1]);
        if (e.key === 'ArrowLeft' && idx > 0) openLightbox(images[idx - 1]);
    });

    // Upload handling
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', e => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

    function handleFile(file) {
        if (!file.type.match(/image\/(jpeg|png|webp|gif)/)) {
            alert('Apenas JPG, PNG, WebP, GIF!');
            return;
        }
        selectedFile = file;
        previewImg.src = URL.createObjectURL(file);
        uploadPreview.hidden = false;
        uploadBtn.hidden = false;
        dropzone.hidden = true;
    }

    cancelUpload.addEventListener('click', () => {
        selectedFile = null;
        uploadPreview.hidden = true;
        uploadBtn.hidden = true;
        dropzone.hidden = false;
    });

    uploadForm.addEventListener('submit', async e => {
        e.preventDefault();
        if (!selectedFile) return;

        uploadBtn.hidden = true;
        uploadProgress.hidden = false;

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const resp = await fetch('/upload', { method: 'POST', body: formData });
            const data = await resp.json();
            
            if (data.success) {
                cancelUpload.click();
                await refreshGallery();
            } else {
                alert(data.error || 'Erro ao enviar');
            }
        } catch (err) {
            alert('Erro: ' + err.message);
        } finally {
            uploadProgress.hidden = true;
            uploadBtn.hidden = false;
        }
    });

    // Trash zone drag handling
    trashZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        trashZone.classList.add('drag-over');
    });

    trashZone.addEventListener('dragleave', () => {
        trashZone.classList.remove('drag-over');
    });

    trashZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        trashZone.classList.remove('drag-over');
        
        const url = e.dataTransfer.getData('text/plain');
        if (!url || !draggedItem) return;

        // Show confirmation
        if (confirm('Excluir esta imagem?')) {
            try {
                const resp = await fetch('/api/images', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await resp.json();

                if (data.success) {
                    draggedItem.remove();
                    showToast('Imagem excluída!', '#ff5252');
                } else {
                    alert(data.error || 'Erro ao excluir');
                }
            } catch (err) {
                alert('Erro: ' + err.message);
            }
        }
    });

    function showToast(message, bgColor = '#4caf50') {
        const toast = document.createElement('div');
        toast.className = 'delete-toast';
        toast.textContent = message;
        toast.style.background = bgColor;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }

    async function refreshGallery() {
        try {
            const resp = await fetch('/api/images');
            const images = await resp.json();
            const grid = document.getElementById('galleryGrid');
            
            if (images.length > 0) {
                grid.innerHTML = images.map(img => `
                    <div class="gallery-item" data-src="${img.url}">
                        <img src="${img.url}" alt="${img.name}">
                        <div class="gallery-item-info"><span>${img.name}</span></div>
                    </div>`).join('');
                
                setupGalleryItems();
                animateGalleryItems();
            } else {
                grid.innerHTML = '<p class="no-images">Nenhuma imagem encontrada.</p>';
            }
        } catch (err) {
            console.error('Erro ao atualizar galeria:', err);
        }
    }

    // Initial setup
    setupGalleryItems();
});
