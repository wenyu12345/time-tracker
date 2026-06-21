// 师带徒管理系统 - 前端逻辑
(function () {
    'use strict';

    const API_BASE = '/api/mentorship';

    // 全局错误捕获
    window.onerror = function(msg, url, line, col, error) {
        console.error('[JS ERROR]', msg, 'at line', line, ':', error);
        return false;
    };

    console.log('[INIT] 师带徒管理系统 JS 加载完成');

    // ============================================================
    // 页面访问方式检测（关键修复）
    // ============================================================
    function checkAccessMode() {
        if (typeof window === 'undefined') return;
        const proto = window.location.protocol;
        if (proto === 'file:' || proto === 'about:') {
            const msg = '❌ 请通过 Flask 服务器访问此页面！\n\n' +
                      '正确地址： http://127.0.0.1:5000/mentorship.html\n\n' +
                      '原因：当前是以 file:// 本地文件方式打开，JS 无法访问 API 接口。';
            alert(msg);
            console.error(msg);
            return false;
        }
        console.log('✅ [mentorship] 访问方式正常:', window.location.href);
        return true;
    }

    checkAccessMode();

    // ============================================================
    // 工具函数
    // ============================================================

    function showToast(message, type) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = 'toast ' + (type || 'info');
        toast.style.display = 'block';
        setTimeout(function () {
            toast.style.display = 'none';
        }, 2500);
    }

    function getShiftBadge(shift) {
        if (!shift) return '';
        const cls = shift === '白班' ? 'shift-day' : shift === '夜班' ? 'shift-night' : 'shift-long';
        return '<span class="node-badge ' + cls + '">' + shift + '</span>';
    }

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // ============================================================
    // API 调用
    // ============================================================

    async function fetchTree() {
        const resp = await fetch(API_BASE + '/tree');
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error('获取树状结构失败: HTTP ' + resp.status + ' - ' + text);
        }
        return await resp.json();
    }

    async function fetchLineage(userId) {
        const resp = await fetch(API_BASE + '/lineage/' + userId);
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error('获取传承链路失败: HTTP ' + resp.status + ' - ' + text);
        }
        return await resp.json();
    }

    async function searchUsers(keyword) {
        const url = API_BASE + '/users/search?q=' + encodeURIComponent(keyword);
        console.log('🌐 [mentorship] 请求:', url);
        const resp = await fetch(url);
        console.log('🌐 [mentorship] 响应状态:', resp.status, 'ok=', resp.ok);
        if (!resp.ok) {
            const text = await resp.text();
            console.error('❌ [mentorship] 响应内容:', text);
            throw new Error('搜索用户失败: HTTP ' + resp.status + ' - ' + text);
        }
        const data = await resp.json();
        console.log('🌐 [mentorship] 响应数据:', data);
        return data;
    }

    async function addRelation(mentorId, apprenticeId, skills) {
        const body = { mentor_id: mentorId, apprentice_id: apprenticeId };
        if (skills) body.skills = skills;
        const resp = await fetch(API_BASE + '/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const text = await resp.text();
        let data;
        try { data = JSON.parse(text); } catch (e) { data = { error: text }; }
        if (!resp.ok) throw new Error((data && data.error) || '添加师徒关系失败: HTTP ' + resp.status);
        return data;
    }

    async function deleteRelation(relationId) {
        const resp = await fetch(API_BASE + '/' + relationId, { method: 'DELETE' });
        const text = await resp.text();
        let data;
        try { data = JSON.parse(text); } catch (e) { data = { error: text }; }
        if (!resp.ok) throw new Error((data && data.error) || '删除师徒关系失败: HTTP ' + resp.status);
        return data;
    }

    async function deleteUserAsMentor(userId) {
        const resp = await fetch(API_BASE + '/user/' + userId, { method: 'DELETE' });
        const text = await resp.text();
        let data;
        try { data = JSON.parse(text); } catch (e) { data = { error: text }; }
        if (!resp.ok) throw new Error((data && data.error) || '删除根师傅失败: HTTP ' + resp.status);
        return data;
    }

    // ============================================================
    // 树状图谱渲染
    // ============================================================

    let treeEventsBound = false;

    function renderTree(data) {
        const trees = data.trees || [];
        const container = document.getElementById('treeContent');

        if (trees.length === 0) {
            container.innerHTML =
                '<div class="no-data">' +
                '<span class="emoji">🌱</span>' +
                '<p>暂无师徒关系</p>' +
                '<p class="hint">点击下方"添加首个师傅"按钮，或通过搜索选择员工建立师徒关系</p>' +
                '<button class="btn primary" id="addFirstMentorBtn" style="margin-top: 1rem;">👤 添加首个师傅</button>' +
                '</div>';
            const btn = document.getElementById('addFirstMentorBtn');
            if (btn) {
                btn.onclick = function () { openUserPicker('师傅', null); };
            }
            return;
        }

        let html = '';
        for (let i = 0; i < trees.length; i++) {
            html += renderNode(trees[i], true);
        }
        container.innerHTML = html;

        try {
            if (!treeEventsBound) {
                bindTreeEvents();
                treeEventsBound = true;
                console.log('[DEBUG] bindTreeEvents 完成，共绑定',
                    document.querySelectorAll('.node-btn[data-action="add-apprentice"]').length,
                    '个添加徒弟按钮');
            }
        } catch (err) {
            console.error('[ERROR] bindTreeEvents 出错:', err);
        }
    }

    function renderNode(node, isRoot) {
        const user = node.user || {};
        const apprentices = node.apprentices || [];
        const hasChildren = apprentices.length > 0;
        const relationId = node.relation_id;
        const isRootNode = !!isRoot;
        const skills = node.skills || '';

        const nodeCls = isRootNode ? 'tree-node tree-root' : 'tree-node';
        const cardCls = isRootNode ? 'node-card is-root' : (hasChildren ? 'node-card is-mentor' : 'node-card');

        let html = '<div class="' + nodeCls + '" data-user-id="' + user.id + '">';
        html += '<div class="' + cardCls + '">';

        // 折叠/展开按钮（有徒弟时才显示）
        if (hasChildren) {
            html += '<button class="node-btn toggle-btn" data-action="toggle" title="折叠/展开">−</button>';
        } else {
            html += '<span style="display: inline-block; width: 24px;"></span>';
        }

        // 用户信息
        html += '<div class="node-info">';
        html += '<span class="node-name">' + escapeHtml(user.username) + '</span>';
        if (user.shift_type) {
            html += getShiftBadge(user.shift_type);
        }
        if (user.role) {
            html += '<span class="node-role">' + escapeHtml(user.role) + '</span>';
        }
        // 显示技能信息
        if (skills) {
            html += '<span class="node-skills" title="岗位技能">🛠 ' + escapeHtml(skills) + '</span>';
        }
        html += '</div>';

        // 操作按钮
        html += '<div class="node-actions">';
        // 根节点额外提供"添加师傅"按钮（支持向上建立多级师徒）
        if (isRootNode) {
            html += '<button class="node-btn add-btn add-mentor-btn" data-action="add-mentor" data-user-id="' + user.id + '" data-user-name="' + escapeHtml(user.username) + '" title="为其添加师傅">+ 师傅</button>';
        }
        html += '<button class="node-btn add-btn" data-action="add-apprentice" data-user-id="' + user.id + '" data-user-name="' + escapeHtml(user.username) + '" title="添加徒弟">+ 徒弟</button>';
        // 非根节点可以删除（即删除与上一级师傅的关系）
        if (!isRootNode && relationId) {
            html += '<button class="node-btn del-btn" data-action="delete-relation" data-relation-id="' + relationId + '" title="移除该师徒关系">×</button>';
        }
        // 根节点：提供"移除该根师傅"按钮，其直接徒弟将变成新的根节点
        if (isRootNode) {
            html += '<button class="node-btn del-btn" data-action="delete-root" data-user-id="' + user.id + '" data-user-name="' + escapeHtml(user.username) + '" title="移除该根师傅（保留其下级关系）">×移除</button>';
        }
        html += '</div>';

        html += '</div>'; // end node-card

        // 子节点
        if (hasChildren) {
            html += '<div class="tree-children">';
            for (let i = 0; i < apprentices.length; i++) {
                html += renderNode(apprentices[i], false);
            }
            html += '</div>';
        }

        html += '</div>'; // end tree-node
        return html;
    }

    function bindTreeEvents() {
        console.log('[DEBUG] bindTreeEvents 开始绑定事件');

        // 使用事件委托处理所有按钮点击
        document.getElementById('treeContent').addEventListener('click', function(e) {
            const btn = e.target.closest('.node-btn');
            if (!btn) return;

            const action = btn.dataset.action;
            const userId = parseInt(btn.dataset.userId, 10);
            const userName = btn.dataset.userName;

            console.log('[DEBUG] 事件委托触发: action=', action, 'userId=', userId);

            if (action === 'add-apprentice') {
                e.stopPropagation();
                console.log('[DEBUG] 调用 openUserPicker 添加徒弟');
                openUserPicker('徒弟', userId, userName);
            } else if (action === 'add-mentor') {
                e.stopPropagation();
                const apprenticeId = userId;
                const apprenticeName = userName;
                openUserPicker('师傅_for_' + apprenticeId, null, null, apprenticeId, apprenticeName);
            } else if (action === 'toggle') {
                e.stopPropagation();
                const parent = btn.closest('.tree-node');
                if (parent) {
                    parent.classList.toggle('collapsed');
                    btn.textContent = parent.classList.contains('collapsed') ? '+' : '−';
                }
            } else if (action === 'delete-relation') {
                e.stopPropagation();
                const rid = btn.dataset.relationId;
                showConfirm('确认删除', '确认要移除该师徒关系吗？此操作不会删除员工账号，其下级关系将被保留。',
                    async function () {
                        try {
                            await deleteRelation(rid);
                            showToast('已移除师徒关系', 'success');
                            loadTree();
                        } catch (err) {
                            showToast(err.message || '操作失败', 'error');
                        }
                    });
            } else if (action === 'delete-root') {
                e.stopPropagation();
                const uid = userId;
                const uname = btn.dataset.userName;
                // 先获取该用户的徒弟数量，给出更精确的提示
                showConfirm(
                    '确认移除根师傅',
                    '确认要移除 "' + uname + '" 作为根师傅吗？\n\n' +
                    '他的直接徒弟将变成新的根节点，所有下级师徒关系都将保留。\n\n' +
                    '此操作不会删除员工账号。',
                    async function () {
                        try {
                            const result = await deleteUserAsMentor(uid);
                            const count = (result && typeof result.deleted_count === 'number')
                                ? result.deleted_count
                                : 0;
                            if (count > 0) {
                                showToast('已移除根师傅，共解除 ' + count + ' 条师徒关系，其徒弟成为新根节点', 'success');
                            } else {
                                showToast('已移除该根节点', 'success');
                            }
                            loadTree();
                        } catch (err) {
                            showToast(err.message || '操作失败', 'error');
                        }
                    }
                );
            }
        });
    }

    // ============================================================
    // 员工选择弹窗
    // ============================================================

    let pickerCallback = null;
    let pickerExcludeId = null;
    let firstMentorInfo = null; // 用于两步式"添加首个师傅"流程
    let freeMode = false; // 自由模式：先选师傅再选徒弟
    let reverseMode = false; // 反向模式：已有徒弟，选师傅
    let reverseApprenticeId = null;
    let reverseApprenticeName = null;

    function openUserPicker(role, mentorId, mentorName, reverseApprenticeId_, reverseApprenticeName_) {
        console.log('[DEBUG] openUserPicker 被调用, role=', role, 'mentorId=', mentorId, 'mentorName=', mentorName);
        const modal = document.getElementById('userPickerModal');
        const title = document.getElementById('pickerTitle');
        const searchInput = document.getElementById('pickerSearch');

        // 判断是否是反向模式（先固定了徒弟，现在要选师傅）
        reverseMode = (typeof role === 'string' && role.startsWith('师傅_for_'));
        if (reverseMode) {
            reverseApprenticeId = reverseApprenticeId_;
            reverseApprenticeName = reverseApprenticeName_;
        } else {
            reverseApprenticeId = null;
            reverseApprenticeName = null;
        }

        pickerExcludeId = mentorId; // 师傅自己不能做自己的徒弟
        freeMode = (role === '师傅' || role === 'free'); // 自由模式

        // 师傅/徒弟两种模式（需要在确认时让用户输入技能）
        if (reverseMode) {
            // 反向模式：用户点了"添加师傅"（当前用户是徒弟），先选择师傅，之后输入技能
            title.textContent = '【选择师傅】为 ' + reverseApprenticeName + ' 选择师傅';
            pickerExcludeId = reverseApprenticeId; // 自己不能做自己的师傅
            pickerCallback = function (mentorUser) {
                // 为这位师傅（师傅）与当前用户（徒弟）建立师徒关系，弹出技能输入框
                openSkillInput(mentorUser.id, mentorUser.username, reverseApprenticeId, reverseApprenticeName);
            };
        } else if (role === '师傅' || role === 'free') {
            // 第一步：选师傅
            title.textContent = (role === 'free' ? '【第 1/2 步】选择师傅' : '【第 1/2 步】选择第一位师傅');
            pickerCallback = function (user) {
                firstMentorInfo = user; // 暂存师傅信息
                // 第二步：为这位师傅选第一个徒弟
                title.textContent = '【第 2/2 步】为 ' + user.username + ' 选择徒弟';
                pickerExcludeId = user.id; // 排除师傅
                pickerCallback = function (apprentice) {
                    openSkillInput(firstMentorInfo.id, firstMentorInfo.username, apprentice.id, apprentice.username);
                };
                renderPickerList('');
            };
        } else {
            firstMentorInfo = null;
            freeMode = false;
            title.textContent = '为 ' + mentorName + ' 选择徒弟';
            pickerCallback = function (user) {
                openSkillInput(mentorId, mentorName, user.id, user.username);
            };
        }

        modal.style.display = 'flex';
        searchInput.value = '';
        searchInput.focus();
        console.log('[DEBUG] 准备调用 renderPickerList');
        renderPickerList('').then(() => {
            console.log('[DEBUG] renderPickerList 完成');
        }).catch(err => {
            console.error('[ERROR] renderPickerList 出错:', err);
        });
    }

    /**
     * 弹出输入岗位技能的对话框，确认后建立师徒关系
     */
    function openSkillInput(mentorId, mentorName, apprenticeId, apprenticeName) {
        const modal = document.getElementById('confirmModal');
        const title = document.getElementById('confirmTitle');
        const body = modal.querySelector('.modal-body');

        title.textContent = '建立师徒关系 · 输入岗位技能';

        // 替换确认弹窗内容：加入技能输入框
        let html = '';
        html += '<p id="confirmMessage" style="margin-bottom: 10px;">师傅：<strong>' + escapeHtml(mentorName) + '</strong></p>';
        html += '<p style="margin-bottom: 10px;">徒弟：<strong>' + escapeHtml(apprenticeName) + '</strong></p>';
        html += '<div style="margin: 16px 0;">';
        html += '<label style="display:block; margin-bottom: 6px; color:#666;">岗位技能（可选）：</label>';
        html += '<input type="text" id="skillInput" placeholder="如：涂布机操作、维修保养、品质管理..." style="width:100%; padding:8px; border:1px solid #ddd; border-radius:6px; box-sizing:border-box;">';
        html += '</div>';
        html += '<div class="confirm-actions" style="margin-top:16px;">';
        html += '<button class="btn secondary" id="confirmCancel">取消</button>';
        html += '<button class="btn primary" id="confirmOk">确认建立</button>';
        html += '</div>';

        body.innerHTML = html;

        modal.style.display = 'flex';

        const skillInput = document.getElementById('skillInput');
        setTimeout(function () {
            skillInput.focus();
        }, 100);

        // 绑定确认按钮
        document.getElementById('confirmOk').onclick = async function () {
            const skills = (skillInput.value || '').trim();
            try {
                await addRelation(mentorId, apprenticeId, skills);
                showToast('师徒关系建立成功！', 'success');
                modal.style.display = 'none';
                closeUserPicker();
                firstMentorInfo = null;
                freeMode = false;
                reverseMode = false;
                reverseApprenticeId = null;
                reverseApprenticeName = null;
                loadTree();
            } catch (err) {
                showToast(err.message || '操作失败', 'error');
            }
        };

        document.getElementById('confirmCancel').onclick = function () {
            modal.style.display = 'none';
        };
    }

    function closeUserPicker() {
        document.getElementById('userPickerModal').style.display = 'none';
        pickerCallback = null;
        pickerExcludeId = null;
        firstMentorInfo = null;
        freeMode = false;
        reverseMode = false;
        reverseApprenticeId = null;
        reverseApprenticeName = null;
    }

    async function renderPickerList(keyword) {
        console.log('[DEBUG] renderPickerList 开始搜索, keyword=', keyword);
        const list = document.getElementById('pickerList');
        list.innerHTML = '<div style="text-align: center; color: #999; padding: 1rem;">搜索中...</div>';

        try {
            const data = await searchUsers(keyword);
            const users = data.users || [];

            if (users.length === 0) {
                list.innerHTML = '<div class="no-data" style="padding: 2rem;"><span class="emoji">🔍</span><p>没有找到匹配的员工（也可以试试输入中文姓名拼音首字母，如：zhangsan、zs）</p></div>';
                return;
            }

            let html = '';
            for (let i = 0; i < users.length; i++) {
                const u = users[i];
                if (pickerExcludeId && parseInt(u.id, 10) === parseInt(pickerExcludeId, 10)) {
                    continue; // 排除指定用户
                }
                html += '<div class="picker-item" data-user-id="' + u.id + '" data-user-name="' + escapeHtml(u.username) + '">';
                html += '<div class="picker-user-info">';
                html += '<span class="picker-user-name">' + escapeHtml(u.username) + '</span>';
                if (u.pinyin_initials) {
                    html += '<span class="picker-user-meta pinyin-meta">[' + escapeHtml(u.pinyin_initials) + ']</span>';
                }
                if (u.shift_type) {
                    html += '<span class="picker-user-meta">[' + escapeHtml(u.shift_type) + ']</span>';
                }
                if (u.role) {
                    html += '<span class="picker-user-meta">' + escapeHtml(u.role) + '</span>';
                }
                html += '</div>';
                html += '<button class="btn primary small">选择</button>';
                html += '</div>';
            }

            if (!html) {
                list.innerHTML = '<div class="no-data" style="padding: 2rem;"><span class="emoji">🔍</span><p>没有找到匹配的员工</p></div>';
                return;
            }

            list.innerHTML = html;
        } catch (err) {
            list.innerHTML = '<div style="text-align: center; color: #ff4757; padding: 1rem;">搜索失败：' + err.message + '</div>';
        }
    }

    let searchTimer = null;

    // ============================================================
    // 确认弹窗
    // ============================================================

    function showConfirm(title, message, onOk) {
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const bodyEl = modal.querySelector('.modal-body');

        // 每次都重建标准结构，避免 openSkillInput 改变后留下的副作用
        bodyEl.innerHTML =
            '<p id="confirmMessage" style="font-size:1rem;line-height:1.6;"></p>' +
            '<div class="confirm-actions" style="margin-top:1rem;">' +
            '<button class="btn secondary" id="confirmCancel">取消</button>' +
            '<button class="btn primary" id="confirmOk">确认</button>' +
            '</div>';

        titleEl.textContent = title;
        document.getElementById('confirmMessage').textContent = message;
        modal.style.display = 'flex';

        document.getElementById('confirmOk').onclick = function () {
            modal.style.display = 'none';
            if (onOk) onOk();
        };
        document.getElementById('confirmCancel').onclick = function () {
            modal.style.display = 'none';
        };
    }

    // ============================================================
    // 搜索员工功能 - 展示传承链路
    // ============================================================

    async function doSearch(keyword) {
        const searchResult = document.getElementById('searchResult');

        if (!keyword || keyword.trim() === '') {
            searchResult.style.display = 'none';
            searchResult.innerHTML = '';
            return;
        }

        searchResult.style.display = 'block';
        searchResult.innerHTML = '<div style="text-align: center; color: #999; padding: 1rem;">搜索中...</div>';

        try {
            const data = await searchUsers(keyword);
            const users = data.users || [];

            if (users.length === 0) {
                searchResult.innerHTML =
                    '<div class="no-data"><span class="emoji">🤔</span><p>没有找到姓名包含"' + escapeHtml(keyword) + '"的员工</p></div>';
                return;
            }

            // 搜索到多个用户时，让用户选择具体查看哪一个
            if (users.length > 1 && !sessionStorage.getItem('autoSelectedUser_' + keyword)) {
                let html = '<h3>🔍 找到 ' + users.length + ' 个匹配员工，点击查看详情：</h3>';
                html += '<div class="picker-list">';
                for (let i = 0; i < users.length; i++) {
                    const u = users[i];
                    html += '<div class="picker-item search-picker-item" data-user-id="' + u.id + '">';
                    html += '<div class="picker-user-info">';
                    html += '<span class="picker-user-name">' + escapeHtml(u.username) + '</span>';
                    if (u.shift_type) html += '<span class="picker-user-meta">[' + escapeHtml(u.shift_type) + ']</span>';
                    if (u.role) html += '<span class="picker-user-meta">' + escapeHtml(u.role) + '</span>';
                    html += '</div>';
                    html += '<button class="btn primary small">查看链路 →</button>';
                    html += '</div>';
                }
                html += '</div>';
                searchResult.innerHTML = html;

                searchResult.querySelectorAll('.search-picker-item').forEach(function (item) {
                    item.addEventListener('click', function () {
                        const uid = parseInt(item.dataset.userId, 10);
                        showLineage(uid);
                    });
                });
            } else {
                // 只有一个用户，直接显示
                showLineage(users[0].id);
            }
        } catch (err) {
            searchResult.innerHTML = '<div style="text-align: center; color: #ff4757; padding: 1rem;">搜索失败：' + err.message + '</div>';
        }
    }

    async function showLineage(userId) {
        const searchResult = document.getElementById('searchResult');
        searchResult.style.display = 'block';
        searchResult.innerHTML = '<div style="text-align: center; color: #999; padding: 1rem;">加载传承链路中...</div>';

        try {
            const data = await fetchLineage(userId);
            const lines = data.lines || [];
            const userInfo = data.user || {};

            let html = '<h3>👥 ' + escapeHtml(userInfo.username) + ' 的传承链路</h3>';

            if (userInfo.shift_type || userInfo.role) {
                html += '<p style="color: #666; margin-bottom: 1rem; font-size: 0.9rem;">';
                if (userInfo.shift_type) html += escapeHtml(userInfo.shift_type) + ' ';
                if (userInfo.role) html += '· ' + escapeHtml(userInfo.role);
                html += '</p>';
            }

            if (lines.length === 0) {
                html += '<div class="no-data" style="padding: 2rem 1rem;"><span class="emoji">📋</span><p>该员工暂无师徒关系记录</p><p class="hint">可在下方树状图谱中为其建立关系</p></div>';
            } else {
                html += '<p style="color: #666; margin-bottom: 1rem; font-size: 0.9rem;">共 ' + lines.length + ' 条传承链路（高亮显示当前员工，🛠 标注岗位技能）</p>';
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];
                    html += '<div class="lineage-card">';
                    html += '<div class="lineage-path">';
                    for (let j = 0; j < line.length; j++) {
                        const u = line[j];
                        if (j > 0) html += '<span class="lineage-arrow">→</span>';
                        const hl = (u.id === userId) ? ' lineage-user highlight' : ' lineage-user';
                        let nodeText = escapeHtml(u.username);
                        // 在有技能信息时附加（第一个节点没有 skills_from_mentor，因为没有上游关系）
                        if (u.skills_from_mentor) {
                            nodeText += ' <span class="lineage-skill" title="岗位技能">🛠' + escapeHtml(u.skills_from_mentor) + '</span>';
                        }
                        html += '<span class="' + hl + '">' + nodeText + '</span>';
                    }
                    html += '</div>';
                    html += '</div>';
                }
            }

            searchResult.innerHTML = html;
        } catch (err) {
            searchResult.innerHTML = '<div style="text-align: center; color: #ff4757; padding: 1rem;">加载失败：' + err.message + '</div>';
        }
    }

    // ============================================================
    // 主流程
    // ============================================================

    async function loadTree() {
        const loading = document.getElementById('treeLoading');
        const content = document.getElementById('treeContent');
        loading.style.display = 'block';
        content.innerHTML = '';

        try {
            const data = await fetchTree();

            // 更新统计信息
            const stats = document.getElementById('statsInfo');
            const total = data.total_relations || 0;
            const mentorCount = data.total_mentors || 0;
            const apprenticeCount = data.total_apprentices || 0;
            stats.textContent = '📊 关系数 ' + total + ' · 师傅 ' + mentorCount + ' · 徒弟 ' + apprenticeCount;

            renderTree(data);
        } catch (err) {
            content.innerHTML = '<div class="no-data" style="color: #ff4757;"><span class="emoji">⚠️</span><p>加载失败：' + err.message + '</p></div>';
        } finally {
            loading.style.display = 'none';
        }
    }

    function init() {
        // 搜索
        document.getElementById('searchBtn').addEventListener('click', function () {
            const kw = document.getElementById('searchInput').value.trim();
            doSearch(kw);
        });
        document.getElementById('searchInput').addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                doSearch(this.value.trim());
            }
        });

        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', loadTree);

        // 新建师徒关系按钮
        document.getElementById('newRelationBtn').addEventListener('click', function () {
            openUserPicker('free', null);
        });

        // 员工选择弹窗 - 关闭
        document.getElementById('closePicker').addEventListener('click', closeUserPicker);
        document.getElementById('userPickerModal').addEventListener('click', function (e) {
            if (e.target === this) closeUserPicker();
        });

        // 员工选择弹窗 - 搜索（防抖，200ms）
        document.getElementById('pickerSearch').addEventListener('input', function () {
            const kw = this.value.trim();
            if (searchTimer) clearTimeout(searchTimer);
            searchTimer = setTimeout(function () {
                renderPickerList(kw);
            }, 200);
        });

        // === 事件委托：picker-item 点击 ===
        // 在 pickerList 容器上绑定一次，而不是在每个 picker-item 上重复绑定
        // 这样第二次、第三次打开弹窗时，点击仍然有效，不会因为 DOM 重渲染而失效
        document.getElementById('pickerList').addEventListener('click', function (e) {
            const item = e.target.closest('.picker-item');
            if (!item) return;
            if (!pickerCallback) {
                console.warn('[DEBUG] pickerCallback is null, ignoring click');
                showToast('请先选择师傅或重新打开选择框', 'error');
                return;
            }
            try {
                pickerCallback({
                    id: parseInt(item.dataset.userId, 10),
                    username: item.dataset.userName
                });
            } catch (err) {
                console.error('[ERROR] pickerCallback 执行失败:', err);
                showToast('选择员工时出现问题，请重试', 'error');
            }
        });

        // 首次加载
        loadTree();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
