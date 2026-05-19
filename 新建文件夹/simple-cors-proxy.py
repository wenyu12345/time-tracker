#!/usr/bin/env python3
"""
简单CORS代理服务器 - 解决Ollama API跨域访问问题
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import json

class CORSProxyHandler(BaseHTTPRequestHandler):
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
            self.handle_proxy_request()
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        """处理POST请求"""
        if self.path.startswith('/proxy/'):
            self.handle_proxy_request()
        else:
            self.send_error(404, "File not found")
    
    def handle_proxy_request(self):
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
            
            # 准备请求头
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'content-length', 'connection']:
                    headers[key] = value
            
            # 发送请求到Ollama
            req = urllib.request.Request(target_url, data=post_data, headers=headers)
            
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
    
    server = HTTPServer(('', PORT), CORSProxyHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()

if __name__ == "__main__":
    main()