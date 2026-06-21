/**
 * ============================================================
 *  页面渲染一键恢复脚本
 *  功能：
 *    1. 检测页面是否正常渲染
 *    2. 如果不正常，自动重新初始化所有模块
 *    3. 给出详细的诊断报告
 * 
 *  使用方法：
 *    方式1. 直接在浏览器 Console 中粘贴本文件内容运行
 *    方式2. 在 index.html 中添加 <script src="js/recover.js"></script>
 * ============================================================
 */
(function () {
    'use strict';

    // ====== 工具函数 ======
    function log(type, msg, data) {
        const colors = {
            info: 'color:#2196f3',
            ok: 'color:#4caf50;font-weight:bold',
            warn: 'color:#ff9800;font-weight:bold',
            error: 'color:#f44336;font-weight:bold',
            title: 'color:#2196f3;font-size:16px;font-weight:bold'
        };
        const prefix = {
            info: 'ℹ️ ',
            ok: '✅ ',
            warn: '⚠️  ',
            error: '❌ ',
            title: '═══ '
        };
        if (data !== undefined) {
            console.log('%c' + prefix[type] + msg, colors[type], data);
        } else {
            console.log('%c' + prefix[type] + msg, colors[type]);
        }
    }

    // ====== 1. 诊断 ======
    function diagnose() {
        log('title', '考勤系统 页面诊断 开始');
        log('info', '时间: ' + new Date().toLocaleString());
        log('info', 'URL: ' + window.location.href);

        const issues = [];

        // 1.1 检查用户登录状态
        log('info', '1. 检查用户登录状态');
        try {
            const userStr = localStorage.getItem('current_user');
            if (!userStr) {
                log('warn', '用户未登录');
                issues.push({ type: 'auth', msg: '用户未登录' });
            } else {
                const user = JSON.parse(userStr);
                log('ok', `已登录: ${user.username} (id=${user.id})`);
            }
        } catch (e) {
            log('error', '解析用户信息失败: ' + e.message);
            issues.push({ type: 'auth', msg: '用户信息损坏' });
        }

        // 1.2 检查必要的 DOM 元素
        log('info', '2. 检查 DOM 元素');
        const domChecks = [
            ['home Tab (首页)', document.getElementById('home')],
            ['考勤日期选择', document.getElementById('attendance-date')],
            ['考勤列表', document.getElementById('attendance-list')],
            ['班别筛选', document.getElementById('shift-filter')],
            ['当月工时', document.getElementById('monthly-total-hours')],
            ['工时记录列表', document.getElementById('records-list')],
        ];
        for (const [name, el] of domChecks) {
            if (el) log('ok', name + ': 存在');
            else {
                log('error', name + ': 缺失');
                issues.push({ type: 'dom', msg: name + ' 缺失' });
            }
        }

        // 1.3 检查 window 暴露的初始化函数
        log('info', '3. 检查 JS 模块初始化接口');
        const moduleChecks = [
            ['考勤 (initAttendance)', typeof window.initAttendance === 'function'],
            ['工时记录 (initTimeRecord)', typeof window.initTimeRecord === 'function'],
            ['工资计算 (initSalaryCalculation)', typeof window.initSalaryCalculation === 'function'],
            ['工资配置 (initSalaryConfig)', typeof window.initSalaryConfig === 'function'],
            ['统计 (initStats)', typeof window.initStats === 'function'],
            ['留言 (initMessageWall)', typeof window.initMessageWall === 'function'],
            ['基金 (FundModule.init)', window.FundModule && typeof window.FundModule.init === 'function'],
        ];
        for (const [name, ok] of moduleChecks) {
            if (ok) log('ok', name + ': 已就绪');
            else {
                log('error', name + ': 未就绪');
                issues.push({ type: 'module', msg: name + ' 未就绪' });
            }
        }

        // 1.4 检查考勤列表是否有内容
        log('info', '4. 检查考勤列表内容');
        const attList = document.getElementById('attendance-list');
        if (attList) {
            const htmlLen = attList.innerHTML.length;
            // > 20 字节表示 renderAttendanceList 至少写入了一条提示（"暂无出勤记录" ≈ 60 字节）
            // 真正的渲染失败是 innerHTML === '' 或依然停留在 "加载中..." 骨架
            const isEmptyData = htmlLen < 20 || htmlLen === '<div style="text-align:center;padding:2rem;color:#666;">加载中...</div>'.length;
            const looksHealthy = htmlLen > 20 && !attList.innerHTML.includes('加载失败') && !attList.innerHTML.includes('加载中...');
            if (looksHealthy) {
                log('ok', '考勤列表有内容 (innerHTML.length=' + htmlLen + ')');
            } else {
                log('warn', '考勤列表可能异常 - innerHTML.length=' + htmlLen);
                issues.push({ type: 'render', msg: '考勤列表异常' });
            }
        }

        // 1.5 检查当月工时
        log('info', '5. 检查当月工时统计');
        const stats = document.getElementById('monthly-total-hours');
        if (stats) {
            const val = stats.textContent.trim();
            // 0 小时也可能是真实状态（新用户/周末），只要 innerHTML 被写入了就视为正常
            const looksHealthy = val !== '';
            if (looksHealthy) {
                log('ok', '当月工时统计已渲染: ' + val + ' 小时');
            } else {
                log('warn', '当月工时未渲染 - textContent 为空');
                issues.push({ type: 'render', msg: '当月工时未更新' });
            }
        }

        return issues;
    }

    // ====== 2. 恢复 ======
    function recover() {
        log('title', '开始执行页面恢复');

        // 2.1 恢复考勤模块
        try {
            if (typeof window.initAttendance === 'function') {
                window.initAttendance();
                log('ok', '考勤模块已重新初始化');
            } else {
                log('error', '考勤模块不可用');
            }
        } catch (e) {
            log('error', '考勤模块初始化失败: ' + e.message);
        }

        // 2.2 恢复工时记录模块（含当月工时统计）
        try {
            if (typeof window.initTimeRecord === 'function') {
                window.initTimeRecord();
                log('ok', '工时记录模块已重新初始化');
            }
        } catch (e) {
            log('error', '工时记录模块初始化失败: ' + e.message);
        }

        // 2.3 恢复工资模块
        try {
            if (typeof window.initSalaryCalculation === 'function') {
                window.initSalaryCalculation();
                log('ok', '工资计算模块已重新初始化');
            }
        } catch (e) {
            log('error', '工资计算模块初始化失败: ' + e.message);
        }

        // 2.4 恢复工资配置
        try {
            if (typeof window.initSalaryConfig === 'function') {
                window.initSalaryConfig();
                log('ok', '工资配置模块已重新初始化');
            }
        } catch (e) {
            log('error', '工资配置模块初始化失败: ' + e.message);
        }

        // 2.5 恢复统计模块
        try {
            if (typeof window.initStats === 'function') {
                window.initStats();
                log('ok', '统计分析模块已重新初始化');
            }
        } catch (e) {
            log('error', '统计模块初始化失败: ' + e.message);
        }

        // 2.6 恢复留言墙
        try {
            if (typeof window.initMessageWall === 'function') {
                window.initMessageWall();
                log('ok', '留言墙模块已重新初始化');
            }
        } catch (e) {
            log('error', '留言墙模块初始化失败: ' + e.message);
        }

        // 2.7 恢复基金
        try {
            if (window.FundModule && typeof window.FundModule.init === 'function') {
                window.FundModule.init();
                log('ok', '基金模块已重新初始化');
            }
        } catch (e) {
            log('error', '基金模块初始化失败: ' + e.message);
        }

        // 2.8 异步确认结果
        setTimeout(() => {
            log('title', '恢复操作完成');
            checkResults();
        }, 3000);
    }

    function checkResults() {
        const checks = [
            ['考勤列表', () => document.getElementById('attendance-list')?.innerHTML?.length > 100],
            ['当月工时统计', () => {
                const v = document.getElementById('monthly-total-hours')?.textContent?.trim();
                return v && v !== '0' && v !== '0.00';
            }],
            ['工时记录列表', () => document.getElementById('records-list')?.innerHTML?.length > 100],
        ];
        log('info', '=== 恢复后检查 ===');
        for (const [name, check] of checks) {
            try {
                if (check()) log('ok', name + ' 正常');
                else log('warn', name + ' 可能仍有问题');
            } catch (e) {
                log('error', name + ' 检查异常: ' + e.message);
            }
        }
        log('title', '诊断恢复结束');
        log('info', '提示: 如果仍无数据，请检查 Network 面板中的 API 请求');
    }

    // ====== 主流程 ======
    const issues = diagnose();
    log('info', `--- 诊断发现 ${issues.length} 个问题 ---`);
    if (issues.length === 0) {
        log('ok', '系统运行正常！如仍有问题，请检查浏览器控制台错误消息');
        log('info', '可以手动执行 window.recoverPage() 来强制重新渲染');
    } else {
        log('warn', '系统需要恢复，500ms 后开始执行恢复操作...');
        setTimeout(recover, 500);
    }

    // 暴露给外部调用
    window.recoverPage = function () {
        log('title', '手动触发页面恢复');
        recover();
    };

})();
