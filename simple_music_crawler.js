// 简单的网易云音乐爬虫
// 功能：搜索歌曲、获取歌曲URL、播放音乐
// 注意：本脚本需要Node.js环境，使用前请安装axios依赖

const axios = require('axios');
const https = require('https');
const fs = require('fs');
const path = require('path');

// 网易云音乐API代理地址（可替换为自己的代理服务）
const API_BASE_URL = 'http://localhost:30488'; // 假设本地运行了netease-cloud-music-api

/**
 * 搜索歌曲
 * @param {string} keyword - 搜索关键词
 * @param {number} limit - 返回结果数量
 * @returns {Promise<Array>} 歌曲列表
 */
async function searchSongs(keyword, limit = 10) {
  try {
    console.log(`正在搜索歌曲：${keyword}`);
    console.log(`尝试连接API：${API_BASE_URL}/search`);
    
    const response = await axios.get(`${API_BASE_URL}/search`, {
      params: { keywords: keyword, limit: limit },
      timeout: 10000 // 设置10秒超时
    });
    
    console.log('API响应状态：', response.status);
    console.log('API响应数据结构：', Object.keys(response.data));
    
    if (response.data.code === 200 && response.data.result) {
      const songs = response.data.result.songs || [];
      console.log(`找到 ${songs.length} 首歌曲`);
      
      return songs.map(song => ({
        id: song.id,
        name: song.name,
        artists: Array.isArray(song.ar) ? song.ar.map(ar => ar.name).join('/') : '未知艺术家',
        album: song.al?.name || '未知专辑',
        duration: Math.floor(song.dt / 1000) // 转换为秒
      }));
    } else {
      console.error('搜索歌曲失败：', response.data);
      return [];
    }
  } catch (error) {
    console.error('搜索歌曲时发生错误：', error.message);
    console.error('提示：请确保本地netease-cloud-music-api服务正在运行');
    console.error(`可以尝试使用以下命令启动API服务：`);
    console.error(`1. git clone https://github.com/Binaryify/NeteaseCloudMusicApi`);
    console.error(`2. cd NeteaseCloudMusicApi`);
    console.error(`3. npm install`);
    console.error(`4. node app.js`);
    return [];
  }
}

/**
 * 获取歌曲播放URL
 * @param {number} songId - 歌曲ID
 * @returns {Promise<string|null>} 歌曲URL
 */
async function getSongUrl(songId) {
  try {
    console.log(`正在获取歌曲URL，ID：${songId}`);
    const response = await axios.get(`${API_BASE_URL}/song/url/v1`, {
      params: {
        id: songId,
        level: 'higher' // 音质：higher, standard, exhigh, lossless, hires
      }
    });
    
    if (response.data.code === 200 && response.data.data[0]) {
      const songData = response.data.data[0];
      if (songData.url) {
        console.log(`成功获取歌曲URL：${songData.url}`);
        return songData.url;
      } else {
        console.log(`无法获取歌曲URL，可能需要会员`);
        return null;
      }
    } else {
      console.error('获取歌曲URL失败：', response.data);
      return null;
    }
  } catch (error) {
    console.error('获取歌曲URL时发生错误：', error.message);
    return null;
  }
}

/**
 * 下载歌曲到本地
 * @param {string} url - 歌曲URL
 * @param {string} filename - 保存的文件名
 * @param {string} saveDir - 保存目录
 * @returns {Promise<string|null>} 保存的文件路径
 */
async function downloadSong(url, filename, saveDir = './downloads') {
  // 创建保存目录
  if (!fs.existsSync(saveDir)) {
    fs.mkdirSync(saveDir, { recursive: true });
  }
  
  const filePath = path.join(saveDir, filename);
  
  try {
    console.log(`正在下载歌曲到：${filePath}`);
    
    const fileStream = fs.createWriteStream(filePath);
    
    // 根据URL协议选择合适的模块
    const protocol = url.startsWith('https') ? https : require('http');
    
    await new Promise((resolve, reject) => {
      protocol.get(url, (response) => {
        if (response.statusCode !== 200) {
          reject(new Error(`下载失败：状态码 ${response.statusCode}`));
          return;
        }
        
        // 添加下载进度显示
        const totalLength = response.headers['content-length'];
        let downloadedLength = 0;
        
        response.on('data', (chunk) => {
          downloadedLength += chunk.length;
          if (totalLength) {
            const percent = Math.floor((downloadedLength / totalLength) * 100);
            process.stdout.write(`\r下载进度：${percent}% (${(downloadedLength / 1024 / 1024).toFixed(2)}MB/${(totalLength / 1024 / 1024).toFixed(2)}MB)`);
          }
        });
        
        response.pipe(fileStream);
        
        fileStream.on('finish', () => {
          process.stdout.write('\n'); // 换行
          fileStream.close();
          resolve(filePath);
        });
        
        fileStream.on('error', (err) => {
          fs.unlink(filePath, () => {}); // 发生错误时删除文件
          reject(err);
        });
      }).on('error', (err) => {
        fs.unlink(filePath, () => {}); // 发生错误时删除文件
        reject(err);
      });
    });
    
    console.log(`歌曲下载完成：${filePath}`);
    return filePath;
  } catch (error) {
    console.error('下载歌曲时发生错误：', error.message);
    return null;
  }
}

/**
 * 简化版备用解析器（通过第三方API）
 * @param {string} songName - 歌曲名称
 * @param {string} artistName - 艺术家名称
 * @returns {Promise<string|null>} 歌曲URL
 */
async function parseAlternativeSource(songName, artistName) {
  try {
    // 使用一个免费的第三方音乐搜索API
    // 注意：这只是一个示例，实际使用时可能需要更换API
    const searchQuery = encodeURIComponent(`${songName} ${artistName}`);
    const apiUrl = `https://music-api.gdstudio.xyz/api.php?types=search&source=netease&name=${searchQuery}&count=1&pages=1`;
    
    console.log('尝试使用备用音源...');
    const searchRes = await axios.get(apiUrl, { timeout: 5000 });
    
    if (Array.isArray(searchRes.data) && searchRes.data.length > 0) {
      const song = searchRes.data[0];
      if (song && song.id) {
        // 获取URL
        const urlRes = await axios.get(
          `https://music-api.gdstudio.xyz/api.php?types=url&source=netease&id=${song.id}&br=320`,
          { timeout: 5000 }
        );
        
        if (urlRes.data && urlRes.data.url) {
          return urlRes.data.url;
        }
      }
    }
    return null;
  } catch (error) {
    console.error('备用解析失败：', error.message);
    return null;
  }
}

/**
 * 主函数：搜索并下载歌曲
 * @param {string} keyword - 搜索关键词
 * @param {number} index - 选择第几个搜索结果，默认第一个
 */
async function main(keyword, index = 0) {
  console.log(`========== 网易云音乐爬虫 ==========`);
  
  // 1. 搜索歌曲
  const songs = await searchSongs(keyword);
  
  if (songs.length === 0) {
    console.log('未找到相关歌曲');
    return;
  }
  
  // 2. 显示搜索结果
  console.log('\n搜索结果：');
  songs.forEach((song, idx) => {
    console.log(`${idx + 1}. ${song.name} - ${song.artists} (${song.album})`);
  });
  
  // 3. 选择歌曲
  if (index < 0 || index >= songs.length) {
    console.log('无效的索引');
    return;
  }
  
  const selectedSong = songs[index];
  console.log(`\n已选择：${selectedSong.name} - ${selectedSong.artists}`);
  
  // 4. 获取歌曲URL
  let songUrl = await getSongUrl(selectedSong.id);
  
  // 如果无法获取，尝试备用解析
  if (!songUrl) {
    console.log('尝试备用解析...');
    songUrl = await parseAlternativeSource(selectedSong.name, selectedSong.artists);
  }
  
  if (!songUrl) {
    console.log('无法获取歌曲URL，请尝试其他歌曲');
    return;
  }
  
  // 5. 下载歌曲
  const filename = `${selectedSong.name} - ${selectedSong.artists}.mp3`;
  const savePath = await downloadSong(songUrl, filename);
  
  if (savePath) {
    console.log(`\n✅ 歌曲已成功下载到：${savePath}`);
  }
}

// 导出函数供其他模块使用
module.exports = {
  searchSongs,
  getSongUrl,
  downloadSong,
  parseAlternativeSource,
  main
};

// 如果直接运行此脚本
if (require.main === module) {
  // 使用命令行参数传入搜索关键词，示例：node simple_music_crawler.js "周杰伦 稻香" 0
  // 第一个参数是搜索关键词，第二个参数是选择的结果索引（可选，默认为0）
  const keyword = process.argv[2] || '周杰伦 稻香';
  const index = parseInt(process.argv[3]) || 0;
  main(keyword, index);
}