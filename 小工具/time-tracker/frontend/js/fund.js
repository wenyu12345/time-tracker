// 基金持仓模块
const FundModule = (function() {
    const API_BASE = '/api/funds';
    const USER_KEY = 'current_user'; // 统一使用这个key
    let currentUser = null;
    let holdings = [];
    let activeHoldingId = null;
    let valueChart = null;
    let profitChart = null;
    let isInitialized = false;       // 防止重复初始化
    let isLoading = false;           // 防止并发加载

    // 初始化
    function init() {
        if (isLoading) {
            console.log('基金模块正在加载中，跳过重复调用');
            return;
        }
        console.log('基金模块初始化');
        // 获取当前登录用户
        const userStr = localStorage.getItem(USER_KEY);
        if (userStr) {
            currentUser = JSON.parse(userStr);
            isLoading = true;
            loadFundData().finally(function() { isLoading = false; });
        } else {
            console.log('未登录');
            const summaryEl = document.getElementById('fundSummary');
            const tabsEl = document.getElementById('fundTabs');
            const detailEl = document.getElementById('fundDetail');
            if (summaryEl) summaryEl.innerHTML = '<div class="empty-state" style="padding: 20px;"><p>请先登录</p></div>';
            if (tabsEl) tabsEl.innerHTML = '';
            if (detailEl) detailEl.innerHTML = '<div class="empty-state"><p>请先登录</p></div>';
        }

        // 绑定事件（只绑定一次）
        if (!isInitialized) {
            bindEvents();
            isInitialized = true;
        }
    }

    // 强制重加载（忽略 isInitialized 标志）
    function reload() {
        const userStr = localStorage.getItem(USER_KEY);
        if (userStr) {
            currentUser = JSON.parse(userStr);
            if (!isLoading) {
                isLoading = true;
                loadFundData().finally(function() { isLoading = false; });
            }
        }
    }

    // 延迟渲染：切换到基金选项卡时调用，若历史数据已加载则立即渲染
    // 没有历史数据时重新调用 loadFundData 拉一次
    function renderLatest() {
        if (!document.getElementById('valueChart') || !document.getElementById('profitCanvas')) {
            // Canvas 还没激活（tab 没显示），立即退出
            return;
        }
        // 若已有历史数据缓存，直接 render
        if (window.__fund_daily_data__ && window.__fund_daily_data__.daily_data && window.__fund_daily_data__.daily_data.length > 0) {
            renderCharts(window.__fund_daily_data__.daily_data);
            return;
        }
        // 否则重新拉一次
        if (!isLoading && currentUser) {
            isLoading = true;
            loadFundData().finally(function() { isLoading = false; });
        }
    }

    // 绑定事件（只绑定一次，避免重复监听）
    function bindEvents() {
        const addBtn = document.getElementById('addFundBtn');
        const saveBtn = document.getElementById('saveFundBtn');
        const closeBtn = document.getElementById('closeFundModal');
        const modal = document.getElementById('fundModal');
        const refreshBtn = document.getElementById('refreshFundPriceBtn');

        if (addBtn && !addBtn._bound) { addBtn.addEventListener('click', openAddModal); addBtn._bound = true; }
        if (saveBtn && !saveBtn._bound) { saveBtn.addEventListener('click', saveFund); saveBtn._bound = true; }
        if (closeBtn && !closeBtn._bound) { closeBtn.addEventListener('click', closeModal); closeBtn._bound = true; }
        if (modal && !modal._bound) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) closeModal();
            });
            modal._bound = true;
        }
        if (refreshBtn && !refreshBtn._bound) { refreshBtn.addEventListener('click', refreshAllPrices); refreshBtn._bound = true; }
    }

    // 加载基金数据
    async function loadFundData() {
        if (!currentUser) return;
        
        console.log('加载基金数据，用户ID:', currentUser.id);
        
        try {
            // 先加载持仓列表（最重要的）
            const holdingsRes = await fetch(`${API_BASE}/holdings?user_id=${currentUser.id}`);
            const holdingsData = await holdingsRes.json();
            holdings = holdingsData.holdings || [];
            console.log('持仓数据:', holdings);
            
            // 加载收益汇总
            let summaryData = {
                total_invest: 0,
                total_value: 0,
                total_profit: 0,
                total_profit_rate: 0
            };
            try {
                const summaryRes = await fetch(`${API_BASE}/summary?user_id=${currentUser.id}`);
                if (summaryRes.ok) {
                    summaryData = await summaryRes.json();
                    console.log('汇总数据:', summaryData);
                }
            } catch (summaryError) {
                console.warn('加载汇总数据失败，使用默认值:', summaryError);
            }
            
            // 加载历史收益数据（可选，如果失败不影响）
            let dailyData = { daily_data: [] };
            try {
                const dailyRes = await fetch(`${API_BASE}/daily-summary?user_id=${currentUser.id}&days=30`);
                if (dailyRes.ok) {
                    dailyData = await dailyRes.json();
                    console.log('历史数据:', dailyData);
                }
            } catch (dailyError) {
                console.warn('加载历史数据失败，不显示图表:', dailyError);
            }
            
            // 渲染
            renderSummary(summaryData);
            renderTabs(holdings);
            
            // 只有在有历史数据时才渲染图表 — 关键：只有 Canvas 真的在 DOM 里才去画
            if (dailyData.daily_data && dailyData.daily_data.length > 0) {
                if (document.getElementById('valueChart') && document.getElementById('profitCanvas')) {
                    renderCharts(dailyData.daily_data);
                } else {
                    console.log('[基金] 基金图表画布未激活，缓存数据等待用户进入基金选项卡后再渲染');
                }
            } else {
                // 没有历史数据，清空图表区域
                clearCharts();
            }
            
            // 如果有持仓，默认选中第一个
            if (holdings.length > 0 && !activeHoldingId) {
                selectHolding(holdings[0].id);
            } else if (holdings.length === 0) {
                renderEmptyDetail();
            }
        } catch (error) {
            console.error('加载基金数据失败:', error);
            const summaryEl = document.getElementById('fundSummary');
            if (summaryEl) {
                summaryEl.innerHTML = '<div class="empty-state" style="padding: 20px;"><p>加载数据失败，请刷新页面重试</p></div>';
            }
        }
    }

    // 清空图表（只在 Canvas 和 Chart 实例真的存在时才操作）
    function clearCharts() {
        try {
            if (valueChart && typeof valueChart.destroy === 'function') {
                valueChart.destroy();
                valueChart = null;
            }
        } catch (e) { /* 忽略 */ }
        try {
            if (profitChart && typeof profitChart.destroy === 'function') {
                profitChart.destroy();
                profitChart = null;
            }
        } catch (e) { /* 忽略 */ }

        try {
            const vC = document.getElementById('valueChart');
            const pC = document.getElementById('profitChart');
            if (vC && vC.getContext) {
                const ctx = vC.getContext('2d');
                if (ctx) { ctx.clearRect(0, 0, vC.width || 1, vC.height || 1); }
                vC.width = vC.width; // 重置
            }
            if (pC && pC.getContext) {
                const ctx = pC.getContext('2d');
                if (ctx) { ctx.clearRect(0, 0, pC.width || 1, pC.height || 1); }
                pC.width = pC.width;
            }
        } catch (e) { /* 忽略 */ }
    }

    // 渲染收益汇总
    function renderSummary(summary) {
        const summaryEl = document.getElementById('fundSummary');
        if (!summaryEl) return;

        const profitClass = summary.total_profit >= 0 ? 'profit' : 'loss';

        summaryEl.innerHTML = `
            <div class="summary-card">
                <div class="summary-item">
                    <span class="summary-label">总投入</span>
                    <span class="summary-value">¥${(summary.total_invest || 0).toFixed(2)}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">当前市值</span>
                    <span class="summary-value">¥${(summary.total_value || 0).toFixed(2)}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">总收益</span>
                    <span class="summary-value ${profitClass}">¥${(summary.total_profit || 0).toFixed(2)}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">收益率</span>
                    <span class="summary-value ${profitClass}">${(summary.total_profit_rate || 0).toFixed(2)}%</span>
                </div>
            </div>
            <div style="margin-top: 10px; display: flex; gap: 10px;">
                <button class="btn primary" id="refreshAndRecordBtn" style="flex: 1;">
                    刷新价格并记录
                </button>
                <button class="btn secondary" id="recordReturnsBtn" style="flex: 1;">
                    记录今日收益
                </button>
            </div>
        `;

        const refreshRecordBtn = document.getElementById('refreshAndRecordBtn');
        const recordReturnsBtn = document.getElementById('recordReturnsBtn');
        if (refreshRecordBtn) refreshRecordBtn.addEventListener('click', refreshAndRecord);
        if (recordReturnsBtn) recordReturnsBtn.addEventListener('click', recordReturns);
    }

    // 格式化日期 - 只取月份-日期，如 2026-05-27 -> 05-27
    function formatDateForChart(dateStr) {
        if (!dateStr) return '';
        return String(dateStr).substring(5);
    }

    // 渲染图表 - Chart.js v3
    function renderCharts(dailyData) {
        console.log('[图表渲染开始] 数据条数:', dailyData ? dailyData.length : 0);

        const valueCanvas = document.getElementById('valueChart');
        const profitCanvas = document.getElementById('profitCanvas');

        if (!valueCanvas || !profitCanvas) {
            if (dailyData && dailyData.length > 0) {
                console.warn('Canvas 元素未就绪，使用数据表格显示（请切换到基金选项卡查看）');
                renderChartsAsText(dailyData);
            }
            return;
        }

        if (typeof Chart === 'undefined') {
            console.warn('Chart.js 未加载，使用降级显示');
            if (dailyData && dailyData.length > 0) {
                const labels = dailyData.map(function (d) { return formatDateForChart(d.date); });
                const values = dailyData.map(function (d) { return Number(d.total_value) || 0; });
                const profits = dailyData.map(function (d) { return Number(d.total_profit) || 0; });
                renderChartFallback(valueCanvas, '总市值', labels, values);
                renderChartFallback(profitCanvas, '当日收益', labels, profits);
            } else {
                renderEmptyCharts();
            }
            return;
        }

        clearCharts();

        if (!dailyData || dailyData.length === 0) {
            renderEmptyCharts();
            return;
        }

        try {
            const labels = dailyData.map(function (d) { return formatDateForChart(d.date); });
            const values = dailyData.map(function (d) { return Number(d.total_value) || 0; });
            const profits = dailyData.map(function (d) { return Number(d.total_profit) || 0; });

            console.log('图表标签:', labels);
            console.log('市值数据:', values);
            console.log('收益数据:', profits);

            // 市值图表
            const vCtx = valueCanvas.getContext('2d');
            valueChart = new Chart(vCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '总市值',
                        data: values,
                        borderColor: 'rgb(52, 152, 219)',
                        backgroundColor: 'rgba(52, 152, 219, 0.15)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });

            // 收益图表
            const pCtx = profitCanvas.getContext('2d');
            profitChart = new Chart(pCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '当日收益',
                        data: profits,
                        borderColor: 'rgb(40, 167, 69)',
                        backgroundColor: 'rgba(40, 167, 69, 0.15)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });

            console.log('✅ 图表渲染成功');

        } catch (error) {
            console.error('❌ 渲染图表失败:', error);
            renderEmptyCharts();
        }
    }

    // Canvas 元素不可用时的降级显示（只显示最近 10 条数据的文本摘要）
    function renderChartsAsText(dailyData) {
        // 只在基金 tab 容器存在时才尝试写入
        const container = document.getElementById('fundSummary');
        if (!container) return;
        if (!dailyData || dailyData.length === 0) return;

        const lastN = dailyData.slice(-10);
        let html = '<div style="padding:10px 14px;background:#f0f4f8;border-radius:6px;margin-top:10px;font-size:12px;color:#444">';
        html += '<div style="font-weight:bold;margin-bottom:6px">📊 最近收益（Chart.js 已降级）</div>';
        for (let i = 0; i < lastN.length; i++) {
            const d = lastN[i];
            const val = Number(d.total_value) || 0;
            const profit = Number(d.total_profit) || 0;
            const color = profit >= 0 ? 'color:#27ae60' : 'color:#e74c3c';
            html += `<div style="display:flex;justify-content:space-between;padding:2px 0"><span>${formatDateForChart(d.date)}</span><span>市值 ¥${val.toFixed(2)}</span><span style="${color}">收益 ${profit >= 0 ? '+' : ''}${profit.toFixed(2)}</span></div>`;
        }
        html += '</div>';
        // 追加到 summary 容器底部（不覆盖原汇总）
        container.insertAdjacentHTML && container.insertAdjacentHTML('beforeend', html);
    }

    // 空图表状态显示
    function renderEmptyCharts() {
        const vC = document.getElementById('valueChart');
        const pC = document.getElementById('profitChart');

        function drawEmpty(canvasEl, text) {
            if (!canvasEl) return;
            const ctx = canvasEl.getContext('2d');
            const w = canvasEl.width = canvasEl.offsetWidth || 300;
            const h = canvasEl.height = canvasEl.offsetHeight || 150;
            ctx.clearRect(0, 0, w, h);
            ctx.fillStyle = '#999';
            ctx.font = '14px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(text, w / 2, h / 2);
        }

        drawEmpty(vC, '暂无历史数据');
        drawEmpty(pC, '暂无历史数据');
    }

    // Chart.js 不可用时的降级显示：用简单的条形图和数据表格
    function renderChartFallback(canvasEl, title, labels, values) {
        if (!canvasEl) return;
        try {
            const parent = canvasEl.parentNode;
            if (!parent) return;
            const container = document.createElement('div');
            container.style.cssText = 'padding:12px;background:#f8f9fa;border:1px solid #e0e0e0;border-radius:6px;font-size:12px;';
            const maxVal = Math.max.apply(null, values.map(Math.abs)) || 1;
            let rows = '';
            const lastN = Math.min(labels.length, 10);
            for (let i = labels.length - lastN; i < labels.length; i++) {
                const val = values[i] || 0;
                const pct = Math.abs(val) / maxVal * 100;
                const color = val >= 0 ? 'background:#3498db;' : 'background:#e74c3c;';
                rows += `<div style="display:flex;align-items:center;margin:4px 0;"><div style="width:50px;color:#666;">${labels[i]}</div><div style="flex:1;background:#eee;border-radius:3px;overflow:hidden;height:14px;"><div style="${color}width:${pct}%;height:100%;"></div></div><div style="width:90px;text-align:right;color:#333;">${val.toFixed(2)}</div></div>`;
            }
            container.innerHTML = `<div style="font-weight:bold;color:#555;margin-bottom:6px;">${title}（简化显示 - Chart.js 未加载）</div>${rows}`;
            canvasEl.style.display = 'none';
            if (parent.lastChild && parent.lastChild !== canvasEl && parent.lastChild.getAttribute && parent.lastChild.getAttribute('data-fallback') === '1') {
                parent.removeChild(parent.lastChild);
            }
            container.setAttribute('data-fallback', '1');
            parent.appendChild(container);
        } catch (e) {
            console.error('降级图表渲染失败:', e);
        }
    }

    // 渲染选项卡
    function renderTabs(holdingList) {
        const tabsEl = document.getElementById('fundTabs');
        if (!tabsEl) return;
        
        if (!holdingList || holdingList.length === 0) {
            tabsEl.innerHTML = '';
            return;
        }
        
        tabsEl.innerHTML = holdingList.map(holding => {
            const profit = holding.current_price ? 
                (holding.current_price - holding.purchase_price) * (holding.current_shares || holding.purchase_shares) : 0;
            const profitClass = profit >= 0 ? 'profit' : 'loss';
            const isActive = holding.id === activeHoldingId;
            
            return `
                <div class="fund-tab ${isActive ? 'active' : ''}" data-id="${holding.id}">
                    ${holding.fund_name}
                    <span class="profit-tag ${profitClass}">
                        ${profit >= 0 ? '+' : ''}${profit.toFixed(2)}
                    </span>
                </div>
            `;
        }).join('');
        
        // 绑定选项卡点击事件
        holdingList.forEach(holding => {
            const tab = tabsEl.querySelector(`[data-id="${holding.id}"]`);
            if (tab) {
                tab.addEventListener('click', () => selectHolding(holding.id));
            }
        });
    }

    // 选中持仓
    function selectHolding(id) {
        activeHoldingId = id;
        renderTabs(holdings);
        
        const holding = holdings.find(h => h.id === id);
        if (holding) {
            renderDetail(holding);
        }
    }

    // 格式化日期为中文格式
    function formatDateChinese(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        return `${year}年${month}月${day}日`;
    }

    // 渲染详情
    function renderDetail(holding) {
        const detailEl = document.getElementById('fundDetail');
        if (!detailEl) return;
        
        const profit = holding.current_price ? 
            (holding.current_price - holding.purchase_price) * (holding.current_shares || holding.purchase_shares) : 0;
        const profitRate = holding.current_price && holding.purchase_price > 0 ? 
            ((holding.current_price / holding.purchase_price) - 1) * 100 : 0;
        const currentValue = holding.current_price ? 
            holding.current_price * (holding.current_shares || holding.purchase_shares) : holding.purchase_amount;
        
        const profitClass = profit >= 0 ? 'profit' : 'loss';
        const statusClass = holding.holding_status === '持有' ? 'holding' : 'sold';
        
        detailEl.innerHTML = `
            <div class="fund-detail-header">
                <div>
                    <h3 class="fund-detail-title">${holding.fund_name}</h3>
                    <div class="fund-detail-code">${holding.fund_code || '暂无代码'}</div>
                </div>
                <span class="fund-detail-status ${statusClass}">${holding.holding_status}</span>
            </div>
            
            <div class="fund-detail-grid">
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">购买日期</span>
                    <span class="fund-detail-item-value">${formatDateChinese(holding.purchase_date)}</span>
                </div>
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">购买金额</span>
                    <span class="fund-detail-item-value">¥${holding.purchase_amount.toFixed(2)}</span>
                </div>
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">购买净值</span>
                    <span class="fund-detail-item-value">¥${holding.purchase_price.toFixed(4)}</span>
                </div>
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">持有份额</span>
                    <span class="fund-detail-item-value">${(holding.current_shares || holding.purchase_shares).toFixed(2)}</span>
                </div>
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">当前净值</span>
                    <span class="fund-detail-item-value">
                        ${holding.current_price ? '¥' + holding.current_price.toFixed(4) : '暂无'}
                    </span>
                </div>
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">当前市值</span>
                    <span class="fund-detail-item-value">¥${currentValue.toFixed(2)}</span>
                </div>
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">持有收益</span>
                    <span class="fund-detail-item-value ${profitClass}">
                        ${profit >= 0 ? '+' : ''}¥${profit.toFixed(2)}
                    </span>
                </div>
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">收益率</span>
                    <span class="fund-detail-item-value ${profitClass}">
                        ${profitRate >= 0 ? '+' : ''}${profitRate.toFixed(2)}%
                    </span>
                </div>
            </div>
            
            ${holding.notes ? `
                <div class="fund-detail-item">
                    <span class="fund-detail-item-label">备注</span>
                    <span class="fund-detail-item-value">${holding.notes}</span>
                </div>
            ` : ''}
            
            <div class="fund-detail-actions">
                <button class="btn primary" onclick="FundModule.refreshOnePrice(${holding.id})">
                    更新当前价格
                </button>
                <button class="btn secondary" onclick="FundModule.editFund(${holding.id})">
                    编辑持仓
                </button>
                <button class="btn danger" onclick="FundModule.deleteFund(${holding.id})">
                    删除持仓
                </button>
            </div>
        `;
    }

    // 渲染空详情
    function renderEmptyDetail() {
        const detailEl = document.getElementById('fundDetail');
        if (!detailEl) return;
        
        detailEl.innerHTML = `
            <div class="empty-state">
                <p>暂无基金持仓，点击"添加持仓"开始记录</p>
            </div>
        `;
    }

    // 打开添加模态框
    function openAddModal() {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        document.getElementById('fundModalTitle').textContent = '添加基金持仓';
        document.getElementById('holdingId').value = '';
        
        // 清空表单
        const fields = ['fundName', 'fundCode', 'purchaseDate', 'purchaseAmount', 'purchaseShares', 'purchasePrice', 'currentPrice', 'notes'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        const statusEl = document.getElementById('holdingStatus');
        if (statusEl) statusEl.value = '持有';
        
        // 默认购买日期为今天
        const today = new Date().toISOString().split('T')[0];
        const dateEl = document.getElementById('purchaseDate');
        if (dateEl) dateEl.value = today;
        
        document.getElementById('fundModal').classList.add('active');
    }

    // 编辑基金
    async function editFund(id) {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        try {
            const res = await fetch(`${API_BASE}/holdings?user_id=${currentUser.id}`);
            const data = await res.json();
            const holding = (data.holdings || []).find(h => h.id === id);
            
            if (holding) {
                document.getElementById('fundModalTitle').textContent = '编辑基金持仓';
                document.getElementById('holdingId').value = holding.id;
                document.getElementById('fundName').value = holding.fund_name;
                document.getElementById('fundCode').value = holding.fund_code || '';
                document.getElementById('purchaseDate').value = holding.purchase_date;
                document.getElementById('purchaseAmount').value = holding.purchase_amount;
                document.getElementById('purchaseShares').value = holding.purchase_shares;
                document.getElementById('purchasePrice').value = holding.purchase_price;
                document.getElementById('currentPrice').value = holding.current_price || '';
                document.getElementById('holdingStatus').value = holding.holding_status;
                document.getElementById('notes').value = holding.notes || '';
                
                document.getElementById('fundModal').classList.add('active');
            }
        } catch (error) {
            console.error(error);
            alert('加载基金数据失败');
        }
    }

    // 关闭模态框
    function closeModal() {
        document.getElementById('fundModal').classList.remove('active');
    }

    // 保存基金
    async function saveFund() {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        const id = document.getElementById('holdingId').value;
        const data = {
            user_id: currentUser.id,
            fund_name: document.getElementById('fundName').value.trim(),
            fund_code: document.getElementById('fundCode').value.trim(),
            purchase_date: document.getElementById('purchaseDate').value,
            purchase_amount: parseFloat(document.getElementById('purchaseAmount').value),
            purchase_shares: parseFloat(document.getElementById('purchaseShares').value),
            purchase_price: parseFloat(document.getElementById('purchasePrice').value),
            current_price: parseFloat(document.getElementById('currentPrice').value) || null,
            current_shares: parseFloat(document.getElementById('purchaseShares').value),
            holding_status: document.getElementById('holdingStatus').value,
            notes: document.getElementById('notes').value.trim()
        };
        
        // 验证必填字段
        if (!data.fund_name || !data.purchase_date || !data.purchase_amount || !data.purchase_shares || !data.purchase_price) {
            alert('请填写所有必填字段');
            return;
        }
        
        try {
            let url = `${API_BASE}/holdings`;
            let method = 'POST';
            
            if (id) {
                url += `/${id}`;
                method = 'PUT';
            }
            
            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                closeModal();
                loadFundData();
            } else {
                const errText = await res.text();
                alert('保存失败: ' + errText);
            }
        } catch (error) {
            console.error(error);
            alert('保存失败');
        }
    }

    // 刷新单个价格
    async function refreshOnePrice(id) {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        const holding = holdings.find(h => h.id === id);
        if (!holding || !holding.fund_code) {
            alert('该基金没有代码，无法自动刷新');
            return;
        }
        
        try {
            const res = await fetch(`${API_BASE}/info/${holding.fund_code}`);
            const data = await res.json();
            
            if (data.success && data.net_value > 0) {
                // 更新价格
                await fetch(`${API_BASE}/holdings/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        user_id: currentUser.id, 
                        current_price: data.net_value 
                    })
                });
                
                alert(`价格已更新：¥${data.net_value.toFixed(4)} (${data.estimated_change >= 0 ? '+' : ''}${data.estimated_change}%)`);
                loadFundData();
            } else {
                alert('获取价格失败，请稍后再试');
            }
        } catch (error) {
            console.error(error);
            alert('刷新失败');
        }
    }

    // 刷新所有价格
    async function refreshAllPrices() {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        if (!holdings || holdings.length === 0) {
            alert('暂无基金持仓');
            return;
        }
        
        const confirmRefresh = confirm('确定要刷新所有基金价格吗？');
        if (!confirmRefresh) return;
        
        try {
            const res = await fetch(`${API_BASE}/refresh-prices`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.id })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                alert(data.message);
                loadFundData();
            } else {
                alert('刷新失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error(error);
            alert('刷新失败');
        }
    }

    // 刷新价格并记录收益
    async function refreshAndRecord() {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        const confirmRefresh = confirm('确定要刷新基金价格并记录今日收益吗？');
        if (!confirmRefresh) return;
        
        try {
            const res = await fetch('/api/funds/refresh-and-record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.id })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                alert(data.message);
                loadFundData();
            } else {
                alert('操作失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error(error);
            alert('操作失败');
        }
    }

    // 记录今日收益
    async function recordReturns() {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        const confirmRecord = confirm('确定要记录今日基金收益吗？');
        if (!confirmRecord) return;
        
        try {
            const res = await fetch('/api/funds/record-returns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.id })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                alert(`${data.message}，共记录 ${data.recorded_count} 条`);
                loadFundData();
            } else {
                alert('操作失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error(error);
            alert('操作失败');
        }
    }

    // 删除基金
    async function deleteFund(id) {
        if (!currentUser) {
            alert('请先登录');
            return;
        }
        
        if (!confirm('确定要删除这条记录吗？')) return;
        
        try {
            await fetch(`${API_BASE}/holdings/${id}?user_id=${currentUser.id}`, {
                method: 'DELETE'
            });
            
            // 如果删除的是当前选中的，清空选中
            if (activeHoldingId === id) {
                activeHoldingId = null;
            }
            
            loadFundData();
        } catch (error) {
            console.error(error);
            alert('删除失败');
        }
    }

    // 暴露方法
    return {
        init: init,
        reload: reload,
        editFund: editFund,
        deleteFund: deleteFund,
        refreshOnePrice: refreshOnePrice
    };
})();

// 暴露到全局，方便onclick调用
window.FundModule = FundModule;
