# 简单的网易云音乐爬虫使用说明

## 功能介绍

这是一个基于Node.js的简单网易云音乐爬虫脚本，可以：
- 搜索歌曲
- 获取歌曲播放URL
- 下载歌曲到本地
- 支持备用解析器（当官方API无法获取时）

## 前置要求

- Node.js 环境
- 需要安装axios依赖
- 可选：本地运行netease-cloud-music-api服务（默认使用http://localhost:30488）

## 使用方法

### 1. 安装依赖

```bash
npm install axios
```

### 2. 运行脚本

**方法一：直接运行指定歌曲**
```bash
node simple_music_crawler.js "歌曲名称 歌手" [索引]
```

示例：
```bash
node simple_music_crawler.js "周杰伦 稻香" 0
```

**方法二：在代码中取消main函数的注释，修改搜索关键词**
```javascript
// 修改simple_music_crawler.js文件末尾的代码
main('周杰伦 稻香', 0);
```

然后运行：
```bash
node simple_music_crawler.js
```

**方法三：作为模块引入使用**
```javascript
const musicCrawler = require('./simple_music_crawler');

// 搜索歌曲
musicCrawler.searchSongs('周杰伦').then(songs => {
  console.log(songs);
});

// 或者完整流程
musicCrawler.main('周杰伦 青花瓷', 0);
```

## 配置说明

- `API_BASE_URL`：网易云音乐API代理地址，默认为`http://localhost:30488`
- 下载目录默认为当前目录下的`downloads`文件夹

## 注意事项

1. 此脚本仅用于学习和个人使用，请遵守相关法律法规
2. 某些歌曲可能需要VIP权限才能下载
3. 备用解析器使用第三方API，可能存在不稳定性
4. 如果本地没有运行netease-cloud-music-api服务，可以修改API_BASE_URL为其他可用的代理服务地址

## 常见问题

### Q: 无法获取歌曲URL怎么办？
A: 脚本会自动尝试备用解析器，如果仍然失败，可能是歌曲需要VIP权限或暂时无法解析，可以尝试其他歌曲。

### Q: 下载的歌曲文件损坏怎么办？
A: 可能是网络问题导致下载不完整，可以尝试重新运行脚本下载。

### Q: 如何修改下载目录？
A: 修改`downloadSong`函数中的`saveDir`参数，默认为`'./downloads'`。

## 扩展提示

如果需要更多功能，可以参考以下方向扩展：
1. 添加歌单解析功能
2. 增加多线程下载
3. 添加ID3标签编辑
4. 实现简单的GUI界面

## 免责声明

本脚本仅供学习和研究使用，请尊重音乐版权，支持正版音乐。作者不对任何非法使用行为负责。