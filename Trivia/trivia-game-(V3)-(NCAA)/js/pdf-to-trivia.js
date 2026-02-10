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
        
        // Render all questions from all sections
        if (sections.length) {
            let totalQuestions = 0;
            for (const section of sections) {
                const sectionDiv = document.createElement('div');
                sectionDiv.className = 'question-section';
                sectionDiv.innerHTML = `<h3>Section ${section.section}</h3>`;
                
                for (const q of section.questions) {
                    totalQuestions++;
                    const questionDiv = document.createElement('div');
                    questionDiv.className = 'question-card';
                    questionDiv.innerHTML = `
                        <div class="question-number">Q${totalQuestions}</div>
                        <div class="question-text"><b>${q.question}</b></div>
                        <div class="question-options">
                            ${q.options.map((opt, i) => `<div class="option ${opt === q.correctAnswer ? 'correct-answer' : ''}">${String.fromCharCode(65 + i)}. ${opt}</div>`).join('')}
                        </div>
                        <div class="question-meta">
                            <span class="difficulty ${q.difficulty}">${q.difficulty}</span>
                            <span class="hint" title="${q.hint}">💡 Hint</span>
                        </div>
                    `;
                    sectionDiv.appendChild(questionDiv);
                }
                previewDiv.appendChild(sectionDiv);
            }
            statusDiv.textContent = `${totalQuestions} questions generated successfully!`;
        } else {
            statusDiv.textContent = 'No questions could be generated from this PDF.';
        }
    } catch (err) {
        statusDiv.textContent = 'Error: ' + err.message;
    }
});
