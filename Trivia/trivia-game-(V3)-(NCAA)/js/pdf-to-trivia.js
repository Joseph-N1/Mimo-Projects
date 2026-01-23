// pdf-to-trivia.js
// Step 1: PDF upload and text extraction (basic, no question generation yet)
document.getElementById('pdf-upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('pdf-file');
    const nameInput = document.getElementById('question-set-name');
    const statusDiv = document.getElementById('generation-status');
    const previewDiv = document.getElementById('questions-preview');
    previewDiv.innerHTML = '';
    statusDiv.textContent = 'Uploading PDF and generating questions...';

    if (!fileInput.files.length) {
        statusDiv.textContent = 'Please select a PDF file.';
        return;
    }
    if (!nameInput.value.trim()) {
        statusDiv.textContent = 'Please enter a name for the question set.';
        nameInput.focus();
        return;
    }

    const formData = new FormData();
    formData.append('pdf', fileInput.files[0]);

    try {
        const response = await fetch('http://127.0.0.1:5000/generate-questions', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error('Server error');
        const sections = await response.json();
        // Render questions as a quiz (implement your quiz UI here)
        previewDiv.innerHTML = `<h2>Question Set: ${nameInput.value}</h2>`;
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
