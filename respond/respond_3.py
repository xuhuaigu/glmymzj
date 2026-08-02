# respond/respond_3.py
import streamlit as st
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import plotly.graph_objects as go
from datetime import datetime

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

# ==================== 质量评估函数 ====================
def assess_data_quality(df, table_name="数据表"):
    """基于五大核心特征评估数据质量"""
    results = {}
    
    # 1. 准确性评估
    accuracy_results = assess_accuracy(df)
    results['准确性'] = accuracy_results
    
    # 2. 完整性评估
    completeness_results = assess_completeness(df)
    results['完整性'] = completeness_results
    
    # 3. 一致性评估
    consistency_results = assess_consistency(df)
    results['一致性'] = consistency_results
    
    # 4. 时效性评估
    timeliness_results = assess_timeliness(df)
    results['时效性'] = timeliness_results
    
    # 5. 唯一性评估
    uniqueness_results = assess_uniqueness(df)
    results['唯一性'] = uniqueness_results
    
    return results

def assess_accuracy(df):
    """准确性评估"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'details': {}
    }
    
    score = 100
    total_rows = len(df)
    total_cols = len(df.columns)
    
    # 1. 异常值检测（数值列）
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in ['id', '订单数']:
            continue
        data = df[col].dropna()
        if len(data) > 0:
            mean = data.mean()
            std = data.std()
            if std > 0:
                outliers = data[(data > mean + 3*std) | (data < mean - 3*std)]
                if len(outliers) > 0:
                    outlier_rate = len(outliers) / len(data)
                    results['issues'].append(f"列 '{col}' 发现 {len(outliers)} 个异常值 ({outlier_rate*100:.2f}%)")
                    score -= min(outlier_rate * 20, 20)
    
    # 2. 枚举值检查（分类列）
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        if col in ['姓名', '备注']:
            continue
        unique_vals = df[col].dropna().unique()
        lower_vals = set([str(v).lower() for v in unique_vals if pd.notna(v)])
        if len(lower_vals) < len(unique_vals):
            results['issues'].append(f"列 '{col}' 存在格式不一致（大小写混用）")
            score -= 5
    
    error_count = sum([len(issue) for issue in results['issues']])
    error_rate = error_count / (total_rows * total_cols) if total_rows * total_cols > 0 else 0
    
    results['score'] = max(score, 0)
    results['details'] = {
        '异常值率': f"{error_rate*100:.2f}%",
        '发现问题数': len(results['issues']),
        '错误率': f"{error_rate*100:.2f}%"
    }
    
    return results

def assess_completeness(df):
    """完整性评估"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'details': {}
    }
    
    total_cells = len(df) * len(df.columns)
    missing_cells = df.isnull().sum().sum()
    missing_rate = missing_cells / total_cells if total_cells > 0 else 1
    
    score = 100 - missing_rate * 100
    score = max(score, 0)
    
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            missing_pct = missing_count / len(df) * 100
            if missing_pct > 5:
                results['issues'].append(f"列 '{col}' 缺失率 {missing_pct:.2f}%")
    
    results['score'] = max(score, 0)
    results['details'] = {
        '总数据量': f"{total_cells:,}",
        '缺失值数量': f"{missing_cells:,}",
        '缺失率': f"{missing_rate*100:.2f}%",
        '必填字段完整': "✅" if missing_rate < 0.01 else "⚠️" if missing_rate < 0.05 else "❌"
    }
    
    return results

def assess_consistency(df):
    """一致性评估"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'details': {}
    }
    
    score = 100
    
    for col in df.columns:
        if col in ['注册日期', '最近登录']:
            try:
                pd.to_datetime(df[col])
            except:
                results['issues'].append(f"列 '{col}' 存在日期格式不一致")
                score -= 10
                break
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in ['id']:
            continue
        data = df[col].dropna()
        if len(data) > 0:
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0 and len(data.unique()) > 1:
                results['issues'].append(f"列 '{col}' 可能存在单位不一致问题（数据过于集中）")
                score -= 5
                break
    
    for col in df.columns:
        if not col.isidentifier():
            results['issues'].append(f"列名 '{col}' 不符合命名规范")
            score -= 3
    
    results['score'] = max(score, 0)
    results['details'] = {
        '格式一致': "✅" if len(results['issues']) < 3 else "⚠️",
        '单位标准': "✅" if len(results['issues']) < 5 else "⚠️",
        '命名规范': "✅" if all(c.isidentifier() for c in df.columns) else "⚠️"
    }
    
    return results

def assess_timeliness(df):
    """时效性评估"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'details': {}
    }
    
    score = 100
    date_cols = [col for col in df.columns if '日期' in col or '时间' in col or 'day' in col.lower()]
    
    if date_cols:
        for col in date_cols:
            try:
                dates = pd.to_datetime(df[col])
                if len(dates) > 0:
                    max_date = dates.max()
                    min_date = dates.min()
                    date_range = (max_date - min_date).days
                    
                    future_dates = dates[dates > pd.Timestamp.now()]
                    if len(future_dates) > 0:
                        results['issues'].append(f"列 '{col}' 存在 {len(future_dates)} 个未来日期")
                        score -= 10
                    
                    days_since_update = (pd.Timestamp.now() - max_date).days
                    if days_since_update > 30:
                        results['issues'].append(f"列 '{col}' 最后更新距今 {days_since_update} 天")
                        score -= min(days_since_update / 30 * 5, 20)
                    
                    results['details']['日期跨度'] = f"{date_range} 天"
                    results['details']['最后更新'] = max_date.strftime('%Y-%m-%d')
            except:
                results['issues'].append(f"列 '{col}' 无法解析为日期")
                score -= 10
    else:
        results['issues'].append("未找到日期列，无法评估时效性")
        score -= 20
    
    results['score'] = max(score, 0)
    
    return results

def assess_uniqueness(df):
    """唯一性评估"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'details': {}
    }
    
    duplicate_rows = df.duplicated().sum()
    duplicate_rate = duplicate_rows / len(df) if len(df) > 0 else 0
    
    score = 100 - duplicate_rate * 100
    
    id_cols = [col for col in df.columns if 'id' in col.lower()]
    if id_cols:
        for col in id_cols:
            if df[col].nunique() < len(df):
                results['issues'].append(f"列 '{col}' 存在重复值，不满足主键约束")
                score -= 10
    else:
        results['issues'].append("未找到主键列，无法保证记录唯一性")
        score -= 20
    
    results['score'] = max(score, 0)
    results['details'] = {
        '总行数': f"{len(df):,}",
        '重复行数': f"{duplicate_rows:,}",
        '重复率': f"{duplicate_rate*100:.2f}%"
    }
    
    return results

def get_overall_grade(results):
    """综合评分"""
    weights = {
        '准确性': 0.25,
        '完整性': 0.25,
        '一致性': 0.20,
        '时效性': 0.15,
        '唯一性': 0.15
    }
    
    total_score = 0
    for dim, weight in weights.items():
        if dim in results:
            total_score += results[dim]['score'] * weight
    
    if total_score >= 90:
        grade = "A"
        grade_text = "优秀"
        color = "#52c41a"
    elif total_score >= 75:
        grade = "B"
        grade_text = "良好"
        color = "#1890ff"
    elif total_score >= 60:
        grade = "C"
        grade_text = "一般"
        color = "#faad14"
    elif total_score >= 40:
        grade = "D"
        grade_text = "较差"
        color = "#ff7a45"
    else:
        grade = "F"
        grade_text = "不及格"
        color = "#ff4d4f"
    
    return {
        'total_score': round(total_score, 2),
        'grade': grade,
        'grade_text': grade_text,
        'color': color
    }

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
            schemas = ["CQ", "DWD", "DWS", "DIM", "ADS", "FDL"]
            selected_schema = st.selectbox("选择模式 (Schema)", schemas, index=0, key="schema_select")
            
            with st.spinner("正在获取表列表..."):
                try:
                    tables = data_loader.get_database_tables(config_name=config_name, schema=selected_schema)
                except TypeError:
                    st.error("当前 data_loader 版本不支持 schema 参数，请升级或修改代码。")
                    tables = []
            
            if tables:
                st.success(f"✅ 连接成功！找到 {len(tables):,} 个表")
                
                selected_table = st.selectbox(
                    "选择要分析的数据表",
                    options=[""] + tables,
                    format_func=lambda x: x if x else "请选择...",
                    key="table_selector"
                )
                st.session_state.selected_table = selected_schema + '_' + selected_table
                
                if selected_table:
                    col1, col2 = st.columns(2)
                    with col1:
                        load_all = st.checkbox("加载全部数据", value=False, help="注意：大表可能加载较慢")
                    with col2:
                        if not load_all:
                            limit_rows = st.number_input("限制行数", min_value=100, max_value=100000, value=1000, step=100, key="limit_rows_input")
                        else:
                            limit_rows = None
                    
                    use_custom_sql = st.checkbox("使用自定义SQL查询", key="use_custom_sql")
                    custom_query = None
                    if use_custom_sql:
                        custom_query = st.text_area(
                            "输入SQL查询语句",
                            placeholder=f"SELECT * FROM {selected_schema}.{selected_table} WHERE ROWNUM <= 1000",
                            height=100,
                            key="custom_query_input"
                        )
                    
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

# ==================== 清除数据按钮 ====================
if st.session_state.df is not None:
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("🗑️ 清除数据"):
            st.session_state.df = None
            st.session_state.data_loaded = False
            st.rerun()
    with col3:
        if st.button("🔄 刷新"):
            st.rerun()

st.divider()

# ==================== 数据显示区域 ====================
if st.session_state.df is not None:
    df = st.session_state.df
    table_name = st.session_state.get('selected_table', '数据表')
    
    # ----- 数据概览卡片 -----
    st.subheader(f"📊 数据概览: {table_name}")
    
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
    
    # ==================== 表结构查看 ====================
    with st.expander("📋 表结构信息【暂时不可用】", expanded=False):
        table_name = st.session_state.get('last_table', '')
        config_name = st.session_state.get('db_config', None)
        
        if table_name:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📌 当前表: `{table_name}`")
            with col2:
                if st.button("🔍 查看表结构", use_container_width=True):
                    with st.spinner("正在获取表结构..."):
                        schema_df = data_loader.get_full_table_schema(table_name, config_name)
                        if schema_df is not None and not schema_df.empty:
                            st.dataframe(schema_df, use_container_width=True)
                            
                            # 统计信息
                            stats = data_loader.get_table_statistics(table_name, config_name)
                            if stats:
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("📊 总行数", f"{stats.get('行数', 0):,}")
                                with col_b:
                                    st.metric("📋 总列数", stats.get('列数', 0))
                                with col_c:
                                    size = stats.get('大小(MB)', 0)
                                    if size and size != 'N/A':
                                        st.metric("💾 表大小", f"{size:.2f} MB")
                                    else:
                                        st.metric("💾 表大小", "N/A")
                        else:
                            st.warning("未能获取表结构信息")
        else:
            st.info("👈 请先从数据库加载一个表")

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
    
    # ----- 快速分析：数值列分布 -----
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
    
    # ==================== 质量评估 ====================
    st.divider()
    st.subheader("✅ 数据质量评估")
    
    if st.button("🔄 开始质量评估", type="primary", use_container_width=True):
        with st.spinner("正在评估数据质量..."):
            results = assess_data_quality(df, table_name)
            overall = get_overall_grade(results)
        
        # ----- 综合评分 -----
        st.subheader("📈 综合评分")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            fig = go.Figure(go.Pie(
                values=[overall['total_score'], 100 - overall['total_score']],
                hole=0.7,
                marker_colors=[overall['color'], '#f0f0f0'],
                textinfo='none',
                hoverinfo='none',
                showlegend=False
            ))
            fig.update_layout(
                annotations=[dict(
                    text=f"{overall['total_score']:.1f}<br><span style='font-size:20px'>{overall['grade']}</span>",
                    x=0.5, y=0.5,
                    font=dict(size=28, color='#1a1a1a'),
                    showarrow=False,
                    align='center'
                )],
                height=200,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            # ✅ 显示工具栏
            st.plotly_chart(fig, use_container_width=True, config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToAdd': [],
                'modeBarButtonsToRemove': [],
                'scrollZoom': True,
                'doubleClick': 'reset',
            })
        
        with col2:
            st.metric(
                "综合评分",
                f"{overall['total_score']:.1f}",
                delta=f"{overall['grade']} - {overall['grade_text']}"
            )
            
            if overall['total_score'] >= 75:
                st.success("✅ 该数据集符合高质量标准")
            elif overall['total_score'] >= 60:
                st.warning("⚠️ 该数据集需要改进")
            else:
                st.error("❌ 该数据集不符合高质量标准")
        
        with col3:
            st.info("""
            **评级标准**
            - A (≥90): 优秀
            - B (≥75): 良好
            - C (≥60): 一般
            - D (≥40): 较差
            - F (<40): 不及格
            """)
        
        st.divider()
        
        # ----- 五大维度雷达图 -----
        st.subheader("🎯 五大核心特征评估")
        
        dimensions = ['准确性', '完整性', '一致性', '时效性', '唯一性']
        scores = [results[dim]['score'] for dim in dimensions]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=dimensions + [dimensions[0]],
            fill='toself',
            name='数据质量',
            line=dict(color='#1890ff', width=2),
            fillcolor='rgba(24, 144, 255, 0.2)'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            height=400,
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        # ✅ 显示工具栏
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': [],
            'modeBarButtonsToRemove': [],
            'scrollZoom': True,
            'doubleClick': 'reset',
        })
        
        st.divider()
        
        # ----- 各维度详细评估 -----
        st.subheader("📋 各维度详细评估")
        
        for dim, result in results.items():
            with st.expander(f"{dim} (得分: {result['score']:.1f}/{result['max_score']})", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.progress(result['score'] / result['max_score'], text=f"{dim}质量")
                    st.json(result['details'])
                
                with col2:
                    if result['issues']:
                        st.warning("⚠️ 发现的问题:")
                        for issue in result['issues']:
                            st.write(f"- {issue}")
                    else:
                        st.success("✅ 未发现问题")
        
        st.divider()
        
        # ----- 改进建议 -----
        st.subheader("💡 改进建议")
        
        suggestions = []
        for dim, result in results.items():
            if result['score'] < 70:
                if dim == '准确性':
                    suggestions.append("🔴 **准确性不足**：建议加强异常值检测和清洗，建立多重校验机制")
                elif dim == '完整性':
                    suggestions.append("🔴 **完整性不足**：建议补充缺失数据，确保必填字段覆盖率100%")
                elif dim == '一致性':
                    suggestions.append("🔴 **一致性不足**：建议统一数据格式、单位和命名规范")
                elif dim == '时效性':
                    suggestions.append("🔴 **时效性不足**：建议建立定期更新机制，确保数据新鲜度")
                elif dim == '唯一性':
                    suggestions.append("🔴 **唯一性不足**：建议建立主键约束，实施去重规则")
        
        if suggestions:
            for s in suggestions:
                st.markdown(s)
        else:
            st.success("✅ 所有维度表现良好，继续保持！")
        
        # ----- 导出报告 -----
        st.divider()
        with st.expander("📄 导出评估报告", expanded=False):
            report = f"""
# 数据质量评估报告

## 基本信息
- 数据表: {table_name}
- 评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 数据行数: {len(df):,}
- 数据列数: {len(df.columns)}

## 综合评分
- 总分: {overall['total_score']:.2f}
- 评级: {overall['grade']} ({overall['grade_text']})
- 结论: {"✅ 高质量数据集" if overall['total_score'] >= 75 else "⚠️ 需改进"}

## 五大维度得分
"""
            for dim, result in results.items():
                report += f"- {dim}: {result['score']:.1f}/{result['max_score']}\n"
            
            report += "\n## 发现的问题\n"
            for dim, result in results.items():
                if result['issues']:
                    report += f"\n### {dim}\n"
                    for issue in result['issues']:
                        report += f"- {issue}\n"
            
            st.download_button(
                label="📥 下载评估报告 (Markdown)",
                data=report,
                file_name=f"data_quality_report_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
    
    # ----- 导出功能 -----
    st.markdown("---")
    with st.expander("💾 导出数据", expanded=False):
        table_name = st.session_state.get('selected_table', 'exported_data')
        data_exporter.set_data(df)
        data_exporter.export_report(file_name=table_name, page_key="respond_3")

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