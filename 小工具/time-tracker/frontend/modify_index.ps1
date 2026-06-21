# 师带徒功能 - PowerShell修改脚本
# 请将此文件保存为 modify_index.ps1 并以管理员权限运行

$filePath = "d:\新建文件夹\小工具\time-tracker\frontend\index.html"

# 读取文件
$content = Get-Content $filePath -Raw -Encoding UTF8

Write-Host "开始修改index.html..."

# 1. 添加师带徒选项卡按钮（在基金持仓按钮后）
if ($content -notmatch 'data-tab="mentorship"') {
    $content = $content -replace '(<button class="tab-btn" data-tab="fund">基金持仓</button>)', '$1' + "`n                <button class=`"tab-btn`" data-tab=`"mentorship`">师带徒</button>"
    Write-Host "✓ 已添加师带徒选项卡按钮"
}

# 2. 添加CSS引用
if ($content -notmatch 'mentorship.css') {
    $content = $content -replace '</head>', "`n    <link rel=`"stylesheet`" href=`"css/mentorship.css`">`n</head>"
    Write-Host "✓ 已添加mentorship.css引用"
}

# 3. 添加师带徒选项卡内容（在基金选项卡后）
$mentorshipTab = @'

                <!-- 师带徒 -->
                <div id="mentorship" class="tab-pane">
                    <div class="mentorship-section">
                        <h2>师徒传承</h2>
                        
                        <div class="section-header">
                            <button id="addMentorshipBtn" class="btn primary">添加关系</button>
                            <button id="refreshTreeBtn" class="btn secondary">刷新</button>
                        </div>
                        
                        <div id="mentorshipStats" class="mentorship-stats"></div>
                        <div id="mentorshipTree" class="mentorship-tree"></div>
                    </div>
                </div>
'@

if ($content -notmatch 'id="mentorship"') {
    $pattern = '(                </div>\s*\n\s*</div>\s*\n\s*<!-- 基金持仓 -->)'
    $replacement = $mentorshipTab + "`n`$1"
    $content = $content -replace $pattern, $replacement
    Write-Host "✓ 已添加师带徒选项卡内容"
}

# 4. 添加模态框
$mentorshipModal = @'

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
                    <select id="mentorSelect" required><option value="">请选择师父</option></select>
                </div>
                <div class="form-group">
                    <label for="apprenticeSelect">徒弟 *</label>
                    <select id="apprenticeSelect" required><option value="">请选择徒弟</option></select>
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
'@

if ($content -notmatch 'id="mentorshipModal"') {
    $content = $content -replace '(</body>)', $mentorshipModal + "`n`$1"
    Write-Host "✓ 已添加师带徒模态框"
}

# 5. 添加JS引用
if ($content -notmatch 'js/mentorship.js') {
    $content = $content -replace '(</body>)', '    <script src="js/mentorship.js"></script>' + "`n`$1"
    Write-Host "✓ 已添加mentorship.js引用"
}

# 保存文件
$content | Set-Content $filePath -Encoding UTF8

Write-Host "`n✅ index.html修改完成！"
Write-Host "`n请刷新浏览器页面查看师带徒选项卡。"
Write-Host "`n注意：后端功能需要单独配置。"
