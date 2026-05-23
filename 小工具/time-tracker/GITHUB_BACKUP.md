# 天命1.0 - GitHub备份说明

## 📋 前置条件
1. 已有 GitHub 账号
2. 已安装 Git（已确认）
3. 已配置 Git 用户名和邮箱

---

## 🚀 完整步骤

### 第一步：创建GitHub仓库
1. 访问：https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `time-tracker` 或你喜欢的名字
   - **Description**: `工时记录管理系统 - 天命1.0版本`
   - **Public/Private**: 根据需要选择
   - ⚠️ 不要勾选"Initialize this repository"
3. 点击 **Create repository**

### 第二步：添加远程仓库
在项目目录下运行：

```bash
cd d:\新建文件夹\小工具\time-tracker
git remote add origin https://github.com/你的用户名/time-tracker.git
```

### 第三步：提交本地更改（如果需要）
虽然我们已经备份了"天命1.0"，但现在添加了.gitignore文件：

```bash
cd d:\新建文件夹\小工具\time-tracker
git add .gitignore GITHUB_SETUP.bat
git commit -m "添加.gitignore和GitHub设置说明"
```

### 第四步：推送到GitHub
```bash
git push -u origin master
```

---

## 📁 已创建的文件

- ✅ [GITHUB_SETUP.bat](file:///d:/新建文件夹/小工具/time-tracker/GITHUB_SETUP.bat) - 便捷设置脚本
- ✅ [.gitignore](file:///d:/新建文件夹/小工具/time-tracker/.gitignore) - Git忽略文件配置

---

## ⚙️ 首次使用Git？

如果是第一次使用Git，需要先配置：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

---

## 🔐 使用SSH（可选）

如果使用SSH而不是HTTPS：
1. 生成SSH密钥
2. 上传到GitHub
3. 使用：`git remote add origin git@github.com:你的用户名/time-tracker.git`

---

## 💡 日常备份

以后有新修改时，只需：
```bash
git add .
git commit -m "更新说明"
git push
```
