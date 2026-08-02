import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.title("📈 数据可视化")

# 生成或加载数据
@st.cache_data
def load_data():
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=365, freq='D')
    df = pd.DataFrame({
        '日期': dates,
        '销售额': np.random.normal(10000, 2000, 365).cumsum(),
        '利润': np.random.normal(2000, 500, 365).cumsum(),
        '客户数': np.random.poisson(100, 365),
        '转化率': np.random.uniform(0.1, 0.3, 365),
        '类别': np.random.choice(['A类', 'B类', 'C类'], 365),
        '地区': np.random.choice(['北区', '南区', '东区', '西区'], 365)
    })
    return df

df = load_data()

# 图表类型选择
col1, col2 = st.columns([1, 2])

with col1:
    chart_type = st.selectbox(
        "选择图表类型",
        ["折线图", "柱状图", "散点图", "饼图", "箱线图", "直方图", "面积图"],
        key="viz_chart_type"
    )
    
    # 数据列选择
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

# 根据图表类型选择不同的配置
with col1:
    if chart_type in ["折线图", "柱状图", "面积图"]:
        x_col = st.selectbox("X轴", df.columns, index=0, key="viz_x")
        y_col = st.selectbox("Y轴", numeric_cols, index=0, key="viz_y")
        color_col = st.selectbox("颜色分组", ["无"] + categorical_cols, key="viz_color")
        
    elif chart_type == "散点图":
        x_col = st.selectbox("X轴", numeric_cols, index=0, key="viz_x")
        y_col = st.selectbox("Y轴", numeric_cols, index=1 if len(numeric_cols) > 1 else 0, key="viz_y")
        color_col = st.selectbox("颜色", ["无"] + categorical_cols, key="viz_color")
        
    elif chart_type == "饼图":
        value_col = st.selectbox("数值", numeric_cols, index=0, key="viz_value")
        names_col = st.selectbox("标签", categorical_cols, index=0 if categorical_cols else None, key="viz_names")
        
    elif chart_type == "箱线图":
        y_col = st.selectbox("数值", numeric_cols, index=0, key="viz_y")
        x_col = st.selectbox("分组", ["无"] + categorical_cols, key="viz_x")
        
    else:  # 直方图
        col = st.selectbox("选择列", numeric_cols, index=0, key="viz_col")
        bins = st.slider("柱数", 10, 100, 30, key="viz_bins")

# 生成图表
with col2:
    if chart_type == "折线图":
        fig = px.line(df, x=x_col, y=y_col, color=color_col if color_col != "无" else None,
                      title=f"{y_col} 趋势图")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "柱状图":
        if len(df) > 100 and x_col == '日期':
            df_agg = df.groupby(pd.to_datetime(df[x_col]).dt.to_period('M')).agg({y_col: 'mean'}).reset_index()
            df_agg[x_col] = df_agg[x_col].astype(str)
            fig = px.bar(df_agg, x=x_col, y=y_col, title=f"{y_col} 月度汇总")
        else:
            fig = px.bar(df, x=x_col, y=y_col, color=color_col if color_col != "无" else None,
                         title=f"{y_col} 柱状图")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "散点图":
        fig = px.scatter(df, x=x_col, y=y_col, 
                         color=color_col if color_col != "无" else None,
                         title=f"{x_col} vs {y_col}")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "饼图":
        pie_data = df.groupby(names_col)[value_col].sum().reset_index()
        fig = px.pie(pie_data, values=value_col, names=names_col, title=f"{value_col} 分布")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "箱线图":
        if x_col != "无":
            fig = px.box(df, x=x_col, y=y_col, title=f"{y_col} 箱线图")
        else:
            fig = px.box(df, y=y_col, title=f"{y_col} 箱线图")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "直方图":
        fig = px.histogram(df, x=col, nbins=bins, title=f"{col} 分布直方图")
        st.plotly_chart(fig, use_container_width=True)
        
    else:  # 面积图
        fig = px.area(df, x=x_col, y=y_col, color=color_col if color_col != "无" else None,
                      title=f"{y_col} 面积图")
        st.plotly_chart(fig, use_container_width=True)

# 显示数据表格
with st.expander("查看数据"):
    st.dataframe(df, use_container_width=True)