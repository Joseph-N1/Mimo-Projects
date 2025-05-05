#### Chess Game

#### Project Overview

This is a complete browser-based chess game implemented with JavaScript, jQuery, and CSS. The game features all standard chess rules with a clean, interactive interface.

#### Game Logic Implementation

Core Mechanics
Board Representation:

8x8 grid with algebraic notation (a1-h8)

Each piece stored as an object with position, type, and movement status

Turn Management:

Alternates between white ('w') and black ('b')

Visual turn indicator with animation

Movement System:

Piece-specific move validation

Highlighting of valid moves

Special moves (castling, pawn promotion)

#### Key Algorithms

Move Validation:

javascript
// Example: Knight movement
coordinates = [
{ x: -1, y: 2 }, { x: 1, y: 2 },
{ x: 1, y: -2 }, { x: -1, y: -2 },
// ... other L-shaped moves
].map(val => `${x+val.x}_${y+val.y}`);
Path Checking (for sliding pieces):

javascript
// Bishop line-of-sight check
bishopDirections.forEach(dir => {
dir.some(step => {
// Check each square until obstruction
});
});
Special Moves:

Castling (king + rook initial move check)

Pawn promotion (automatic queen conversion)

En passant (planned)

#### Technologies Used

Core Stack
JavaScript (Game logic, state management)

jQuery (DOM manipulation, event handling)

CSS3 (Styling, animations)

HTML5 (Board structure)

#### Key Concepts Applied

Object-Oriented Design:

Piece objects with properties/behaviors

Game state management

Event-Driven Programming:

Click handlers for moves

Turn-based flow control

Functional Programming:

Array methods (map, filter, reduce)

Pure functions for move validation

#### Recent Improvements

Code Quality
Structural Improvements:

Removed duplicate endturn implementation

Fixed syntax errors (braces/parentheses)

Consolidated methods into proper objects

Game Logic Fixes:

Corrected castling conditions

Improved pawn promotion

Enhanced move validation

Performance
Optimized DOM updates

Reduced redundant calculations

Improved jQuery selector efficiency

#### Future Enhancements

CSS Improvements Planned
Visual Upgrades:

css
/_ Proposed piece styling _/
.piece {
transition: transform 0.2s ease;
cursor: grab;
}
.piece:active {
transform: scale(1.1);
cursor: grabbing;
}
Responsive Design:

Media queries for mobile devices

Flexible board sizing

Animations:

Smooth piece movements

Capture effects

Check/checkmate indicators

Game Features
En passant implementation

Check/checkmate detection

Move history panel

Player vs AI mode

Game timer/clock

#### Setup Instructions

Clone repository:

bash
git clone https://github.com/Joseph-N1/Mimo-Projects/tree/main/JavaScript%20Chess%20Game
Open index.html in browser

No dependencies needed (jQuery loaded from CDN)

#### How to Contribute

Report bugs via Issues

Submit CSS improvements

Suggest new features

Implement planned enhancements

#### Credits

Developed by [Joseph-N1]

chess-game/
├── index.html # Main interface
├── script.js # Game logic (25KB)
├── style.css # Styles (3KB)
├── assets/ # Piece images/sounds
└── README.md # This file
License: MIT
