import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.title("⏰ 时间序列分析")

# 生成时间序列数据
@st.cache_data
def load_data():
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    n = len(dates)
    
    trend = np.linspace(0, 100, n)
    seasonal = 20 * np.sin(2 * np.pi * np.arange(n) / 365)
    noise = np.random.normal(0, 10, n)
    
    data = {
        '日期': dates,
        '销售额': 1000 + trend + seasonal + noise,
        '利润': 200 + trend * 0.3 + seasonal * 0.5 + noise * 0.5,
        '访问量': 5000 + trend * 20 + seasonal * 500 + noise * 50
    }
    return pd.DataFrame(data)

df = load_data()

# 选择指标
metric = st.selectbox(
    "选择分析指标",
    ["销售额", "利润", "访问量"],
    key="ts_metric"
)

# 时间范围
min_date = df['日期'].min().date()
max_date = df['日期'].max().date()
date_range = st.date_input(
    "选择时间范围",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date,
    key="ts_date_range"
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[(df['日期'].dt.date >= start_date) & (df['日期'].dt.date <= end_date)]
else:
    df_filtered = df

# 重采样频率
resample_freq = st.selectbox(
    "重采样频率",
    ["日", "周", "月", "季度"],
    key="ts_freq"
)

freq_map = {"日": 'D', "周": 'W', "月": 'M', "季度": 'Q'}

df_resampled = df_filtered.set_index('日期').resample(freq_map[resample_freq]).agg({
    '销售额': 'mean',
    '利润': 'mean',
    '访问量': 'mean'
}).reset_index()

# 时间序列图
st.subheader(f"{metric} 时间序列图")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_resampled['日期'], y=df_resampled[metric],
                         mode='lines+markers',
                         name=metric,
                         line=dict(width=2)))
fig.update_layout(title=f"{metric} 趋势",
                  xaxis_title="日期",
                  yaxis_title=metric,
                  hovermode='x unified')
st.plotly_chart(fig, use_container_width=True)

# 移动平均
st.subheader("移动平均分析")

window = st.slider("移动平均窗口（天）", 7, 90, 30, key="ts_window")
df_filtered['移动平均'] = df_filtered[metric].rolling(window=window).mean()

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df_filtered['日期'], y=df_filtered[metric],
                          mode='lines', name='原始数据', opacity=0.5))
fig2.add_trace(go.Scatter(x=df_filtered['日期'], y=df_filtered['移动平均'],
                          mode='lines', name=f'{window}日移动平均',
                          line=dict(color='red', width=2)))
fig2.update_layout(title="移动平均分析", xaxis_title="日期", yaxis_title=metric)
st.plotly_chart(fig2, use_container_width=True)

# 季节性分析
st.subheader("季节性分析")

df['月份'] = df['日期'].dt.month
df['年份'] = df['日期'].dt.year
monthly_avg = df.groupby('月份')[metric].mean().reset_index()

fig3 = px.bar(monthly_avg, x='月份', y=metric, 
              title=f"{metric} 月度季节性模式",
              labels={'月份': '月份', metric: metric})
st.plotly_chart(fig3, use_container_width=True)

# 年度对比
st.subheader("年度对比")

years = df['年份'].unique()
selected_years = st.multiselect("选择对比年份", years, default=years[:2], key="ts_years")

if selected_years:
    fig4 = go.Figure()
    for year in selected_years:
        year_data = df[df['年份'] == year].copy()
        year_data['日期'] = year_data['日期'].dt.strftime('%m-%d')
        fig4.add_trace(go.Scatter(x=year_data['日期'], y=year_data[metric],
                                  mode='lines', name=str(year)))
    fig4.update_layout(title=f"{metric} 年度对比", xaxis_title="月-日", yaxis_title=metric)
    st.plotly_chart(fig4, use_container_width=True)

# 数据导出
st.subheader("数据导出")

if st.button("导出当前数据", key="ts_export"):
    csv = df_resampled.to_csv(index=False)
    st.download_button(
        label="下载CSV",
        data=csv,
        file_name=f"timeseries_{metric}.csv",
        mime="text/csv",
        key="ts_download"
    )