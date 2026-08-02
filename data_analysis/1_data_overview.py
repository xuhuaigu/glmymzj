# respond/respond_1.py
import streamlit as st
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from data_processing import data_loader, data_exporter

st.title("📊 响应页面 - 数据概览")

# 初始化 session_state
if 'df' not in st.session_state:
    st.session_state.df = None

# ==================== 数据加载区域 ====================
with st.expander("📂 加载数据", expanded=st.session_state.df is None):
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
            if st.button("📊 加载示例数据", type="primary", key="load_sample_btn"):
                with st.spinner("正在加载数据..."):
                    df = data_loader.load_sample_data(n_rows=n_rows)
                    st.session_state.df = df
                    st.success(f"✅ 已成功加载 {len(df)} 行数据")
                    st.rerun()
    
    elif data_source == "上传CSV":
        uploaded_file = st.file_uploader("选择CSV文件", type=['csv'], key="csv_uploader")
        if uploaded_file is not None:
            if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
                with st.spinner("正在加载数据..."):
                    df = data_loader.load_from_csv(uploaded_file)
                    if df is not None:
                        st.session_state.df = df
                        st.session_state.last_uploaded_file = uploaded_file.name
                        st.success(f"✅ 已成功加载 {len(df)} 行数据")
                        st.rerun()
    
    elif data_source == "上传Excel":
        uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'], key="excel_uploader")
        if uploaded_file is not None:
            if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
                with st.spinner("正在加载数据..."):
                    df = data_loader.load_from_excel(uploaded_file)
                    if df is not None:
                        st.session_state.df = df
                        st.session_state.last_uploaded_file = uploaded_file.name
                        st.success(f"✅ 已成功加载 {len(df)} 行数据")
                        st.rerun()
    
    else:  # 上传数据库
        st.subheader("📊 数据库连接")
        
        # 显示数据库连接状态
        try:
            # 尝试获取表列表
            tables = data_loader.get_database_tables()
            
            if tables:
                st.success(f"✅ 数据库连接成功！找到 {len(tables)} 个表")
                
                # 选择表
                selected_table = st.selectbox(
                    "选择要分析的数据表",
                    tables,
                    key="table_selector"
                )
                
                # 数据加载选项
                col1, col2 = st.columns(2)
                with col1:
                    load_all = st.checkbox("加载全部数据", value=False, help="注意：大表可能加载较慢")
                with col2:
                    if not load_all:
                        limit_rows = st.number_input("限制行数", min_value=100, max_value=100000, value=1000, step=100)
                    else:
                        limit_rows = None
                
                # 高级选项：自定义SQL
                use_custom_sql = st.checkbox("使用自定义SQL查询", key="use_custom_sql")
                
                if use_custom_sql:
                    custom_query = st.text_area(
                        "输入SQL查询语句",
                        placeholder=f"SELECT * FROM {selected_table} WHERE 条件 LIMIT 100",
                        height=100
                    )
                
                # 加载按钮
                if st.button("📥 从数据库加载数据", type="primary", key="load_db_btn"):
                    with st.spinner("正在从数据库加载数据..."):
                        if use_custom_sql and custom_query:
                            df = data_loader.execute_custom_query(custom_query)
                        else:
                            df = data_loader.load_from_database(selected_table, limit=limit_rows)
                        
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.last_table = selected_table
                            st.success(f"✅ 已成功加载 {len(df)} 行数据")
                            st.rerun()
            else:
                st.error("❌ 无法获取数据库表，请检查数据库配置")
                st.info("请在 .streamlit/secrets.toml 中配置数据库连接信息")
                
                # 显示配置示例
                with st.expander("📖 查看数据库配置示例"):
                    st.code("""
# .streamlit/secrets.toml 配置示例

# MySQL 配置
host = "localhost"
port = 3306
database = "your_database"
user = "your_username"
password = "your_password"

# 或者使用 postgresql
# host = "localhost"
# port = 5432
# database = "your_db"
# user = "postgres"
# password = "your_password"
                    """, language="toml")
                    
        except Exception as e:
            st.error(f"数据库连接失败: {e}")
            st.info("请确保已安装必要的依赖: pip install pymysql sqlalchemy")

# 清除数据按钮
if st.session_state.df is not None:
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("🗑️ 清除数据"):
            st.session_state.df = None
            st.rerun()
    with col3:
        if st.button("🔄 刷新"):
            st.rerun()

st.divider()

# ==================== 数据显示区域 ====================
if st.session_state.df is not None:
    df = st.session_state.df
    
    # 直接从 DataFrame 获取统计信息
    rows = len(df)
    cols = len(df.columns)
    missing_total = df.isnull().sum().sum()
    memory_usage = f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
    
    # 顶部统计卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 数据行数", f"{rows:,}")
    with col2:
        st.metric("📋 数据列数", cols)
    with col3:
        missing_pct = (missing_total / (rows * cols) * 100) if rows > 0 and cols > 0 else 0
        st.metric("⚠️ 缺失值", f"{missing_total:,}", delta=f"{missing_pct:.1f}%", delta_color="inverse")
    with col4:
        st.metric("💾 内存使用", memory_usage)
    
    # 数据预览
    st.subheader("🔍 数据预览")
    preview_rows = st.selectbox("预览行数", [5, 10, 20, 50, 100], index=1, key="preview_rows")
    st.dataframe(df.head(preview_rows), use_container_width=True)
    
    # 列信息
    st.subheader("📝 列信息")
    dtype_df = pd.DataFrame({
        '列名': df.columns,
        '数据类型': df.dtypes.astype(str).values,
        '非空值数': df.count().values,
        '空值数': df.isnull().sum().values,
        '空值比例(%)': (df.isnull().sum() / len(df) * 100).round(2).values,
        '唯一值数': df.nunique().values
    })
    st.dataframe(dtype_df, use_container_width=True)
    
    # 描述性统计
    st.subheader("📐 描述性统计")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        st.dataframe(df[numeric_cols].describe(), use_container_width=True)
    else:
        st.info("没有数值列可供统计")
    
    # 导出功能
    st.markdown("---")
    with st.expander("💾 导出数据", expanded=False):
        data_exporter.set_data(df)
        data_exporter.export_report(page_key="respond_1")

else:
    st.info("👈 请先展开「加载数据」区域，选择数据源并加载数据")