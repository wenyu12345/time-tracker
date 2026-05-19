# 开红莲模式 API 使用文档

## 目录
1. [服务概述](#服务概述)
2. [快速开始](#快速开始)
3. [核心API接口](#核心api接口)
4. [数据结构说明](#数据结构说明)
5. [完整示例](#完整示例)
6. [常见问题](#常见问题)

---

## 服务概述

**开红莲模式**是Excel上传分析系统的专用处理模式，用于处理极片流转数据，支持型号自动映射、车间数据筛选、重量统计汇总等功能。

**服务地址：** 
- 本地访问：`http://localhost:2006`
- 网络访问：`http://<服务器IP>:2006`

**当前版本：** 3.1.0

---

## 快速开始

### 1. 前置条件
- Python 3.7+ 环境
- 安装依赖（运行 `pip install -r requirements.txt`）
- 服务已启动（运行 `python main.py`）

### 2. 基本使用流程
1. 上传Excel/CSV文件 → 2. 系统处理数据 → 3. 查看/筛选结果 → 4. 发送钉钉通知

---

## 核心API接口

### 1. 文件上传接口

**接口地址：** `POST /process`

**功能说明：** 上传Excel/CSV文件并使用开红莲模式处理

**请求参数（Form Data）：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `file` | File | 是 | 上传的文件（支持 .xlsx, .xls, .csv） |
| `mode` | String | 否 | 模式选择，固定值：`honglian` |
| `time_option` | String | 否 | 时间选项：`auto`(自动)、`today`(今天)、`shift`(班次)、`custom`(自定义) |
| `shift_type` | String | 否 | 班次类型（time_option=shift时必填）：`day`(白班)、`night`(夜班) |
| `custom_start` | String | 否 | 自定义开始时间（time_option=custom时必填） |
| `custom_end` | String | 否 | 自定义结束时间（time_option=custom时必填） |

**请求示例（JavaScript）：**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('mode', 'honglian');
formData.append('time_option', 'auto');

fetch('http://localhost:2006/process', {
    method: 'POST',
    body: formData
})
.then(response => {
    if (response.redirected) {
        window.location.href = response.url;
    }
})
.catch(error => console.error('上传失败:', error));
```

**响应说明：**
- 成功：重定向到 `/honglian_result` 结果页面
- 失败：返回错误信息，留在首页

---

### 2. 结果查询接口

**接口地址：** `GET /honglian_result`

**功能说明：** 获取开红莲模式的处理结果，支持多种筛选条件

**请求参数（Query String）：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `汇总型号` | String | 否 | 按汇总型号筛选（支持空格分隔多关键词OR） |
| `工序` | String | 否 | 按工序筛选（支持空格分隔多关键词OR） |
| `批号` | String | 否 | 按批号筛选（支持空格分隔多关键词OR） |
| `重量` | String | 否 | 按重量筛选（支持空格分隔多关键词OR） |
| `原车间` | String | 否 | 按原车间筛选（支持空格分隔多关键词OR） |
| `接收车间` | String | 否 | 按接收车间筛选（支持空格分隔多关键词OR） |
| `exclude_workshop` | String | 否 | 排除指定车间数据，例如：`四二车间` |
| `manual_exclude` | String | 否 | 手动输入需要屏蔽的车间（支持逗号、空格、换行分隔） |
| `page` | Integer | 否 | 页码，默认：1 |
| `page_size` | String/Integer | 否 | 每页条数，`all`表示全部或数字 |

**请求示例：**

```
GET http://localhost:2006/honglian_result?汇总型号=A732&原车间=五一 四一&exclude_workshop=四二车间&page=1&page_size=20
```

**响应数据结构（Session）：**

```javascript
{
  honglian_data: {
    filename: "文件名_时间戳.xlsx",
    columns: ["汇总型号", "工序", "批号", "重量", "原车间", "接收车间"],
    data: [/* 数据列表 */],
    operation_time_range: "2025-05-15 08:00:00 - 2025-05-15 20:00:00"
  },
  honglian_original_data: [/* 完整原始数据 */]
}
```

---

### 3. 发送钉钉通知接口

**接口地址：** `POST /send_to_dingtalk`

**功能说明：** 将红莲模式明细数据发送到钉钉群

**请求参数（JSON）：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `file_name` | String | 是 | 文件名称/标题 |
| `operation` | String | 是 | 操作描述，例如：`红莲模式 明细` |
| `table_data` | Array | 是 | 表格数据数组 |
| `data_count` | Integer | 否 | 数据条数 |
| `page_count` | Integer | 否 | 页数 |
| `image_data` | String | 否 | 图片Base64数据 |
| `image_name` | String | 否 | 图片名称 |

**请求示例（JavaScript）：**

```javascript
const tableData = [
  {
    "汇总型号": "A732正极片",
    "工序": "涂布",
    "批号": "47720250515001",
    "重量": "150.5",
    "原车间": "五一车间",
    "接收车间": "四一车间"
  },
  // ... 更多数据
];

fetch('http://localhost:2006/send_to_dingtalk', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        file_name: '2025-05-15生产数据',
        operation: '红莲模式 明细',
        table_data: tableData,
        data_count: tableData.length
    })
})
.then(response => response.json())
.then(data => {
    if (data.errcode === 0) {
        console.log('发送成功！');
    } else {
        console.error('发送失败:', data.errmsg);
    }
})
.catch(error => console.error('请求失败:', error));
```

**响应数据：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `errcode` | Integer | 错误码，0表示成功，非0表示失败 |
| `errmsg` | String | 错误信息 |

---

### 4. 切换自定义映射接口

**接口地址：** `POST /toggle_custom_mapping`

**功能说明：** 启用或禁用型号自动映射功能

**请求参数（JSON）：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `enabled` | Boolean | 是 | 是否启用自定义映射 |

**请求示例：**

```javascript
fetch('http://localhost:2006/toggle_custom_mapping', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        enabled: true
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('映射状态已更新');
        location.reload(); // 刷新页面
    }
});
```

**响应数据：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `success` | Boolean | 是否成功 |
| `enabled` | Boolean | 当前状态 |

---

### 5. 保存数据修改接口

**接口地址：** `POST /save_honglian_changes`

**功能说明：** 保存编辑后的数据修改

**请求参数（JSON）：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `modified_data` | Object | 是 | 修改的数据对象 |
| `new_rows` | Array | 是 | 新增的数据行数组 |
| `total_changes` | Integer | 否 | 修改总数 |
| `total_new_rows` | Integer | 否 | 新增行数 |

**请求示例：**

```javascript
fetch('http://localhost:2006/save_honglian_changes', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        modified_data: {
            0: {
                "重量": {
                    oldValue: "150.5",
                    newValue: "155.0"
                }
            }
        },
        new_rows: [
            {
                "汇总型号": "A732负极片",
                "工序": "分切",
                "批号": "47720250515002",
                "重量": "200.0",
                "原车间": "四一车间",
                "接收车间": "五一车间"
            }
        ],
        total_changes: 1,
        total_new_rows: 1
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('保存成功！');
    }
});
```

**响应数据：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `success` | Boolean | 是否成功 |
| `message` | String | 提示信息 |

---

## 数据结构说明

### 数据提取字段映射

系统会自动从上传的Excel/CSV文件中识别并提取以下字段：

| 目标字段名 | 可能的原始列名 | 说明 |
|------------|----------------|------|
| `汇总型号` | 型号, 汇总型号, 产品型号, 极片型号 | 极片型号 |
| `工序` | 工序, 工序名称, 工位 | 生产工序 |
| `批号` | 批号, 批次, 批次号, 批次条码 | 产品批号 |
| `重量` | 重量, 净重, 质量, kg, KG | 重量数据 |
| `原车间` | 原车间, 来源车间, 生产车间 | 来源车间 |
| `接收车间` | 接收车间, 目标车间, 去向车间 | 目标车间 |

### 型号映射规则

当前支持的型号映射关系（批号前3位→型号）：

| 批号前缀 | 对应型号 |
|----------|----------|
| 477 | A732负极片 |
| 466 | A732正极片 |
| 467 | A730正极片 |
| 505 | A730负极片 |
| 476 | PF50N1-T正极片 |
| 504 | PF50N1-T负极片 |
| 490 | PF25N1负极片 |
| 472 | PF25N1正极片 |
| B12 | D680-A0N正极片 |
| X07 | D680-A0N负极片 |
| X08 | C951-B负极极片 |
| A04 | C951-B负极极片 |
| X10 | D648负极片 |
| B16 | D648正极片 |
| B17 | D326正极极片 |
| X11 | D326负极片 |
| 468 | C717正极片 |
| A83 | A322正极片 |
| Y38 | A322负极片 |

*注意：映射规则保存在 `data/model_mappings.json` 文件中，可通过管理页面修改*

---

## 完整示例

### 完整流程示例（Python）

```python
import requests
import json

# 配置
BASE_URL = "http://localhost:2006"

def upload_and_process(file_path):
    """上传并处理文件"""
    print(f"正在上传文件: {file_path}")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'mode': 'honglian',
            'time_option': 'auto'
        }
        
        response = requests.post(f"{BASE_URL}/process", files=files, data=data, allow_redirects=False)
        
        if response.status_code == 302:
            print("上传成功！")
            return True
        else:
            print(f"上传失败: {response.status_code}")
            return False

def send_to_dingtalk(table_data, file_name):
    """发送数据到钉钉"""
    payload = {
        "file_name": file_name,
        "operation": "红莲模式 明细",
        "table_data": table_data,
        "data_count": len(table_data)
    }
    
    response = requests.post(
        f"{BASE_URL}/send_to_dingtalk",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    result = response.json()
    if result.get('errcode') == 0:
        print("钉钉通知发送成功！")
        return True
    else:
        print(f"钉钉通知发送失败: {result.get('errmsg')}")
        return False

# 使用示例
if __name__ == "__main__":
    # 1. 上传并处理文件
    success = upload_and_process("生产数据.xlsx")
    
    if success:
        # 2. 准备要发送的数据（实际应用中需要从结果页面获取）
        sample_data = [
            {
                "汇总型号": "A732正极片",
                "工序": "涂布",
                "批号": "47720250515001",
                "重量": "150.5",
                "原车间": "五一车间",
                "接收车间": "四一车间"
            }
        ]
        
        # 3. 发送钉钉通知
        send_to_dingtalk(sample_data, "2025-05-15生产数据")
```

### 完整流程示例（JavaScript）

```javascript
// 配置
const BASE_URL = "http://localhost:2006";

// 文件上传处理
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', 'honglian');
    formData.append('time_option', 'auto');
    
    try {
        const response = await fetch(`${BASE_URL}/process`, {
            method: 'POST',
            body: formData
        });
        
        if (response.redirected) {
            console.log('上传成功！');
            // 页面会自动重定向到结果页
            window.location.href = response.url;
        }
    } catch (error) {
        console.error('上传失败:', error);
    }
}

// 发送钉钉通知
async function sendToDingTalk(tableData, fileName) {
    try {
        const response = await fetch(`${BASE_URL}/send_to_dingtalk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_name: fileName,
                operation: '红莲模式 明细',
                table_data: tableData,
                data_count: tableData.length
            })
        });
        
        const result = await response.json();
        if (result.errcode === 0) {
            console.log('钉钉通知发送成功！');
            return true;
        } else {
            console.error('发送失败:', result.errmsg);
            return false;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return false;
    }
}

// 完整使用示例
document.addEventListener('DOMContentLoaded', function() {
    // 绑定文件上传
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                handleFileUpload(file);
            }
        });
    }
    
    // 发送按钮
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', function() {
            // 获取表格数据
            const tableData = getTableData();
            sendToDingTalk(tableData, '生产数据');
        });
    }
});

// 从表格提取数据
function getTableData() {
    const table = document.getElementById('dataTable');
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    
    return rows.map(row => {
        const rowData = {};
        Array.from(row.cells).forEach((cell, index) => {
            const displaySpan = cell.querySelector('.cell-display');
            rowData[headers[index]] = displaySpan ? displaySpan.textContent.trim() : cell.textContent.trim();
        });
        return rowData;
    });
}
```

---

## 常见问题

### Q1: 服务无法启动？
**A:** 检查端口2006是否被占用，可使用 `netstat -ano | findstr :2006` 检查

### Q2: 文件上传失败？
**A:** 检查文件格式（仅支持 .xlsx, .xls, .csv），文件大小不超过50MB

### Q3: 型号映射不生效？
**A:** 确认已启用自定义映射功能，并检查 `data/model_mappings.json` 文件内容

### Q4: 钉钉通知发送失败？
**A:** 检查钉钉机器人webhook地址配置是否正确，确认网络连接

### Q5: 如何获取处理后的数据？
**A:** 处理完成后页面会重定向到 `/honglian_result`，可以通过页面筛选导出或直接从session获取数据

---

## 附录：型号映射管理

### 查看当前映射
访问：`http://localhost:2006/manage_model_mapping`

### 修改映射规则
1. 访问映射管理页面
2. 添加/删除型号前缀和对应型号
3. 点击保存

---

## 联系支持

如有问题，请查看系统日志文件 `app.log` 或联系开发团队。
