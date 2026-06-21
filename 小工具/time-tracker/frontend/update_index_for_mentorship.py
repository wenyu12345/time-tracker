"""
自动更新index.html，添加师徒传承功能
运行此脚本会自动完成所有HTML修改
"""

import re

def update_index_html():
    """更新index.html文件"""
    file_path = 'd:/新建文件夹/小工具/time-tracker/frontend/index.html'
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("开始更新index.html...")
    
    # 1. 添加CSS引用
    if 'mentorship.css' not in content:
        css_link = '<link rel="stylesheet" href="css/mentorship.css">'
        # 在</head>前添加
        content = content.replace('</head>', css_link + '\n</head>')
        print("✓ 已添加mentorship.css引用")
    
    # 2. 添加选项卡按钮
    if 'data-tab="mentorship"' not in content:
        # 在基金持仓按钮后添加
        fund_btn = '<button class="tab-btn" data-tab="fund">基金持仓</button>'
        new_btn = fund_btn + '\n                <button class="tab-btn" data-tab="mentorship">师带徒</button>'
        content = content.replace(fund_btn, new_btn)
        print("✓ 已添加师带徒选项卡按钮")
    
    # 3. 添加师徒传承选项卡内容
    mentorship_tab = '''                <!-- 师带徒 -->
                <div id="mentorship" class="tab-pane">
                    <div class="mentorship-section">
                        <h2>师徒传承</h2>
                        
                        <div class="section-header">
                            <button id="addMentorshipBtn" class="btn primary">添加关系</button>
                            <button id="refreshTreeBtn" class="btn secondary">刷新</button>
                        </div>
                        
                        <!-- 统计信息 -->
                        <div id="mentorshipStats" class="mentorship-stats">
                            <!-- 统计将通过JavaScript动态生成 -->
                        </div>
                        
                        <!-- 师徒关系树状图 -->
                        <div id="mentorshipTree" class="mentorship-tree">
                            <!-- 树状图将通过JavaScript动态生成 -->
                        </div>
                    </div>
                </div>'''
    
    if 'id="mentorship"' not in content:
        # 在</div> (tab-content结束标签前) 添加
        # 找到基金选项卡结束的位置
        fund_tab_end = content.find('<div id="fund" class="tab-pane">')
        if fund_tab_end != -1:
            # 找到下一个</div>的位置（tab-content结束）
            next_div = content.find('</div>', fund_tab_end)
            if next_div != -1:
                # 在tab-content结束前插入师徒传承选项卡
                content = content[:next_div] + mentorship_tab + '\n                ' + content[next_div:]
                print("✓ 已添加师徒传承选项卡内容")
    
    # 4. 添加师徒传承模态框
    mentorship_modal = '''    <!-- 师徒传承模态框 -->
    <div id="mentorshipModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="mentorshipModalTitle">添加师徒关系</h3>
                <button id="closeMentorshipModal" class="close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="mentorSelect">师父 *</label>
                    <select id="mentorSelect" required>
                        <option value="">请选择师父</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="apprenticeSelect">徒弟 *</label>
                    <select id="apprenticeSelect" required>
                        <option value="">请选择徒弟</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="relationshipType">关系类型</label>
                    <select id="relationshipType">
                        <option value="direct">直接师徒</option>
                        <option value="indirect">再传弟子</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="startDate">开始日期</label>
                    <input type="date" id="startDate">
                </div>
                <div class="form-group">
                    <label for="mentorshipNotes">备注</label>
                    <textarea id="mentorshipNotes" placeholder="备注信息"></textarea>
                </div>
                <button id="saveMentorshipBtn" class="btn primary">保存</button>
            </div>
        </div>
    </div>'''
    
    if 'id="mentorshipModal"' not in content:
        # 在基金模态框后添加
        fund_modal_end = content.find('<div id="fundModal" class="modal">')
        if fund_modal_end != -1:
            # 找到该模态框的结束</div>
            modal_end = content.find('</div>', fund_modal_end)
            # 找到模态框结束后的</div>
            modal_container_end = content.find('</div>', modal_end + 10)
            if modal_end != -1 and modal_container_end != -1:
                content = content[:modal_container_end + 6] + '\n' + mentorship_modal + content[modal_container_end + 6:]
                print("✓ 已添加师徒传承模态框")
    
    # 5. 添加JavaScript引用
    if 'js/mentorship.js' not in content:
        # 在</body>前添加
        content = content.replace('</body>', '    <script src="js/mentorship.js"></script>\n</body>')
        print("✓ 已添加mentorship.js引用")
    
    # 6. 更新tabs.js以触发mentorship模块初始化
    tabs_file = 'd:/新建文件夹/小工具/time-tracker/frontend/js/tabs.js'
    try:
        with open(tabs_file, 'r', encoding='utf-8') as f:
            tabs_content = f.read()
        
        if 'MentorshipModule' not in tabs_content:
            # 在tabChanged事件触发处添加
            if 'tabChanged' in tabs_content:
                # 找到tabChanged事件触发处
                pattern = r"(// Trigger tab changed event\s+document\.dispatchEvent\(new CustomEvent\('tabChanged'\)"
                replacement = '''if (targetTab === 'mentorship') {
                    MentorshipModule.init();
                }
                
                // Trigger tab changed event
                document.dispatchEvent(new CustomEvent('tabChanged', { detail: { tab: targetTab } }))'''
                
                tabs_content = re.sub(pattern, replacement, tabs_content)
                
                with open(tabs_file, 'w', encoding='utf-8') as f:
                    f.write(tabs_content)
                print("✓ 已更新tabs.js")
    except Exception as e:
        print(f"⚠ 更新tabs.js失败: {e}")
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ index.html更新完成！")
    print("\n下一步操作：")
    print("1. 运行数据库迁移: python migrate_create_mentorship_table.py")
    print("2. 更新app.py: python update_app_for_mentorship.py")
    print("3. 重启服务器")

if __name__ == '__main__':
    update_index_html()
