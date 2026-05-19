import os
import sys
from dingtalk_robot import send_dingtalk_message

# 直接导入dingtalk_robot模块
print("测试钉钉消息发送...")

# 发送一条简单的文本消息测试
result = send_dingtalk_message("@小艺 测试消息发送")
print(f"发送结果: {result}")

# 检查结果是否包含错误码
if isinstance(result, dict) and result.get('errcode') == 0:
    print("钉钉消息发送成功！")
else:
    print("钉钉消息发送失败！")
