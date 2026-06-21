import re

# 读取文件
with open('d:/新建文件夹/小工具/time-tracker/frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("开始修改index.html...")

# 1. 添加师带徒选项卡按钮
if 'data-tab="mentorship"' not in content:
    # 在基金持仓按钮后添加师带徒按钮
    pattern = r'(<button class="tab-btn" data-tab="fund">基金持仓</button>\n)'
    replacement = r'\1                <button class="tab-btn" data-tab="mentorship">师带徒</button>\n'
    content = re.sub(pattern, replacement, content)
    print("✓ 已添加师带徒选项卡按钮")

# 2. 添加CSS引用
if 'mentorship.css' not in content:
    content = content.replace('</head>', '    <link rel="stylesheet" href="css/mentorship.css">\n</head>')
    print("✓ 已添加mentorship.css引用")

# 3. 添加师带徒选项卡内容
mentorship_content = '''
                <!-- 师带徒 -->
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
                </div>
'''

if 'id="mentorship"' not in content:
    # 在基金选项卡结束后添加
    fund_end = content.find('<div id="fund" class="tab-pane">')
    if fund_end != -1:
        # 找到下一个 </div>
        next_div = content.find('</div>', fund_end)
        content = content[:next_div + 6] + mentorship_content + content[next_div + 6:]
        print("✓ 已添加师带徒选项卡内容")

# 4. 添加模态框
mentorship_modal = '''
    <!-- 师徒传承模态框 -->
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
    </div>
'''

if 'id="mentorshipModal"' not in content:
    # 在基金模态框后添加
    fund_modal_end = content.find('<div id="fundModal" class="modal">')
    if fund_modal_end != -1:
        # 找到模态框结束
        modal_end = content.find('</div>\n\n    <!-- 引入第三方库 -->', fund_modal_end)
        if modal_end != -1:
            content = content[:modal_end + 6] + mentorship_modal + content[modal_end + 6:]
            print("✓ 已添加师带徒模态框")

# 5. 添加JS引用
if 'js/mentorship.js' not in content:
    content = content.replace('</body>', '    <script src="js/mentorship.js"></script>\n</body>')
    print("✓ 已添加mentorship.js引用")

# 保存文件
with open('d:/新建文件夹/小工具/time-tracker/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ index.html修改完成！")
print("\n请刷新浏览器页面查看师带徒选项卡。")
