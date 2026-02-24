// pdf-select.js - PDF selection page logic

const API_BASE = 'http://127.0.0.1:5000';

// Elements
const btnDatabase = document.getElementById('btn-database');
const btnUpload = document.getElementById('btn-upload');
const databaseSection = document.getElementById('database-section');
const uploadSection = document.getElementById('upload-section');
const dbSelect = document.getElementById('db-pdf');
const fileInput = document.getElementById('pdf-file');
const fileNameDisplay = document.getElementById('file-name');
const generateBtn = document.getElementById('generate-btn');
const statusMessage = document.getElementById('status-message');

let currentSource = 'database'; // 'database' or 'upload'

// Load database PDFs on page load
async function loadDbPdfs() {
    try {
        const response = await fetch(`${API_BASE}/list-db-pdfs`);
        if (!response.ok) throw new Error('Failed to load database PDFs');
        const pdfs = await response.json();
        
        dbSelect.innerHTML = '';
        
        if (!pdfs.length) {
            dbSelect.innerHTML = '<option value="">No PDFs found in database</option>';
            return;
        }
        
        dbSelect.innerHTML = '<option value="">-- Select a PDF --</option>';
        for (const name of pdfs) {
            const opt = document.createElement('option');
            opt.value = name;
            // Clean up the filename for display
            opt.textContent = name.replace(/-/g, ' ').replace('.pdf', '').replace(/nig cars /i, '');
            dbSelect.appendChild(opt);
        }
    } catch (err) {
        dbSelect.innerHTML = '<option value="">Error loading PDFs - Is the server running?</option>';
        statusMessage.textContent = 'Cannot connect to server. Make sure the backend is running.';
        statusMessage.className = 'status-error';
    }
}

// Toggle between database and upload
btnDatabase.addEventListener('click', () => {
    currentSource = 'database';
    btnDatabase.classList.add('active');
    btnUpload.classList.remove('active');
    databaseSection.classList.add('active');
    uploadSection.classList.remove('active');
    statusMessage.textContent = '';
});

btnUpload.addEventListener('click', () => {
    currentSource = 'upload';
    btnUpload.classList.add('active');
    btnDatabase.classList.remove('active');
    uploadSection.classList.add('active');
    databaseSection.classList.remove('active');
    statusMessage.textContent = '';
});

// File input display
fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name}`;
        fileNameDisplay.className = 'file-selected';
    } else {
        fileNameDisplay.textContent = '';
    }
});

// Generate button click
generateBtn.addEventListener('click', () => {
    if (currentSource === 'database') {
        if (!dbSelect.value) {
            statusMessage.textContent = 'Please select a PDF from the dropdown.';
            statusMessage.className = 'status-error';
            return;
        }
        // Navigate to questions page with database PDF
        window.location.href = `questions.html?source=database&pdf=${encodeURIComponent(dbSelect.value)}`;
    } else {
        if (!fileInput.files.length) {
            statusMessage.textContent = 'Please select a PDF file to upload.';
            statusMessage.className = 'status-error';
            return;
        }
        // Store file in sessionStorage and navigate
        const file = fileInput.files[0];
        const reader = new FileReader();
        
        statusMessage.textContent = 'Preparing file...';
        statusMessage.className = 'status-loading';
        generateBtn.disabled = true;
        
        reader.onload = function(e) {
            try {
                sessionStorage.setItem('uploadedPdf', e.target.result);
                sessionStorage.setItem('uploadedPdfName', file.name);
                window.location.href = 'questions.html?source=upload';
            } catch (err) {
                statusMessage.textContent = 'File too large for browser storage. Try a smaller PDF.';
                statusMessage.className = 'status-error';
                generateBtn.disabled = false;
            }
        };
        
        reader.onerror = function() {
            statusMessage.textContent = 'Error reading file. Please try again.';
            statusMessage.className = 'status-error';
            generateBtn.disabled = false;
        };
        
        reader.readAsDataURL(file);
    }
});

// Initialize
loadDbPdfs();
