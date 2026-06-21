/**
 * ============================================================
 *  考勤系统 - 完整启动与诊断脚本
 *  
 *  功能:
 *    - 页面加载时自动初始化所有模块
 *    - 提供手动初始化按钮
 *    - 捕获所有模块初始化错误并显示
 *    - 提供在线诊断工具
 * 
 *  在 index.html 中引入: <script src="js/boot.js"></script>
 * ============================================================
 */
(function () {
    'use strict';

    // ====== 配置 ======
    // 每个模块定义：名称、init 函数（运行时从 window 读取）、对应 tab
    const MODULES = [
        { name: '考勤列表', check: () => typeof window.initAttendance === 'function', init: () => window.initAttendance?.(), tab: 'home' },
        { name: '工时记录', check: () => typeof window.initTimeRecord === 'function', init: () => window.initTimeRecord?.(), tab: 'records' },
        { name: '工资计算', check: () => typeof window.initSalaryCalculation === 'function', init: () => window.initSalaryCalculation?.(), tab: 'salary' },
        { name: '工资配置', check: () => typeof window.initSalaryConfig === 'function', init: () => window.initSalaryConfig?.(), tab: 'salary-config' },
        { name: '统计分析', check: () => typeof window.initStats === 'function', init: () => window.initStats?.(), tab: 'stats' },
        { name: '留言墙', check: () => typeof window.initMessageWall === 'function', init: () => window.initMessageWall?.(), tab: 'message' },
        { name: '电子木鱼', check: () => typeof window.initWoodenFish === 'function', init: () => window.initWoodenFish?.(), tab: 'wooden-fish' },
        { name: '数独游戏', check: () => typeof window.initSudoku === 'function', init: () => window.initSudoku?.(), tab: 'sudoku' },
        { name: '猜数字', check: () => typeof window.initGuessNumber === 'function', init: () => window.initGuessNumber?.(), tab: 'guess-number' },
        { name: '基金持仓', check: () => !!(window.FundModule && typeof window.FundModule.init === 'function'), init: () => window.FundModule?.init?.(), tab: 'fund' },
    ];

    const errors = [];

    // ====== 初始化函数 ======
    // 【最小化加载模式】默认只启动 auth + 考勤，其他模块延迟到用户点击 tab 时触发
    async function initAll(showLog) {
        if (showLog) console.log('%c🚀 开始初始化所有模块...', 'color:#667eea;font-weight:bold');

        // 1. 认证模块先初始化
        try {
            if (typeof window.initAuth === 'function') {
                await window.initAuth();
                if (showLog) console.log('✅ 认证模块初始化完成');
            }
        } catch (e) {
            errors.push('认证: ' + e.message);
            console.error('❌ 认证模块初始化失败:', e);
        }

        // 2. 只启动 考勤列表（home tab），其余模块延后到用户点击对应 tab 时触发
        // （由 tabs.js 的 switchTab -> initTabByName 处理）
        for (const m of MODULES) {
            if (m.tab === 'home') {
                try {
                    const result = m.init();
                    if (result && typeof result.then === 'function') await result;
                    if (showLog) console.log('✅ ' + m.name + ' 初始化完成');
                } catch (e) {
                    errors.push(m.name + ': ' + e.message);
                    console.error('❌ ' + m.name + ' 初始化失败:', e);
                }
            } else {
                if (showLog) console.log('⏸  ' + m.name + ' 【延迟加载】点击对应 tab 时再初始化');
            }
        }

        if (showLog) {
            if (errors.length === 0) {
                console.log('%c🎉 考勤模块初始化成功！（其他模块采用懒加载）', 'color:#4caf50;font-weight:bold;font-size:14px');
            } else {
                console.warn('%c⚠️ 部分模块初始化失败: ' + errors.length + ' 项', 'color:#ff9800;font-weight:bold');
                errors.forEach(e => console.warn('  - ' + e));
            }
        }

        return errors.length === 0;
    }

    // ====== 初始化指定选项卡 ======
    function initTab(tabName) {
        const module = MODULES.find(m => m.tab === tabName);
        if (!module) {
            console.warn('未找到选项卡对应的模块:', tabName);
            return;
        }
        try {
            const result = module.init();
            if (result && typeof result.then === 'function') {
                result.catch(e => console.error(tabName + ' 初始化失败:', e));
            }
            console.log('✅ 已初始化: ' + module.name);
        } catch (e) {
            console.error('❌ 初始化 ' + module.name + ' 失败:', e);
        }
    }

    // ====== 显示诊断浮窗 ======
    function showDiagnosticBar() {
        // 防止重复创建
        if (document.getElementById('boot-diagnostic-bar')) return;

        const bar = document.createElement('div');
        bar.id = 'boot-diagnostic-bar';
        bar.style.cssText = `
            position:fixed;bottom:10px;right:10px;z-index:999999;
            background:rgba(0,0,0,0.85);color:white;padding:10px 15px;
            border-radius:8px;font-size:12px;font-family:Arial,sans-serif;
            box-shadow:0 4px 12px rgba(0,0,0,0.3);max-width:320px;
        `;

        const isOK = errors.length === 0;
        const user = window.getCurrentUser ? window.getCurrentUser() : null;

        bar.innerHTML = `
            <div style="margin-bottom:8px;font-weight:bold;${isOK ? 'color:#7ec699' : 'color:#f087bd'}">
                ${isOK ? '✅ 系统正常' : '⚠️ 发现 ' + errors.length + ' 个问题'}
            </div>
            <div style="margin-bottom:8px;color:#aaa;font-size:11px">
                用户: ${user ? user.username : '未登录'}
            </div>
            <div style="display:flex;gap:5px;flex-wrap:wrap">
                <button onclick="window.Boot.reinitAll()" style="background:#667eea;color:white;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px">🔄 重新加载</button>
                <button onclick="window.Boot.diagnose()" style="background:#ff9800;color:white;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px">🔍 诊断</button>
                <button onclick="window.Boot.close()" style="background:#666;color:white;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px">✕</button>
            </div>
        `;

        document.body.appendChild(bar);
    }

    // ====== 运行完整诊断 ======
    async function runDiagnose() {
        alert('🔍 运行完整诊断...\n\n请在浏览器 Console (F12) 查看详细输出。\n\n或者访问 diagnose.html 查看图形化诊断报告。');

        console.log('%c========== 完整诊断报告 ==========', 'color:#2196f3;font-weight:bold;font-size:14px');

        // 0. 环境自检（关键 — "Failed to fetch" 80% 来自 page origin 与 API 不匹配）
        console.log('\n%c[0/4] 环境检查:', 'color:#2196f3;font-weight:bold');
        try {
            const href = (window.location && window.location.href) || 'unknown';
            const proto = (window.location && window.location.protocol) || 'unknown';
            const apiTarget = window.__API_BASE_URL__ || '/api';
            let status = '✅ 正常';
            let tips = '';
            if (proto === 'file:') {
                status = '❌ 严重问题';
                tips = '（您直接双击了 index.html，应当用浏览器打开 http://127.0.0.1:5000/）';
            } else if (apiTarget !== '/api' && apiTarget.indexOf('127.0.0.1') < 0) {
                status = '⚠️ 注意';
                tips = '（API 目标已显式覆盖为：' + apiTarget + '）';
            }
            console.log('  页面地址: ' + href);
            console.log('  API 目标: ' + apiTarget);
            console.log('  状态: ' + status + (tips ? ' ' + tips : ''));
        } catch (e) { console.log('  环境检查异常: ' + e); }

        // 1. 检查模块暴露（只检查函数是否存在，不执行）
        console.log('\n%c[1/4] 检查模块暴露:', 'color:#667eea;font-weight:bold');
        for (const m of MODULES) {
            if (m.check && m.check()) {
                console.log('  ✅ ' + m.name + ' - 已就绪');
            } else {
                console.log('  ❌ ' + m.name + ' - 初始化函数未就绪');
            }
        }

        // 2. 检查 API 连通性
        console.log('\n%c[2/4] 检查后端 API:', 'color:#667eea;font-weight:bold');
        const apis = [
            '考勤列表', '/api/attendance/list?date=' + new Date().toISOString().split('T')[0],
            '工时记录', '/api/time-records?user_id=' + (window.getCurrentUser?.()?.id || 39),
            '工资配置', '/api/salary/config',
            '统计数据', '/api/stats/shift?user_id=' + (window.getCurrentUser?.()?.id || 39),
            '留言墙', '/api/messages?page=1&per_page=3',
            '基金持仓', '/api/funds/holdings?user_id=' + (window.getCurrentUser?.()?.id || 39),
        ];

        for (let i = 0; i < apis.length; i += 2) {
            try {
                const t0 = performance.now();
                const res = await fetch(apis[i + 1]);
                const t1 = performance.now();
                const text = await res.text();
                const len = text.length;
                let sample = '';
                try { sample = JSON.stringify(JSON.parse(text)).slice(0, 100); }
                catch (_e) { sample = text.slice(0, 100).replace(/\s+/g, ' '); }

                if (res.ok) {
                    console.log('  ✅ ' + apis[i] + ' → ' + apis[i + 1] + '  状态:' + res.status + '  耗时:' + (t1 - t0).toFixed(0) + 'ms  长度:' + len + '  样本:' + sample);
                } else {
                    console.log('  ❌ ' + apis[i] + ' → ' + apis[i + 1] + '  HTTP ' + res.status + '  样本:' + sample);
                }
            } catch (e) {
                console.log('  ❌ ' + apis[i] + ' → ' + apis[i + 1] + '  fetch 异常: ' + (e.message || String(e)));
            }
        }

        // 3. 检查 DOM 元素
        console.log('\n%c[3/4] 检查 DOM 元素:', 'color:#667eea;font-weight:bold');
        const doms = ['attendance-list', 'records-list', 'monthly-total-hours', 'config-list'];
        for (const id of doms) {
            const el = document.getElementById(id);
            console.log('  ' + (el ? '✅' : '⚠️') + ' ' + id + (el ? ' 存在' : ' 未找到'));
        }

        // 4. 检查渲染结果
        console.log('\n%c[4/4] 检查渲染结果:', 'color:#667eea;font-weight:bold');
        const attList = document.getElementById('attendance-list');
        if (attList) {
            console.log('  考勤列表 HTML 长度: ' + attList.innerHTML.length);
            if (attList.innerHTML.length > 100) console.log('  ✅ 考勤列表有内容');
            else console.log('  ⚠️ 考勤列表内容较少，请检查 API');
        }

        console.log('\n%c========== 诊断完成 ==========', 'color:#667eea;font-weight:bold;font-size:14px');
        const errCount = errors.length;
        if (errCount === 0) {
            console.log('%c✅ 所有检查通过！系统运行正常。', 'color:#4caf50;font-weight:bold');
        } else {
            console.log('%c⚠️ 发现 ' + errCount + ' 个问题，请检查上方错误信息。', 'color:#ff9800;font-weight:bold');
        }
    }

    // ====== 暴露到全局 ======
    window.Boot = {
        initAll: () => initAll(true),
        reinitAll: () => { errors.length = 0; initAll(true); },
        initTab: initTab,
        diagnose: runDiagnose,
        close: () => {
            const bar = document.getElementById('boot-diagnostic-bar');
            if (bar) bar.remove();
        },
        showBar: showDiagnosticBar,
    };

    // ====== 页面加载后自动执行 ======
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => initAll(true), 100);
            // 诊断浮窗已默认关闭，不再自动显示
        });
    } else {
        initAll(true);
        // 诊断浮窗已默认关闭，不再自动显示
    }

    console.log('%c🚀 考勤系统启动脚本已加载 (boot.js)', 'color:#667eea;font-weight:bold');
})();
