class TriviaGame {
    constructor(gameMode) {
        this.sections = [];
        this.currentSection = 0;
        this.currentQuestion = 0;
        this.score = 0;
        this.wrongAttempts = 0;
        this.gameMode = gameMode;
        
        this.loadQuestions().then(() => {
            this.initGame();
            this.displayQuestion();
        });
    }

    async loadQuestions() {
        const jsonFile = this.gameMode === 'anime' ? 'anime-questions.json' : 'questions.json';
        const response = await fetch(jsonFile);
        this.sections = await response.json();
    }

    // Rest of the code remains the same as in the original app.js
}

// Modify initialization to check for game mode
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const gameMode = urlParams.get('mode');
    
    if (gameMode) {
        new TriviaGame(gameMode);
    }
});