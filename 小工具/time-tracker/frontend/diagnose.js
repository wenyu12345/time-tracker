/**
 * ============================================================
 *  考勤系统页面渲染诊断 & 修复脚本
 *  用法：在浏览器中打开 http://127.0.0.1:5000/，
 *        按 F12 打开开发者工具，将本文件内容复制粘贴到 Console 回车
 * ============================================================
 */
(function () {
    'use strict';

    const results = [];
    const fixes = [];
    const line = (msg) => { console.log('%c' + msg, 'color:#666;font-size:12px'); };
    const ok = (msg) => { console.log('%c✅ ' + msg, 'color:#4caf50;font-weight:bold'); results.push({ status: 'ok', msg }); };
    const warn = (msg) => { console.log('%c⚠️  ' + msg, 'color:#ff9800;font-weight:bold'); results.push({ status: 'warn', msg }); };
    const err = (msg) => { console.log('%c❌ ' + msg, 'color:#f44336;font-weight:bold'); results.push({ status: 'error', msg }); };

    console.log('%c============ 考勤系统页面渲染诊断 ============',
        'color:#2196f3;font-size:16px;font-weight:bold');
    console.log('%c开始时间: ' + new Date().toLocaleString(), 'color:#666');

    // ---- 1. 检查 DOM 基础结构 ----
    line('\n--- 1. 检查 DOM 结构 ---');
    const requiredElements = [
        'home', 'records', 'salary', 'salary-config', 'stats', 'profile',
        'message', 'wooden-fish', 'sudoku', 'guess-number',
        'fund',
        'attendance-date', 'attendance-list', 'shift-filter',
        'monthly-total-hours', 'monthly-day-shifts', 'monthly-night-shifts',
    ];
    for (const id of requiredElements) {
        const el = document.getElementById(id);
        if (el) ok(`DOM 元素存在: #${id}`);
        else warn(`DOM 元素缺失: #${id}`);
    }

    // ---- 2. 检查 window 全局函数 ----
    line('\n--- 2. 检查 window 全局初始化函数 ---');
    const requiredFns = [
        'initAttendance', 'initTimeRecord', 'initSalaryCalculation',
        'initSalaryConfig', 'initStats', 'initAuth', 'initMessageWall',
        'initWoodenFish', 'initSudoku', 'initGuessNumber',
    ];
    for (const fn of requiredFns) {
        if (typeof window[fn] === 'function') ok(`window.${fn} 已定义`);
        else err(`window.${fn} 未定义！`);
    }

    // ---- 3. 检查 Module 形式暴露的模块 ----
    line('\n--- 3. 检查 Module 对象 ---');
    if (window.FundModule && typeof window.FundModule.init === 'function')
        ok('FundModule.init 已定义');
    else err('FundModule.init 未定义！');

    // ---- 4. 检查当前用户 ----
    line('\n--- 4. 检查用户登录状态 ---');
    const userStr = localStorage.getItem('current_user');
    if (userStr) {
        try {
            const u = JSON.parse(userStr);
            ok(`已登录: user_id=${u.id}, username=${u.username}`);
        } catch (e) { err('current_user JSON 解析失败: ' + e.message); }
    } else {
        warn('未检测到登录用户 (localStorage.current_user 为空)');
    }

    // ---- 5. 测试关键 API 连通性 ----
    line('\n--- 5. 测试关键 API 连通性 ---');
    const date = new Date().toISOString().split('T')[0];
    const apiTests = [
        { name: '考勤列表', url: `/api/attendance/list?date=${date}&shift=all` },
        { name: '工时记录', url: '/api/time-records?user_id=39' },
        { name: '工资信息', url: `/api/salary/info/${date.slice(0, 7)}?user_id=39` },
        { name: '留言', url: '/api/messages?page=1&per_page=5' },
        { name: '基金', url: '/api/funds/holdings?user_id=39' },
    ];

    const apiPromises = apiTests.map(test =>
        fetch(test.url)
            .then(r => r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)))
            .then(data => {
                ok(`${test.name} API 正常 (${Array.isArray(data) ? data.length + '条' : 'object'})`);
                return { name: test.name, ok: true, data };
            })
            .catch(e => {
                err(`${test.name} API 失败: ${e.message}`);
                return { name: test.name, ok: false };
            })
    );

    Promise.all(apiPromises).then(apiResults => {

        // ---- 6. 执行各模块初始化并捕获错误 ----
        line('\n--- 6. 执行各模块初始化 ---');
        const initFunctions = [
            { name: '考勤 (home)', fn: () => window.initAttendance() },
            { name: '工时记录 (records)', fn: () => window.initTimeRecord() },
            { name: '工资计算 (salary)', fn: () => window.initSalaryCalculation() },
            { name: '工资配置 (salary-config)', fn: () => window.initSalaryConfig() },
            { name: '统计 (stats)', fn: () => window.initStats() },
            { name: '留言 (message)', fn: () => window.initMessageWall() },
            { name: '基金 (fund)', fn: () => window.FundModule.init() },
        ];

        for (const item of initFunctions) {
            try {
                if (typeof item.fn !== 'function') continue;
                const result = item.fn();
                if (result && typeof result.then === 'function') {
                    result.then(() => ok(`${item.name} 初始化成功 (async)`))
                        .catch(e => err(`${item.name} 初始化失败: ${e.message}`));
                } else {
                    ok(`${item.name} 初始化成功`);
                }
            } catch (e) {
                err(`${item.name} 初始化异常: ${e.message}`);
                fixes.push(item.name);
            }
        }

        // ---- 7. 渲染结果检查 ----
        setTimeout(() => {
            line('\n--- 7. 检查实际渲染结果 ---');
            const attList = document.getElementById('attendance-list');
            if (attList && attList.innerHTML && attList.innerHTML.length > 50)
                ok('考勤列表已渲染 (innerHTML.length=' + attList.innerHTML.length + ')');
            else warn('考勤列表内容为空或未加载完成');

            const recList = document.getElementById('records-list');
            if (recList && recList.innerHTML && recList.innerHTML.length > 50)
                ok('工时记录已渲染 (innerHTML.length=' + recList.innerHTML.length + ')');
            else warn('工时记录内容为空或未加载完成');

            const totalHours = document.getElementById('monthly-total-hours');
            if (totalHours && totalHours.textContent && totalHours.textContent !== '0.00' && totalHours.textContent !== '0')
                ok(`当月工时统计已更新: ${totalHours.textContent} 小时`);
            else warn('当月工时统计仍为默认值 0，可能 loadMonthlyStats 未执行或无数据');

            // ---- 8. 汇总报告 ----
            line('\n========================================');
            console.log('%c=========== 诊断报告 ===========',
                'color:#2196f3;font-size:14px;font-weight:bold');
            const errorCount = results.filter(r => r.status === 'error').length;
            const warnCount = results.filter(r => r.status === 'warn').length;
            const okCount = results.filter(r => r.status === 'ok').length;

            console.log(`%c通过: ${okCount}  警告: ${warnCount}  错误: ${errorCount}`,
                errorCount > 0 ? 'color:#f44336;font-weight:bold' :
                warnCount > 0 ? 'color:#ff9800;font-weight:bold' :
                    'color:#4caf50;font-weight:bold');

            if (errorCount > 0 || warnCount > 0) {
                console.log('%c\n需要修复的项:', 'color:#ff9800;font-weight:bold');
                results.filter(r => r.status !== 'ok').forEach(r =>
                    console.log(`  - [${r.status.toUpperCase()}] ${r.msg}`)
                );
            }

            if (errorCount === 0) {
                line('\n🎉 系统核心功能正常！如果页面仍未显示数据，请检查：');
                line('   1. 浏览器控制台是否有 JS 错误');
                line('   2. 网络请求 (Network 面板) 是否全部 200 OK');
                line('   3. 是否在首页 Tab 而不是其他 Tab');
            }

            console.log('%c\n============ 诊断结束 ============',
                'color:#2196f3;font-size:14px;font-weight:bold');
            line('提示: 可以直接点击选项卡，查看各 Tab 的加载情况');
            line('');
        }, 2500);
    });

    return { results };
})();
