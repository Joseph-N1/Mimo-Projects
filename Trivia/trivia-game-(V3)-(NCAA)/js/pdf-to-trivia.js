// pdf-to-trivia.js
// Step 1: PDF upload and text extraction (basic, no question generation yet)
document.getElementById('pdf-upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('pdf-file');
    const statusDiv = document.getElementById('generation-status');
    const previewDiv = document.getElementById('questions-preview');
    previewDiv.innerHTML = '';
    statusDiv.textContent = 'Extracting text from PDF...';

    if (!fileInput.files.length) {
        statusDiv.textContent = 'Please select a PDF file.';
        return;
    }
    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = async function() {
        const typedarray = new Uint8Array(this.result);
        try {
            const pdf = await pdfjsLib.getDocument({data: typedarray}).promise;
            let fullText = '';
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const content = await page.getTextContent();
                const strings = content.items.map(item => item.str);
                fullText += strings.join(' ') + '\n';
            }
            statusDiv.textContent = 'PDF text extracted. (Question generation coming next...)';
            previewDiv.innerHTML = `<pre style="white-space:pre-wrap;">${fullText.substring(0, 2000)}${fullText.length > 2000 ? '... (truncated)' : ''}</pre>`;
        } catch (err) {
            statusDiv.textContent = 'Error reading PDF: ' + err.message;
        }
    };
    reader.readAsArrayBuffer(file);
});
