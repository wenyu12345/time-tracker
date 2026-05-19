#!/usr/bin/env python3
"""
Ollama CORS代理服务器
用于解决浏览器CORS限制，让前端可以直接访问本地Ollama服务
"""

import http.server
import socketserver
import requests
import json
import urllib.parse
from urllib.parse import urlparse

class CORSProxyHandler(http.server.SimpleHTTPRequestHandler):
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
        try:
            # 解析路径
            parsed_path = urlparse(self.path)
            
            # 如果是静态文件请求，直接返回文件
            if parsed_path.path.endswith(('.html', '.css', '.js', '.png', '.jpg', '.ico')):
                return super().do_GET()
            
            # 代理到Ollama服务
            ollama_url = f"http://localhost:11434{self.path}"
            
            response = requests.get(ollama_url)
            
            self.send_response(response.status_code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(response.content)
            
        except Exception as e:
            self.send_error(500, f"Proxy error: {str(e)}")
    
    def do_POST(self):
        """处理POST请求"""
        try:
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # 代理到Ollama服务
            ollama_url = f"http://localhost:11434{self.path}"
            
            response = requests.post(
                ollama_url,
                data=post_data,
                headers={'Content-Type': 'application/json'}
            )
            
            self.send_response(response.status_code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(response.content)
            
        except Exception as e:
            self.send_error(500, f"Proxy error: {str(e)}")

if __name__ == "__main__":
    PORT = 8081
    
    with socketserver.TCPServer(("", PORT), CORSProxyHandler) as httpd:
        print(f"CORS代理服务器运行在 http://localhost:{PORT}")
        print("前端可以通过此代理访问Ollama服务，绕过CORS限制")
        print("请访问 http://localhost:8081/ollama-chat-fixed.html")
        print("按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")