// 文件上传表单处理
// 优化：延迟加载非关键功能
document.addEventListener('DOMContentLoaded', function() {
    // 延迟加载图表相关功能
    setTimeout(function() {
        initializeAdvancedFeatures();
    }, 1000);

    // 监听网络状态变化（优化：使用节流）
    if ('connection' in navigator) {
        const updateConnectionStatus = throttle(function() {
            const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            if (connection) {
                console.log('网络状态变化:', connection.effectiveType, connection.downlink);
                // 根据网络状态调整上传策略
                if (connection.effectiveType === '2g' || connection.effectiveType === 'slow-2g') {
                    console.log('检测到慢速网络，启用优化模式');
                    // 可以在这里添加慢速网络的优化策略
                }
            }
        }, 1000);
        
        navigator.connection.addEventListener('change', updateConnectionStatus);
    }
    
    // 文件上传表单提交（优化：添加防抖）
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        const debouncedSubmit = debounce(function(e) {
            handleUploadSubmit(e);
        }, 300);
        
        uploadForm.addEventListener('submit', debouncedSubmit);
    }
    
    // 分析表单提交
    const analyzeForm = document.getElementById('analyze-form');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> 分析中...';
        });
    }
    
    // 其他模式按钮处理
    const honglianBtn = document.getElementById('honglian-mode-btn');
    if (honglianBtn) {
        honglianBtn.addEventListener('click', function() {
            document.getElementById('mode').value = 'honglian';
            document.getElementById('upload-form').submit();
        });
    }
    

    
    // 时间选项切换
    const timeOptions = document.querySelectorAll('input[name="time_option"]');
    timeOptions.forEach(option => {
        option.addEventListener('change', function() {
            const shiftSelector = document.getElementById('shift-selector');
            const customTime = document.getElementById('custom-time');
            
            // 隐藏所有选项
            if (shiftSelector) shiftSelector.style.display = 'none';
            if (customTime) customTime.style.display = 'none';
            
            // 显示对应选项
            if (this.value === 'shift' && shiftSelector) {
                shiftSelector.style.display = 'block';
            } else if (this.value === 'custom' && customTime) {
                customTime.style.display = 'block';
            }
        });
    });
    
    // 清理移动端上传进度提示
    window.addEventListener('beforeunload', function() {
        const progressDiv = document.getElementById('mobile-upload-progress');
        if (progressDiv) {
            progressDiv.remove();
        }
    });
    
    // 数据预览表格处理
    const previewTable = document.querySelector('.preview-container table');
    if (previewTable) {
        // 添加表格样式和响应式处理
        previewTable.classList.add('table', 'table-striped', 'table-hover');
        
        // 限制表格列宽
        const thElements = previewTable.querySelectorAll('th');
        thElements.forEach(th => {
            th.style.maxWidth = '200px';
            th.style.overflow = 'hidden';
            th.style.textOverflow = 'ellipsis';
            th.style.whiteSpace = 'nowrap';
        });
    }
    
    // 图表容器处理
    const chartItems = document.querySelectorAll('.chart-item');
    chartItems.forEach(item => {
        const img = item.querySelector('img');
        if (img) {
            // 图表加载处理
            img.style.display = 'none';
            
            const loading = document.createElement('div');
            loading.className = 'loading';
            loading.style.margin = '20px auto';
            item.appendChild(loading);
            
            img.onload = function() {
                loading.remove();
                img.style.display = 'block';
            };
            
            // 图表点击放大功能
            img.addEventListener('click', function() {
                if (this.classList.contains('expanded')) {
                    this.classList.remove('expanded');
                    this.style.cursor = 'zoom-in';
                } else {
                    this.classList.add('expanded');
                    this.style.cursor = 'zoom-out';
                    this.style.position = 'relative';
                    this.style.zIndex = '1000';
                    this.style.transform = 'scale(1.5)';
                    this.style.transition = 'transform 0.3s';
                    this.style.boxShadow = '0 4px 20px rgba(0,0,0,0.2)';
                }
            });
        }
    });
    
    // 开红莲模式按钮处理
    const honglianModeBtn = document.getElementById('honglian-mode-btn');
    if (honglianModeBtn) {
        honglianModeBtn.addEventListener('click', function() {
            const modeInput = document.getElementById('mode');
            modeInput.value = 'honglian';
            const uploadForm = document.getElementById('upload-form');
            uploadForm.submit();
        });
    }
    
    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // 自动隐藏消息
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        });
    }, 5000);
    
    // 数据质量指标显示
    const qualityReport = document.querySelector('.quality-report');
    if (qualityReport) {
        // 为质量报告添加可视化标记
        const cells = qualityReport.querySelectorAll('td');
        cells.forEach(cell => {
            // 处理缺失值百分比
            if (cell.textContent.includes('%')) {
                const percentage = parseFloat(cell.textContent);
                if (percentage > 50) {
                    cell.style.backgroundColor = '#ffdddd';
                } else if (percentage > 10) {
                    cell.style.backgroundColor = '#fff3cd';
                }
            }
        });
    }
    
}); // DOMContentLoaded 结束

// 延迟初始化高级功能
function initializeAdvancedFeatures() {
    console.log('初始化高级功能...');
    // 这里可以添加图表、复杂交互等功能的初始化
}

// 优化：防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 优化：节流函数  
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 处理上传提交（分离函数）
function handleUploadSubmit(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('file');
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    if (!fileInput.files.length) {
        alert('请选择一个文件');
        return;
    }
    
    const file = fileInput.files[0];
    console.log('文件信息:', {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
    });
    
    // 验证文件类型
    const allowedTypes = ['xlsx', 'xls', 'csv'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        alert('不支持的文件类型，请上传Excel或CSV文件');
        return;
    }
    
    // 文件大小检查（50MB限制）
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        alert('文件大小超过50MB限制');
        return;
    }
    
    // 显示加载状态
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading"></span> 处理中...';
    
    // 移动端网络检测提示
    if (navigator.connection && navigator.connection.effectiveType) {
        const connection = navigator.connection.effectiveType;
        if (connection === '2g' || connection === 'slow-2g') {
            alert('📱 检测到慢速网络，建议使用WiFi上传大文件');
        }
    }
    
    // 移动端文件上传兼容性处理
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        console.log('检测到移动设备，启用移动端上传模式');
        
        // 检查文件大小，移动端建议小于10MB
        if (file.size > 10 * 1024 * 1024) {
            if (!confirm('📱 文件较大 (' + Math.round(file.size / 1024 / 1024) + 'MB)，移动设备上传可能较慢。是否继续？')) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '上传并分析';
                return;
            }
        }
        
        // 设置更长的超时时间
        e.target.setAttribute('data-mobile-upload', 'true');
        
        // 显示上传进度提示
        const progressDiv = document.createElement('div');
        progressDiv.id = 'mobile-upload-progress';
        progressDiv.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.8); color: white; padding: 20px; border-radius: 10px; z-index: 9999; text-align: center;';
        progressDiv.innerHTML = '<div class="spinner"></div><p>正在上传文件，请稍候...</p>';
        document.body.appendChild(progressDiv);
        
        // 添加旋转动画
        const style = document.createElement('style');
        style.textContent = '.spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 0 auto 10px; } @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
        document.head.appendChild(style);
    }
    
    console.log('表单提交开始，文件名:', file.name);
    
    // 实际提交表单
    e.target.submit();
}