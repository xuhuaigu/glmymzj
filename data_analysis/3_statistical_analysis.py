import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go

st.title("📐 统计分析")

# 生成示例数据
@st.cache_data
def load_data():
    np.random.seed(42)
    df = pd.DataFrame({
        '组别': np.repeat(['对照组', '实验组A', '实验组B'], 100),
        '指标1': np.concatenate([
            np.random.normal(100, 15, 100),
            np.random.normal(115, 15, 100),
            np.random.normal(110, 15, 100)
        ]),
        '指标2': np.random.normal(50, 10, 300),
        '指标3': np.random.exponential(20, 300),
        '类别': np.random.choice(['高', '中', '低'], 300)
    })
    return df

df = load_data()

# 选择分析类型
analysis_type = st.selectbox(
    "选择分析类型",
    ["描述性统计", "正态性检验", "T检验", "方差分析(ANOVA)", "相关性分析", "频率分析"],
    key="stats_type"
)

if analysis_type == "描述性统计":
    st.subheader("描述性统计分析")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    selected_col = st.selectbox("选择分析列", numeric_cols, key="stats_col")
    
    # 计算统计量
    stats_dict = {
        '样本量': len(df[selected_col]),
        '均值': df[selected_col].mean(),
        '中位数': df[selected_col].median(),
        '标准差': df[selected_col].std(),
        '方差': df[selected_col].var(),
        '最小值': df[selected_col].min(),
        '最大值': df[selected_col].max(),
        '峰度': df[selected_col].kurtosis(),
        '偏度': df[selected_col].skew(),
        '四分位距': df[selected_col].quantile(0.75) - df[selected_col].quantile(0.25)
    }
    
    col1, col2, col3 = st.columns(3)
    for i, (key, value) in enumerate(stats_dict.items()):
        with [col1, col2, col3][i % 3]:
            st.metric(key, f"{value:.2f}" if isinstance(value, float) else value)
    
    fig = px.histogram(df, x=selected_col, marginal='box', title=f"{selected_col} 分布图")
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "正态性检验":
    st.subheader("正态性检验")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    selected_col = st.selectbox("选择检验列", numeric_cols, key="norm_col")
    
    statistic, p_value = stats.shapiro(df[selected_col])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Shapiro-Wilk统计量", f"{statistic:.4f}")
    with col2:
        st.metric("P值", f"{p_value:.4f}")
    
    if p_value > 0.05:
        st.success(f"结论: 数据服从正态分布 (p={p_value:.4f} > 0.05)")
    else:
        st.warning(f"结论: 数据不服从正态分布 (p={p_value:.4f} < 0.05)")
    
    # Q-Q图
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stats.probplot(df[selected_col], dist="norm")[0][0],
        y=stats.probplot(df[selected_col], dist="norm")[0][1],
        mode='markers',
        name='样本'
    ))
    fig.add_trace(go.Scatter(
        x=[-3, 3],
        y=[-3, 3],
        mode='lines',
        name='正态分布线',
        line=dict(color='red', dash='dash')
    ))
    fig.update_layout(title=f"{selected_col} Q-Q图", xaxis_title="理论分位数", yaxis_title="样本分位数")
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "T检验":
    st.subheader("独立样本T检验")
    
    groups = df['组别'].unique()
    col1, col2 = st.columns(2)
    with col1:
        group1 = st.selectbox("选择第一组", groups, key="t_group1")
    with col2:
        group2 = st.selectbox("选择第二组", groups, key="t_group2")
    
    metric = st.selectbox("选择指标", df.select_dtypes(include=[np.number]).columns, key="t_metric")
    
    data1 = df[df['组别'] == group1][metric]
    data2 = df[df['组别'] == group2][metric]
    
    t_stat, p_value = stats.ttest_ind(data1, data2)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{group1} 均值", f"{data1.mean():.2f}")
        st.metric(f"{group1} 标准差", f"{data1.std():.2f}")
    with col2:
        st.metric(f"{group2} 均值", f"{data2.mean():.2f}")
        st.metric(f"{group2} 标准差", f"{data2.std():.2f}")
    
    st.divider()
    st.metric("T统计量", f"{t_stat:.4f}")
    st.metric("P值", f"{p_value:.4f}")
    
    if p_value < 0.05:
        st.success(f"结论: 两组之间存在显著差异 (p={p_value:.4f} < 0.05)")
    else:
        st.info(f"结论: 两组之间无显著差异 (p={p_value:.4f} > 0.05)")

elif analysis_type == "方差分析(ANOVA)":
    st.subheader("单因素方差分析")
    
    metric = st.selectbox("选择指标", df.select_dtypes(include=[np.number]).columns, key="anova_metric")
    
    groups = df['组别'].unique()
    group_data = [df[df['组别'] == g][metric].values for g in groups]
    
    f_stat, p_value = stats.f_oneway(*group_data)
    
    st.metric("F统计量", f"{f_stat:.4f}")
    st.metric("P值", f"{p_value:.4f}")
    
    if p_value < 0.05:
        st.success(f"结论: 各组之间存在显著差异 (p={p_value:.4f} < 0.05)")
    else:
        st.info(f"结论: 各组之间无显著差异 (p={p_value:.4f} > 0.05)")
    
    fig = px.box(df, x='组别', y=metric, title=f"{metric} 组间对比")
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "相关性分析":
    st.subheader("相关性分析")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    corr_matrix = df[numeric_cols].corr()
    
    fig = px.imshow(corr_matrix, text_auto=True, aspect='auto',
                    title="相关系数矩阵热力图",
                    color_continuous_scale='RdBu_r')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("散点图矩阵")
    selected_cols = st.multiselect("选择要显示的列", numeric_cols, default=numeric_cols[:3], key="corr_cols")
    if len(selected_cols) >= 2:
        fig = px.scatter_matrix(df[selected_cols], title="散点图矩阵")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.subheader("频率分析")
    
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    selected_col = st.selectbox("选择分类列", categorical_cols, key="freq_col")
    
    freq_table = df[selected_col].value_counts().reset_index()
    freq_table.columns = [selected_col, '频数']
    freq_table['频率'] = freq_table['频数'] / freq_table['频数'].sum()
    freq_table['百分比'] = freq_table['频率'] * 100
    
    st.dataframe(freq_table, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(freq_table, x=selected_col, y='频数', title=f"{selected_col} 频率分布")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(freq_table, values='频数', names=selected_col, title=f"{selected_col} 占比")
        st.plotly_chart(fig, use_container_width=True)