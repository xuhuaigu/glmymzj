# gxglmy/gxglmy1.py
import streamlit as st
from components import NavigationCards

st.set_page_config(page_title="桂柳牧业导航", page_icon="🏠", layout="wide")

# ==================== 页面跳转处理 ====================
query_params = st.query_params
target_page = query_params.get("page", None)

if target_page:
    try:
        st.switch_page(target_page)
    except Exception:
        st.query_params.clear()
        st.rerun()

# ==================== 使用封装的导航卡片组件 ====================

# 创建导航卡片实例
nav = NavigationCards(
    title="🏠 桂柳牧业管理系统",
    subtitle="请选择您要进入的功能模块"
)
nav.render_header()  # ✅ 只渲染一次

# 第一行：养猪网数据分析
nav.add_card("养猪网分析", "🐷", "养猪网数据分析", "data_analysis/9_yangzhuwang_analysis.py")
nav.add_card("数据质量", "📉", "数据质量评估系统", "respond/respond_3.py")
nav.render(cols=6, section_title="养猪网", auto_header=False)
nav.clear() # 清空卡片

# 第二行：生猪&饲料
nav.add_card("生猪分析", "🐷", "养殖数据分析与监控", "data_analysis/7_pig_analysis.py")
nav.add_card("饲料分析", "🌾", "饲料成本与效率", "data_analysis/8_feed_analysis.py")
nav.render(cols=6, section_title="生猪&饲料", auto_header=False, card_width="100%")
nav.clear() # 清空卡片

# 第三行：爬虫&图表
nav.add_card("爬虫管理", "🕷️", "数据采集与任务", "spider_manager/1_spider_list.py")
nav.add_card("时间序列", "⏰", "序列分析与预测", "data_analysis/5_time_series.py")
nav.add_card("爬虫日志", "📋", "查看运行日志", "spider_manager/3_spider_log.py")
nav.add_card("图表分析", "📊", "自定义图表工具", "data_analysis/6_chart_analysis.py")
nav.add_card("爬虫配置", "⚙️", "配置爬虫参数", "spider_manager/2_spider_config.py")
nav.add_card("数据查看", "📅", "查看爬取数据", "spider_manager/4_data_view.py")
# 渲染卡片（每行4个）
nav.render(cols=6, section_title="爬虫", auto_header=False)
nav.clear() # 清空卡片

# 第四行：桂柳牧业
nav.add_card("桂柳牧业", "🐷", "桂柳牧业介绍", "gxglmy/gxglmy2.py")
nav.render(cols=6, section_title="桂柳牧业", auto_header=False)
nav.clear() # 清空卡片

# 第五行：数据处理
nav.add_cards_from_list([
    {"title": "数据概览", "icon": "📊", "description": "查看数据总览与统计", "page_path": "data_analysis/1_data_overview.py"},
    {"title": "数据可视化", "icon": "📈", "description": "图表与可视化分析", "page_path": "data_analysis/2_data_visualization.py"},
    {"title": "统计分析", "icon": "📐", "description": "统计检验与描述", "page_path": "data_analysis/3_statistical_analysis.py"},
    {"title": "相关性分析", "icon": "🔗", "description": "变量关系研究", "page_path": "data_analysis/4_correlation_analysis.py"},
])
nav.render(cols=6, section_title="数据处理", auto_header=False, card_width="100%")
nav.clear() # 清空卡片

# 渲染侧边栏
nav.render_sidebar()