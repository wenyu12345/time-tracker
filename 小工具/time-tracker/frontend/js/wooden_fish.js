class WoodenFish {
    constructor() {
        this.sound = null;
        this.dailyCount = 0;
        this.leaderboardData = [];
        this.syncInterval = null;
        this.soundEnabled = true;
        this.soundRetries = 0;
        this.maxSoundRetries = 6;  // 3 个 URL × 2 次，避免无限重试

        this.SOUND_URLS = [
            'https://assets.mixkit.co/sfx/preview/mixkit-wooden-hit-2181.mp3',
            'https://assets.mixkit.co/sfx/preview/mixkit-wooden-hit-2182.mp3',
            'https://assets.mixkit.co/sfx/preview/mixkit-wooden-block-hit-1353.mp3'
        ];

        this.currentSoundIndex = 0;

        this.bindMethods();
    }

    bindMethods() {
        this.init = this.init.bind(this);
        this.initSound = this.initSound.bind(this);
        this.playSound = this.playSound.bind(this);
        this.getCurrentDate = this.getCurrentDate.bind(this);
        this.loadDailyCount = this.loadDailyCount.bind(this);
        this.saveDailyCount = this.saveDailyCount.bind(this);
        this.updateDailyCountDisplay = this.updateDailyCountDisplay.bind(this);
        this.handleClick = this.handleClick.bind(this);
        this.syncToServer = this.syncToServer.bind(this);
        this.loadLatestCountFromServer = this.loadLatestCountFromServer.bind(this);
        this.getLeaderboardData = this.getLeaderboardData.bind(this);
        this.updateLeaderboard = this.updateLeaderboard.bind(this);
        this.displayLeaderboard = this.displayLeaderboard.bind(this);
        this.startSyncInterval = this.startSyncInterval.bind(this);
        this.stopSyncInterval = this.stopSyncInterval.bind(this);
    }

    async init() {
        console.log('初始化电子木鱼功能');

        this.initSound();
        this.loadDailyCount();
        this.updateDailyCountDisplay();
        
        await this.loadLatestCountFromServer();
        await this.updateLeaderboard();
        
        this.bindClickEvent();
        this.startSyncInterval();

        console.log('电子木鱼功能初始化完成');
    }

    initSound() {
        try {
            // 超过最大重试次数：关闭音效（无声模式仍可用）
            if (this.soundRetries >= this.maxSoundRetries) {
                console.log('音效加载失败过多，进入无声模式');
                this.soundEnabled = false;
                this.sound = null;
                return;
            }

            this.sound = new Audio(this.SOUND_URLS[this.currentSoundIndex]);
            this.sound.preload = 'auto';
            this.sound.volume = 0.5;

            this.sound.addEventListener('canplaythrough', () => {
                console.log('木鱼音效加载完成');
                this.soundRetries = 0;
            });

            this.sound.addEventListener('error', () => {
                // 静默处理，不打印 error 到控制台
                this.soundRetries++;
                this.currentSoundIndex = (this.currentSoundIndex + 1) % this.SOUND_URLS.length;
                if (this.soundRetries < this.maxSoundRetries) {
                    setTimeout(() => this.initSound(), 500);
                } else {
                    this.soundEnabled = false;
                    this.sound = null;
                }
            });
        } catch (err) {
            this.soundEnabled = false;
            this.sound = null;
        }
    }

    playSound() {
        if (!this.soundEnabled) return;
        if (!this.sound) {
            this.initSound();
            return;
        }

        try {
            this.sound.currentTime = 0;
            this.sound.play().catch(() => {
                this.currentSoundIndex = (this.currentSoundIndex + 1) % this.SOUND_URLS.length;
                const fallbackSound = new Audio(this.SOUND_URLS[this.currentSoundIndex]);
                fallbackSound.volume = 0.5;
                fallbackSound.play().catch(() => { /* 静默失败 */ });
            });
        } catch (error) {
            console.error('播放音效失败:', error);
        }
    }

    getCurrentDate() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    loadDailyCount() {
        const date = this.getCurrentDate();
        const count = localStorage.getItem(`wooden_fish_${date}`);
        this.dailyCount = count ? parseInt(count) : 0;
    }

    saveDailyCount(count) {
        const date = this.getCurrentDate();
        this.dailyCount = count;
        localStorage.setItem(`wooden_fish_${date}`, count.toString());
    }

    updateDailyCountDisplay() {
        const countElement = document.getElementById('daily-count');
        if (countElement) {
            countElement.textContent = this.dailyCount;
        }
    }

    bindClickEvent() {
        const woodenFishImage = document.getElementById('wooden-fish-image');
        if (woodenFishImage) {
            woodenFishImage.addEventListener('click', this.handleClick);
        }
    }

    async handleClick() {
        const woodenFishImage = document.getElementById('wooden-fish-image');
        if (!woodenFishImage) return;

        woodenFishImage.classList.add('shake');
        this.playSound();
        await this.syncToServer(1);

        setTimeout(() => {
            woodenFishImage.classList.remove('shake');
        }, 200);
    }

    async syncToServer(count) {
        const user = this.getCurrentUser();
        if (!user) return;

        try {
            const response = await fetch('/api/wooden-fish/tap', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: user.id,
                    count: count
                })
            });

            if (!response.ok) {
                throw new Error('服务器响应失败');
            }

            const data = await response.json();
            console.log('同步敲击次数到服务器成功:', data);

            if (data.count !== undefined) {
                this.saveDailyCount(data.count);
                this.updateDailyCountDisplay();
            }

            await this.updateLeaderboard();
        } catch (error) {
            console.error('同步数据到服务器失败:', error);
        }
    }

    async loadLatestCountFromServer() {
        const user = this.getCurrentUser();
        if (!user) return;

        try {
            const response = await fetch(`/api/wooden-fish/daily-count/${user.id}`);

            if (!response.ok) {
                throw new Error('服务器响应失败');
            }

            const data = await response.json();
            console.log('从服务器加载最新敲击次数成功:', data);

            if (data.count !== undefined) {
                this.saveDailyCount(data.count);
                this.updateDailyCountDisplay();
            }
        } catch (error) {
            console.error('从服务器加载最新敲击次数失败:', error);
        }
    }

    async getLeaderboardData() {
        console.log('开始获取木鱼排行榜数据');
        try {
            const apiUrl = '/api/wooden-fish/leaderboard';
            console.log('API请求URL:', apiUrl);

            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            console.log('API响应状态:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`服务器响应失败，状态码: ${response.status}`);
            }

            const rawText = await response.text();
            console.log('API响应原始文本:', rawText);

            let data = {};
            try {
                data = JSON.parse(rawText);
                console.log('解析后的JSON数据:', data);
            } catch (parseError) {
                console.error('解析JSON数据失败:', parseError);
                throw new Error('解析服务器响应数据失败');
            }

            let leaderboardList = [];

            if (data && data.leaderboard) {
                if (Array.isArray(data.leaderboard)) {
                    leaderboardList = data.leaderboard;
                    console.log('排行榜数据格式：包含leaderboard属性的对象');
                } else {
                    console.error('排行榜数据格式不正确：leaderboard不是数组', data.leaderboard);
                    leaderboardList = [];
                }
            } else if (Array.isArray(data)) {
                leaderboardList = data;
                console.log('排行榜数据格式：直接数组');
            } else {
                console.error('排行榜数据格式不正确:', data);
                leaderboardList = [];
            }

            if (leaderboardList.length === 0) {
                console.log('排行榜数据为空，添加模拟数据');
                leaderboardList = [
                    { username: '用户1', count: 100 },
                    { username: '用户2', count: 80 },
                    { username: '用户3', count: 60 },
                    { username: '用户4', count: 40 },
                    { username: '用户5', count: 20 }
                ];
            }

            console.log('最终使用的排行榜数据:', leaderboardList);
            return leaderboardList;
        } catch (error) {
            console.error('获取排行榜数据失败:', error);

            const mockData = [
                { username: '用户1', count: 100 },
                { username: '用户2', count: 80 },
                { username: '用户3', count: 60 },
                { username: '用户4', count: 40 },
                { username: '用户5', count: 20 }
            ];
            console.log('使用模拟数据:', mockData);
            return mockData;
        }
    }

    async updateLeaderboard() {
        console.log('开始更新木鱼排行榜显示');
        this.leaderboardData = await this.getLeaderboardData();
        this.displayLeaderboard();
    }

    displayLeaderboard() {
        let leaderboardList = document.getElementById('wooden-fish-leaderboard-list');
        
        if (!leaderboardList) {
            console.error('没有找到木鱼排行榜列表元素，尝试查找所有leaderboard-list元素');
            const allLeaderboardLists = document.querySelectorAll('.leaderboard-list');
            console.log('找到的所有leaderboard-list元素:', allLeaderboardLists.length);
            if (allLeaderboardLists.length > 0) {
                leaderboardList = allLeaderboardLists[0];
                console.log('使用第一个leaderboard-list元素作为备选');
            } else {
                console.error('没有找到任何leaderboard-list元素');
                return;
            }
        }

        try {
            console.log('获取到的排行榜数据:', this.leaderboardData);

            leaderboardList.innerHTML = '';

            if (this.leaderboardData.length === 0) {
                leaderboardList.innerHTML = '<div class="empty-message">暂无排行榜数据</div>';
                console.log('排行榜数据为空，显示提示信息');
                return;
            }

            this.leaderboardData.forEach((item, index) => {
                console.log('生成排行榜项:', index + 1, item);
                const leaderboardItem = document.createElement('div');
                leaderboardItem.className = 'leaderboard-item';

                let rankColorClass = this.getRankColorClass(index);
                const username = item.username || `用户${index + 1}`;
                const count = item.count || 0;

                leaderboardItem.innerHTML = `
                    <div class="leaderboard-rank ${rankColorClass}">${index + 1}</div>
                    <div class="leaderboard-username ${rankColorClass}">${username}</div>
                    <div class="leaderboard-score ${rankColorClass}">${count}</div>
                `;

                leaderboardList.appendChild(leaderboardItem);
            });

            console.log('排行榜更新完成');
        } catch (error) {
            console.error('更新排行榜显示失败:', error);
            leaderboardList.innerHTML = '<div class="empty-message">获取排行榜数据失败</div>';
        }
    }

    getRankColorClass(index) {
        if (index === 0) return 'rank-gold';
        if (index === 1) return 'rank-purple';
        if (index === 2) return 'rank-green';
        return 'rank-black';
    }

    startSyncInterval() {
        this.stopSyncInterval();
        this.syncInterval = setInterval(() => {
            this.loadLatestCountFromServer();
            this.updateLeaderboard();
        }, 30000);
        console.log('同步定时器已启动');
    }

    stopSyncInterval() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
            console.log('同步定时器已停止');
        }
    }

    getCurrentUser() {
        return window.getCurrentUser ? window.getCurrentUser() : null;
    }

    destroy() {
        this.stopSyncInterval();
        
        const woodenFishImage = document.getElementById('wooden-fish-image');
        if (woodenFishImage) {
            woodenFishImage.removeEventListener('click', this.handleClick);
        }

        if (this.sound) {
            this.sound.pause();
            this.sound = null;
        }

        console.log('电子木鱼已销毁');
    }
}

window.WoodenFish = WoodenFish;
window.initWoodenFish = () => {
    const woodenFish = new WoodenFish();
    woodenFish.init();
    return woodenFish;
};