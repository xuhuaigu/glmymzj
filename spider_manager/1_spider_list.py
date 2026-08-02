# spider_manager/1_spider_list.py
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import time
import threading

sys.path.append(str(Path(__file__).parent.parent))

from spider_manager.spider_core import spider_core

st.title("🕷️ 爬虫任务管理")

# 初始化session state
if 'current_task_id' not in st.session_state:
    st.session_state.current_task_id = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'show_detail' not in st.session_state:
    st.session_state.show_detail = False
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False

# ==================== 爬虫控制面板 ====================
st.subheader("🎯 新建爬虫任务")

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        target_date = st.date_input(
            "选择爬取日期",
            value=datetime.now() - timedelta(days=1),
            help="选择要爬取的商品报价日期"
        )
    
    with col2:
        max_pages = st.number_input(
            "每个分类最大页数",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
            help="每天每个类别的数据量通常只有1-2页，建议设置为5页"
        )
    
    save_path = st.text_input(
        "保存路径",
        value="./spider_data"
    )
    
    task_name = st.text_input(
        "任务名称",
        value=f"商品报价_{target_date.strftime('%Y%m%d')}",
        placeholder="输入任务名称"
    )
    
    # 加载配置
    default_urls = spider_core.get_default_urls()
    st.info(f"📋 将爬取 {len(default_urls)} 个商品分类的数据，每个分类最多 {max_pages} 页")
    
    # 启动按钮
    if st.button("🚀 开始爬取", type="primary", use_container_width=True):
        if not task_name:
            st.error("请输入任务名称")
        else:
            # 确保 max_pages 在1-50范围内
            max_pages_value = max(1, min(50, max_pages))
            
            config = {
                'max_pages_per_category': max_pages_value,
                'save_path': save_path,
                'target_urls': default_urls
            }
            task_id = spider_core.create_and_start_task(task_name, target_date, config)
            st.session_state.current_task_id = task_id
            st.session_state.show_detail = True
            st.session_state.stop_requested = False
            st.success(f"任务已启动！每个分类最多爬取 {max_pages_value} 页")
            st.rerun()

st.divider()

# ==================== 当前运行任务监控 ====================
if st.session_state.current_task_id:
    task = spider_core.get_task_status(st.session_state.current_task_id)
    
    if task:
        status = task.get('status', 'unknown')
        
        if status == 'running':
            st.subheader("🔄 实时爬取监控")
            
            # 进度条
            progress = task.get('progress', 0)
            st.progress(progress / 100, text=f"总体进度: {progress}%")
            
            # 任务基本信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("任务名称", task['name'])
            with col2:
                st.metric("目标日期", task['target_date'])
            with col3:
                st.metric("已获取数据", task.get('total_records', 0))
            with col4:
                st.metric("当前处理", task.get('current_category', '等待中')[:25])
            
            # 进度详情
            col1, col2 = st.columns(2)
            with col1:
                processed = task.get('processed_categories', 0)
                total = task.get('total_categories', 0)
                st.metric("分类进度", f"{processed}/{total}")
            with col2:
                st.metric("最大页数/分类", max_pages)
            
            # 控制按钮
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("⏹️ 停止任务", type="secondary", use_container_width=True):
                    spider_core.stop_task(st.session_state.current_task_id)
                    st.session_state.stop_requested = True
                    st.warning("正在停止任务...")
                    st.rerun()
            
            with col2:
                if st.button("🔄 刷新页面", use_container_width=True):
                    st.rerun()
            
            with col3:
                auto_refresh = st.checkbox("自动刷新", value=st.session_state.auto_refresh)
                st.session_state.auto_refresh = auto_refresh
            
            with col4:
                if st.button("📊 查看数据", use_container_width=True):
                    st.switch_page("spider_manager/4_data_view.py")
            
            st.divider()
            
            # ==================== 实时爬取数据展示 ====================
            st.subheader("📊 实时爬取数据")
            
            # 获取当前任务已爬取的数据
            crawled_data = spider_core.get_task_data(st.session_state.current_task_id, limit=100)
            
            if crawled_data:
                import pandas as pd
                df = pd.DataFrame(crawled_data)
                
                # 显示数据统计
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("已爬取记录", len(df))
                with col2:
                    if 'category_name' in df.columns:
                        categories = df['category_name'].nunique()
                        st.metric("已处理分类", categories)
                with col3:
                    st.metric("最后更新", datetime.now().strftime("%H:%M:%S"))
                
                # 数据表格
                with st.expander("📋 查看爬取数据", expanded=True):
                    display_columns = ['category_name', 'product_name', 'price', 'trader', 'publish_time']
                    available_cols = [col for col in display_columns if col in df.columns]
                    if available_cols:
                        st.dataframe(df[available_cols].tail(20), use_container_width=True)
                    else:
                        st.dataframe(df.tail(20), use_container_width=True)
            else:
                st.info("等待数据... 爬虫正在运行中")
            
            st.divider()
            
            # ==================== 实时日志 ====================
            st.subheader("📝 实时运行日志")
            log_container = st.container(height=200)
            
            logs = spider_core.get_task_logs(st.session_state.current_task_id, limit=30)
            with log_container:
                if logs:
                    for log in logs[::-1]:
                        level = log['level']
                        timestamp = log['timestamp'][:19] if log['timestamp'] else ''
                        message = log['message']
                        
                        if level == "INFO":
                            st.info(f"🟢 [{timestamp}] {message}")
                        elif level == "WARNING":
                            st.warning(f"🟡 [{timestamp}] {message}")
                        elif level == "ERROR":
                            st.error(f"🔴 [{timestamp}] {message}")
                        elif level == "SUCCESS":
                            st.success(f"✅ [{timestamp}] {message}")
                        else:
                            st.text(f"📝 [{timestamp}] {message}")
                else:
                    st.info("等待日志...")
            
            # 自动刷新
            if st.session_state.auto_refresh and not st.session_state.stop_requested:
                time.sleep(2)
                st.rerun()
        
        elif status == 'stopped':
            st.warning(f"⏹️ 任务「{task['name']}」已停止")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 删除任务", use_container_width=True):
                    spider_core.delete_task(st.session_state.current_task_id)
                    st.session_state.current_task_id = None
                    st.rerun()
            with col2:
                if st.button("➕ 新建任务", use_container_width=True):
                    st.session_state.current_task_id = None
                    st.rerun()
        
        elif status == 'completed':
            st.success(f"✅ 任务「{task['name']}」已完成！")
            
            # 显示完成信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总数据量", task.get('total_records', 0))
            with col2:
                file_path = task.get('file_path', '')
                st.metric("保存路径", file_path[:40] + "..." if len(file_path) > 40 else file_path)
            with col3:
                if task.get('end_time'):
                    st.metric("完成时间", task['end_time'][:16])
            
            # 显示所有爬取的数据
            st.subheader("📊 爬取数据汇总")
            crawled_data = spider_core.get_task_data(st.session_state.current_task_id, limit=500)
            if crawled_data:
                import pandas as pd
                df = pd.DataFrame(crawled_data)
                st.dataframe(df, use_container_width=True)
            
            # 下载按钮
            if task.get('file_path') and os.path.exists(task['file_path']):
                with open(task['file_path'], 'rb') as f:
                    st.download_button(
                        label="📥 下载Excel文件",
                        data=f,
                        file_name=task['file_path'].split('/')[-1],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            # 关闭按钮
            if st.button("关闭任务详情"):
                st.session_state.current_task_id = None
                st.rerun()
        
        elif status == 'failed':
            st.error(f"❌ 任务失败: {task.get('error_msg', '未知错误')}")
            if st.button("关闭"):
                st.session_state.current_task_id = None
                st.rerun()

st.divider()

# ==================== 历史任务列表 ====================
st.subheader("📋 历史任务")

tasks = spider_core.get_all_tasks(limit=20)

if tasks:
    for task in tasks:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])
            
            with col1:
                st.write(f"**{task['name']}**")
                st.caption(f"ID: {task['id'][:20]}...")
            
            with col2:
                status = task['status']
                if status == "pending":
                    st.badge("等待中", icon="⏳", color="gray")
                elif status == "running":
                    st.badge("运行中", icon="🔄", color="blue")
                elif status == "completed":
                    st.badge("已完成", icon="✅", color="green")
                elif status == "failed":
                    st.badge("失败", icon="❌", color="red")
                elif status == "stopped":
                    st.badge("已停止", icon="⏹️", color="orange")
                else:
                    st.badge(status, icon="📋")
                st.caption(f"数据: {task.get('total_records', 0)}条")
            
            with col3:
                st.caption(f"目标日期: {task['target_date']}")
                if task.get('start_time'):
                    st.caption(f"开始: {task['start_time'][:16]}")
            
            with col4:
                progress = task.get('progress', 0)
                st.progress(progress / 100, text=f"{progress}%")
            
            with col5:
                # 查看详情按钮
                if st.button("📋 查看", key=f"view_{task['id']}"):
                    st.session_state.current_task_id = task['id']
                    st.rerun()
                
                # 下载按钮（已完成的任务）
                if task['status'] == "completed" and task.get('file_path'):
                    import os
                    if os.path.exists(task['file_path']):
                        with open(task['file_path'], 'rb') as f:
                            st.download_button(
                                label="📥",
                                data=f,
                                file_name=task['file_path'].split('/')[-1],
                                key=f"download_{task['id']}"
                            )
                
                # 删除按钮
                if st.button("🗑️", key=f"delete_{task['id']}"):
                    spider_core.delete_task(task['id'])
                    if st.session_state.current_task_id == task['id']:
                        st.session_state.current_task_id = None
                    st.rerun()
            
            st.divider()
else:
    st.info("暂无历史任务")

# ==================== 使用说明 ====================
with st.expander("📖 使用说明"):
    st.markdown("""
    ### 如何使用爬虫功能
    
    1. **设置爬取参数**
       - 选择要爬取的日期（建议选择昨天，因为当天数据可能未更新）
       - 设置每个分类最大页数（每天数据通常1-2页，建议3-5页）
       - 输入任务名称
    
    2. **启动爬虫**
       - 点击「开始爬取」按钮
       - 任务会在后台运行
    
    3. **实时监控**
       - 可以看到总体进度
       - 实时显示爬取到的数据
       - 实时显示运行日志
    
    4. **停止任务**
       - 点击「停止任务」按钮可以随时停止正在运行的爬虫
       - 停止后可以查看已爬取的数据
    
    5. **刷新页面**
       - 点击「刷新页面」按钮可以手动刷新界面
       - 开启「自动刷新」可以实时查看进度
    
    6. **查看结果**
       - 任务完成后可以下载Excel文件
       - 可以在「数据查看」页面查看所有爬取的数据
    """)