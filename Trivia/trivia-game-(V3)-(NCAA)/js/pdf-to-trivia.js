// pdf-to-trivia.js
// PDF upload or database selection -> question generation
const useDbCheckbox = document.getElementById('use-db');
const dbSelect = document.getElementById('db-pdf');
const fileInput = document.getElementById('pdf-file');

async function loadDbPdfs() {
    try {
        const response = await fetch('http://127.0.0.1:5000/list-db-pdfs');
        if (!response.ok) throw new Error('Failed to load database PDFs');
        const pdfs = await response.json();
        dbSelect.innerHTML = '';
        if (!pdfs.length) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'No PDFs found in database';
            dbSelect.appendChild(opt);
            dbSelect.disabled = true;
            return;
        }
        for (const name of pdfs) {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            dbSelect.appendChild(opt);
        }
    } catch (err) {
        dbSelect.innerHTML = '';
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Database unavailable';
        dbSelect.appendChild(opt);
        dbSelect.disabled = true;
    }
}

useDbCheckbox.addEventListener('change', () => {
    const useDb = useDbCheckbox.checked;
    dbSelect.disabled = !useDb;
    fileInput.disabled = useDb;
    if (useDb) {
        loadDbPdfs();
    }
});

document.getElementById('pdf-upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const statusDiv = document.getElementById('generation-status');
    const previewDiv = document.getElementById('questions-preview');
    previewDiv.innerHTML = '';
    statusDiv.textContent = 'Uploading PDF and generating questions...';

    const useDb = useDbCheckbox.checked;
    if (useDb) {
        if (!dbSelect.value) {
            statusDiv.textContent = 'Please select a PDF from the database.';
            return;
        }
    } else if (!fileInput.files.length) {
        statusDiv.textContent = 'Please select a PDF file.';
        return;
    }

    try {
        let response;
        if (useDb) {
            response = await fetch('http://127.0.0.1:5000/generate-questions-from-db', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pdf_name: dbSelect.value })
            });
        } else {
            const formData = new FormData();
            formData.append('pdf', fileInput.files[0]);
            response = await fetch('http://127.0.0.1:5000/generate-questions', {
                method: 'POST',
                body: formData
            });
        }
        if (!response.ok) throw new Error('Server error');
        const sections = await response.json();
        // Render questions as a quiz (implement your quiz UI here)
        // Example: show first question
        if (sections.length && sections[0].questions.length) {
            const q = sections[0].questions[0];
            previewDiv.innerHTML += `<div><b>${q.question}</b><br>Options: ${q.options.join(', ')}</div>`;
        }
        statusDiv.textContent = 'Questions generated!';
    } catch (err) {
        statusDiv.textContent = 'Error: ' + err.message;
    }
});
