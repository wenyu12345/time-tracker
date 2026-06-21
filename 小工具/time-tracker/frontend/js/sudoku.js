class SudokuGame {
    constructor() {
        this.gameState = {
            board: [],
            solution: [],
            difficulty: 'easy',
            selectedCell: null,
            gameStarted: false,
            gameCompleted: false,
            hintCount: 0,
            maxHints: 3
        };

        this.userData = {
            level: 1,
            exp: 0,
            wins: 0,
            totalGames: 0,
            username: ''
        };

        this.leaderboardData = [];

        this.DIFFICULTY_CONFIG = {
            easy: { emptyCells: 30, minClues: 40, expGain: 10 },
            medium: { emptyCells: 40, minClues: 30, expGain: 20 },
            hard: { emptyCells: 50, minClues: 20, expGain: 40 },
            hell: { emptyCells: 55, minClues: 15, expGain: 80 },
            abyss: { emptyCells: 60, minClues: 10, expGain: 160 }
        };

        this.LEVEL_CONFIG = {
            1: { requiredWins: 0 },
            2: { requiredWins: 1 },
            3: { requiredWins: 2 },
            4: { requiredWins: 4 },
            5: { requiredWins: 8 },
            6: { requiredWins: 16 },
            7: { requiredWins: 32 },
            8: { requiredWins: 64 },
            9: { requiredWins: 128 },
            10: { requiredWins: 256 }
        };

        this.bindMethods();
    }

    bindMethods() {
        this.init = this.init.bind(this);
        this.loadUserData = this.loadUserData.bind(this);
        this.saveUserData = this.saveUserData.bind(this);
        this.loadLeaderboard = this.loadLeaderboard.bind(this);
        this.updateLeaderboard = this.updateLeaderboard.bind(this);
        this.displayLeaderboard = this.displayLeaderboard.bind(this);
        this.updateUserInfoDisplay = this.updateUserInfoDisplay.bind(this);
        this.initGameControls = this.initGameControls.bind(this);
        this.initKeypadEvents = this.initKeypadEvents.bind(this);
        this.handleKeyPress = this.handleKeyPress.bind(this);
        this.handleArrowKeyPress = this.handleArrowKeyPress.bind(this);
        this.generateNewGame = this.generateNewGame.bind(this);
        this.generateSolution = this.generateSolution.bind(this);
        this.fillBoard = this.fillBoard.bind(this);
        this.shuffleArray = this.shuffleArray.bind(this);
        this.isValidMove = this.isValidMove.bind(this);
        this.generatePuzzle = this.generatePuzzle.bind(this);
        this.hasUniqueSolution = this.hasUniqueSolution.bind(this);
        this.renderBoard = this.renderBoard.bind(this);
        this.selectCell = this.selectCell.bind(this);
        this.updateCellDisplay = this.updateCellDisplay.bind(this);
        this.checkAnswer = this.checkAnswer.bind(this);
        this.isGameCompleted = this.isGameCompleted.bind(this);
        this.completeGame = this.completeGame.bind(this);
        this.checkLevelUp = this.checkLevelUp.bind(this);
        this.showHint = this.showHint.bind(this);
        this.resetGame = this.resetGame.bind(this);
        this.clearErrors = this.clearErrors.bind(this);
        this.updateGameStatus = this.updateGameStatus.bind(this);
    }

    async init() {
        console.log('初始化数独游戏');

        await this.loadUserData();
        await this.loadLeaderboard();
        this.updateUserInfoDisplay();
        this.displayLeaderboard();
        this.initGameControls();
        this.initKeypadEvents();
        this.generateNewGame();

        console.log('数独游戏初始化完成');
    }

    async loadUserData() {
        const currentUser = this.getCurrentUser();
        if (currentUser && currentUser.username) {
            this.userData.username = currentUser.username;

            try {
                const scoreData = await this.api.getScores(currentUser.id);
                if (scoreData) {
                    this.userData.level = scoreData.level || 1;
                    this.userData.exp = scoreData.exp || 0;
                    this.userData.wins = scoreData.wins || 0;
                    this.userData.totalGames = scoreData.total_games || 0;
                }
            } catch (error) {
                console.error('获取积分经验数据失败:', error);
                const savedData = localStorage.getItem('sudokuUserData');
                if (savedData) {
                    const localData = JSON.parse(savedData);
                    this.userData.level = localData.level || 1;
                    this.userData.exp = localData.exp || 0;
                    this.userData.wins = localData.wins || 0;
                    this.userData.totalGames = localData.totalGames || 0;
                }
            }
        } else {
            this.userData.username = this.userData.username || '匿名玩家';
            this.userData.level = 1;
            this.userData.exp = 0;
            this.userData.wins = 0;
            this.userData.totalGames = 0;
        }

        localStorage.setItem('sudokuUserData', JSON.stringify(this.userData));
    }

    async saveUserData() {
        localStorage.setItem('sudokuUserData', JSON.stringify(this.userData));

        const currentUser = this.getCurrentUser();
        if (currentUser && currentUser.id) {
            try {
                await this.api.updateScores({
                    user_id: currentUser.id,
                    level: this.userData.level,
                    exp: this.userData.exp,
                    wins: this.userData.wins,
                    total_games: this.userData.totalGames
                });
            } catch (error) {
                console.error('保存积分经验数据到服务器失败:', error);
            }
        }
    }

    async loadLeaderboard() {
        try {
            const leaderboard = await this.api.getLeaderboard();
            console.log('获取到的排行榜数据:', leaderboard);

            if (leaderboard && Array.isArray(leaderboard)) {
                this.leaderboardData = leaderboard;
            } else if (leaderboard && typeof leaderboard === 'object' && leaderboard.leaderboard && Array.isArray(leaderboard.leaderboard)) {
                this.leaderboardData = leaderboard.leaderboard;
            } else {
                console.error('排行榜数据格式不正确:', leaderboard);
                this.leaderboardData = [];
            }
            localStorage.setItem('sudokuLeaderboard', JSON.stringify(this.leaderboardData));
        } catch (error) {
            console.error('获取排行榜数据失败:', error);
            const savedLeaderboard = localStorage.getItem('sudokuLeaderboard');
            this.leaderboardData = savedLeaderboard ? JSON.parse(savedLeaderboard) : [];
        }
    }

    async updateLeaderboard() {
        try {
            await this.loadLeaderboard();
            this.displayLeaderboard();
        } catch (error) {
            console.error('更新排行榜失败:', error);
        }
    }

    displayLeaderboard() {
        const leaderboardList = document.getElementById('sudoku-leaderboard-list');
        if (!leaderboardList) return;

        leaderboardList.innerHTML = '';

        this.leaderboardData.forEach((item, index) => {
            const leaderboardItem = document.createElement('div');
            leaderboardItem.className = 'leaderboard-item';

            let rankColorClass = this.getRankColorClass(index);

            leaderboardItem.innerHTML = `
                <div class="leaderboard-rank ${rankColorClass}">${index + 1}</div>
                <div class="leaderboard-username ${rankColorClass}">${item.username}</div>
                <div class="leaderboard-score ${rankColorClass}">LV${item.level} | ${item.exp}经验</div>
            `;

            leaderboardList.appendChild(leaderboardItem);
        });

        if (this.leaderboardData.length === 0) {
            leaderboardList.innerHTML = '<div class="empty-message">暂无排行榜数据</div>';
        }
    }

    getRankColorClass(index) {
        if (index === 0) return 'rank-gold';
        if (index === 1) return 'rank-purple';
        if (index === 2) return 'rank-green';
        return 'rank-black';
    }

    updateUserInfoDisplay() {
        const levelElement = document.getElementById('sudoku-level');
        const expElement = document.getElementById('sudoku-exp');
        const winsElement = document.getElementById('sudoku-wins');

        if (levelElement) levelElement.textContent = `LV${this.userData.level}`;
        if (expElement) expElement.textContent = this.userData.exp;
        if (winsElement) winsElement.textContent = this.userData.wins;
    }

    initGameControls() {
        const newGameBtn = document.getElementById('new-game-btn');
        const checkAnswerBtn = document.getElementById('check-answer-btn');
        const hintBtn = document.getElementById('hint-btn');
        const resetBtn = document.getElementById('reset-btn');
        const difficultySelect = document.getElementById('sudoku-difficulty');

        if (newGameBtn) newGameBtn.addEventListener('click', this.generateNewGame);
        if (checkAnswerBtn) checkAnswerBtn.addEventListener('click', this.checkAnswer);
        if (hintBtn) hintBtn.addEventListener('click', this.showHint);
        if (resetBtn) resetBtn.addEventListener('click', this.resetGame);

        if (difficultySelect) {
            difficultySelect.addEventListener('change', (e) => {
                this.gameState.difficulty = e.target.value;
                this.generateNewGame();
            });
        }
    }

    initKeypadEvents() {
        const keypadBtns = document.querySelectorAll('.keypad-btn');
        keypadBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const num = parseInt(e.target.dataset.num);
                if (!isNaN(num)) this.handleKeyPress(num);
            });
        });

        document.addEventListener('keydown', (e) => {
            const key = e.key;
            if (key >= '1' && key <= '9') {
                this.handleKeyPress(parseInt(key));
            } else if (key === '0' || key === 'Backspace' || key === 'Delete') {
                this.handleKeyPress(0);
            } else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
                this.handleArrowKeyPress(key);
            }
        });
    }

    handleKeyPress(num) {
        if (!this.gameState.selectedCell || this.gameState.gameCompleted) return;

        const [row, col] = this.gameState.selectedCell;
        const cellElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);

        if (cellElement && cellElement.classList.contains('initial')) return;

        this.gameState.board[row][col] = num;
        this.updateCellDisplay(row, col, num);

        if (cellElement) cellElement.classList.remove('error');

        if (this.isGameCompleted()) {
            this.completeGame();
        }
    }

    handleArrowKeyPress(key) {
        if (!this.gameState.selectedCell) {
            for (let row = 0; row < 9; row++) {
                for (let col = 0; col < 9; col++) {
                    if (this.gameState.board[row][col] === 0) {
                        this.selectCell(row, col);
                        return;
                    }
                }
            }
            this.selectCell(0, 0);
            return;
        }

        let [row, col] = this.gameState.selectedCell;

        switch (key) {
            case 'ArrowUp': row = Math.max(0, row - 1); break;
            case 'ArrowDown': row = Math.min(8, row + 1); break;
            case 'ArrowLeft': col = Math.max(0, col - 1); break;
            case 'ArrowRight': col = Math.min(8, col + 1); break;
        }

        this.selectCell(row, col);
    }

    async generateNewGame() {
        const solution = this.generateSolution();
        const board = this.generatePuzzle(solution, this.gameState.difficulty);

        this.gameState = {
            board,
            solution,
            difficulty: this.gameState.difficulty,
            selectedCell: null,
            gameStarted: true,
            gameCompleted: false,
            hintCount: 0,
            maxHints: 3
        };

        this.renderBoard();
        this.updateGameStatus('新游戏已开始，请开始填写数独。');
        this.clearErrors();

        this.userData.totalGames++;
        await this.saveUserData();
    }

    generateSolution() {
        const board = Array(9).fill().map(() => Array(9).fill(0));
        this.fillBoard(board);
        return board;
    }

    fillBoard(board) {
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                if (board[row][col] === 0) {
                    const numbers = this.shuffleArray([1, 2, 3, 4, 5, 6, 7, 8, 9]);

                    for (const num of numbers) {
                        if (this.isValidMove(board, row, col, num)) {
                            board[row][col] = num;
                            if (this.fillBoard(board)) return true;
                            board[row][col] = 0;
                        }
                    }
                    return false;
                }
            }
        }
        return true;
    }

    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    isValidMove(board, row, col, num) {
        for (let c = 0; c < 9; c++) {
            if (board[row][c] === num) return false;
        }

        for (let r = 0; r < 9; r++) {
            if (board[r][col] === num) return false;
        }

        const boxRow = Math.floor(row / 3) * 3;
        const boxCol = Math.floor(col / 3) * 3;

        for (let r = boxRow; r < boxRow + 3; r++) {
            for (let c = boxCol; c < boxCol + 3; c++) {
                if (board[r][c] === num) return false;
            }
        }

        return true;
    }

    generatePuzzle(solution, difficulty) {
        const config = this.DIFFICULTY_CONFIG[difficulty] || this.DIFFICULTY_CONFIG.easy;
        const board = solution.map(row => [...row]);

        let emptyCells = 0;
        const maxEmptyCells = config.emptyCells;
        const skipUniqueCheck = difficulty === 'hell' || difficulty === 'abyss';

        while (emptyCells < maxEmptyCells) {
            const row = Math.floor(Math.random() * 9);
            const col = Math.floor(Math.random() * 9);

            if (board[row][col] !== 0) {
                const originalValue = board[row][col];
                board[row][col] = 0;
                emptyCells++;

                if (!skipUniqueCheck && !this.hasUniqueSolution(board)) {
                    board[row][col] = originalValue;
                    emptyCells--;
                }
            }
        }

        return board;
    }

    hasUniqueSolution(board) {
        const boardCopy = board.map(row => [...row]);
        let solutionCount = 0;

        const solve = (board) => {
            for (let row = 0; row < 9; row++) {
                for (let col = 0; col < 9; col++) {
                    if (board[row][col] === 0) {
                        for (let num = 1; num <= 9; num++) {
                            if (this.isValidMove(board, row, col, num)) {
                                board[row][col] = num;
                                if (solve(board)) {
                                    solutionCount++;
                                    if (solutionCount >= 2) return false;
                                }
                                board[row][col] = 0;
                            }
                        }
                        return false;
                    }
                }
            }
            return true;
        };

        solve(boardCopy);
        return solutionCount === 1;
    }

    renderBoard() {
        const boardElement = document.getElementById('sudoku-board');
        if (!boardElement) return;

        boardElement.innerHTML = '';

        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                const cell = document.createElement('div');
                cell.className = 'sudoku-cell';
                cell.dataset.row = row;
                cell.dataset.col = col;

                const value = this.gameState.board[row][col];
                if (value !== 0) {
                    cell.textContent = value;
                    cell.classList.add('initial');
                }

                cell.addEventListener('click', () => this.selectCell(row, col));
                boardElement.appendChild(cell);
            }
        }
    }

    selectCell(row, col) {
        const prevSelected = document.querySelector('.sudoku-cell.selected');
        if (prevSelected) prevSelected.classList.remove('selected');

        const cellElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        if (cellElement) cellElement.classList.add('selected');

        this.gameState.selectedCell = [row, col];
    }

    updateCellDisplay(row, col, value) {
        const cellElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        if (!cellElement) return;

        cellElement.textContent = value === 0 ? '' : value;
        cellElement.classList.add('user-input');
    }

    checkAnswer() {
        let hasError = false;

        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                const cellValue = this.gameState.board[row][col];
                const solutionValue = this.gameState.solution[row][col];
                const cellElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);

                if (cellElement) {
                    cellElement.classList.remove('error');

                    if (cellValue !== 0 && cellValue !== solutionValue) {
                        cellElement.classList.add('error');
                        hasError = true;
                    }
                }
            }
        }

        if (hasError) {
            this.updateGameStatus('答案中有错误，请检查并修改。', 'error');
        } else if (this.isGameCompleted()) {
            this.completeGame();
        } else {
            this.updateGameStatus('当前答案正确，请继续填写。', 'success');
        }
    }

    isGameCompleted() {
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                if (this.gameState.board[row][col] === 0 || 
                    this.gameState.board[row][col] !== this.gameState.solution[row][col]) {
                    return false;
                }
            }
        }
        return true;
    }

    async completeGame() {
        this.gameState.gameCompleted = true;
        this.updateGameStatus('恭喜你，完成了数独游戏！', 'success');

        this.userData.wins++;
        const expGain = this.DIFFICULTY_CONFIG[this.gameState.difficulty]?.expGain || 10;
        this.userData.exp += expGain;

        this.checkLevelUp();
        await this.saveUserData();
        this.updateUserInfoDisplay();
        await this.updateLeaderboard();
    }

    checkLevelUp() {
        for (let level = this.userData.level + 1; level <= 10; level++) {
            const config = this.LEVEL_CONFIG[level];
            if (!config) break;

            if (this.userData.wins >= config.requiredWins) {
                this.userData.level = level;
            } else {
                break;
            }
        }
    }

    showHint() {
        if (this.gameState.gameCompleted) return;

        if (this.gameState.hintCount >= this.gameState.maxHints) {
            this.updateGameStatus(`提示次数已用完，本局游戏只能提示${this.gameState.maxHints}次！`, 'error');
            return;
        }

        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                if (this.gameState.board[row][col] === 0) {
                    const solutionValue = this.gameState.solution[row][col];
                    this.gameState.board[row][col] = solutionValue;

                    const cellElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
                    if (cellElement) {
                        cellElement.textContent = solutionValue;
                        cellElement.classList.add('user-input', 'hint');
                    }

                    this.gameState.hintCount++;
                    this.updateGameStatus(`已显示一个提示，继续加油！（${this.gameState.hintCount}/${this.gameState.maxHints}）`, 'info');

                    if (this.isGameCompleted()) {
                        this.completeGame();
                    }

                    return;
                }
            }
        }

        this.updateGameStatus('没有可提示的单元格，游戏已完成！', 'success');
    }

    resetGame() {
        this.generateNewGame();
    }

    clearErrors() {
        const errorCells = document.querySelectorAll('.sudoku-cell.error');
        errorCells.forEach(cell => cell.classList.remove('error'));
    }

    updateGameStatus(message, type = 'info') {
        const statusElement = document.getElementById('sudoku-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `sudoku-status ${type}`;
        }
    }

    getCurrentUser() {
        return window.getCurrentUser ? window.getCurrentUser() : null;
    }

    get api() {
        return window.api || {};
    }
}

window.SudokuGame = SudokuGame;
window.initSudoku = () => {
    const game = new SudokuGame();
    game.init();
};