class TriviaGame {
    constructor(gameMode) {
        this.sections = [];
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.gameMode = gameMode;
        this.timer = 30 + (this.currentSection * 10); // Timer logic for all modes
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
            literature: '18-literature-questions.json'
            // Niche mode uses sessionStorage, so no JSON file is needed
        };

        try {
            if (this.gameMode === 'niche') {
                const nicheData = sessionStorage.getItem('nicheQuizData');
                if (nicheData) {
                    const parsedData = JSON.parse(nicheData);
                    
                    // Improved data validation
                    if (parsedData?.sections?.length) {
                        this.sections = parsedData.sections;
                        
                        // Add topic context to questions
                        const topic = parsedData.topic || 'Niche Topic';
                        this.sections.forEach((section, index) => {
                            section.questions.forEach(question => {
                                question.question = `${topic} (Section ${index + 1}): ${question.question}`;
                            });
                        });
                    } else {
                        throw new Error('Invalid niche quiz structure');
                    }
                } else {
                    alert('No quiz data found. Please select a topic again.');
                    window.location.href = 'niche-game.html';
                    return;
                }
            } else {
                // Load questions from JSON files for other modes
                const response = await fetch(jsonFiles[this.gameMode]);
                this.sections = await response.json();
            }
        } catch (error) {
            console.error('Error loading questions:', error);
            alert(`Failed to load questions: ${error.message}`);
            if (this.gameMode === 'niche') window.location.href = 'niche-game.html';
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

    sanitizeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    } 

    showAIFact() {
        const question = this.getCurrentQuestion();
        const aiFactElement = document.getElementById('ai-fact');
        const fact = question.funFact || question.fact;
        
        aiFactElement.innerHTML = `
            <strong>Did you know?</strong> 
            ${this.sanitizeHTML(fact)}
        `;
        aiFactElement.classList.add('visible');
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
        this.timer = 30 + (this.currentSection * 10); // Timer increases with sections
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
        const timerElement = document.getElementById('time-remaining');
        this.timerInterval = setInterval(() => {
            this.timer = Math.max(0, this.timer - 1);
            if (timerElement) timerElement.textContent = this.timer;
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
        const totalQuestions = this.sections.reduce((acc, section) => 
            acc + section.questions.length, 0
        );
    
        gameContainer.innerHTML = `
            <h2>Quiz Complete!</h2>
            <div class="score-display">
                <p>Final Score: ${this.score}/${totalQuestions}</p>
                <p>Accuracy: ${Math.round((this.score/totalQuestions)*100)}%</p>
            </div>
            <div class="end-game-controls">
                <button id="restart-game-btn" class="control-btn">Play Again</button>
                <a href="niche-game.html" class="control-btn">New Topic</a>
                <a href="01-index.html" class="control-btn">Main Menu</a>
            </div>
        `;

        document.getElementById('restart-game-btn')?.addEventListener('click', () => {
            this.resetGameState();
            this.displayQuestion();
        });
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
        'niche-game': 'niche' // Added Niche mode
    };

    const gameMode = Object.entries(gameModes).find(([key]) => path.includes(key))?.[1] || 'math';
    new TriviaGame(gameMode);
});