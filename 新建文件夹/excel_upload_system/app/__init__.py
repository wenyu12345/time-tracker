from flask import Flask
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用实例
app = Flask(__name__)

# 配置上传文件夹
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

# 配置 session secret key（用于红莲模式等功能）
app.config['SECRET_KEY'] = 'honglian_mode_secret_key_2026_may_19'

# 注册蓝图 - 但先检查是否有其他蓝图需要注册
try:
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
except ImportError:
    pass

# 注册工艺文件蓝图
try:
    from app.routes.process_files import process_files_bp
    app.register_blueprint(process_files_bp, url_prefix='/process_files')
except ImportError:
    pass

# 注册模板管理蓝图
try:
    from app.routes.template_manager import template_manager_bp
    app.register_blueprint(template_manager_bp, url_prefix='/template')
except ImportError:
    pass

# 注册员工工装蓝图
try:
    from app.routes.employee_uniform import employee_uniform_bp
    app.register_blueprint(employee_uniform_bp)
except ImportError:
    pass

# 注册卷径计算蓝图
try:
    from app.routes.coil_calculator import coil_calculator_bp
    app.register_blueprint(coil_calculator_bp)
except ImportError:
    pass

def create_app():
    """Flask应用工厂（与现有系统兼容）"""
    return app
