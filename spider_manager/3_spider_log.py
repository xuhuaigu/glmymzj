# spider_manager/3_spider_log.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from spider_manager.spider_core import spider_core

st.title("📋 爬虫运行日志")

# 初始化日志
if 'crawler_logs' not in st.session_state:
    st.session_state.crawler_logs = []

# 获取任务历史
tasks = spider_core.get_tasks()

if tasks:
    st.subheader("📊 任务汇总")
    
    # 统计信息
    completed = len([t for t in tasks if t.status == "completed"])
    running = len([t for t in tasks if t.status == "running"])
    failed = len([t for t in tasks if t.status == "failed"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总任务数", len(tasks))
    with col2:
        st.metric("已完成", completed)
    with col3:
        st.metric("运行中", running)
    with col4:
        st.metric("失败", failed)
    
    st.divider()
    
    # 任务详情表格
    task_data = []
    for task in tasks:
        task_data.append({
            "任务名称": task.name,
            "状态": task.status,
            "数据量": task.total_records,
            "开始时间": task.start_time.strftime("%Y-%m-%d %H:%M:%S") if task.start_time else "",
            "结束时间": task.end_time.strftime("%Y-%m-%d %H:%M:%S") if task.end_time else "",
            "文件": task.file_path.split("/")[-1] if task.file_path else ""
        })
    
    df = pd.DataFrame(task_data)
    st.dataframe(df, use_container_width=True)
    
    # 详细日志
    st.subheader("📝 详细日志")
    
    # 选择要查看的任务
    selected_task = st.selectbox("选择任务查看日志", [t.name for t in tasks])
    
    if selected_task:
        st.info(f"任务「{selected_task}」的运行日志（模拟数据，实际可接入真实日志）")
        
        # 模拟日志内容
        logs = [
            f"[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务「{selected_task}」开始执行",
            f"[INFO] 目标日期: {datetime.now().strftime('%Y-%m-%d')}",
            f"[INFO] 开始爬取第1个商品分类...",
            f"[INFO] 第1个分类爬取完成，获取数据 15 条",
            f"[INFO] 开始爬取第2个商品分类...",
            f"[INFO] 第2个分类爬取完成，获取数据 23 条",
            f"[INFO] 继续爬取剩余分类...",
            f"[SUCCESS] 任务「{selected_task}」执行完成，共获取数据 {sum([t.total_records for t in tasks if t.name == selected_task])} 条",
            f"[INFO] 文件已保存至 spider_data 目录"
        ]
        
        for log in logs:
            if "[INFO]" in log:
                st.info(log)
            elif "[SUCCESS]" in log:
                st.success(log)
            elif "[WARNING]" in log:
                st.warning(log)
            elif "[ERROR]" in log:
                st.error(log)
            else:
                st.text(log)

else:
    st.info("暂无任务记录，请先在「爬虫任务」页面创建并运行爬虫任务")