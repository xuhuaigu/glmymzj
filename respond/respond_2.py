# respond/respond_1.py
import streamlit as st
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from data_processing import data_loader, data_exporter

st.set_page_config(page_title="数据概览", page_icon="📊", layout="wide")

# ==================== 页面标题 ====================
st.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
    <h1 style="margin: 0;">📊 数据概览</h1>
    <span style="background: #e8f4fd; padding: 4px 12px; border-radius: 20px; font-size: 14px; color: #0066cc;">
        🙍🏻 数据管理
    </span>
</div>
""", unsafe_allow_html=True)

# ==================== 初始化状态 ====================
if 'df' not in st.session_state:
    st.session_state.df = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# ==================== 数据加载区域 ====================
with st.expander("📂 加载数据", expanded=not st.session_state.data_loaded):
    data_source = st.radio(
        "选择数据源",
        ["示例数据", "上传CSV", "上传Excel", "上传数据库"],
        horizontal=True,
        key="data_source_radio"
    )
    
    if data_source == "示例数据":
        col1, col2 = st.columns([1, 3])
        with col1:
            n_rows = st.number_input("样本数量", min_value=100, max_value=10000, value=1000, step=100, key="n_rows_input")
        with col2:
            if st.button("📊 加载示例数据", type="primary", use_container_width=True, key="load_sample_btn"):
                with st.spinner("正在生成示例数据..."):
                    df = data_loader.load_sample_data(n_rows=n_rows)
                    st.session_state.df = df
                    st.session_state.data_loaded = True
                    st.success(f"✅ 已成功加载 {len(df):,} 行数据")
                    st.rerun()
    
    elif data_source == "上传CSV":
        uploaded_file = st.file_uploader("选择CSV文件", type=['csv'], key="csv_uploader")
        if uploaded_file is not None:
            if st.button("📥 加载CSV文件", type="primary", use_container_width=True):
                with st.spinner("正在解析CSV文件..."):
                    df = data_loader.load_from_csv(uploaded_file)
                    if df is not None:
                        st.session_state.df = df
                        st.session_state.data_loaded = True
                        st.success(f"✅ 已成功加载 {len(df):,} 行数据")
                        st.rerun()
    
    elif data_source == "上传Excel":
        uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'], key="excel_uploader")
        if uploaded_file is not None:
            if st.button("📥 加载Excel文件", type="primary", use_container_width=True):
                with st.spinner("正在解析Excel文件..."):
                    df = data_loader.load_from_excel(uploaded_file)
                    if df is not None:
                        st.session_state.df = df
                        st.session_state.data_loaded = True
                        st.success(f"✅ 已成功加载 {len(df):,} 行数据")
                        st.rerun()
    
    else:  # 上传数据库
        st.markdown("##### 🔌 数据库连接")
        
        # 数据库配置选择
        available_dbs = data_loader.get_available_databases()
        if available_dbs:
            config_name = st.selectbox(
                "选择数据库配置",
                options=available_dbs,
                format_func=lambda x: x.replace('_', ' ').title(),
                key="db_config_select"
            )
        else:
            st.warning("未找到数据库配置，请检查 .streamlit/secrets.toml")
            config_name = None
        
        if config_name:
            # 模式选择（Oracle特有）
            schemas = ["CQ", "DWD", "DWS", "DIM", "ADS"]
            selected_schema = st.selectbox("选择模式 (Schema)", schemas, index=0, key="schema_select")
            
            # 获取表列表
            with st.spinner("正在获取表列表..."):
                try:
                    # 注意：这里假设 data_loader.get_database_tables 支持 schema 参数
                    # 如果当前版本不支持，需要先调用 data_loader.set_schema(selected_schema) 或修改函数
                    tables = data_loader.get_database_tables(config_name=config_name, schema=selected_schema)
                except TypeError:
                    # 如果 get_database_tables 不支持 schema 参数，则先设置模式（需自行实现）
                    st.error("当前 data_loader 版本不支持 schema 参数，请升级或修改代码。")
                    tables = []
            
            if tables:
                st.success(f"✅ 连接成功！找到 {len(tables):,} 个表")
                
                # 表选择器（带搜索）
                selected_table = st.selectbox(
                    "选择要分析的数据表",
                    options=[""] + tables,  # 添加一个空选项，让用户主动选择
                    format_func=lambda x: x if x else "请选择...",
                    key="table_selector"
                )
                st.session_state.selected_table = selected_schema + '_' + selected_table  # ✅ 保存到 session_state
                
                if selected_table:
                    # 数据加载选项
                    col1, col2 = st.columns(2)
                    with col1:
                        load_all = st.checkbox("加载全部数据", value=False, help="注意：大表可能加载较慢")
                    with col2:
                        if not load_all:
                            limit_rows = st.number_input("限制行数", min_value=100, max_value=100000, value=1000, step=100, key="limit_rows_input")
                        else:
                            limit_rows = None
                    
                    # 自定义SQL
                    use_custom_sql = st.checkbox("使用自定义SQL查询", key="use_custom_sql")
                    custom_query = None
                    if use_custom_sql:
                        custom_query = st.text_area(
                            "输入SQL查询语句",
                            placeholder=f"SELECT * FROM {selected_schema}.{selected_table} WHERE ROWNUM <= 1000",
                            height=100,
                            key="custom_query_input"
                        )
                    
                    # 加载按钮
                    if st.button("📥 从数据库加载数据", type="primary", use_container_width=True, key="load_db_btn"):
                        with st.spinner("正在从数据库加载数据..."):
                            try:
                                if use_custom_sql and custom_query:
                                    df = data_loader.execute_custom_query(custom_query, config_name=config_name)
                                else:
                                    df = data_loader.load_from_database(
                                        f"{selected_schema}.{selected_table}" if selected_schema else selected_table,
                                        limit=limit_rows,
                                        config_name=config_name
                                    )
                                
                                if df is not None:
                                    st.session_state.df = df
                                    st.session_state.data_loaded = True
                                    st.session_state.last_table = selected_table
                                    st.success(f"✅ 已成功加载 {len(df):,} 行数据")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"加载数据失败: {e}")
            else:
                st.warning("未找到任何表，请检查模式或数据库配置")

# ==================== 数据显示区域 ====================
if st.session_state.df is not None:
    df = st.session_state.df
    
    # ----- 数据概览卡片 -----
    st.markdown("---")
    st.subheader("📈 数据概览")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 数据行数", f"{len(df):,}")
    with col2:
        st.metric("📋 数据列数", len(df.columns))
    with col3:
        missing_total = df.isnull().sum().sum()
        missing_pct = (missing_total / (len(df) * len(df.columns)) * 100) if len(df) > 0 else 0
        st.metric("⚠️ 缺失值", f"{missing_total:,}", delta=f"{missing_pct:.1f}%", delta_color="inverse")
    with col4:
        mem = df.memory_usage(deep=True).sum() / 1024 / 1024
        st.metric("💾 内存使用", f"{mem:.2f} MB")
    
    # ----- 数据预览 -----
    with st.expander("🔍 数据预览", expanded=False):
        preview_rows = st.selectbox("预览行数", [5, 10, 20, 50, 100], index=1, key="preview_rows")
        st.dataframe(df.head(preview_rows), use_container_width=True)
    
    # ----- 列信息 -----
    with st.expander("📝 列信息", expanded=False):
        dtype_df = pd.DataFrame({
            '列名': df.columns,
            '数据类型': df.dtypes.astype(str).values,
            '非空值数': df.count().values,
            '空值数': df.isnull().sum().values,
            '空值比例(%)': (df.isnull().sum() / len(df) * 100).round(2).values,
            '唯一值数': df.nunique().values
        })
        st.dataframe(dtype_df, use_container_width=True)
    
    # ----- 描述性统计 -----
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        with st.expander("📐 描述性统计", expanded=False):
            st.dataframe(df[numeric_cols].describe(), use_container_width=True)
    
    # ----- 快速分析：数值列分布（可选） -----
    if numeric_cols and len(numeric_cols) <= 10:
        with st.expander("📊 数值列分布", expanded=False):
            selected_col = st.selectbox("选择列查看分布", numeric_cols, key="dist_col")
            if selected_col:
                fig, ax = plt.subplots(figsize=(10, 4))
                df[selected_col].hist(bins=30, ax=ax, color='#1890ff', edgecolor='white')
                ax.set_title(f"{selected_col} 分布")
                ax.set_xlabel(selected_col)
                ax.set_ylabel("频数")
                st.pyplot(fig)
    
    # ----- 导出功能 -----
    st.markdown("---")
    with st.expander("💾 导出数据", expanded=False):
        # data_exporter.set_data(df)
        # data_exporter.export_report(file_name=selected_table, page_key="respond_1")
        table_name = st.session_state.get('selected_table', 'exported_data')
        data_exporter.set_data(df)
        data_exporter.export_report(file_name=table_name, page_key="respond_1")

else:
    st.info("👈 请先在「加载数据」区域选择数据源并加载数据")
    st.markdown("""
    <div style="background: #f6f8fa; border-radius: 8px; padding: 20px; margin-top: 20px;">
        <h4>📌 支持的数据源</h4>
        <ul style="list-style: none; padding-left: 0;">
            <li>✅ <b>示例数据</b> — 自动生成模拟数据用于快速演示</li>
            <li>✅ <b>上传CSV</b> — 支持UTF-8编码的CSV文件</li>
            <li>✅ <b>上传Excel</b> — 支持.xlsx和.xls格式</li>
            <li>✅ <b>上传数据库</b> — 连接Oracle/MySQL数据库，选择表或自定义SQL</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)