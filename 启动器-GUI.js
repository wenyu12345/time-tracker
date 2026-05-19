const { app, BrowserWindow, Menu, MenuItem, Tray, screen, globalShortcut, clipboard, shell, ipcMain, nativeTheme, MessageChannelMain } = require('electron');
const { exec, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// 创建主窗口
function createWindow() {
  const win = new BrowserWindow({
    width: 400,
    height: 300,
    title: 'AlgerMusicPlayer 启动器',
    resizable: true,
    center: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    }
  });

  // 加载HTML内容
  win.loadFile('启动器-界面.html');

  // 打开开发者工具
  // win.webContents.openDevTools();
}

// 当Electron完成初始化后创建窗口
app.whenReady().then(() => {
  createWindow();

  // macOS上，当点击dock图标并且没有其他窗口打开时，会创建一个新窗口
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// 关闭所有窗口时退出应用（Windows & Linux）
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// 监听渲染进程的IPC消息
ipcMain.on('run-algermusicplayer', (event) => {
  try {
    const cwd = path.join(__dirname, 'AlgerMusicPlayer');
    const child = spawn('npm', ['run', 'dev'], {
      cwd: cwd,
      shell: true,
      detached: true
    });
    
    child.stdout.on('data', (data) => {
      console.log(`stdout: ${data}`);
      event.sender.send('process-output', `[AlgerMusicPlayer] ${data}`);
    });

    child.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
      event.sender.send('process-output', `[AlgerMusicPlayer-ERROR] ${data}`);
    });

    child.on('close', (code) => {
      console.log(`child process exited with code ${code}`);
      event.sender.send('process-exit', { code: code, name: 'AlgerMusicPlayer' });
    });

    event.sender.send('process-started', 'AlgerMusicPlayer');
  } catch (error) {
    console.error('启动AlgerMusicPlayer失败:', error);
    event.sender.send('process-error', `启动AlgerMusicPlayer失败: ${error.message}`);
  }
});

ipcMain.on('run-music-crawler', (event, searchText) => {
  try {
    const cwd = __dirname;
    const child = spawn('node', ['simple_music_crawler.js', searchText || '周杰伦 稻香'], {
      cwd: cwd,
      shell: true,
      detached: true
    });
    
    child.stdout.on('data', (data) => {
      console.log(`stdout: ${data}`);
      event.sender.send('process-output', `[MusicCrawler] ${data}`);
    });

    child.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
      event.sender.send('process-output', `[MusicCrawler-ERROR] ${data}`);
    });

    child.on('close', (code) => {
      console.log(`child process exited with code ${code}`);
      event.sender.send('process-exit', { code: code, name: 'MusicCrawler' });
    });

    event.sender.send('process-started', 'MusicCrawler');
  } catch (error) {
    console.error('启动音乐爬虫失败:', error);
    event.sender.send('process-error', `启动音乐爬虫失败: ${error.message}`);
  }
});

ipcMain.on('open-downloads-folder', () => {
  const downloadsFolder = path.join(__dirname, 'downloads');
  if (fs.existsSync(downloadsFolder)) {
    shell.openPath(downloadsFolder);
  } else {
    console.error('下载文件夹不存在');
  }
});

ipcMain.on('check-running', (event) => {
  // 这里可以添加检查进程是否在运行的逻辑
  event.sender.send('running-status', {
    algermusicplayer: false,  // 需要实现进程检查逻辑
    musiccrawler: false
  });
});