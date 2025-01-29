class TriviaGame {
    constructor(gameMode) {
        this.sections = [];
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.gameMode = gameMode;
        this.timer = 30; // 30 seconds for the first section
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
        const jsonFile = jsonFiles[this.gameMode];
        const response = await fetch(jsonFile);
        this.sections = await response.json();
    }

    initGame() {
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.timer = 30; // Reset timer for the first section
        document.getElementById('restart-btn').addEventListener('click', () => this.restartSection());
        document.getElementById('next-btn').addEventListener('click', () => this.nextQuestion());
    }

    displayQuestion() {
        const section = this.sections[this.currentSection];
        const question = section.questions[this.currentQuestion];
        const optionsContainer = document.getElementById('options-container');

        // Clear previous content
        optionsContainer.innerHTML = '';
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('ai-fact').innerHTML = '';
        document.getElementById('next-btn').style.display = 'none'; // Hide "Next" button initially

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

        // Start timer
        this.startTimer();
    }

    checkAnswer(isCorrect) {
        const feedback = document.getElementById('feedback');
        if (isCorrect) {
            this.score++;
            this.wrongAttempts = 0;
            feedback.textContent = 'Correct!';
            feedback.className = 'correct';
        } else {
            this.wrongAttempts++;
            feedback.textContent = 'Not quite, try again.';
            feedback.className = 'incorrect';
            if (this.currentSection >= 6 && this.wrongAttempts >= 2) {
                this.provideHint();
            }
        }

        // Stop timer and show "Next" button
        this.stopTimer();
        document.getElementById('next-btn').style.display = 'block';
        this.showAIFact();
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
                this.endGame();
                return;
            }
        }

        // Increase timer by 10 seconds for each new section
        this.timer = 30 + (this.currentSection * 10);
        this.displayQuestion();
    }

    endGame() {
        const gameContainer = document.getElementById('game-container');
        gameContainer.innerHTML = `
            <h2>Game Over!</h2>
            <p>Your final score is: ${this.score}</p>
            <button id="restart-btn">Restart Game</button>
            <a href="01-index.html" class="mode-btn">Choose Another Category</a>
        `;
        document.getElementById('restart-btn').addEventListener('click', () => this.initGame());
    }

    startTimer() {
        document.getElementById('timer').textContent = this.timer;
        this.timerInterval = setInterval(() => {
            this.timer--;
            document.getElementById('timer').textContent = this.timer;
            if (this.timer <= 0) {
                this.stopTimer();
                this.checkAnswer(false); // Automatically mark as incorrect
            }
        }, 1000);
    }

    stopTimer() {
        clearInterval(this.timerInterval);
    }

    restartSection() {
        this.currentQuestion = 0;
        this.wrongAttempts = 0;
        this.displayQuestion();
    }
}

// Initialize game when loaded
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    let gameMode = urlParams.get('mode');

    // Fallback to default mode if none specified
    if (!gameMode) {
        const path = window.location.pathname;
        if (path.includes('math-game')) {
            gameMode = 'math';
        } else if (path.includes('anime-game')) {
            gameMode = 'anime';
        } else if (path.includes('science-game')) {
            gameMode = 'science';
        } else if (path.includes('geography-game')) {
            gameMode = 'geography';
        } else if (path.includes('worldhistory-game')) {
            gameMode = 'worldhistory';
        } else if (path.includes('sports-game')) {
            gameMode = 'sports';
        } else if (path.includes('literature-game')) {
            gameMode = 'literature';
        } else {
            gameMode = 'math'; // Default fallback
        }
    }

    console.log('Initializing game with mode:', gameMode);
    new TriviaGame(gameMode);
});