class MockAIGenerator {
    constructor() {
        this.mockData = {
            sections: [{
                section: 1,
                questions: [
                    {
                        question: "Which country grows the most corn?",
                        options: ["USA", "China", "Brazil", "India"],
                        correctAnswer: "USA",
                        funFact: "USA produces 32% of world's corn!",
                        hint: "North American country"
                    },
                    {
                        question: "What is the scientific name for corn?",
                        options: ["Zea mays", "Triticum aestivum", "Oryza sativa", "Hordeum vulgare"],
                        correctAnswer: "Zea mays",
                        funFact: "Corn was first domesticated in Mexico over 10,000 years ago!",
                        hint: "Starts with 'Zea'"
                    }
                ]
            }]
        };
    }

    generate(topic) {
        const data = JSON.parse(JSON.stringify(this.mockData));
        data.sections[0].questions.forEach(question => {
            // Replace "corn" with the user's topic in both questions and fun facts
            question.question = question.question.replace(/corn/gi, topic);
            question.funFact = question.funFact.replace(/corn/gi, topic);
        });
        return data;
    }
}

class NicheGame {
    constructor() {
        this.currentTopic = null;
        this.gameData = null;
    }
    
    startGame(topic) {
        const generator = new MockAIGenerator();
        this.gameData = generator.generate(topic);
        sessionStorage.setItem('nicheQuizData', JSON.stringify(this.gameData)); // Consistent key
        window.location.href = 'niche-game-play.html';
    }
}

export default NicheGame;