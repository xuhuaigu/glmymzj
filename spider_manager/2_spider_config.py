# spider_manager/2_spider_config.py
import streamlit as st
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

st.title("⚙️ 爬虫配置管理")

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "spider_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "request_delay": 1.5,  # 请求延迟（秒）
    "max_retries": 3,
    "timeout": 30,
    "max_pages_per_category": 50,  # 每个分类最大页数
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    },
    "output_format": "excel",  # excel, csv, json
    "save_path": "./spider_data",
    "target_urls": [
        "https://www.100ppi.com/mprice/plist-1-86-1.html",
        "https://www.100ppi.com/mprice/plist-1-1090-1.html",
        "https://www.100ppi.com/mprice/plist-1-3107-1.html",
        "https://www.100ppi.com/mprice/plist-1-83-1.html",
        "https://www.100ppi.com/mprice/plist-1-81-1.html",
        "https://www.100ppi.com/mprice/plist-1-837-1.html",
        "https://www.100ppi.com/mprice/plist-1-2309-1.html",
        "https://www.100ppi.com/mprice/plist-1-9071-1.html",
        "https://www.100ppi.com/mprice/plist-1-490-1.html",
        "https://www.100ppi.com/mprice/plist-1-11234-1.html"
    ]
}

# 加载配置
def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

# 保存配置
def save_config(config):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 重置配置
def reset_config():
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

# 当前配置
config = load_config()

# ==================== 基础爬虫配置 ====================
st.subheader("🔧 基础爬虫配置")

col1, col2 = st.columns(2)
with col1:
    user_agent = st.text_input(
        "User-Agent", 
        config.get("user_agent", DEFAULT_CONFIG["user_agent"]),
        help="浏览器标识，用于模拟真实浏览器访问"
    )
    request_delay = st.slider(
        "请求延迟（秒）", 
        0.5, 5.0, 
        config.get("request_delay", 1.5), 
        0.5,
        help="每个页面请求之间的延迟时间，避免被反爬"
    )
    max_pages = st.number_input(
        "每个分类最大页数", 
        min_value=10, 
        max_value=100, 
        value=config.get("max_pages_per_category", 50),
        step=10,
        help="每个商品分类最多爬取多少页"
    )

with col2:
    max_retries = st.number_input(
        "最大重试次数", 
        1, 10, 
        config.get("max_retries", 3),
        help="请求失败时的重试次数"
    )
    timeout = st.number_input(
        "超时时间（秒）", 
        10, 120, 
        config.get("timeout", 30),
        help="每个请求的超时时间"
    )
    output_format = st.selectbox(
        "输出格式",
        ["excel", "csv", "json"],
        index=["excel", "csv", "json"].index(config.get("output_format", "excel")),
        help="数据保存的文件格式"
    )

st.divider()

# ==================== 保存路径配置 ====================
st.subheader("💾 保存路径配置")

save_path = st.text_input(
    "数据保存路径",
    config.get("save_path", "./spider_data"),
    help="爬取数据的保存目录（相对路径或绝对路径）"
)

# 创建目录按钮
col1, col2 = st.columns(2)
with col1:
    if st.button("📁 创建保存目录", use_container_width=True):
        Path(save_path).mkdir(parents=True, exist_ok=True)
        st.success(f"目录已创建: {save_path}")
with col2:
    if st.button("📂 打开保存目录", use_container_width=True):
        import os
        if os.path.exists(save_path):
            if os.name == 'nt':  # Windows
                os.startfile(save_path)
            else:
                st.info(f"目录路径: {os.path.abspath(save_path)}")
        else:
            st.warning("目录不存在，请先创建")

st.divider()

# ==================== 目标URL配置 ====================
st.subheader("🔗 目标URL配置")

st.info(f"当前配置了 {len(config.get('target_urls', DEFAULT_CONFIG['target_urls']))} 个目标URL")

with st.expander("📋 查看/编辑目标URL列表", expanded=False):
    urls_text = st.text_area(
        "URL列表（每行一个）",
        value="\n".join(config.get("target_urls", DEFAULT_CONFIG["target_urls"])),
        height=300,
        help="每行一个商品分类的URL"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存URL列表", use_container_width=True):
            new_urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
            config["target_urls"] = new_urls
            save_config(config)
            st.success(f"已保存 {len(new_urls)} 个URL")
            st.rerun()
    
    with col2:
        if st.button("🔄 恢复默认URL列表", use_container_width=True):
            config["target_urls"] = DEFAULT_CONFIG["target_urls"]
            save_config(config)
            st.success("已恢复默认URL列表")
            st.rerun()

st.divider()

# ==================== 请求头配置 ====================
st.subheader("📋 请求头配置")

with st.expander("自定义请求头", expanded=False):
    headers = config.get("headers", DEFAULT_CONFIG["headers"])
    
    headers_json = st.text_area(
        "请求头 (JSON格式)",
        value=json.dumps(headers, ensure_ascii=False, indent=2),
        height=200,
        help="JSON格式的自定义请求头"
    )
    
    try:
        new_headers = json.loads(headers_json) if headers_json else headers
        if st.button("💾 保存请求头", use_container_width=True):
            config["headers"] = new_headers
            save_config(config)
            st.success("请求头已保存")
    except json.JSONDecodeError:
        st.error("JSON格式错误，请检查")

st.divider()

# ==================== 配置操作 ====================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💾 保存所有配置", type="primary", use_container_width=True):
        # 收集所有配置
        new_config = {
            "user_agent": user_agent,
            "request_delay": request_delay,
            "max_retries": max_retries,
            "timeout": timeout,
            "max_pages_per_category": max_pages,
            "headers": config.get("headers", DEFAULT_CONFIG["headers"]),
            "output_format": output_format,
            "save_path": save_path,
            "target_urls": config.get("target_urls", DEFAULT_CONFIG["target_urls"])
        }
        save_config(new_config)
        st.success("✅ 所有配置已保存！")
        st.balloons()

with col2:
    if st.button("🔄 重置为默认配置", use_container_width=True):
        config = reset_config()
        st.success("已重置为默认配置")
        st.rerun()

with col3:
    if st.button("📄 导出配置", use_container_width=True):
        config_json = json.dumps(config, ensure_ascii=False, indent=2)
        st.download_button(
            label="下载配置文件",
            data=config_json,
            file_name="spider_config.json",
            mime="application/json",
            key="export_config"
        )

st.divider()

# ==================== 配置预览 ====================
with st.expander("📄 当前完整配置预览"):
    st.json(config)

# ==================== 配置说明 ====================
with st.expander("📖 配置说明"):
    st.markdown("""
    ### 配置项说明
    
    #### 基础爬虫配置
    - **User-Agent**: 浏览器标识，模拟真实浏览器访问
    - **请求延迟**: 每个页面请求之间的等待时间，建议1-3秒
    - **每个分类最大页数**: 每个商品分类最多爬取的页数
    - **最大重试次数**: 请求失败时的重试次数
    - **超时时间**: 每个请求的超时时间（秒）
    - **输出格式**: 数据保存的文件格式（excel/csv/json）
    
    #### 保存路径配置
    - 爬取数据的保存目录，支持相对路径和绝对路径
    
    #### 目标URL配置
    - 需要爬取的商品分类URL列表，每行一个
    
    #### 请求头配置
    - 自定义HTTP请求头，JSON格式
    - 可添加Referer、Cookie等反爬措施
    
    ### 注意事项
    1. 请合理设置请求延迟，避免对目标网站造成压力
    2. 建议使用动态IP或代理池避免被封
    3. 爬取大量数据时请分批进行
    """)