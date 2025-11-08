// ============================================
// SESSION MANAGEMENT
// ============================================
class SessionManager {
    constructor() {
        this.checkInterval = null;
        this.checkFrequency = 5 * 60 * 1000; // 5 minutes
    }

    init() {
        this.startSessionCheck();
        this.setupPageShowHandler();
    }

    async checkSession() {
        try {
            const response = await fetch('/api/session-status');
            const data = await response.json();
            
            if (!data.authenticated) {
                this.handleSessionExpired();
            }
        } catch (error) {
            console.error('Session check failed:', error);
        }
    }

    handleSessionExpired() {
        this.stopSessionCheck();
        UIManager.showModal('session-expired-popup');
        
        setTimeout(() => {
            window.location.href = '/login';
        }, 3000);
    }

    startSessionCheck() {
        this.checkInterval = setInterval(() => {
            this.checkSession();
        }, this.checkFrequency);
    }

    stopSessionCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }

    setupPageShowHandler() {
        window.addEventListener('pageshow', (event) => {
            if (event.persisted) {
                window.location.reload();
            }
        });
    }
}

// ============================================
// FILE UPLOAD HANDLER
// ============================================
class FileUploadHandler {
    constructor() {
        this.fileInput = document.getElementById('file-input');
        this.uploadForm = document.getElementById('upload-form');
        this.uploadBtn = document.getElementById('upload-btn');
        this.dropZone = document.getElementById('drop-zone');
        this.fileNameDisplay = document.getElementById('file-name');
        
        this.maxFileSize = 100 * 1024 * 1024; // 100MB
    }

    init() {
        if (!this.uploadForm) return;

        this.setupFileInput();
        this.setupDragAndDrop();
        this.setupFormSubmit();
    }

    setupFileInput() {
        this.fileInput.addEventListener('change', () => {
            this.handleFileSelect(this.fileInput.files[0]);
        });
    }

    setupDragAndDrop() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.remove('drag-over');
            });
        });

        this.dropZone.addEventListener('drop', (e) => {
            const file = e.dataTransfer.files[0];
            if (file) {
                this.fileInput.files = e.dataTransfer.files;
                this.handleFileSelect(file);
            }
        });
    }

    handleFileSelect(file) {
        if (!file) {
            this.fileNameDisplay.textContent = '';
            return;
        }

        if (file.size > this.maxFileSize) {
            NotificationManager.showError('File too large', 'Maximum file size is 100MB');
            this.fileInput.value = '';
            this.fileNameDisplay.textContent = '';
            return;
        }

        this.fileNameDisplay.textContent = `${file.name} (${this.formatFileSize(file.size)})`;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    setupFormSubmit() {
        this.uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleUpload();
        });
    }

    async handleUpload() {
        const file = this.fileInput.files[0];
        
        if (!file) {
            NotificationManager.showError('No file selected', 'Please select a file to upload');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        this.setUploadingState(true);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.handleUploadSuccess(data);
            } else {
                this.handleUploadError(data.message || 'Upload failed');
            }

        } catch (error) {
            console.error('Upload error:', error);
            this.handleUploadError('Network error occurred');
        } finally {
            this.setUploadingState(false);
        }
    }

    handleUploadSuccess(data) {
        PopupManager.showUploadSuccess(data);
        this.resetForm();
        
        // Reload after short delay
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }

    handleUploadError(message) {
        PopupManager.showUploadError(message);
    }

    setUploadingState(isUploading) {
        this.uploadBtn.disabled = isUploading;
        
        if (isUploading) {
            this.uploadBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" class="spinner">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                Uploading...
            `;
            this.uploadBtn.classList.add('loading');
        } else {
            this.uploadBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="2"/>
                </svg>
                Upload to IPFS
            `;
            this.uploadBtn.classList.remove('loading');
        }
    }

    resetForm() {
        this.uploadForm.reset();
        this.fileNameDisplay.textContent = '';
    }
}

// ============================================
// FILE VIEW HANDLER
// ============================================
class FileViewHandler {
    constructor() {
        this.viewBtn = document.getElementById('view-file-btn');
        this.hashInput = document.getElementById('ipfs-hash-input');
    }

    init() {
        if (!this.viewBtn) return;

        this.viewBtn.addEventListener('click', () => {
            this.handleViewFile();
        });

        this.hashInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleViewFile();
            }
        });
    }

    handleViewFile() {
        const ipfsHash = this.hashInput.value.trim();

        if (!ipfsHash) {
            NotificationManager.showError('Invalid Hash', 'Please enter an IPFS hash');
            return;
        }

        if (!this.isValidIPFSHash(ipfsHash)) {
            NotificationManager.showError('Invalid Hash Format', 'Please enter a valid IPFS hash (starts with Qm)');
            return;
        }

        window.open(`/download?ipfs_hash=${encodeURIComponent(ipfsHash)}`, '_blank');
        this.hashInput.value = '';
    }

    isValidIPFSHash(hash) {
        // Basic validation for IPFS CIDv0 (Qm...) or CIDv1 (b...)
        return /^(Qm[1-9A-HJ-NP-Za-km-z]{44}|b[A-Za-z2-7]{58})$/.test(hash);
    }
}

// ============================================
// COPY HASH HANDLER
// ============================================
class CopyHashHandler {
    constructor() {
        this.copyButtons = document.querySelectorAll('.copy-btn');
    }

    init() {
        this.copyButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                await this.handleCopy(e.target.closest('.copy-btn'));
            });
        });
    }

    async handleCopy(button) {
        const hash = button.getAttribute('data-hash');
        const originalHTML = button.innerHTML;

        try {
            await navigator.clipboard.writeText(hash);
            
            button.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <polyline points="20 6 9 17 4 12" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span class="btn-text">Copied!</span>
            `;
            button.classList.add('copied');

            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);

        } catch (err) {
            console.error('Failed to copy:', err);
            
            button.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
                    <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span class="btn-text">Failed</span>
            `;

            setTimeout(() => {
                button.innerHTML = originalHTML;
            }, 2000);
        }
    }
}

// ============================================
// POPUP MANAGER
// ============================================
class PopupManager {
    static showUploadSuccess(data) {
        const popup = document.getElementById('upload-popup');
        const icon = document.getElementById('popup-icon');
        const title = document.getElementById('popup-title');
        const message = document.getElementById('popup-message');
        const hashDisplay = document.getElementById('popup-ipfs-hash');

        icon.className = 'popup-icon success';
        icon.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;

        title.textContent = 'Upload Successful!';
        message.textContent = data.message || 'Your file has been uploaded to IPFS';
        hashDisplay.innerHTML = `
            <strong>IPFS Hash:</strong><br>
            <span style="word-break: break-all;">${data.ipfs_hash}</span>
        `;

        UIManager.showModal('upload-popup');
    }

    static showUploadError(errorMessage) {
        const popup = document.getElementById('upload-popup');
        const icon = document.getElementById('popup-icon');
        const title = document.getElementById('popup-title');
        const message = document.getElementById('popup-message');
        const hashDisplay = document.getElementById('popup-ipfs-hash');

        icon.className = 'popup-icon error';
        icon.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
        `;

        title.textContent = 'Upload Failed';
        message.textContent = errorMessage;
        hashDisplay.textContent = '';

        UIManager.showModal('upload-popup');
    }
}

// ============================================
// UI MANAGER
// ============================================
class UIManager {
    static showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    static setupModalHandlers() {
        // Close button handlers
        const closeX = document.getElementById('close-x');
        const closeBtn = document.getElementById('close-popup-btn');
        const uploadPopup = document.getElementById('upload-popup');

        if (closeX) {
            closeX.addEventListener('click', () => {
                UIManager.hideModal('upload-popup');
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                UIManager.hideModal('upload-popup');
            });
        }

        // Click outside to close
        if (uploadPopup) {
            uploadPopup.addEventListener('click', (e) => {
                if (e.target === uploadPopup) {
                    UIManager.hideModal('upload-popup');
                }
            });
        }

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                UIManager.hideModal('upload-popup');
            }
        });
    }
}

// ============================================
// NOTIFICATION MANAGER
// ============================================
class NotificationManager {
    static showError(title, message) {
        // Simple alert implementation - can be replaced with toast notifications
        alert(`${title}\n\n${message}`);
    }

    static showSuccess(title, message) {
        // Simple alert implementation - can be replaced with toast notifications
        alert(`${title}\n\n${message}`);
    }
}

// ============================================
// INITIALIZE APPLICATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all handlers
    const sessionManager = new SessionManager();
    const fileUploadHandler = new FileUploadHandler();
    const fileViewHandler = new FileViewHandler();
    const copyHashHandler = new CopyHashHandler();

    sessionManager.init();
    fileUploadHandler.init();
    fileViewHandler.init();
    copyHashHandler.init();
    UIManager.setupModalHandlers();

    // Add loading animation to login container
    const loginContainer = document.querySelector('.login-container');
    if (loginContainer) {
        setTimeout(() => {
            loginContainer.classList.add('loaded');
        }, 100);
    }

    console.log('CloudSend initialized successfully');
});

// Add CSS for spinner animation
const style = document.createElement('style');
style.textContent = `
    .spinner {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);