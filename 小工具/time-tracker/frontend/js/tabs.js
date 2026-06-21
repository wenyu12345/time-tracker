// 选项卡切换逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 获取所有选项卡按钮和内容面板
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // 去重集合：每个 tab 只初始化一次
    const tabInited = new Set();

    // 各 tab 对应的初始化函数
    function initTabByName(tabName) {
        // 已经初始化过就直接跳过（避免重复请求）
        if (tabInited.has(tabName)) return;
        tabInited.add(tabName);

        try {
            switch (tabName) {
                case 'home':
                    // 首页：考勤列表 / 排班 / 当月工时
                    if (typeof window.initAttendance === 'function') {
                        window.initAttendance();
                    }
                    break;
                case 'records':
                    // 工时记录
                    if (typeof window.initTimeRecord === 'function') {
                        window.initTimeRecord();
                    }
                    break;
                case 'salary':
                    // 工资计算
                    if (typeof window.initSalaryCalculation === 'function') {
                        window.initSalaryCalculation();
                    }
                    break;
                case 'salary-config':
                    // 工资算法配置
                    if (typeof window.initSalaryConfig === 'function') {
                        window.initSalaryConfig();
                    }
                    break;
                case 'stats':
                    // 统计分析
                    if (typeof window.initStats === 'function') {
                        window.initStats();
                    }
                    break;
                case 'profile':
                    // 个人中心：认证
                    if (typeof window.initAuth === 'function') {
                        window.initAuth();
                    }
                    break;
                case 'message':
                    // 留言墙
                    if (typeof window.initMessageWall === 'function') {
                        window.initMessageWall();
                    }
                    break;
                case 'fund':
                    // 基金持仓
                    if (window.FundModule && typeof window.FundModule.init === 'function') {
                        window.FundModule.init();
                    }
                    break;
                case 'wooden-fish':
                    // 电子木鱼
                    if (typeof window.initWoodenFish === 'function') {
                        window.initWoodenFish();
                    } else if (window.WoodenFish && typeof window.WoodenFish === 'function') {
                        new window.WoodenFish();
                    }
                    break;
                case 'sudoku':
                    // 数独游戏
                    if (typeof window.initSudoku === 'function') {
                        window.initSudoku();
                    } else if (window.SudokuGame && typeof window.SudokuGame === 'function') {
                        new window.SudokuGame();
                    }
                    break;
                case 'guess-number':
                    // 猜数字游戏
                    if (typeof window.initGuessNumber === 'function') {
                        window.initGuessNumber();
                    } else if (window.GuessNumberGame && typeof window.GuessNumberGame === 'function') {
                        new window.GuessNumberGame().init();
                    }
                    break;
                default:
                    tabInited.delete(tabName); // 未知 tab 不标记
                    break;
            }
        } catch (err) {
            console.error('初始化 tab 失败:', tabName, err);
        }
    }

    // 选项卡切换函数
    function switchTab(tabName) {
        // 移除所有按钮的active类
        tabBtns.forEach(btn => btn.classList.remove('active'));
        // 移除所有面板的active类
        tabPanes.forEach(pane => pane.classList.remove('active'));

        // 添加当前按钮和面板的active类
        const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
        const activePane = document.getElementById(tabName);

        if (activeBtn && activePane) {
            activeBtn.classList.add('active');
            activePane.classList.add('active');
        }

        // 初始化对应 tab 的数据 / 功能
        initTabByName(tabName);
    }
    
    // 为选项卡按钮添加点击事件
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // 模态框逻辑
    const modal = document.getElementById('batch-modal');
    const batchBtn = document.getElementById('batch-btn');
    const closeBtn = document.querySelector('.close-btn');
    
    // 打开模态框
    if (batchBtn && modal) {
        batchBtn.addEventListener('click', function() {
            modal.classList.add('active');
        });
    }
    
    // 关闭模态框
    function closeModal() {
        if (modal) {
            modal.classList.remove('active');
        }
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    // 点击模态框外部关闭
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    // 认证表单切换逻辑
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const showRegisterBtn = document.getElementById('show-register');
    const showLoginBtn = document.getElementById('show-login');
    
    if (showRegisterBtn) {
        showRegisterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
        });
    }
    
    if (showLoginBtn) {
        showLoginBtn.addEventListener('click', function(e) {
            e.preventDefault();
            registerForm.style.display = 'none';
            loginForm.style.display = 'block';
        });
    }
});
