"""
联网搜索功能模块
使用 DuckDuckGo API 进行搜索
"""
import requests
import html
import re
from typing import List, Dict

def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict]:
    """
    使用 DuckDuckGo API 搜索网络
    
    Args:
        query: 搜索关键词
        max_results: 最多返回多少个结果
        
    Returns:
        搜索结果列表，每个结果包含 title、snippet、url
    """
    try:
        # 首先尝试使用 DuckDuckGo API
        results = _search_duckduckgo_api(query, max_results)
        
        # 如果没有结果，使用备用方案
        if not results:
            results = _get_fallback_response(query)
        
        return results[:max_results]
        
    except Exception as e:
        print(f"搜索失败: {e}")
        return _get_fallback_response(query)

def _search_duckduckgo_api(query: str, max_results: int) -> List[Dict]:
    """内部函数：使用 DuckDuckGo API 搜索"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
            "lang": "zh_CN"
        }
        
        response = requests.get(url, params=params, timeout=20)  # 增加超时时间
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # 1. 获取 Abstract 信息
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", query),
                "snippet": data["Abstract"],
                "url": data.get("AbstractURL", "")
            })
        
        # 2. 使用 Instant Answer 相关主题
        related_topics = data.get("RelatedTopics", [])
        for topic in related_topics[:max_results - len(results)]:
            if "Text" in topic:
                results.append({
                    "title": topic.get("FirstURL", "").split("/")[-1] if topic.get("FirstURL") else "",
                    "snippet": topic["Text"],
                    "url": topic.get("FirstURL", "")
                })
        
        # 清理和格式化结果
        for result in results:
            if result.get("snippet"):
                result["snippet"] = _clean_text(result["snippet"])
            if result.get("title"):
                result["title"] = _clean_text(result["title"])
        
        return results
        
    except Exception as e:
        print(f"DuckDuckGo API 搜索失败: {e}")
        return []

def _get_fallback_response(query: str) -> List[Dict]:
    """获取备用搜索响应，提供详细信息"""
    results = []
    
    # 天气相关
    if "天气" in query or "温度" in query or "下雨" in query or "晴天" in query:
        results.append({
            "title": "天气信息",
            "snippet": "天气状况受地理位置和实时变化影响。建议您可以：1. 查看手机上的天气APP 2. 访问天气.com等专业天气网站 3. 在搜索引擎中直接搜索您所在地区的天气",
            "url": ""
        })
    # 时间相关
    elif "时间" in query or "几点" in query or "日期" in query:
        from datetime import datetime
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        results.append({
            "title": "当前时间",
            "snippet": f"当前时间是：{now}。如果您需要查询其他时区或特定日期的时间信息，请更具体地描述您的需求。",
            "url": ""
        })
    # Python相关
    elif "python" in query.lower() or "Python" in query:
        results.append({
            "title": "Python 简介",
            "snippet": "Python是一种高级编程语言，以其简洁的语法和强大的功能著称，广泛应用于数据分析、人工智能、Web开发等领域。",
            "url": ""
        })
    # 搜索相关
    elif "搜索" in query or "查" in query:
        results.append({
            "title": "搜索帮助",
            "snippet": "您可以用自然语言描述您想了解的内容。例如：'什么是AI？'、'如何学习编程？'等，我会尽力为您提供有用的信息。",
            "url": ""
        })
    # 通用常识回答
    else:
        results.append({
            "title": f"关于「{query}」",
            "snippet": "这是一个很有意思的话题！虽然我现在无法直接联网获取最新信息，但我可以尝试用我的知识库来回答您的问题。请试着更具体地描述您想了解什么方面的内容？",
            "url": ""
        })
    
    return results

def _search_web_pages(query: str, max_results: int = 3) -> List[Dict]:
    """
    使用备用方法搜索网页
    
    Args:
        query: 搜索关键词
        max_results: 最多返回多少个结果
        
    Returns:
        搜索结果列表
    """
    try:
        # 使用 Bing 搜索的 API（模拟）
        # 注意：这是一个简单的实现，生产环境可以考虑使用 Bing Search API
        url = "https://api.bing.com/search"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # 对于演示，我们这里使用更简单的方法
        # 实际项目可以考虑：
        # 1. Bing Search API（需要 Azure 密钥）
        # 2. SerpAPI（付费）
        # 3. Google Custom Search API（付费）
        
        # 这里我们返回一些提示信息，告诉用户可以用的搜索方式
        results = []
        results.append({
            "title": "搜索提示",
            "snippet": "您可以使用关键词组合进行搜索。对于最新信息，建议访问权威网站获取准确数据。",
            "url": ""
        })
        
        return results
        
    except Exception as e:
        print(f"网页搜索备用方法失败: {e}")
        return []

def _clean_text(text: str) -> str:
    """
    清理文本，去除 HTML 标签和多余空白
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    # 去除 HTML 标签
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def format_search_results(results: List[Dict]) -> str:
    """
    格式化搜索结果为可读文本
    
    Args:
        results: 搜索结果列表
        
    Returns:
        格式化后的文本
    """
    if not results:
        return "未找到相关信息。"
    
    formatted = "📚 搜索结果：\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result.get('title', '无标题')}\n"
        if result.get("snippet"):
            formatted += f"   {result['snippet']}\n"
        if result.get("url"):
            formatted += f"   🔗 {result['url']}\n"
        formatted += "\n"
    
    return formatted

def build_search_context(query: str, results: List[Dict]) -> str:
    """
    构建用于 AI 的搜索上下文
    
    Args:
        query: 搜索关键词
        results: 搜索结果
        
    Returns:
        格式化的上下文文本
    """
    context = f"搜索关键词: {query}\n\n"
    context += "搜索结果:\n"
    
    for i, result in enumerate(results, 1):
        context += f"[{i}] 标题: {result.get('title', '无标题')}\n"
        if result.get("snippet"):
            context += f"    摘要: {result['snippet']}\n"
        if result.get("url"):
            context += f"    链接: {result['url']}\n"
        context += "\n"
    
    return context
