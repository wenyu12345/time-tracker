#!/usr/bin/env python3
"""
CORS代理服务器 - 解决Ollama API跨域访问问题
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import sys
from urllib.parse import urlparse

class CORSMiddleware:
    def __init__(self, handler):
        self.handler = handler
    
    def __call__(self, request, client_address):
        return CORSHTTPRequestHandler(request, client_address, self.handler)

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        if self.path.startswith('/proxy/'):
            self.proxy_request()
        else:
            super().do_GET()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path.startswith('/proxy/'):
            self.proxy_request()
        else:
            super().do_POST()
    
    def proxy_request(self):
        """代理请求到Ollama API"""
        try:
            # 解析目标URL
            target_url = self.path[7:]  # 移除'/proxy/'前缀
            
            # 构造完整的Ollama API URL
            if not target_url.startswith('http'):
                target_url = f'http://localhost:11434{target_url}'
            
            print(f"代理请求: {target_url}")
            
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # 准备请求
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'content-length']:
                    headers[key] = value
            
            # 发送请求到Ollama
            req = urllib.request.Request(target_url, data=post_data, headers=headers)
            
            if self.command == 'POST':
                req.method = 'POST'
            
            # 执行请求
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read()
                
                # 设置响应头
                self.send_response(response.getcode())
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                
                # 复制原始响应头
                for key, value in response.headers.items():
                    if key.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(key, value)
                
                self.end_headers()
                
                # 发送响应数据
                self.wfile.write(response_data)
                
                print(f"请求成功: {response.getcode()}")
                
        except Exception as e:
            print(f"代理请求错误: {e}")
            self.send_error(500, f"代理错误: {str(e)}")
    
    def end_headers(self):
        """确保所有响应都包含CORS头"""
        if not self.headers_sent:
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def main():
    PORT = 8080
    
    print(f"启动CORS代理服务器，端口: {PORT}")
    print("代理地址: http://localhost:8080/proxy/")
    print("示例: http://localhost:8080/proxy/api/tags")
    print("按 Ctrl+C 停止服务器")
    
    with socketserver.TCPServer(("", PORT), CORSMiddleware(http.server.SimpleHTTPRequestHandler)) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == "__main__":
    main()