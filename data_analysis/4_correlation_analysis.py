import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.title("🔗 相关性分析")

# 生成数据
@st.cache_data
def load_data():
    np.random.seed(42)
    n = 500
    data = {
        '销售额': np.random.normal(10000, 2000, n),
        '广告投入': np.random.normal(1000, 300, n),
        '客户数': np.random.poisson(100, n),
        '评分': np.random.uniform(3, 5, n),
        '员工数': np.random.poisson(50, n),
        '门店面积': np.random.normal(200, 50, n)
    }
    data['销售额'] = data['销售额'] + data['广告投入'] * 2
    data['客户数'] = data['客户数'] + data['评分'] * 10
    return pd.DataFrame(data)

df = load_data()

# 选择相关性方法
method = st.selectbox(
    "相关性方法",
    ["皮尔逊(Pearson)", "斯皮尔曼(Spearman)", "肯德尔(Kendall)"],
    key="corr_method"
)

method_map = {
    "皮尔逊(Pearson)": "pearson",
    "斯皮尔曼(Spearman)": "spearman",
    "肯德尔(Kendall)": "kendall"
}

# 计算相关系数矩阵
corr_matrix = df.corr(method=method_map[method])

# 显示相关系数矩阵
st.subheader(f"{method} 相关系数矩阵")

col1, col2 = st.columns([2, 1])

with col1:
    fig = px.imshow(corr_matrix, text_auto=True, aspect='auto',
                    color_continuous_scale='RdBu_r',
                    title="相关系数热力图")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.info(f"""
    ### 相关系数解读
    - **1.0**: 完全正相关
    - **0.7-0.9**: 强正相关
    - **0.3-0.7**: 中等正相关
    - **0.0-0.3**: 弱正相关
    - **0.0**: 无相关
    - **-0.3-0.0**: 弱负相关
    - **-0.7--0.3**: 中等负相关
    - **-0.9--0.7**: 强负相关
    - **-1.0**: 完全负相关
    """)

# 强相关分析
st.subheader("强相关关系分析")

threshold = st.slider("相关系数阈值", 0.0, 1.0, 0.5, key="corr_threshold")
strong_corrs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        if abs(corr_matrix.iloc[i, j]) >= threshold:
            strong_corrs.append({
                '变量1': corr_matrix.columns[i],
                '变量2': corr_matrix.columns[j],
                '相关系数': corr_matrix.iloc[i, j],
                '相关强度': '强正相关' if corr_matrix.iloc[i, j] > 0 else '强负相关'
            })

if strong_corrs:
    strong_df = pd.DataFrame(strong_corrs).sort_values('相关系数', ascending=False)
    st.dataframe(strong_df, use_container_width=True)
    
    selected_pair = st.selectbox(
        "选择要详细分析的变量对",
        [f"{row['变量1']} - {row['变量2']}" for _, row in strong_df.iterrows()],
        key="corr_pair"
    )
    
    if selected_pair:
        var1, var2 = selected_pair.split(' - ')
        fig = px.scatter(df, x=var1, y=var2, trendline="ols",
                         title=f"{var1} vs {var2} (相关系数: {corr_matrix.loc[var1, var2]:.3f})")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"没有找到相关系数绝对值大于 {threshold} 的变量对")

# 散点图矩阵
st.subheader("散点图矩阵")
selected_vars = st.multiselect(
    "选择要显示的变量",
    df.columns.tolist(),
    default=df.columns[:4].tolist(),
    key="corr_vars"
)

if len(selected_vars) >= 2:
    fig = px.scatter_matrix(df[selected_vars], title="变量关系散点图矩阵")
    st.plotly_chart(fig, use_container_width=True)