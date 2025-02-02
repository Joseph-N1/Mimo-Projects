class TriviaGame {
    constructor(gameMode) {
        this.sections = [];
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.gameMode = gameMode;
        this.timer = 30 + (this.currentSection * 10);
        this.timerInterval = null;

        this.loadQuestions().then(() => {
            this.initGame();
            this.displayQuestion();
            this.startTimer();
        });
    }

    async loadQuestions() {
        const jsonFiles = {
            anime: '13-anime-questions.json',
            math: '12-questions.json',
            science: '14-science-questions.json',
            geography: '15-geography-questions.json',
            worldhistory: '16-worldhistory-questions.json',
            sports: '17-sports-questions.json',
            literature: '18-literature-questions.json'
        };
        const response = await fetch(jsonFiles[this.gameMode]);
        this.sections = await response.json();
    }

    initGame() {
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.timer = 30 + (this.currentSection * 10);

        // Event listeners
        document.getElementById('restart-btn').addEventListener('click', () => this.restartSection());
        document.getElementById('next-btn').addEventListener('click', () => this.nextQuestion());
        document.getElementById('try-again-btn').addEventListener('click', () => this.resetQuestion());
    }

    displayQuestion() {
        const section = this.sections[this.currentSection];
        const question = section.questions[this.currentQuestion];
        const optionsContainer = document.getElementById('options-container');

        // Reset UI state
        optionsContainer.innerHTML = '';
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('ai-fact').innerHTML = '';
        document.getElementById('next-btn').style.display = 'none';
        document.getElementById('try-again-btn').style.display = 'none';

        // Update displays
        document.getElementById('current-section').textContent = this.currentSection + 1;
        document.getElementById('timer').textContent = this.timer;
        document.getElementById('question-container').innerHTML = `<h3>${question.question}</h3>`;

        // Create options with checkboxes
        question.options.forEach(option => {
            const label = document.createElement('label');
            label.className = 'material-checkbox';

            const input = document.createElement('input');
            input.type = 'checkbox';
            input.value = option;

            const span = document.createElement('span');
            span.className = 'checkmark';

            const text = document.createTextNode(option);

            label.appendChild(input);
            label.appendChild(span);
            label.appendChild(text);

            // Add click handler
            label.addEventListener('click', () => {
                // Uncheck all other checkboxes
                document.querySelectorAll('.material-checkbox input').forEach(checkbox => {
                    if (checkbox !== input) checkbox.checked = false;
                });

                // Check the answer
                this.checkAnswer(option === (question.correctAnswer || question.answer));
            });

            optionsContainer.appendChild(label);
        });

        // Start timer
        this.startTimer();
    }

    checkAnswer(isCorrect) {
        this.stopTimer();
        const feedback = document.getElementById('feedback');

        if (isCorrect) {
            this.handleCorrectAnswer(feedback);
        } else {
            this.handleIncorrectAnswer(feedback);
        }
    }

    handleCorrectAnswer(feedback) {
        this.score++;
        this.wrongAttempts = 0;
        feedback.textContent = 'Correct!';
        feedback.className = 'correct';
        document.getElementById('next-btn').style.display = 'block';
        this.showAIFact();
    }

    handleIncorrectAnswer(feedback) {
        this.wrongAttempts++;
        feedback.textContent = 'Not quite. Try again!';
        feedback.className = 'incorrect';
        document.getElementById('try-again-btn').style.display = 'block';

        if (this.currentSection >= 6 && this.wrongAttempts >= 2) {
            this.provideHint();
        }
    }

    resetQuestion() {
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('ai-fact').innerHTML = '';
        document.getElementById('try-again-btn').style.display = 'none';
        this.timer = 30 + (this.currentSection * 10);
        this.startTimer();
    }

    nextQuestion() {
        this.currentQuestion++;
        if (this.currentQuestion >= this.sections[this.currentSection].questions.length) {
            this.currentSection++;
            this.currentQuestion = 0;
            if (this.currentSection >= this.sections.length) {
                return this.endGame();
            }
        }
        this.timer = 30 + (this.currentSection * 10);
        this.displayQuestion();
    }

    startTimer() {
        document.getElementById('timer').textContent = this.timer;
        this.timerInterval = setInterval(() => {
            this.timer = Math.max(0, this.timer - 1);
            document.getElementById('timer').textContent = this.timer;
            if (this.timer <= 0) {
                this.stopTimer();
                this.checkAnswer(false);
            }
        }, 1000);
    }

    stopTimer() {
        clearInterval(this.timerInterval);
    }

    showAIFact() {
        const question = this.sections[this.currentSection].questions[this.currentQuestion];
        const fact = question.funFact || question.fact;
        document.getElementById('ai-fact').innerHTML = `<strong>Did you know?</strong> ${fact}`;
    }

    provideHint() {
        const question = this.sections[this.currentSection].questions[this.currentQuestion];
        document.getElementById('ai-fact').innerHTML = `<strong>Hint:</strong> ${question.hint}`;
    }

    endGame() {
        const gameContainer = document.getElementById('game-container');
        gameContainer.innerHTML = `
            <h2>Game Over!</h2>
            <p>Final Score: ${this.score}</p>
            <button id="restart-btn">Restart Game</button>
            <a href="01-index.html" class="mode-btn">Main Menu</a>
        `;
        document.getElementById('restart-btn').addEventListener('click', () => this.initGame());
    }

    restartSection() {
        this.currentQuestion = 0;
        this.wrongAttempts = 0;
        this.displayQuestion();
    }
}

// Initialize game
window.addEventListener('load', () => {
    const path = window.location.pathname;
    const gameModes = {
        'math-game': 'math',
        'anime-game': 'anime',
        'science-game': 'science',
        'geography-game': 'geography',
        'worldhistory-game': 'worldhistory',
        'sports-game': 'sports',
        'literature-game': 'literature'
    };

    const gameMode = Object.entries(gameModes).find(([key]) => path.includes(key))?.[1] || 'math';
    new TriviaGame(gameMode);
});