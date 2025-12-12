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

    // ========== CORE METHODS ========== //
    async loadQuestions() {
        const jsonFiles = {
            anime: '13-anime-questions.json',
            math: '12-questions.json',
            science: '14-science-questions.json',
            geography: '15-geography-questions.json',
            worldhistory: '16-worldhistory-questions.json',
            sports: '17-sports-questions.json',
            literature: '18-literature-questions.json',
            ncaa: '19-ncaa-questions.json'
        };
        
        try {
            const response = await fetch(jsonFiles[this.gameMode]);
            this.sections = await response.json();
        } catch (error) {
            console.error('Error loading questions:', error);
        }
    }

    initGame() {
        this.resetGameState();
        this.setupEventListeners();
    }

    displayQuestion() {
        this.resetUIState();
        this.updateDisplayHeaders();
        this.createQuestionOptions();
        this.startTimer();
        this.updateProgressBar();
    }

    // ========== GAME LOGIC ========== //
    checkAnswer(isCorrect) {
        this.stopTimer();
        const feedback = document.getElementById('feedback');
        isCorrect ? this.handleCorrectAnswer(feedback) : this.handleIncorrectAnswer(feedback);
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

    showAIFact() {
        const question = this.sections[this.currentSection].questions[this.currentQuestion];
        const fact = question.funFact || question.fact;
        const aiFactElement = document.getElementById('ai-fact');
        aiFactElement.innerHTML = `<strong>Did you know?</strong> ${fact}`;
        aiFactElement.classList.add('visible'); // Make AI fact visible
    }

    provideHint() {
        const question = this.sections[this.currentSection].questions[this.currentQuestion];
        const aiFactElement = document.getElementById('ai-fact');
        aiFactElement.innerHTML = `<strong>Hint:</strong> ${question.hint}`;
        aiFactElement.classList.add('visible'); // Make AI fact visible
    }

    // ========== NAVIGATION CONTROLS ========== //
    nextQuestion() {
        this.currentQuestion++;
        if (this.currentQuestion >= this.sections[this.currentSection].questions.length) {
            this.currentSection++;
            this.currentQuestion = 0;
            if (this.currentSection >= this.sections.length) return this.endGame();
        }
        this.timer = 30 + (this.currentSection * 10);
        this.displayQuestion();
    }

    restartSection() {
        this.currentQuestion = 0;
        this.wrongAttempts = 0;
        this.displayQuestion();
    }

    resetQuestion() {
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('ai-fact').innerHTML = '';
        document.getElementById('try-again-btn').style.display = 'none';
        this.timer = 30 + (this.currentSection * 10);
        this.startTimer();
    }

    // ========== UTILITY METHODS ========== //
    updateProgressBar() {
        const totalSections = this.sections.length;
        const progress = ((this.currentSection + 1) / totalSections) * 100;
        document.getElementById('progress-bar').style.width = `${progress}%`;
        document.getElementById('progress-text').textContent = 
            `${Math.round(progress)}% Complete`;
    }

    createQuestionOptions() {
        const question = this.getCurrentQuestion();
        question.options.forEach(option => {
            const label = this.createOptionLabel(option, question);
            document.getElementById('options-container').appendChild(label);
        });
    }

    createOptionLabel(option, question) {
        const label = document.createElement('label');
        label.className = 'material-checkbox';
        
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.value = option;
    
        // Properly create checkmark span
        const span = document.createElement('span');
        span.className = 'checkmark';
    
        const text = document.createTextNode(option);
    
        label.appendChild(input);
        label.appendChild(span);
        label.appendChild(text);
    
        label.addEventListener('click', () => this.handleOptionSelect(input, option, question));
        return label;
    }

    // ========== HELPER METHODS ========== //
    handleOptionSelect(input, option, question) {
        document.querySelectorAll('.material-checkbox input').forEach(checkbox => {
            if (checkbox !== input) checkbox.checked = false;
        });
        this.checkAnswer(option === (question.correctAnswer || question.answer));
    }

    getCurrentQuestion() {
        return this.sections[this.currentSection].questions[this.currentQuestion];
    }

    resetGameState() {
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.timer = 30 + (this.currentSection * 10);
    }

    resetUIState() {
        document.getElementById('options-container').innerHTML = '';
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('feedback').style.display = 'none'; // Hide feedback
        document.getElementById('feedback').className = '';
        document.getElementById('ai-fact').innerHTML = '';
        document.getElementById('ai-fact').classList.remove('visible'); // Hide AI fact
        document.getElementById('next-btn').style.display = 'none';
        document.getElementById('try-again-btn').style.display = 'none';
    }

    updateDisplayHeaders() {
        document.getElementById('current-section').textContent = this.currentSection + 1;
        document.getElementById('timer').textContent = this.timer;
        document.getElementById('question-container').innerHTML = 
            `<h3>${this.getCurrentQuestion().question}</h3>`;
    }

    setupEventListeners() {
        document.getElementById('restart-btn').addEventListener('click', () => this.restartSection());
        document.getElementById('next-btn').addEventListener('click', () => this.nextQuestion());
        document.getElementById('try-again-btn').addEventListener('click', () => this.resetQuestion());
    }

    // ========== TIMER METHODS ========== //
    startTimer() {
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

    // ========== GAME END ========== //
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
        'literature-game': 'literature',
        'ncaa-game': 'ncaa'
    };

    const gameMode = Object.entries(gameModes).find(([key]) => path.includes(key))?.[1] || 'math';
    new TriviaGame(gameMode);
});