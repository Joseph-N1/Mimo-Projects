/* 20-app.js - Trivia game with hearts, shield, streaks, toasts, sounds, and game-over overlay
   Drop into your trivia-game folder (replace existing 20-app.js)
*/

/* Feature flags - enable features per gameMode */
const GAME_FEATURES = {
    ncaa: {
        hearts: true,
        shield: true,
        streaks: true,
        sounds: true,
        gameOverStats: true
    }
    // you can add other game modes here later
};

class TriviaGame {
    // ========== CONSTRUCTOR ==========
    constructor(gameMode) {
        this.sections = [];
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.gameMode = gameMode;

        // timer
        this.timer = 60;
        this.timerInterval = null;

        // lives / hearts
        this.maxHearts = 5;
        this.hearts = this.maxHearts;
        this.shieldAvailable = true;     // one-time shield per category run
        this.correctStreak = 0;
        this.bestStreak = 0;

        // basic init
        this.loadQuestions().then(() => {
            this.initGame();
            this.displayQuestion();
        });
    }

    // ========== DATA LOADING ==========
    async loadQuestions() {
        const jsonFiles = {
            math: '12-questions.json',
            anime: '13-anime-questions.json',
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

    // ========== GAME INITIALIZATION ==========
    initGame() {
        this.resetGameState();
        this.setupEventListeners();
        // ensure hearts and toast container are rendered
        this.renderHearts();
    }

    resetGameState() {
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.timer = 60;

        // reset lives & shield for a fresh run
        this.hearts = this.maxHearts;
        this.shieldAvailable = GAME_FEATURES[this.gameMode]?.shield ?? false;
        this.correctStreak = 0;
        this.bestStreak = 0;

        this.renderHearts();
    }

    // ========== MAIN RENDER FLOW ==========
    displayQuestion() {
        this.resetUIState();
        this.updateDisplayHeaders();
        this.createQuestionOptions();
        this.startTimer();
        this.updateProgressBar();
        this.renderHearts();
    }

    resetUIState() {
        const opt = document.getElementById('options-container');
        if (opt) opt.innerHTML = '';

        const fb = document.getElementById('feedback');
        if (fb) {
            fb.innerHTML = '';
            fb.className = '';
            fb.style.display = 'none';
        }

        const ai = document.getElementById('ai-fact');
        if (ai) {
            ai.innerHTML = '';
            ai.classList.remove('visible');
        }

        const nextBtn = document.getElementById('next-btn');
        if (nextBtn) nextBtn.style.display = 'none';

        const tryBtn = document.getElementById('try-again-btn');
        if (tryBtn) tryBtn.style.display = 'none';

        // ensure hearts area exists
        if (!document.getElementById('hearts-container')) {
            this.renderHearts();
        }
    }

    updateDisplayHeaders() {
        const curSectionEl = document.getElementById('current-section');
        if (curSectionEl) curSectionEl.textContent = this.currentSection + 1;

        const timerEl = document.getElementById('timer');
        if (timerEl) timerEl.textContent = this.timer;

        const qEl = document.getElementById('question-container');
        if (qEl) qEl.innerHTML = `<h3>${this.getCurrentQuestion().question}</h3>`;
    }

    // ========== QUESTION & OPTIONS ==========
    getCurrentQuestion() {
        return this.sections[this.currentSection].questions[this.currentQuestion];
    }

    createQuestionOptions() {
        const question = this.getCurrentQuestion();
        if (!question || !question.options) return;

        const container = document.getElementById('options-container');
        question.options.forEach(option => {
            container.appendChild(this.createOptionLabel(option, question));
        });
    }

    createOptionLabel(option, question) {
        const label = document.createElement('label');
        label.className = 'material-checkbox';

        const input = document.createElement('input');
        input.type = 'checkbox';
        input.value = option;

        const span = document.createElement('span');
        span.className = 'checkmark';

        label.append(input, span, document.createTextNode(option));
        label.addEventListener('click', () => this.handleOptionSelect(input, option, question));

        return label;
    }

    handleOptionSelect(input, option, question) {
        // single-select behavior for checkboxes
        document.querySelectorAll('.material-checkbox input').forEach(cb => {
            if (cb !== input) cb.checked = false;
        });

        this.checkAnswer(option === (question.correctAnswer || question.answer));
    }

    // ========== GAME LOGIC ==========
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

        // streak logic
        this.correctStreak++;
        this.bestStreak = Math.max(this.bestStreak, this.correctStreak);

        // toast: streak building
        if (GAME_FEATURES[this.gameMode]?.streaks) {
            if (this.correctStreak === 2) {
                this.showToast('🔥 Streak building...', 'info');
            }
        }

        // award golden heart for 3 in a row
        if (GAME_FEATURES[this.gameMode]?.streaks && this.correctStreak >= 3) {
            if (this.hearts < this.maxHearts) {
                this.hearts++;
                this.renderHearts();
                this.playSound('heart-gain');
                this.showToast('✨ Perfect streak! +1 Heart', 'success');
            }
            // reset streak so user must get another 3 to earn again
            this.correctStreak = 0;
        }

        if (feedback) {
            feedback.textContent = 'Correct!';
            feedback.className = 'correct';
            feedback.style.display = 'block';
        }

        if (GAME_FEATURES[this.gameMode]?.sounds) this.playSound('correct');

        this.showAIFact();

        const nextBtn = document.getElementById('next-btn');
        if (nextBtn) nextBtn.style.display = 'block';
    }

    handleIncorrectAnswer(feedback) {
        this.wrongAttempts++;
        // reset streak
        this.correctStreak = 0;

        // shield check (one-time)
        if (GAME_FEATURES[this.gameMode]?.shield && this.shieldAvailable) {
            this.shieldAvailable = false;
            this.showToast('🛡️ Shield activated — no heart lost this time', 'success');
            if (GAME_FEATURES[this.gameMode]?.sounds) this.playSound('shield');
            // show hint/ai fact and continue allowing "try again"
            if (feedback) {
                feedback.textContent = 'Shield used — no heart lost.';
                feedback.className = 'correct';
                feedback.style.display = 'block';
            }
            this.showAIFact();
            document.getElementById('try-again-btn').style.display = 'block';
            return;
        }

        // consume a heart
        this.loseHeart();

        if (feedback) {
            feedback.textContent = 'Incorrect!';
            feedback.className = 'incorrect';
            feedback.style.display = 'block';
        }

        // highlight correct and show fact/hint
        this.highlightCorrectAnswer();
        this.showAIFact();

        const nextBtn = document.getElementById('next-btn');
        if (nextBtn) nextBtn.style.display = 'block';
    }

    highlightCorrectAnswer() {
        const correct = this.getCurrentQuestion().correctAnswer || this.getCurrentQuestion().answer;
        document.querySelectorAll('.material-checkbox').forEach(label => {
            const input = label.querySelector('input');
            if (input && input.value === correct) {
                label.classList.add('correct-answer');
            }
        });
    }

    showAIFact() {
        const q = this.getCurrentQuestion();
        if (!q) return;
        const fact = q.funFact || q.fact || '';
        const el = document.getElementById('ai-fact');
        if (el) {
            el.innerHTML = `<strong>Did you know?</strong> ${fact}`;
            el.classList.add('visible');
        }
    }

    // ========== LIVES / HEARTS ==========
    renderHearts() {
        if (!(GAME_FEATURES[this.gameMode]?.hearts)) return;
        let container = document.getElementById('hearts-container');
        if (!container) {
            // create container next to timer if missing
            const timerEl = document.getElementById('timer');
            if (timerEl && timerEl.parentNode) {
                const wrapper = document.createElement('div');
                wrapper.className = 'timer-hearts';
                timerEl.parentNode.insertBefore(wrapper, timerEl.nextSibling);
                wrapper.appendChild(timerEl); // move timer inside to wrapper
                container = document.createElement('div');
                container.id = 'hearts-container';
                container.className = 'heart-container';
                wrapper.appendChild(container);
            } else {
                // fallback: create container at top of body
                container = document.createElement('div');
                container.id = 'hearts-container';
                container.className = 'heart-container';
                document.body.appendChild(container);
            }
        }

        container.innerHTML = '';
        for (let i = 0; i < this.maxHearts; i++) {
            const s = document.createElement('span');
            s.className = 'heart ' + (i < this.hearts ? 'red' : 'gray');
            s.textContent = '❤';
            container.appendChild(s);
        }
    }

    loseHeart() {
        if (!GAME_FEATURES[this.gameMode]?.hearts) return;

        this.hearts = Math.max(0, this.hearts - 1);
        this.renderHearts();

        // animate last lost heart
        const container = document.getElementById('hearts-container');
        if (container) {
            const children = container.querySelectorAll('.heart');
            const index = Math.min(children.length - 1, this.hearts); // heart we just lost is at this index
            const heart = children[index];
            if (heart) {
                heart.classList.add('lost', 'shake');
                setTimeout(() => heart.classList.remove('shake'), 600);
            }
        }

        this.playSoundIfEnabled('wrong');
        this.showToast(`❌ Wrong — ${this.hearts} hearts remaining`, 'error');

        if (this.hearts <= 0) {
            // forced restart of the category with a 10s game over animation
            this.triggerGameOver();
        }
    }

    resetHearts() {
        this.hearts = this.maxHearts;
        this.shieldAvailable = GAME_FEATURES[this.gameMode]?.shield ?? false;
        this.renderHearts();
        this.showToast('Hearts reset to 5', 'info');
    }

    // ========== NAVIGATION ==========
    nextQuestion() {
        this.currentQuestion++;

        if (this.currentQuestion >= this.sections[this.currentSection].questions.length) {
            this.currentSection++;
            this.currentQuestion = 0;
            if (this.currentSection >= this.sections.length) {
                return this.endGame();
            }
        }

        // reset per-question timer
        this.timer = 60;
        this.displayQuestion();
    }

    restartSection() {
        this.currentQuestion = 0;
        this.wrongAttempts = 0;
        this.resetHearts();
        this.timer = 60;
        this.displayQuestion();
    }

    // ========== PROGRESS ==========
    updateProgressBar() {
        if (!this.sections || this.sections.length === 0) return;
        const progress = ((this.currentSection + 1) / this.sections.length) * 100;
        const bar = document.getElementById('progress-bar');
        if (bar) bar.style.width = `${progress}%`;
        const txt = document.getElementById('progress-text');
        if (txt) txt.textContent = `${Math.round(progress)}% Complete`;
    }

    // ========== TIMER ==========
    startTimer() {
        this.stopTimer();
        this.timerInterval = setInterval(() => {
            this.timer = Math.max(0, this.timer - 1);
            const timerEl = document.getElementById('timer');
            if (timerEl) timerEl.textContent = this.timer;
            if (this.timer <= 0) {
                this.stopTimer();
                this.checkAnswer(false);
            }
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    // ========== TOASTS ==========
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return; // container should be present in HTML (we provide snippet)
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        }, duration);
    }

    // ========== SOUNDS ==========
    playSoundIfEnabled(name) {
        if (!GAME_FEATURES[this.gameMode]?.sounds) return;
        this.playSound(name);
    }

    playSound(name) {
        // user already has assets/sounds/*.mp3
        try {
            const path = `assets/sounds/${name}.mp3`;
            const audio = new Audio(path);
            audio.volume = 0.6;
            audio.play().catch(() => {});
        } catch (e) {
            // ignore sound playback issues
            console.warn('Sound playback failed', e);
        }
    }

    // ========== GAME OVER & RESTART ==========
    triggerGameOver() {
        // stop timer & disable input
        this.stopTimer();

        // create overlay
        const overlay = document.createElement('div');
        overlay.id = 'game-over-overlay';
        overlay.innerHTML = `
            <div class="go-inner">
                <h1>GAME OVER</h1>
                <p>Final Score: ${this.score}</p>
                <p>Best streak this run: ${this.bestStreak}</p>
                <p id="go-countdown">Restarting in 10s...</p>
            </div>
        `;
        document.body.appendChild(overlay);

        if (GAME_FEATURES[this.gameMode]?.sounds) this.playSound('gameover');

        let counter = 10;
        const countdownEl = document.getElementById('go-countdown');
        const timer = setInterval(() => {
            counter--;
            if (countdownEl) countdownEl.textContent = `Restarting in ${counter}s...`;
            if (counter <= 0) {
                clearInterval(timer);
                overlay.remove();
                // reset to beginning of category (section 0) with full hearts
                this.currentSection = 0;
                this.currentQuestion = 0;
                this.resetGameState();
                this.renderHearts();
                this.displayQuestion();
                this.showToast('🔄 Restarting category with 5 hearts', 'info', 3000);
            }
        }, 1000);
    }

    // ========== GAME END ==========
    endGame() {
        const container = document.getElementById('game-container');
        if (!container) return;
        container.innerHTML = `
            <h2>Game Over!</h2>
            <p>Final Score: ${this.score}</p>
            <button id="restart-btn">Restart Game</button>
            <a href="01-index.html" class="mode-btn">Main Menu</a>
        `;
        document.getElementById('restart-btn').addEventListener('click', () => this.initGame());
    }

    // ========== EVENTS ==========
    setupEventListeners() {
        const restartBtn = document.getElementById('restart-btn');
        if (restartBtn) restartBtn.addEventListener('click', () => this.restartSection());

        const nextBtn = document.getElementById('next-btn');
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextQuestion());

        const tryBtn = document.getElementById('try-again-btn');
        if (tryBtn) tryBtn.addEventListener('click', () => this.resetQuestion());

        // ensure toast container exists
        if (!document.getElementById('toast-container')) {
            const toast = document.createElement('div');
            toast.id = 'toast-container';
            document.body.appendChild(toast);
        }
    }

    resetQuestion() {
        const fb = document.getElementById('feedback');
        if (fb) { fb.innerHTML = ''; fb.className = ''; fb.style.display = 'none'; }
        const ai = document.getElementById('ai-fact');
        if (ai) { ai.innerHTML = ''; ai.classList.remove('visible'); }
        const tryBtn = document.getElementById('try-again-btn');
        if (tryBtn) tryBtn.style.display = 'none';

        // uncheck checkboxes
        document.querySelectorAll('.material-checkbox input').forEach(checkbox => {
            checkbox.checked = false;
        });

        this.timer = 60;
        this.startTimer();
    }
}

// ========== GAME BOOTSTRAP ==========
window.addEventListener('load', () => {
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

    const path = window.location.pathname;
    const mode = Object.entries(gameModes).find(([key]) => path.includes(key))?.[1] || 'math';
    new TriviaGame(mode);
});
