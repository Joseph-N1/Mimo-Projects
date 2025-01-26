class TriviaGame {
    constructor() {
        this.sections = [];
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        
        this.loadQuestions().then(() => {
            this.initGame();
            this.displayQuestion();
        });
    }

    async loadQuestions() {
        const response = await fetch('questions.json');
        this.sections = await response.json();
    }

    initGame() {
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        document.getElementById('restart-btn').addEventListener('click', () => this.restartSection());
    }

    displayQuestion() {
        const section = this.sections[this.currentSection];
        const question = section.questions[this.currentQuestion];
        const optionsContainer = document.getElementById('options-container');
        
        // Clear previous content
        optionsContainer.innerHTML = '';
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('ai-fact').innerHTML = '';

        // Update section display
        document.getElementById('current-section').textContent = this.currentSection + 1;

        // Display question
        document.getElementById('question-container').innerHTML = `
            <h3>${question.question}</h3>
        `;

        // Create answer buttons
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.textContent = option;
            button.addEventListener('click', () => this.checkAnswer(option === question.correctAnswer));
            optionsContainer.appendChild(button);
        });

        // Set grid layout based on options count
        const columns = Math.min(question.options.length, 5);
        optionsContainer.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
    }

    checkAnswer(isCorrect) {
        const feedback = document.getElementById('feedback');
        if (isCorrect) {
            this.score++;
            this.wrongAttempts = 0;
            feedback.textContent = 'Correct!';
            feedback.className = 'correct';
            this.showAIFact();
            this.nextQuestion();
        } else {
            this.wrongAttempts++;
            feedback.textContent = 'Not quite, try again.';
            feedback.className = 'incorrect';
            if (this.currentSection >= 6 && this.wrongAttempts >= 2) {
                this.provideHint();
            }
        }
    }

    showAIFact() {
        const question = this.sections[this.currentSection].questions[this.currentQuestion];
        const aiFact = document.getElementById('ai-fact');
        aiFact.innerHTML = `<strong>Did you know?</strong> ${question.funFact}`;
    }

    provideHint() {
        const question = this.sections[this.currentSection].questions[this.currentQuestion];
        const aiFact = document.getElementById('ai-fact');
        aiFact.innerHTML = `<strong>Hint:</strong> ${question.hint}`;
    }

    nextQuestion() {
        this.currentQuestion++;
        if (this.currentQuestion >= this.sections[this.currentSection].questions.length) {
            this.currentSection++;
            this.currentQuestion = 0;
            if (this.currentSection >= this.sections.length) {
                alert(`Game Over! Final Score: ${this.score}`);
                this.initGame();
                return;
            }
        }
        setTimeout(() => this.displayQuestion(), 1500);
    }

    restartSection() {
        this.currentQuestion = 0;
        this.wrongAttempts = 0;
        this.displayQuestion();
    }
}

// Initialize game when loaded
window.addEventListener('load', () => new TriviaGame());