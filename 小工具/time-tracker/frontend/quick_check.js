/**
 * 浏览器控制台快速测试脚本
 * 使用方法:
 * 1. 打开 http://127.0.0.1:5000/index.html
 * 2. 按 F12 打开开发者工具
 * 3. 复制此文件内容到 Console 回车执行
 * 4. 查看输出，是否所有模块正常工作
 */
(function () {
    const logs = [];
    const line = (msg, color) => {
        const c = color || 'color:#333';
        console.log('%c' + msg, c);
        logs.push(msg);
    };
    const ok = (msg, detail) => line('✅ ' + msg + (detail ? ' -> ' + detail : ''), 'color:#4caf50;font-weight:bold');
    const warn = (msg, detail) => line('⚠️  ' + msg + (detail ? ' -> ' + detail : ''), 'color:#ff9800;font-weight:bold');
    const err = (msg, detail) => line('❌ ' + msg + (detail ? ' -> ' + detail : ''), 'color:#f44336;font-weight:bold');
    const info = (msg) => line('ℹ️ ' + msg, 'color:#2196f3;font-weight:bold');

    info('========== 考勤系统快速诊断 ==========');
    info('时间: ' + new Date().toLocaleString());
    info('URL: ' + window.location.href);

    // 1. 检查用户
    line('--- 用户状态 ---');
    try {
        const user = window.getCurrentUser ? window.getCurrentUser() : null;
        if (user) ok('已登录: ' + user.username + ' (ID=' + user.id + ')');
        else warn('未登录', '部分功能会受限');
    } catch (e) { err('检查用户失败', e.message); }

    // 2. 检查核心模块
    line('--- 核心模块初始化函数 ---');
    const checks = [
        ['考勤 (initAttendance)', typeof window.initAttendance === 'function'],
        ['工时记录 (initTimeRecord)', typeof window.initTimeRecord === 'function'],
        ['工资 (initSalaryCalculation)', typeof window.initSalaryCalculation === 'function'],
        ['工资配置 (initSalaryConfig)', typeof window.initSalaryConfig === 'function'],
        ['统计 (initStats)', typeof window.initStats === 'function'],
        ['留言 (initMessageWall)', typeof window.initMessageWall === 'function'],
        ['木鱼 (initWoodenFish)', typeof window.initWoodenFish === 'function'],
        ['数独 (initSudoku)', typeof window.initSudoku === 'function'],
        ['猜数字 (initGuessNumber)', typeof window.initGuessNumber === 'function'],
        ['基金 (FundModule)', !!(window.FundModule && typeof window.FundModule.init === 'function')],
    ];
    for (const [name, ok_bool] of checks) {
        if (ok_bool) ok(name + ' 已就绪');
        else err(name + ' 未就绪');
    }

    // 3. 测试关键 API
    line('--- 测试后端 API ---');
    (async function testAPIs() {
        const tests = [
            { name: '考勤列表', url: '/api/attendance/list?date=' + new Date().toISOString().split('T')[0] },
            { name: '工时记录', url: '/api/time-records?user_id=' + (window.getCurrentUser?.()?.id || 39) },
            { name: '统计', url: '/api/stats/shift?user_id=' + (window.getCurrentUser?.()?.id || 39) },
            { name: '留言', url: '/api/messages?page=1&per_page=3' },
            { name: '职位', url: '/api/positions' },
        ];

        for (const t of tests) {
            try {
                const res = await fetch(t.url);
                if (res.ok) {
                    const data = await res.json();
                    const desc = Array.isArray(data) ? (data.length + ' 条') : (Object.keys(data).length + ' 字段');
                    ok(t.name + ' API', desc);
                } else {
                    err(t.name + ' API', 'HTTP ' + res.status);
                }
            } catch (e) {
                err(t.name + ' API', e.message);
            }
        }

        // 4. 尝试实际初始化模块
        line('--- 尝试初始化各模块 ---');
        const initList = [
            { name: '考勤', fn: () => window.initAttendance?.() },
            { name: '工时记录', fn: () => window.initTimeRecord?.() },
            { name: '工资计算', fn: () => window.initSalaryCalculation?.() },
            { name: '基金', fn: () => window.FundModule?.init?.() },
        ];

        for (const item of initList) {
            try {
                const result = item.fn();
                if (result && typeof result.then === 'function') await result;
                ok(item.name + ' 初始化', '无错误');
            } catch (e) {
                err(item.name + ' 初始化', e.message);
            }
        }

        // 5. 检查页面实际渲染
        line('--- 检查实际渲染结果 ---');
        const attList = document.getElementById('attendance-list');
        if (attList) {
            ok('考勤列表容器存在', 'innerHTML 长度: ' + (attList.innerHTML?.length || 0));
            if (attList.innerHTML && attList.innerHTML.length > 100) {
                ok('考勤列表有内容');
            } else {
                warn('考勤列表内容可能为空', '尝试点击刷新按钮或检查 API 返回');
            }
        }

        const recList = document.getElementById('records-list');
        if (recList) {
            ok('工时记录列表容器存在', 'innerHTML 长度: ' + (recList.innerHTML?.length || 0));
        }

        const totalHours = document.getElementById('monthly-total-hours');
        if (totalHours) {
            const val = totalHours.textContent?.trim();
            if (val && val !== '0.00' && val !== '0') ok('当月工时', val + ' 小时');
            else warn('当月工时可能为空', '显示值: ' + val);
        }

        info('========== 诊断完成 ==========');
        line('提示: 如果有错误，请将上面的 ❌ 消息发给开发人员', 'color:#999');
        line('提示: 如果所有 API 返回错误，请确认后端服务器在 http://127.0.0.1:5000 运行', 'color:#999');
        line('提示: 如果一切正常但数据不显示，请尝试按 Ctrl+F5 强制刷新页面', 'color:#999');
    })();
})();
