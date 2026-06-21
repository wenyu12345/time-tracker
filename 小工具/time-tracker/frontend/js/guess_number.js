class GuessNumberGame {
    constructor() {
        this.gameState = {
            targetNumber: 0,
            remainingGuesses: 6,
            maxGuesses: 6,
            gameStarted: false,
            gameCompleted: false,
            guessHistory: []
        };

        this.userStats = {
            totalGames: 0,
            wins: 0,
            winRate: 0
        };

        this.leaderboardData = [];

        this.bindMethods();
    }

    bindMethods() {
        this.init = this.init.bind(this);
        this.startNewGame = this.startNewGame.bind(this);
        this.submitGuess = this.submitGuess.bind(this);
        this.handleWin = this.handleWin.bind(this);
        this.handleLose = this.handleLose.bind(this);
        this.updateGameStatus = this.updateGameStatus.bind(this);
        this.updateRemainingGuesses = this.updateRemainingGuesses.bind(this);
        this.updateGuessHistory = this.updateGuessHistory.bind(this);
        this.loadUserStats = this.loadUserStats.bind(this);
        this.loadLeaderboard = this.loadLeaderboard.bind(this);
        this.updateUserStatsDisplay = this.updateUserStatsDisplay.bind(this);
        this.displayLeaderboard = this.displayLeaderboard.bind(this);
        this.saveGameResult = this.saveGameResult.bind(this);
        this.bindEventListeners = this.bindEventListeners.bind(this);
    }

    async init() {
        console.log('猜数字游戏初始化开始');

        this.resetGameState();

        await this.loadUserStats();
        await this.loadLeaderboard();

        this.updateUserStatsDisplay();
        this.displayLeaderboard();
        this.updateGameStatus('游戏未开始，请点击"开始新游戏"按钮。', 'info');
        this.updateRemainingGuesses();
        this.updateGuessHistory();

        this.bindEventListeners();

        console.log('猜数字游戏初始化完成');
    }

    resetGameState() {
        this.gameState = {
            targetNumber: 0,
            remainingGuesses: 6,
            maxGuesses: 6,
            gameStarted: false,
            gameCompleted: false,
            guessHistory: []
        };
        console.log('游戏状态已重置:', this.gameState);
    }

    bindEventListeners() {
        console.log('绑定事件监听器');

        document.addEventListener('click', (e) => {
            if (e.target.id === 'new-guess-game-btn') {
                console.log('开始新游戏按钮被点击');
                this.startNewGame();
            } else if (e.target.id === 'submit-guess-btn') {
                console.log('提交猜测按钮被点击');
                this.submitGuess();
            }
        });

        document.addEventListener('keypress', (e) => {
            if (e.target.id === 'guess-input' && e.key === 'Enter') {
                console.log('猜测输入框回车键被按下');
                this.submitGuess();
            }
        });

        console.log('事件监听器绑定完成');
    }

    async loadUserStats() {
        console.log('加载用户统计数据');

        try {
            let currentUser = null;
            if (window.getCurrentUser) {
                currentUser = window.getCurrentUser();
            }

            this.userStats.totalGames = 0;
            this.userStats.wins = 0;
            this.userStats.winRate = 0;

            if (currentUser && currentUser.id) {
                console.log('当前用户ID:', currentUser.id);
                const stats = await this.api.getStats(currentUser.id);
                if (stats) {
                    console.log('从服务器获取的统计数据:', stats);
                    this.userStats.totalGames = stats.total_games || 0;
                    this.userStats.wins = stats.wins || 0;
                }
            } else {
                console.log('未登录用户或用户ID不存在');
            }

            this.userStats.winRate = this.userStats.totalGames > 0 ?
                Math.round((this.userStats.wins / this.userStats.totalGames) * 100) : 0;

            console.log('用户统计数据加载完成:', this.userStats);
        } catch (error) {
            console.error('加载用户统计数据失败:', error);
            this.userStats.totalGames = 0;
            this.userStats.wins = 0;
            this.userStats.winRate = 0;
        }
    }

    async loadLeaderboard() {
        console.log('加载排行榜数据');

        try {
            this.leaderboardData = await this.api.getLeaderboard();
            console.log('排行榜数据加载完成:', this.leaderboardData);
        } catch (error) {
            console.error('加载排行榜数据失败:', error);
            this.leaderboardData = [];
        }
    }

    updateUserStatsDisplay() {
        console.log('更新用户统计显示:', this.userStats);

        const totalGamesElement = document.getElementById('guess-total-games');
        const winsElement = document.getElementById('guess-wins');
        const winRateElement = document.getElementById('guess-win-rate');

        if (totalGamesElement) totalGamesElement.textContent = this.userStats.totalGames;
        if (winsElement) winsElement.textContent = this.userStats.wins;
        if (winRateElement) winRateElement.textContent = `${this.userStats.winRate}%`;
    }

    displayLeaderboard() {
        console.log('显示排行榜:', this.leaderboardData);

        const leaderboardList = document.getElementById('guess-number-leaderboard-list');
        if (!leaderboardList) {
            console.error('没有找到排行榜列表元素');
            return;
        }

        leaderboardList.innerHTML = '';

        this.leaderboardData.forEach((item, index) => {
            const leaderboardItem = document.createElement('div');
            leaderboardItem.className = 'leaderboard-item';

            let rankColorClass = this.getRankColorClass(index);
            const username = item.username || `用户${index + 1}`;

            leaderboardItem.innerHTML = `
                <div class="leaderboard-rank ${rankColorClass}">${index + 1}</div>
                <div class="leaderboard-username ${rankColorClass}">${username}</div>
                <div class="leaderboard-score ${rankColorClass}">
                    <span>胜率: ${item.win_rate}%</span>
                    <span>游戏次数: ${item.total_games}</span>
                    <span>胜利次数: ${item.wins}</span>
                </div>
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

    startNewGame() {
        console.log('开始新游戏');

        this.gameState = {
            targetNumber: this.generateRandomNumber(),
            remainingGuesses: 6,
            maxGuesses: 6,
            gameStarted: true,
            gameCompleted: false,
            guessHistory: []
        };

        console.log('新游戏开始，目标数字:', this.gameState.targetNumber);

        this.updateGameStatus('游戏已开始，请输入1-100之间的数字进行猜测。', 'info');
        this.updateRemainingGuesses();
        this.updateGuessHistory();

        const guessInput = document.getElementById('guess-input');
        if (guessInput) {
            guessInput.value = '';
            guessInput.disabled = false;
            guessInput.focus();
        }
    }

    generateRandomNumber() {
        return Math.floor(Math.random() * 100) + 1;
    }

    async submitGuess() {
        console.log('提交猜测');

        if (!this.gameState.gameStarted || this.gameState.gameCompleted) {
            this.updateGameStatus('游戏未开始或已结束，请点击"开始新游戏"按钮。', 'error');
            return;
        }

        const guessInput = document.getElementById('guess-input');
        if (!guessInput) {
            console.error('没有找到猜测输入框');
            return;
        }

        const inputValue = guessInput.value.trim();
        const guess = parseInt(inputValue);

        if (!this.isValidGuess(guess)) {
            this.updateGameStatus('请输入1-100之间的有效数字。', 'error');
            return;
        }

        this.gameState.remainingGuesses--;
        this.gameState.guessHistory.push(guess);

        if (guess === this.gameState.targetNumber) {
            await this.handleWin();
        } else if (this.gameState.remainingGuesses <= 0) {
            await this.handleLose();
        } else {
            const isHigh = guess > this.gameState.targetNumber;
            const message = isHigh ?
                `猜大了！还有 ${this.gameState.remainingGuesses} 次机会。` :
                `猜小了！还有 ${this.gameState.remainingGuesses} 次机会。`;
            this.updateGameStatus(message, isHigh ? 'error' : 'info');
        }

        this.updateRemainingGuesses();
        this.updateGuessHistory();
        guessInput.value = '';
    }

    isValidGuess(guess) {
        return !isNaN(guess) && guess >= 1 && guess <= 100;
    }

    async handleWin() {
        console.log('处理胜利');

        this.gameState.gameCompleted = true;

        this.updateGameStatus(
            `恭喜你，猜对了！目标数字是 ${this.gameState.targetNumber}！`,
            'success'
        );

        this.userStats.totalGames++;
        this.userStats.wins++;
        this.userStats.winRate = Math.round((this.userStats.wins / this.userStats.totalGames) * 100);

        this.updateUserStatsDisplay();

        const guessInput = document.getElementById('guess-input');
        if (guessInput) guessInput.disabled = true;

        await this.saveGameResult(true);
        await this.loadLeaderboard();
        this.displayLeaderboard();
    }

    async handleLose() {
        console.log('处理失败');

        this.gameState.gameCompleted = true;

        this.updateGameStatus(
            `很遗憾，你没有猜对。目标数字是 ${this.gameState.targetNumber}！`,
            'error'
        );

        this.userStats.totalGames++;
        this.userStats.winRate = Math.round((this.userStats.wins / this.userStats.totalGames) * 100);

        this.updateUserStatsDisplay();

        const guessInput = document.getElementById('guess-input');
        if (guessInput) guessInput.disabled = true;

        await this.saveGameResult(false);
        await this.loadLeaderboard();
        this.displayLeaderboard();
    }

    async saveGameResult(isWin) {
        console.log('保存游戏结果到服务器:', isWin);

        try {
            let currentUser = null;
            if (window.getCurrentUser) {
                currentUser = window.getCurrentUser();
            }

            if (currentUser && currentUser.id) {
                console.log('当前用户ID:', currentUser.id, '保存游戏结果，胜利:', isWin);
                const response = await this.api.updateStats({
                    user_id: currentUser.id,
                    is_win: isWin
                });
                console.log('游戏结果保存成功，服务器响应:', response);
            } else {
                console.log('未登录用户或用户ID不存在，不保存游戏结果');
            }
        } catch (error) {
            console.error('保存游戏结果失败:', error);
        }
    }

    updateGameStatus(message, type = 'info') {
        console.log('更新游戏状态:', message, type);

        const statusElement = document.getElementById('guess-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status-message ${type}`;
        } else {
            console.error('没有找到游戏状态元素');
        }
    }

    updateRemainingGuesses() {
        console.log('更新剩余猜测次数:', this.gameState.remainingGuesses);

        const remainingGuessesElement = document.getElementById('remaining-guesses');
        if (remainingGuessesElement) {
            remainingGuessesElement.textContent = this.gameState.remainingGuesses;
        }
    }

    updateGuessHistory() {
        console.log('更新猜测历史:', this.gameState.guessHistory);

        const guessHistoryElement = document.getElementById('guess-history');
        if (!guessHistoryElement) {
            console.error('没有找到猜测历史元素');
            return;
        }

        guessHistoryElement.innerHTML = '';

        this.gameState.guessHistory.forEach(guess => {
            const historyItem = document.createElement('div');
            historyItem.className = 'guess-history-item';

            if (guess === this.gameState.targetNumber) {
                historyItem.className += ' correct';
                historyItem.textContent = `${guess} ✓`;
            } else if (guess > this.gameState.targetNumber) {
                historyItem.className += ' high';
                historyItem.textContent = `${guess} ↑`;
            } else {
                historyItem.className += ' low';
                historyItem.textContent = `${guess} ↓`;
            }

            guessHistoryElement.appendChild(historyItem);
        });
    }

    get api() {
        return window.api || {};
    }
}

// 暴露给 app.js 统一调度初始化，以及 tabs.js 切换 tab 时调用
window.GuessNumberGame = GuessNumberGame;
window.initGuessNumber = () => {
    if (typeof window.api === 'undefined') {
        console.error('猜数字游戏：API对象未就绪，跳过初始化');
        return;
    }
    const game = new GuessNumberGame();
    game.init();
    return game;
};