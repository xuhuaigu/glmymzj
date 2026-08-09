# livestock_analysis/1_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="生猪养殖数据分析", page_icon="🐷", layout="wide")

st.title("🐷 生猪养殖数据分析仪表板")

# ==================== 初始化数据 ====================
@st.cache_data
def generate_livestock_data():
    """生成模拟养殖数据"""
    np.random.seed(42)
    
    # 使用 'ME' 替代 'M'（Month End）
    # months = pd.date_range('2024-01-01', periods=12, freq='ME').strftime('%Y-%m')
    # months = pd.date_range('2024-01-01', periods=12, freq='ME').strftime('%Y年%m月')
    months = pd.date_range('2025-07-01', periods=12, freq='ME').strftime('%Y/%m')
    # 成活率趋势（从88%逐步提升到94%）
    survival_rate = 88 + np.cumsum(np.random.normal(0.6, 0.3, 12))
    survival_rate = np.clip(survival_rate, 85, 96) 
    
    # 料肉比趋势（逐步下降）
    fcr = 2.48 - np.cumsum(np.random.normal(0.02, 0.015, 12))
    fcr = np.clip(fcr, 2.28, 2.55)
    
    # PSY趋势（逐步提升）
    psy = 20 + np.cumsum(np.random.normal(0.4, 0.2, 12))
    psy = np.clip(psy, 19, 25)
    
    # 日增重趋势
    adg = 680 + np.cumsum(np.random.normal(5, 3, 12))
    adg = np.clip(adg, 650, 750)
    
    # 头均成本趋势（逐步下降）
    head_cost = 58 - np.cumsum(np.random.normal(0.3, 0.2, 12))
    head_cost = np.clip(head_cost, 50, 62)
    
    # 出栏头数（随PSY和成活率提升而增加）
    base_pigs = 8500
    head_count = base_pigs + np.cumsum(np.random.normal(120, 80, 12))
    head_count = np.clip(head_count, 8000, 10500)
    
    df = pd.DataFrame({
        '月份': months,
        '成活率': survival_rate,
        '料肉比': fcr,
        'PSY': psy,
        '日增重': adg,
        '头均成本': head_cost,
        '出栏头数': head_count
    })
    
    return df

# ==================== 加载数据 ====================
df = generate_livestock_data()

# ==================== 当前值计算 ====================
current = df.iloc[-1] # 取最后一行数据
targets = {
    '成活率': 95,
    '料肉比': 2.28,
    'PSY': 24,
    '日增重': 730,
    '头均成本': 52.5,
}

# ==================== 顶部KPI卡片 ====================
st.subheader("📊 核心KPI概览")

col1, col2, col3, col4, col5 = st.columns(5)
from components.metric_card_class import MetricCard, MetricCardDown, MetricCardDownGroup


# 创建卡片实例
card1 = MetricCard(
    label="成活率",
    icon="🐖",
    current_val=current['成活率'],
    prev_val=df.iloc[-2]['成活率'] if len(df) > 1 else current['成活率'],
    last_year_val=df.iloc[-13]['成活率'] if len(df) > 12 else current['成活率'],
    decimal=2
)

card2 = MetricCard(
    label="料肉比",
    icon="📊",
    current_val=current['料肉比'],
    prev_val=df.iloc[-2]['料肉比'] if len(df) > 1 else current['料肉比'],
    last_year_val=df.iloc[-13]['料肉比'] if len(df) > 12 else current['料肉比'],
    unit="",
    decimal=2
)

card3 = MetricCard(
    label="PSY",
    icon="📊",
    current_val=current['PSY'],
    prev_val=df.iloc[-2]['PSY'] if len(df) > 1 else current['PSY'],
    last_year_val=df.iloc[-13]['PSY'] if len(df) > 12 else current['PSY'],
    unit="",
    decimal=2
)

card4 = MetricCard(
    label="日增重",
    icon="📊",
    current_val=current['日增重'],
    prev_val=df.iloc[-2]['日增重'] if len(df) > 1 else current['日增重'],
    last_year_val=df.iloc[-13]['日增重'] if len(df) > 12 else current['日增重'],
    unit="g",
    decimal=0
)

card5 = MetricCard(
    label="头均成本(元/头)",
    icon="📊",
    current_val=current['头均成本'],
    prev_val=df.iloc[-2]['头均成本'] if len(df) > 1 else current['头均成本'],
    last_year_val=df.iloc[-13]['头均成本'] if len(df) > 12 else current['头均成本'],
    unit="",
    decimal=2
)

# 渲染
card1.render(col1)
card2.render(col2)
card3.render(col3)
card4.render(col4)
card5.render(col5)
st.divider()

# ==================== 趋势图表 ====================
st.subheader("📈 指标趋势分析")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 成活率", "📊 料肉比", "👶 PSY", "📏 日增重", "💰 头均成本", "🐖 农副价格"])

with tab1:
    fig = go.Figure() # 创建图表对象
    fig.add_trace(go.Scatter(
        x=df['月份'], y=df['成活率'],
        mode='lines+markers+text', # 线条+标记+文本
        name='成活率', # 图例名称
        line=dict(color='#52c41a', width=3),
        marker=dict(size=10),
        text=[f"{v:.1f}%" for v in df['成活率']],  # 设置标签
        textposition='top center', # 标签位置
        textfont=dict(size=16, color='#333'), # 设置标签样式
        hovertemplate="时间：<b>%{x}</b><br>成活率：<b>%{y:.1f}%</b><extra></extra>"
    ))
    fig.add_hline(y=targets['成活率'], line_dash="dash", line_color="red",
                  annotation_text=f"目标: {targets['成活率']}%", annotation_position="bottom right")
    fig.update_layout(
                        title="成活率趋势", 
                        xaxis_title="月份", 
                        yaxis_title="成活率 (%)", 
                        height=500, 
                        showlegend=True,
                        # legend=dict(x=0.5, y=1.05, xanchor='center', yanchor='bottom'), # 图例位置
                        hoverlabel=dict(
                                        bgcolor="white",           # 背景色
                                        bordercolor="#52c41a",     # 边框颜色
                                        font=dict(
                                            size=16,               # ⭐ 字体大小16
                                            color="#1a1a1a",       # 字体颜色
                                            family="Microsoft YaHei, Arial, sans-serif"  # 字体
                                        ),
                                        namelength=-1,             # 显示完整名称
                                        align="left"               # 左对齐
                                    )
                        )
    st.plotly_chart(fig, use_container_width=True) # 图表宽度填满容器 

with tab2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['月份'], y=df['料肉比'],
        mode='lines+markers',
        name='料肉比',
        line=dict(color='#1890ff', width=3),
        marker=dict(size=10)
    ))
    fig.add_hline(y=targets['料肉比'], line_dash="dash", line_color="red",
                  annotation_text=f"目标: {targets['料肉比']}", annotation_position="top right")
    fig.update_layout(title="料肉比趋势", xaxis_title="月份", yaxis_title="料肉比", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['月份'], y=df['PSY'],
        mode='lines+markers',
        name='PSY',
        line=dict(color='#faad14', width=3),
        marker=dict(size=10)
    ))
    fig.add_hline(y=targets['PSY'], line_dash="dash", line_color="red",
                  annotation_text=f"目标: {targets['PSY']}", annotation_position="bottom right")
    fig.update_layout(title="PSY趋势", xaxis_title="月份", yaxis_title="PSY", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['月份'], y=df['日增重'],
        mode='lines+markers',
        name='日增重',
        line=dict(color='#722ed1', width=3),
        marker=dict(size=10)
    ))
    fig.add_hline(y=targets['日增重'], line_dash="dash", line_color="red",
                  annotation_text=f"目标: {targets['日增重']}g", annotation_position="bottom right")
    fig.update_layout(title="日增重趋势", xaxis_title="月份", yaxis_title="日增重 (g)", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['月份'], y=df['头均成本'],
        mode='lines+markers',
        name='头均成本',
        line=dict(color='#ff4d4f', width=3),
        marker=dict(size=10)
    ))
    fig.add_hline(y=targets['头均成本'], line_dash="dash", line_color="green",
                  annotation_text=f"目标: ¥{targets['头均成本']}", annotation_position="top right")
    fig.update_layout(title="头均成本趋势", xaxis_title="月份", yaxis_title="头均成本 (¥)", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab6:
    import pandas as pd
    import streamlit as st
    import plotly.graph_objects as go
    # file_path = r"M:\Mxuhuaigu\xiangmuwenjian\mzj\mzjxuhuaigu\Python脚本\6--自动化\原料价格采集自动化流程\合并处理后的数据.xlsx"
    file_path = r"..\data_save\shengyishe\农副_报价_合并结果_20260809_172657.xlsx"
    df_master = pd.read_excel(file_path, sheet_name="合并去重数据")
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        chart_type = st.selectbox(
        "选择物料名称：",
        options = sorted(df_master['物料名称'].unique()),
        key="pig_viz_chart_type"
        )
    # 过滤出"生猪"类别
    df = df_master[df_master['物料名称'] == chart_type].copy()
    
    if df.empty:
        st.warning(f"⚠️ 没有找到'{chart_type}'类别的数据！")
    else:
        # 处理日期
        df['发布时间_dt'] = pd.to_datetime(df['发布时间'])
        df = df.sort_values('发布时间_dt')

        
        # 按日期分组计算平均价格
        daily_avg = df.groupby(df['发布时间_dt'].dt.date)['报价数值'].mean()
        
        # 获取单位
        unit = df['报价单位'].iloc[0] if not df['报价单位'].empty else '元/公斤'
        
        # 计算最高、最低、最新
        max_price = daily_avg.max()
        max_date = daily_avg.idxmax()
        min_price = daily_avg.min()
        min_date = daily_avg.idxmin()
        last_price = daily_avg.iloc[-1]
        last_date = daily_avg.index[-1]
        
        # ===== 创建图表 =====
        fig = go.Figure()
        
        # 主价格曲线
        fig.add_trace(go.Scatter(
            x=daily_avg.index,
            y=daily_avg.values,
            mode='lines+markers',
            name=f'{chart_type}价格',
            line=dict(color='#0060A9', width=3),
            marker=dict(size=8, color='#0060A9'),
            # ===== 修正：使用 f-string =====
            hovertemplate=f"日期：<b>%{{x|%Y%m%d}}</b><br>价格：<b>%{{y:.2f}} {unit}</b><extra></extra>"
        ))
        
        # 最高价标注
        fig.add_trace(go.Scatter(
            x=[max_date],
            y=[max_price],
            mode='markers+text',
            name='最高价',
            text=[f'最高:{max_price:.2f}'],
            textposition='top center',
            marker=dict(size=15, color='red', symbol='triangle-up'),
            textfont=dict(size=14, color='red'),
            # ===== 修正：使用 f-string =====
            hovertemplate=f"最高价：<b>%{{y:.2f}} {unit}</b><extra></extra>"
        ))
        
        # 最低价标注
        fig.add_trace(go.Scatter(
            x=[min_date],
            y=[min_price],
            mode='markers+text',
            name='最低价',
            text=[f'最低:{min_price:.2f}'],
            textposition='bottom center',
            marker=dict(size=15, color='green', symbol='triangle-down'),
            textfont=dict(size=14, color='green'),
            # ===== 修正：使用 f-string =====
            hovertemplate=f"最低价：<b>%{{y:.2f}} {unit}</b><extra></extra>"
        ))
        
        # 最新价标注
        fig.add_trace(go.Scatter(
            x=[last_date],
            y=[last_price],
            mode='markers+text',
            name='最新价',
            text=[f'最新:{last_price:.2f}'],
            textposition='top center',
            marker=dict(size=15, color='blue', symbol='star'),
            textfont=dict(size=14, color='blue'),
            # ===== 修正：使用 f-string =====
            hovertemplate=f"最新价：<b>%{{y:.2f}} {unit}</b><extra></extra>"
        ))
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=f"{chart_type}价格变化趋势",
                font=dict(size=18, color='#1a1a1a')
            ),
            xaxis_title=dict(
                text="日期",
                font=dict(size=14)
            ),
            yaxis_title=dict(
                text=f"{unit}",
                font=dict(size=14)
            ),
            height=500,
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12)
            ),

            # hovermode='x', # 悬停时显示最近的数据点
            # hoverdistance=10,  # 鼠标距离数据点10像素内触发
            hoverlabel=dict(
                bgcolor="white",
                bordercolor="#0060A9",
                font=dict(
                    size=16,
                    color="#1a1a1a",
                    family="Microsoft YaHei, Arial, sans-serif"
                ),
                namelength=-1,
                align="left"
            )
        )
        
        # 设置x轴
        fig.update_xaxes(
            tickangle=0,
            tickfont=dict(size=16),
            tickformat="%Y%m",
            nticks=12
        )
        
        # 设置y轴
        y_min = daily_avg.min()
        y_max = daily_avg.max()
        y_padding = (y_max - y_min) * 0.1
        fig.update_yaxes(
            range=[y_min - y_padding, y_max + y_padding],
            tickfont=dict(size=16)
        )
        
        with col2:
            # 显示图表
            st.plotly_chart(fig, use_container_width=True)
 

        
 

st.divider()

# ==================== 数据明细 ====================
with st.expander("📋 数据明细表", expanded=False):
    # 格式化显示
    display_df = df.copy()
    st.dataframe(display_df.style.format({
        '成活率': '{:.1f}%',
        '料肉比': '{:.2f}',
        'PSY': '{:.1f}',
        '日增重': '{:.0f}',
        '头均成本': '¥{:.1f}',
        '出栏头数': '{:,.0f}'
    }), use_container_width=True)
    
    # 下载按钮
    csv = df.to_csv(index=False)
    st.download_button("📥 下载数据", csv, "livestock_data.csv", "text/csv")

st.divider()

# ==================== 数据总结 ====================
st.subheader("📊 指标总览")

col1, col2 = st.columns([2, 1])

with col1:
    summary_df = pd.DataFrame({
        '指标': ['成活率', '料肉比', 'PSY', '日增重', '头均成本'],
        '当前值': [f"{current['成活率']:.1f}%", f"{current['料肉比']:.2f}", f"{current['PSY']:.1f}", f"{current['日增重']:.0f}g", f"¥{current['头均成本']:.1f}"],
        '目标值': [f"{targets['成活率']}%", f"{targets['料肉比']}", f"{targets['PSY']}", f"{targets['日增重']}g", f"¥{targets['头均成本']}"],
        '差距': [f"{targets['成活率'] - current['成活率']:.1f}%", f"{current['料肉比'] - targets['料肉比']:.2f}", f"{targets['PSY'] - current['PSY']:.1f}", f"{targets['日增重'] - current['日增重']:.0f}g", f"¥{current['头均成本'] - targets['头均成本']:.1f}"],
    })
    
    # 添加状态列
    status = []
    for i, row in summary_df.iterrows():
        if i == 0:  # 成活率：目标减当前，正数表示未达标
            diff = targets['成活率'] - current['成活率']
            status.append('🔴 需改善' if diff > 1 else '🟢 达标')
        elif i == 1:  # 料肉比：当前减目标，正数表示未达标
            diff = current['料肉比'] - targets['料肉比']
            status.append('🔴 需改善' if diff > 0.05 else '🟢 达标')
        elif i == 2:  # PSY：目标减当前，正数表示未达标
            diff = targets['PSY'] - current['PSY']
            status.append('🔴 需改善' if diff > 0.5 else '🟢 达标')
        elif i == 3:  # 日增重：目标减当前，正数表示未达标
            diff = targets['日增重'] - current['日增重']
            status.append('🔴 需改善' if diff > 10 else '🟢 达标')
        else:  # 头均成本：当前减目标，正数表示未达标
            diff = current['头均成本'] - targets['头均成本']
            status.append('🔴 需改善' if diff > 1 else '🟢 达标')
    
    summary_df['状态'] = status
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

with col2:
    st.info("""
    ### 📌 核心发现
    
    - **成活率**：当前 {:.1f}%，距目标 {:.1f}%
    - **料肉比**：当前 {:.2f}，距目标 {:.2f}
    - **PSY**：当前 {:.1f}，距目标 {:.1f}
    - **日增重**：当前 {:.0f}g，距目标 {:.0f}g
    - **头均成本**：当前 ¥{:.1f}，距目标 ¥{:.1f}
    """.format(
        current['成活率'], targets['成活率'] - current['成活率'],
        current['料肉比'], current['料肉比'] - targets['料肉比'],
        current['PSY'], targets['PSY'] - current['PSY'],
        current['日增重'], targets['日增重'] - current['日增重'],
        current['头均成本'], current['头均成本'] - targets['头均成本']
    ))




