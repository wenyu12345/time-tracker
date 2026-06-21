/* 族谱树状·员工师带徒电子档案系统 - 前端逻辑（独立页面专用） */
(function () {
    'use strict';

    // 仅在有 Tab 按钮的页面运行
    if (document.querySelectorAll('.tab-btn[data-tab]').length === 0) return;

    const API_BASE = '/api/mentorship';
    let currentLedgerFilter = 'all';

    // ========== 工具函数 ==========
    function $(id) { return document.getElementById(id); }

    function safeRemoveClass(selector, cls) {
        document.querySelectorAll(selector).forEach(el => el.classList.remove(cls));
    }

    function showToast(message, type) {
        const tip = document.createElement('div');
        const color = type === 'error' ? '#f44336' : type === 'warn' ? '#ff9800' : '#4caf50';
        Object.assign(tip.style, {
            position: 'fixed', top: '1rem', left: '50%', transform: 'translateX(-50%)',
            background: color, color: '#fff', padding: '0.75rem 1.5rem', borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.2)', zIndex: '9999', fontSize: '0.95rem'
        });
        tip.textContent = message;
        document.body.appendChild(tip);
        setTimeout(() => tip.remove(), 2500);
    }

    // ========== Tab 切换 & 事件委托 ==========
    document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
        btn.addEventListener('click', function () {
            const tab = this.getAttribute('data-tab');
            safeRemoveClass('.tab-btn', 'active');
            this.classList.add('active');
            safeRemoveClass('.tab-content', 'active');
            const target = document.getElementById('tab-' + tab);
            if (target) target.classList.add('active');

            // 进入对应 Tab 时重新加载数据
            if (tab === 'rules') loadRules();
            else if (tab === 'tree') loadTree();
            else if (tab === 'ledger') loadLedger();
            else if (tab === 'stats') loadStats();
            else if (tab === 'create') loadUserOptions();
        });
    });

    // 委托：台账行的按钮
    document.addEventListener('click', function (e) {
        const target = e.target;
        if (!(target instanceof HTMLElement)) return;

        if (target.matches('[data-action="edit"]')) {
            const id = parseInt(target.getAttribute('data-id'));
            if (id) openEditModal(id);
        } else if (target.matches('[data-action="graduate"]')) {
            const id = parseInt(target.getAttribute('data-id'));
            if (id) markGraduated(id);
        } else if (target.matches('[data-action="delay"]')) {
            const id = parseInt(target.getAttribute('data-id'));
            if (id) markDelayed(id);
        } else if (target.matches('[data-action="delete"]')) {
            const id = parseInt(target.getAttribute('data-id'));
            if (id) deleteRelation(id);
        }
    });

    // ========== 规则说明 ==========
    async function loadRules() {
        const container = $('rules-container');
        if (!container) return;
        try {
            const resp = await fetch(API_BASE + '/rules');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            container.innerHTML = data.rules.map((r, i) => `
                <div class="rule-card">
                    <div class="rule-num">${String(i + 1).padStart(2, '0')}</div>
                    <div class="rule-text">${r}</div>
                </div>`).join('');

            const fieldBody = $('field-table-body');
            if (fieldBody) {
                const fieldDesc = [
                    ['姓名/工号', '员工姓名与工号（从系统用户中选择）'],
                    ['师承来源（师父）', '该员工的直接指导者是谁'],
                    ['拜师开始时间', '建立师徒关系的日期'],
                    ['学习/传授技能', '岗位技能、设备技能、业务技能'],
                    ['预设出师周期', '默认 30 天，可手动调整'],
                    ['当前状态', '学习中 / 已出师 / 延期培养'],
                    ['收徒权限', '是否具备带徒资格（出师即自动开通）'],
                    ['门下徒弟清单', '该员工作为师父带出的所有传承人']
                ];
                fieldBody.innerHTML = fieldDesc.map((f, i) =>
                    `<tr><td>${i + 1}</td><td><strong>${f[0]}</strong></td><td>${f[1]}</td></tr>`
                ).join('');
            }
        } catch (err) {
            container.innerHTML = '<div style="color:#f44336;padding:1rem;text-align:center">加载失败：' + err.message + '</div>';
            console.error('[规则说明]', err);
        }
    }

    // ========== 族谱树 ==========
    async function loadTree() {
        const container = $('tree-container');
        const loading = $('tree-loading');
        const empty = $('tree-empty');
        if (!container) return;
        loading.style.display = 'block';
        container.innerHTML = '';
        empty.style.display = 'none';

        try {
            const resp = await fetch(API_BASE + '/tree');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            loading.style.display = 'none';
            if (!data.tree || data.tree.length === 0) {
                empty.style.display = 'block';
                return;
            }
            data.tree.forEach(rootNode => {
                const rootEl = document.createElement('div');
                rootEl.className = 'tree-root';
                rootEl.appendChild(renderNode(rootNode));
                container.appendChild(rootEl);
            });
        } catch (err) {
            loading.innerHTML = '<span style="color:#f44336">加载失败：' + err.message + '</span>';
            console.error('[族谱树]', err);
        }
    }

    function renderNode(node) {
        const wrap = document.createElement('div');
        wrap.className = 'tree-node level-' + Math.min(node.level, 7);

        const info = document.createElement('div');
        info.className = 'tree-node-info';

        const name = document.createElement('span');
        name.className = 'tree-name';
        name.textContent = (node.employee_id ? `[${node.employee_id}] ` : '') + node.name;
        info.appendChild(name);

        const badge = document.createElement('span');
        badge.className = 'tree-badge';
        if (node.level === 0) {
            badge.classList.add('root');
            badge.textContent = '初代宗师';
        } else if (node.display_status === '已出师') {
            badge.classList.add('graduated');
            badge.textContent = '已出师';
        } else if (node.display_status === '延期培养') {
            badge.classList.add('delayed');
            badge.textContent = '延期培养';
        } else {
            badge.classList.add('learning');
            badge.textContent = '学习中';
        }
        info.appendChild(badge);

        if (node.can_mentor) {
            const m = document.createElement('span');
            m.className = 'tree-badge mentor';
            m.textContent = '✨ 可收徒';
            info.appendChild(m);
        }
        if (node.mentor_name) {
            const d = document.createElement('span');
            d.className = 'tree-meta';
            d.textContent = '师承：' + node.mentor_name;
            info.appendChild(d);
        }
        if (node.start_date) {
            const d = document.createElement('span');
            d.className = 'tree-meta';
            d.textContent = '拜师日：' + node.start_date;
            info.appendChild(d);
        }
        if (node.expected_end_date) {
            const d = document.createElement('span');
            d.className = 'tree-meta';
            d.textContent = '预期结业：' + node.expected_end_date;
            info.appendChild(d);
        }
        if (node.skills) {
            const d = document.createElement('span');
            d.className = 'tree-meta';
            d.textContent = '技能：' + node.skills;
            info.appendChild(d);
        }
        if (typeof node.days_passed === 'number') {
            const d = document.createElement('span');
            d.className = 'tree-meta';
            d.textContent = '已学 ' + node.days_passed + ' 天 / 剩 ' + node.days_left + ' 天';
            info.appendChild(d);
        }

        wrap.appendChild(info);

        if (node.children && node.children.length > 0) {
            const toggle = document.createElement('span');
            toggle.className = 'tree-toggle';
            toggle.textContent = '▼ 门下 ' + node.children.length + ' 名传承人';
            wrap.appendChild(toggle);

            const childrenWrap = document.createElement('div');
            childrenWrap.className = 'tree-children';
            node.children.forEach(child => childrenWrap.appendChild(renderNode(child)));
            wrap.appendChild(childrenWrap);

            toggle.addEventListener('click', function () {
                if (childrenWrap.style.display === 'none') {
                    childrenWrap.style.display = 'block';
                    toggle.textContent = '▼ 门下 ' + node.children.length + ' 名传承人';
                } else {
                    childrenWrap.style.display = 'none';
                    toggle.textContent = '▶ 展开 ' + node.children.length + ' 名传承人';
                }
            });
        }
        return wrap;
    }

    // ========== 档案台账 ==========
    async function loadLedger() {
        const tbody = $('ledger-body');
        const loading = $('ledger-loading');
        const empty = $('ledger-empty');
        if (!tbody) return;
        tbody.innerHTML = '';
        loading.style.display = 'block';
        empty.style.display = 'none';

        try {
            const url = currentLedgerFilter === 'all'
                ? API_BASE + '/list'
                : API_BASE + '/list?status=' + currentLedgerFilter;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            loading.style.display = 'none';
            if (!data.relations || data.relations.length === 0) {
                empty.style.display = 'block';
                return;
            }
            data.relations.forEach(rel => {
                const tr = document.createElement('tr');
                if (rel.display_status === '已出师') tr.classList.add('status-graduated');
                else if (rel.display_status === '延期培养') tr.classList.add('status-delayed');

                const apprenticeName = rel.apprentice_name || ('用户' + rel.apprentice_id);
                const mentorName = rel.mentor_name || ('用户' + rel.mentor_id);

                const statusBadge = rel.display_status === '已出师'
                    ? '<span class="tree-badge graduated">已出师</span>'
                    : rel.display_status === '延期培养'
                        ? '<span class="tree-badge delayed">延期培养</span>'
                        : '<span class="tree-badge learning">学习中</span>';

                const qualifiedBadge = rel.apprentice_can_mentor
                    ? '<span class="tree-badge mentor">已开通收徒</span>'
                    : '<span class="tree-badge" style="background:#bdbdbd">未开通</span>';

                const startDate = (rel.start_date || '').substring(0, 10);
                const daysPassed = typeof rel.days_passed === 'number' ? rel.days_passed : '-';
                const daysLeft = rel.days_left || 0;

                tr.innerHTML = `
                    <td><strong>${escapeHtml(apprenticeName)}</strong></td>
                    <td>${escapeHtml(mentorName)}</td>
                    <td>${startDate}</td>
                    <td>${rel.planned_duration_days || 30} 天</td>
                    <td>${rel.expected_end_date || '-'}</td>
                    <td>${daysPassed} / 剩 ${daysLeft}</td>
                    <td>${escapeHtml(rel.skills || '-')}</td>
                    <td>${statusBadge}</td>
                    <td>${qualifiedBadge}</td>
                    <td>
                        <button class="btn small primary" data-action="edit" data-id="${rel.id}">编辑</button>
                        <button class="btn small success" data-action="graduate" data-id="${rel.id}">✓ 出师</button>
                        <button class="btn small warning" data-action="delay" data-id="${rel.id}">⏳ 延期</button>
                        <button class="btn small danger" data-action="delete" data-id="${rel.id}">🗑 删除</button>
                    </td>`;
                tbody.appendChild(tr);
            });
        } catch (err) {
            loading.innerHTML = '<span style="color:#f44336">加载失败：' + err.message + '</span>';
            console.error('[档案台账]', err);
        }
    }

    function escapeHtml(s) {
        if (s === undefined || s === null) return '';
        return String(s).replace(/[&<>"']/g, ch => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        })[ch]);
    }

    const ledgerFilterEl = $('ledger-filter');
    if (ledgerFilterEl) {
        ledgerFilterEl.addEventListener('change', function () {
            currentLedgerFilter = this.value;
            loadLedger();
        });
    }
    const refLedgerBtn = $('refresh-ledger-btn');
    if (refLedgerBtn) refLedgerBtn.addEventListener('click', loadLedger);
    const refTreeBtn = $('refresh-tree-btn');
    if (refTreeBtn) refTreeBtn.addEventListener('click', loadTree);

    // ========== 统计 ==========
    async function loadStats() {
        const loading = $('stats-loading');
        const grid = $('stats-grid');
        if (!grid) return;
        loading.style.display = 'block';
        grid.innerHTML = '';

        try {
            const resp = await fetch(API_BASE + '/statistics');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            loading.style.display = 'none';
            const stats = [
                ['total', '总师徒关系数', data.total],
                ['learning', '学习中', data.learning],
                ['graduated', '已出师', data.graduated],
                ['delayed', '延期培养', data.delayed],
                ['mentors', '在带师父数', data.total_mentors],
                ['apprentices', '现有徒弟数', data.total_apprentices],
                ['generation', '最高传承代数', data.max_generation]
            ];
            stats.forEach(s => {
                const card = document.createElement('div');
                card.className = 'stat-card stat-' + s[0];
                card.innerHTML = `<div class="stat-value">${s[2]}</div><div class="stat-label">${s[1]}</div>`;
                grid.appendChild(card);
            });
        } catch (err) {
            loading.innerHTML = '<span style="color:#f44336">加载失败：' + err.message + '</span>';
            console.error('[统计]', err);
        }
    }

    // ========== 新建师徒 ==========
    async function loadUserOptions() {
        const mentorSel = $('new-mentor');
        const apprenticeSel = $('new-apprentice');
        if (!mentorSel || !apprenticeSel) return;

        // 先显示加载占位
        mentorSel.innerHTML = '<option value="">用户列表加载中…</option>';
        apprenticeSel.innerHTML = '<option value="">用户列表加载中…</option>';

        try {
            const resp = await fetch(API_BASE + '/users');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            const users = data.users || [];

            mentorSel.innerHTML = '';
            apprenticeSel.innerHTML = '';

            const p1 = document.createElement('option');
            p1.value = '';
            p1.textContent = '请选择师父';
            mentorSel.appendChild(p1);

            const p2 = document.createElement('option');
            p2.value = '';
            p2.textContent = '请选择徒弟';
            apprenticeSel.appendChild(p2);

            users.forEach(u => {
                const label = u.employee_id ? (u.username + ' (' + u.employee_id + ')') : u.username;
                const opt1 = document.createElement('option');
                opt1.value = u.id;
                opt1.textContent = label + (u.can_mentor ? ' ✨（可收徒）' : '');
                mentorSel.appendChild(opt1);

                const opt2 = document.createElement('option');
                opt2.value = u.id;
                opt2.textContent = label;
                apprenticeSel.appendChild(opt2);
            });

            const dateEl = $('new-start-date');
            if (dateEl && !dateEl.value) {
                dateEl.value = new Date().toISOString().substring(0, 10);
            }
        } catch (err) {
            mentorSel.innerHTML = '<option value="">加载失败：' + err.message + '</option>';
            apprenticeSel.innerHTML = '<option value="">加载失败</option>';
            console.error('[新建师徒]', err);
        }
    }

    const submitBtn = $('submit-new-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', async function () {
            const mentor_id = parseInt($('new-mentor').value);
            const apprentice_id = parseInt($('new-apprentice').value);
            const start_date = $('new-start-date').value;
            const planned_duration_days = parseInt($('new-duration').value);
            const skills = $('new-skills').value.trim();
            const notes = $('new-notes').value.trim();

            if (!mentor_id || !apprentice_id) {
                showToast('请选择师父和徒弟', 'warn');
                return;
            }
            if (mentor_id === apprentice_id) {
                showToast('师父与徒弟不能是同一人', 'warn');
                return;
            }
            try {
                submitBtn.disabled = true;
                const oldText = submitBtn.textContent;
                submitBtn.textContent = '保存中…';
                const resp = await fetch(API_BASE + '/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mentor_id, apprentice_id, start_date, planned_duration_days, skills, notes })
                });
                const data = await resp.json();
                submitBtn.disabled = false;
                submitBtn.textContent = oldText;
                if (resp.ok) {
                    showToast('✅ 师徒关系创建成功！' + (data.message || ''), 'success');
                    $('new-skills').value = '';
                    $('new-notes').value = '';
                } else {
                    showToast('创建失败：' + (data.error || '未知错误'), 'error');
                }
            } catch (e) {
                submitBtn.disabled = false;
                submitBtn.textContent = '✅ 创建师徒关系';
                showToast('创建失败：' + e.message, 'error');
            }
        });
    }

    // ========== 编辑 / 操作 ==========
    let currentEditRelationId = null;

    async function openEditModal(relationId) {
        currentEditRelationId = relationId;
        try {
            const resp = await fetch(API_BASE + '/list');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            const relation = data.relations.find(r => r.id === relationId);
            if (!relation) {
                showToast('找不到该记录', 'warn');
                return;
            }
            $('edit-start-date').value = (relation.start_date || '').substring(0, 10);
            $('edit-duration').value = relation.planned_duration_days || 30;
            $('edit-skills').value = relation.skills || '';
            $('edit-notes').value = relation.notes || '';
            if (relation.mentorship_status === 'delayed') {
                $('edit-status').value = 'delayed';
            } else if (relation.display_status === '已出师') {
                $('edit-status').value = 'graduated';
            } else {
                $('edit-status').value = 'learning';
            }
            $('edit-modal').classList.add('active');
        } catch (e) {
            showToast('加载数据失败：' + e.message, 'error');
        }
    }

    function closeEditModal() {
        $('edit-modal').classList.remove('active');
        currentEditRelationId = null;
    }

    document.addEventListener('click', function (e) {
        const target = e.target;
        if (!(target instanceof HTMLElement)) return;
        // 点击模态框背景关闭
        if (target.id === 'edit-modal') {
            closeEditModal();
        }
        // 点击模态框关闭按钮
        if (target.matches('[data-modal-close]')) {
            closeEditModal();
        }
    });

    const editSaveBtn = $('edit-save-btn');
    if (editSaveBtn) {
        editSaveBtn.addEventListener('click', async function () {
            if (!currentEditRelationId) return;
            try {
                editSaveBtn.disabled = true;
                editSaveBtn.textContent = '保存中…';
                const resp = await fetch(API_BASE + '/' + currentEditRelationId, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        start_date: $('edit-start-date').value,
                        planned_duration_days: parseInt($('edit-duration').value),
                        skills: $('edit-skills').value,
                        mentorship_status: $('edit-status').value,
                        notes: $('edit-notes').value
                    })
                });
                editSaveBtn.disabled = false;
                editSaveBtn.textContent = '保存修改';
                if (resp.ok) {
                    showToast('✅ 保存成功', 'success');
                    closeEditModal();
                    loadLedger();
                } else {
                    const data = await resp.json();
                    showToast('保存失败：' + (data.error || '未知错误'), 'error');
                }
            } catch (e) {
                editSaveBtn.disabled = false;
                editSaveBtn.textContent = '保存修改';
                showToast('保存失败：' + e.message, 'error');
            }
        });
    }

    const cancelBtn = $('edit-cancel-btn');
    if (cancelBtn) cancelBtn.addEventListener('click', closeEditModal);

    async function markGraduated(relationId) {
        if (!confirm('确认标记为「已出师」？\n将为该员工开通收徒权限。')) return;
        try {
            const resp = await fetch(API_BASE + '/graduate/' + relationId, { method: 'POST' });
            if (resp.ok) {
                showToast('✅ 已标记为已出师，收徒权限已开通', 'success');
                loadLedger();
            } else {
                const data = await resp.json();
                showToast('操作失败：' + (data.error || '未知错误'), 'error');
            }
        } catch (e) {
            showToast('操作失败：' + e.message, 'error');
        }
    }

    async function markDelayed(relationId) {
        if (!confirm('确认标记为「延期培养」？')) return;
        try {
            const resp = await fetch(API_BASE + '/delay/' + relationId, { method: 'POST' });
            if (resp.ok) {
                showToast('✅ 已标记为延期培养', 'success');
                loadLedger();
            } else {
                const data = await resp.json();
                showToast('操作失败：' + (data.error || '未知错误'), 'error');
            }
        } catch (e) {
            showToast('操作失败：' + e.message, 'error');
        }
    }

    async function deleteRelation(relationId) {
        if (!confirm('确认删除该师徒关系？此操作不可恢复。')) return;
        try {
            const resp = await fetch(API_BASE + '/' + relationId, { method: 'DELETE' });
            if (resp.ok) {
                showToast('✅ 已删除', 'success');
                loadLedger();
            } else {
                const data = await resp.json();
                showToast('删除失败：' + (data.error || '未知错误'), 'error');
            }
        } catch (e) {
            showToast('删除失败：' + e.message, 'error');
        }
    }

    // ========== 初始化：页面打开时加载规则说明 ==========
    loadRules();
})();
