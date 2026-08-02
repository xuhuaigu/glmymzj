# config.py
"""
全局配置文件
存放应用级别的常量、配置和全局变量
"""

import streamlit as st

# ==================== 角色定义 ====================
class Roles:
    """角色常量类"""
    NONE = None
    TESTER = "测试员"
    DB_ADMIN = "数据库管理员"
    SYS_ADMIN = "系统管理员"
    DATA_ANALYST = "数据分析员"
    GLMY = "桂柳牧业"
    
    # 所有角色列表
    ALL = [NONE, TESTER, DB_ADMIN, SYS_ADMIN, DATA_ANALYST, GLMY]
    
    # 角色英文名称映射（用于代码判断）
    EN = {
        TESTER: "tester",
        DB_ADMIN: "db_admin", 
        SYS_ADMIN: "sys_admin",
        DATA_ANALYST: "data_analyst",
        GLMY: "glmy"
    }
    
    # 角色图标映射
    ICONS = {
        TESTER: "🧪",
        DB_ADMIN: "🗄️",
        SYS_ADMIN: "👑",
        DATA_ANALYST: "📊"
    }
    
    # 角色权限级别（数字越大权限越高）
    LEVELS = {
        NONE: 0,
        TESTER: 1,
        DB_ADMIN: 2,
        DATA_ANALYST: 3,
        GLMY: 4,
        SYS_ADMIN: 99
    }
    
    # 数据分析员密码
    DATA_ANALYST_PASSWORD = "123456"

# ==================== 页面配置 ====================
class PageConfig:
    """页面配置常量"""
    TITLE = "桂柳牧业管理系统"
    ICON = ":spider:"
    LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"
    
    # 菜单配置
    MENU_ITEMS = {
        "Get help": "https://www.example.com/help",
        "Report a bug": "https://www.example.com/bug",
        "About": """
        ### 桂柳牧业管理系统
        - 版本: 1.0.0
        - 作者: 桂柳牧业
        - 功能: 爬虫管理、数据分析、数据可视化
        """
    }

# ==================== 爬虫配置 ====================
class SpiderConfig:
    """爬虫配置常量"""
    DEFAULT_MAX_PAGES = 5
    MAX_PAGES_MIN = 1
    MAX_PAGES_MAX = 50
    REQUEST_DELAY = 1.5
    MAX_RETRIES = 3
    TIMEOUT = 30
    DEFAULT_SAVE_PATH = "./spider_data"

# ==================== 页面导航配置 ====================
class NavigationConfig:
    """页面导航配置"""
    
    # 页面分组及对应的角色
    PAGE_GROUPS = {
        "测试页面": {
            "pages": ["request/request_1.py", "request/request_2.py"],
            "roles": [Roles.TESTER, Roles.SYS_ADMIN],
            "key": "test_pages"
        },
        "数据库管理": {
            "pages": ["respond/respond_1.py", "respond/respond_2.py"],
            "roles": [Roles.DB_ADMIN, Roles.SYS_ADMIN],
            "key": "db_pages"
        },
        "系统管理": {
            "pages": ["admin/admin_1.py", "admin/admin_2.py"],
            "roles": [Roles.SYS_ADMIN],
            "key": "admin_pages"
        },
        "数据分析": {
            "pages": [
                "data_analysis/1_data_overview.py",
                "data_analysis/2_data_visualization.py",
                "data_analysis/3_statistical_analysis.py",
                "data_analysis/4_correlation_analysis.py",
                "data_analysis/5_time_series.py",
                "spider_manager/4_data_view.py"  # 数据分析员只能查看数据
            ],
            "roles": [Roles.DATA_ANALYST],
            "key": "data_pages"
        },
        "爬虫管理": {
            "pages": [
                "spider_manager/1_spider_list.py",
                "spider_manager/2_spider_config.py",
                "spider_manager/3_spider_log.py",
                "spider_manager/4_data_view.py"
            ],
            "roles": [Roles.SYS_ADMIN],
            "key": "spider_pages"
        }
    }
    
    # 设置页面
    SETTINGS_PAGE = "settings.py"
    LOGOUT_PAGE = "logout"

# ==================== 辅助函数 ====================
def get_role_icon(role: str) -> str:
    """获取角色的图标"""
    return Roles.ICONS.get(role, "👤")

def has_permission(role: str, required_level: int) -> bool:
    """检查角色是否有权限"""
    return Roles.LEVELS.get(role, 0) >= required_level

def init_session_state():
    """初始化 session_state 中的全局变量"""
    if "role" not in st.session_state:
        st.session_state.role = Roles.NONE # 默认角色为空

# ==================== 导出列表 ====================
__all__ = [
    'Roles',
    'PageConfig', 
    'SpiderConfig',
    'NavigationConfig',
    'get_role_icon',
    'has_permission',
    'init_session_state'
]