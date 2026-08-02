# data_analysis/6_chart_analysis.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="图表分析", page_icon="📊", layout="wide")

st.title("📊 图表分析中心")

# ==================== 辅助函数（必须在最前面定义） ====================
def generate_mock_data(data_type: str, rows: int) -> pd.DataFrame:
    """生成模拟数据"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=rows, freq='D')
    
    if data_type == "销售数据":
        df = pd.DataFrame({
            '日期': dates,
            '销售额': np.random.normal(10000, 2000, rows).cumsum(),
            '利润': np.random.normal(2000, 500, rows).cumsum(),
            '销量': np.random.poisson(100, rows),
            '客户数': np.random.poisson(80, rows),
            '转化率': np.random.uniform(0.1, 0.4, rows),
            '地区': np.random.choice(['北区', '南区', '东区', '西区'], rows),
            '产品': np.random.choice(['产品A', '产品B', '产品C'], rows)
        })
    elif data_type == "财务数据":
        df = pd.DataFrame({
            '日期': dates,
            '收入': np.random.normal(50000, 10000, rows).cumsum(),
            '支出': np.random.normal(30000, 8000, rows).cumsum(),
            '净利润': np.random.normal(20000, 5000, rows).cumsum(),
            '部门': np.random.choice(['销售部', '市场部', '研发部'], rows)
        })
    elif data_type == "用户数据":
        df = pd.DataFrame({
            '日期': dates,
            '新增用户': np.random.poisson(100, rows),
            '活跃用户': np.random.normal(5000, 500, rows),
            '留存率': np.random.uniform(0.3, 0.8, rows),
            '平台': np.random.choice(['iOS', 'Android', 'Web'], rows)
        })
    elif data_type == "产品数据":
        df = pd.DataFrame({
            '产品': np.random.choice(['产品A', '产品B', '产品C', '产品D'], rows),
            '价格': np.random.uniform(50, 500, rows),
            '销量': np.random.poisson(200, rows),
            '评分': np.random.uniform(3, 5, rows)
        })
    elif data_type == "三元图数据":
        # 生成三元图数据
        raw = np.random.rand(rows, 3)
        row_sums = raw.sum(axis=1, keepdims=True)
        normalized = raw / row_sums
        
        df = pd.DataFrame({
            '成分A': normalized[:, 0],
            '成分B': normalized[:, 1],
            '成分C': normalized[:, 2],
            '样品': [f'样{i+1}' for i in range(rows)],
            '类别': np.random.choice(['类型1', '类型2', '类型3'], rows),
            '大小': np.random.uniform(5, 20, rows)
        })

    else:  # 时间序列数据
        df = pd.DataFrame({
            '日期': dates,
            '指标A': np.random.normal(100, 20, rows) + np.sin(np.linspace(0, 4*np.pi, rows)) * 30,
            '指标B': np.random.normal(80, 15, rows) + np.cos(np.linspace(0, 3*np.pi, rows)) * 25,
            '类别': np.random.choice(['预测', '实际', '目标'], rows)
        })
    
    return df

def create_chart(df: pd.DataFrame, chart_type: str, x_col: str, y_col: str, 
                 color_col: str, title: str, size_col: str = None) -> go.Figure:
    """根据参数创建图表"""
    
    if chart_type == "折线图":
        if color_col and color_col != "无":
            fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = px.line(df, x=x_col, y=y_col, title=title)
    
    elif chart_type == "柱状图":
        if color_col and color_col != "无":
            fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = px.bar(df, x=x_col, y=y_col, title=title)
    
    elif chart_type == "散点图":
        if color_col and color_col != "无":
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = px.scatter(df, x=x_col, y=y_col, title=title)
    
    elif chart_type == "饼图":
        pie_data = df.groupby(x_col)[y_col].sum().reset_index()
        fig = px.pie(pie_data, values=y_col, names=x_col, title=title)
    
    elif chart_type == "面积图":
        if color_col and color_col != "无":
            fig = px.area(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = px.area(df, x=x_col, y=y_col, title=title)
    
    elif chart_type == "箱线图":
        if x_col and x_col != y_col:
            fig = px.box(df, x=x_col, y=y_col, title=title)
        else:
            fig = px.box(df, y=y_col, title=title)
    
    elif chart_type == "热力图":
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        corr_df = df[numeric_cols].corr()
        fig = px.imshow(corr_df, text_auto=True, aspect='auto', title=title,
                       color_continuous_scale='RdBu_r')
    
    elif chart_type == "条形图":
        if color_col and color_col != "无":
            fig = px.bar(df, x=y_col, y=x_col, color=color_col, orientation='h', title=title)
        else:
            fig = px.bar(df, x=y_col, y=x_col, orientation='h', title=title)
    
    elif chart_type == "气泡图":
        fig = px.scatter(df, x=x_col, y=y_col, size=size_col, 
                        color=color_col if color_col and color_col != "无" else None,
                        title=title, hover_name=x_col)
    
    else:
        fig = px.line(df, x=x_col, y=y_col, title=title)
    
    return fig

def generate_kline_data(rows: int = 100) -> pd.DataFrame:
    """生成模拟的K线图数据（开高低收）"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=rows, freq='D')
    
    base_price = 100
    prices = [base_price]
    for i in range(rows - 1):
        change = np.random.normal(0, 2)
        prices.append(max(prices[-1] + change, 10))
    
    open_prices = []
    high_prices = []
    low_prices = []
    close_prices = []
    
    for i in range(rows):
        if i == 0:
            open_p = prices[i]
        else:
            open_p = prices[i-1]
        
        close_p = prices[i]
        intraday_range = abs(close_p - open_p) * np.random.uniform(0.5, 1.5)
        high_p = max(open_p, close_p) + np.random.uniform(0, intraday_range)
        low_p = min(open_p, close_p) - np.random.uniform(0, intraday_range)
        
        open_prices.append(open_p)
        high_prices.append(high_p)
        low_prices.append(low_p)
        close_prices.append(close_p)
    
    volumes = np.random.poisson(10000, rows) + np.abs(np.random.normal(0, 2000, rows))
    
    df = pd.DataFrame({
        '日期': dates,
        '开盘': [round(x, 2) for x in open_prices],
        '最高': [round(x, 2) for x in high_prices],
        '最低': [round(x, 2) for x in low_prices],
        '收盘': [round(x, 2) for x in close_prices],
        '成交量': [int(x) for x in volumes]
    })
    
    return df

def generate_ternary_data(rows: int = 50) -> pd.DataFrame:
    """生成三元图数据（三列之和为1）"""
    np.random.seed(42)
    
    # 生成随机数据并归一化
    raw = np.random.rand(rows, 3)
    row_sums = raw.sum(axis=1, keepdims=True)
    normalized = raw / row_sums
    
    df = pd.DataFrame({
        '成分A': normalized[:, 0],
        '成分B': normalized[:, 1],
        '成分C': normalized[:, 2],
        '样品': [f'样{i+1}' for i in range(rows)],
        '类别': np.random.choice(['类型1', '类型2', '类型3'], rows)
    })
    
    return df

def create_ternary_chart(df: pd.DataFrame, color_col: str, title: str) -> go.Figure:
    """创建三元图"""
    import plotly.express as px
    
    # 检查是否有颜色分组列
    if color_col and color_col != "无" and color_col in df.columns:
        fig = px.scatter_ternary(
            df,
            a='成分A',
            b='成分B',
            c='成分C',
            color=color_col,
            title=title,
            labels={'成分A': '成分A (%)', '成分B': '成分B (%)', '成分C': '成分C (%)'},
            hover_name='样品'
        )
    else:
        fig = px.scatter_ternary(
            df,
            a='成分A',
            b='成分B',
            c='成分C',
            title=title,
            labels={'成分A': '成分A (%)', '成分B': '成分B (%)', '成分C': '成分C (%)'},
            hover_name='样品'
        )
    
    # 设置图例位置
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig
def create_kline_chart(df: pd.DataFrame, title: str = "K线图（蜡烛图）") -> go.Figure:
    """创建K线图（蜡烛图）"""
    fig = go.Figure(data=[go.Candlestick(
        x=df['日期'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        name='价格',
        increasing_line_color='red',
        decreasing_line_color='green'
    )])
    
    fig.add_trace(go.Bar(
        x=df['日期'],
        y=df['成交量'],
        name='成交量',
        yaxis='y2',
        marker_color='lightgray',
        opacity=0.5
    ))
    
    fig.update_layout(
        title=title,
        yaxis_title='价格',
        yaxis2=dict(
            title='成交量',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_title='日期',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    return fig

# ==================== 初始化session状态 ====================
if 'chart_df' not in st.session_state:
    st.session_state.chart_df = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = "模拟数据"
if 'current_display_df' not in st.session_state:
    st.session_state.current_display_df = None

# ==================== 侧边栏 ====================
with st.sidebar:
    st.subheader("📁 数据源")
    
    data_source = st.radio(
        "选择数据源",
        ["模拟数据", "上传Excel文件"],
        horizontal=True,
        key="data_source_radio"
    )
    st.session_state.data_source = data_source
    
    st.divider()
    
    if data_source == "模拟数据":
        st.subheader("🔧 模拟数据配置")
        
        data_type = st.selectbox(
            "数据类型",
            ["销售数据", "财务数据", "用户数据", "产品数据", "时间序列数据", "三元图数据"],
            key="mock_data_type"
        )
        
        data_rows = st.slider(
            "数据行数", 
            min_value=10, 
            max_value=2000, 
            value=200, 
            step=50,
            key="mock_data_rows"
        )
        
        if st.button("🔄 生成数据", type="primary", use_container_width=True):
            st.session_state.chart_df = generate_mock_data(data_type, data_rows)
            st.session_state.current_display_df = st.session_state.chart_df
            st.success(f"✅ 已生成 {data_rows} 行模拟数据")
            st.rerun()
    
    else:
        st.subheader("📂 上传Excel文件")
        
        uploaded_file = st.file_uploader(
            "选择Excel文件",
            type=['xlsx', 'xls'],
            help="支持上传.xlsx或.xls格式的Excel文件",
            key="excel_uploader"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
                st.session_state.chart_df = df
                st.session_state.current_display_df = df
                st.success(f"✅ 成功加载 {len(df)} 行数据，{len(df.columns)} 列")
            except Exception as e:
                st.error(f"读取文件失败: {e}")
        
        st.markdown("---")
        st.caption("📥 没有数据？下载示例模板")
        
        sample_df = generate_mock_data("销售数据", 50)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            sample_df.to_excel(writer, index=False, sheet_name='示例数据')
        
        st.download_button(
            label="📊 下载Excel模板",
            data=excel_buffer.getvalue(),
            file_name="chart_sample.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.divider()
    
    st.subheader("📈 图表类型")
    
    chart_type = st.selectbox(
        "选择图表",
        [
            "📈 折线图", "📊 柱状图", "🔵 散点图", "🥧 饼图", 
            "📉 面积图", "📦 箱线图", "🔥 热力图", "📊 条形图", "💨 气泡图",
            "🕯️ K线图（蜡烛图）",
            "🔺 三元图"  # 新增
        ],
        key="chart_type_select"
    )
    
    # 判断是否为K线图
    is_kline = "K线图" in chart_type
    is_ternary = "三元图" in chart_type
    
    # 如果是K线图，自动生成演示数据并更新显示数据
    if is_kline:
        # 检查是否需要重新生成K线图数据
        if 'kline_data' not in st.session_state:
            st.session_state.kline_data = generate_kline_data(100)
        st.session_state.current_display_df = st.session_state.kline_data
    else:
        # 非K线图时，使用用户选择的数据
        if st.session_state.chart_df is not None:
            st.session_state.current_display_df = st.session_state.chart_df

st.divider()

# ==================== 主内容区域 ====================
# 获取当前要显示的数据
display_df = st.session_state.current_display_df if st.session_state.current_display_df is not None else st.session_state.chart_df

if display_df is not None:
    df = display_df
    
    # 数据概览卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 数据行数", f"{len(df):,}")
    with col2:
        st.metric("📋 数据列数", len(df.columns))
    with col3:
        numeric_count = len(df.select_dtypes(include=[np.number]).columns)
        st.metric("🔢 数值列", numeric_count)
    with col4:
        if is_kline:
            st.metric("📅 数据源", "K线图演示数据")
        else:
            st.metric("📅 数据源", st.session_state.data_source)
    
    st.divider()
    
    # ==================== 图表配置区域（K线图不显示） ====================
    if not is_kline:
        st.subheader("⚙️ 图表配置")
        
        all_cols = df.columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        col1, col2, col3 = st.columns(3)
        
        chart_type_clean = chart_type.split(" ")[1] if " " in chart_type else chart_type
        
        with col1:
            if chart_type_clean in ["饼图"]:
                x_options = categorical_cols if categorical_cols else all_cols
            elif chart_type_clean in ["热力图"]:
                x_options = ["自动（使用所有数值列）"]
            else:
                x_options = all_cols
            
            default_x = None
            if '日期' in all_cols and chart_type_clean in ["折线图", "面积图"]:
                default_x = '日期'
            elif categorical_cols and chart_type_clean in ["柱状图", "条形图"]:
                default_x = categorical_cols[0]
            
            x_col = st.selectbox("X轴", x_options, index=x_options.index(default_x) if default_x in x_options else 0)
        
        with col2:
            if chart_type_clean in ["饼图", "热力图"]:
                y_options = numeric_cols if numeric_cols else all_cols
            else:
                y_options = numeric_cols if numeric_cols else all_cols
            
            y_col = st.selectbox("Y轴", y_options, index=0 if y_options else 0)
        
        with col3:
            color_options = ["无"] + categorical_cols
            color_col = st.selectbox("颜色分组", color_options, index=0)
        
        size_col = None
        if chart_type_clean == "气泡图" and len(numeric_cols) >= 3:
            size_col = st.selectbox("气泡大小", numeric_cols, index=2)
        
        chart_title = st.text_input("图表标题", value=f"{chart_type_clean} - {y_col} vs {x_col}")
        
        color_theme = st.selectbox("颜色主题", ["默认", "鲜艳", "柔和", "深色"], index=0)
        
        st.divider()
    else:
        # K线图模式：只显示标题输入
        chart_title = st.text_input("图表标题", value="K线图分析")
        st.divider()
    
    # ==================== 图表展示 ====================
    st.subheader("📈 图表展示")
    
    try:
        if is_kline:
            # K线图处理（使用当前的 display_df）
            if all(col in df.columns for col in ['开盘', '最高', '最低', '收盘']):
                fig = create_kline_chart(df, chart_title)
                st.info("📊 使用当前数据中的K线图字段（开盘/最高/最低/收盘/成交量）")
            else:
                # 理论上不会执行到这里，因为已经在侧边栏设置了kline_data
                kline_df = generate_kline_data(100)
                fig = create_kline_chart(kline_df, f"{chart_title}（自动生成演示数据）")
                st.info("📊 已自动生成100个交易日的演示K线图数据")
            
            st.plotly_chart(fig, use_container_width=True)
        elif is_ternary:
            # 三元图处理
            if all(col in df.columns for col in ['成分A', '成分B', '成分C']):
                ternary_df = df
                st.info("📊 使用当前数据中的三元图字段（成分A/成分B/成分C）")
            else:
                ternary_df = generate_ternary_data(50)
                st.info("📊 当前数据不含三元图所需字段，已自动生成50个样本的演示数据")
            
            # 颜色分组
            categorical_cols = ternary_df.select_dtypes(include=['object', 'category']).columns.tolist()
            color_options = ["无"] + categorical_cols
            color_col = st.selectbox("颜色分组", color_options, index=0, key="ternary_color")
            chart_title = st.text_input("图表标题", value="三元图分析", key="ternary_title")
            
            fig = create_ternary_chart(ternary_df, color_col, chart_title)
            st.plotly_chart(fig, use_container_width=True)
            
            # 统计信息
            with st.expander("📊 数据统计"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("成分A均值", f"{ternary_df['成分A'].mean():.3f}")
                with col2:
                    st.metric("成分B均值", f"{ternary_df['成分B'].mean():.3f}")
                with col3:
                    st.metric("成分C均值", f"{ternary_df['成分C'].mean():.3f}")
                sums = ternary_df[['成分A', '成分B', '成分C']].sum(axis=1)
                st.write(f"**验证**：A+B+C = {sums.iloc[0]:.3f} (应为1.000)")
            
            # 更新显示数据
            display_df = ternary_df


        else:
            # 普通图表处理
            chart_type_clean = chart_type.split(" ")[1] if " " in chart_type else chart_type
            
            if chart_type_clean == "热力图":
                if len(numeric_cols) >= 2:
                    fig = create_chart(df, chart_type_clean, x_col, y_col, color_col, chart_title)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"热力图需要至少2个数值列，当前只有 {len(numeric_cols)} 个数值列")
            
            elif chart_type_clean == "饼图":
                if x_col and y_col:
                    fig = create_chart(df, chart_type_clean, x_col, y_col, color_col, chart_title)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("请选择X轴（分类）和Y轴（数值）")
            
            elif chart_type_clean == "气泡图":
                if x_col and y_col and size_col:
                    fig = create_chart(df, chart_type_clean, x_col, y_col, color_col, chart_title, size_col)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("气泡图需要选择X轴、Y轴和气泡大小")
            
            else:
                if x_col and y_col:
                    fig = create_chart(df, chart_type_clean, x_col, y_col, color_col, chart_title)
                    
                    if color_theme == "鲜艳":
                        fig.update_layout(template="plotly")
                    elif color_theme == "柔和":
                        fig.update_layout(template="plotly_white")
                    elif color_theme == "深色":
                        fig.update_layout(template="plotly_dark")
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("请选择X轴和Y轴")
            
            # 数据统计
            if 'y_col' in locals() and y_col and y_col in df.columns:
                with st.expander("📊 数据统计"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("平均值", f"{df[y_col].mean():.2f}")
                    with col2:
                        st.metric("最大值", f"{df[y_col].max():.2f}")
                    with col3:
                        st.metric("最小值", f"{df[y_col].min():.2f}")
                    with col4:
                        st.metric("标准差", f"{df[y_col].std():.2f}")
    
    except Exception as e:
        st.error(f"生成图表失败: {e}")
        st.info("请尝试其他图表类型或调整列选择")
    
    st.divider()
    
    # ==================== 数据明细表（根据当前显示的数据） ====================
    with st.expander("📋 数据明细表", expanded=False):
        all_cols = df.columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            search_col = st.selectbox("按列搜索", ["无"] + all_cols)
        with col2:
            if search_col != "无":
                search_term = st.text_input("搜索关键词")
        
        rows_to_show = st.selectbox("显示行数", [10, 20, 50, 100, len(df)], index=2)
        
        filtered_df = df.copy()
        if search_col != "无" and search_term:
            filtered_df = filtered_df[filtered_df[search_col].astype(str).str.contains(search_term, case=False)]
        
        st.dataframe(filtered_df.head(rows_to_show), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button("📥 下载CSV", csv, "chart_data.csv", "text/csv")
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='data')
            st.download_button("📊 下载Excel", output.getvalue(), "chart_data.xlsx")

else:
    st.info("👈 请先在左侧选择数据源并生成/上传数据")
    
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 使用步骤
        
        1. **选择数据源** - 模拟数据或上传Excel文件
        2. **生成/上传数据** - 点击生成按钮或上传文件
        3. **选择图表类型** - 在侧边栏选择
        4. **配置图表** - 选择X轴、Y轴、颜色等（K线图除外）
        5. **查看结果** - 图表自动生成
        
        ### 支持的图表类型
        折线图、柱状图、散点图、饼图、面积图、箱线图、热力图、条形图、气泡图、K线图
        
        ### K线图说明
        - 选择K线图时，自动使用K线图演示数据
        - 数据明细表和数据概览都会同步更新为K线图数据
        - K线图包含：日期、开盘、最高、最低、收盘、成交量
        """)