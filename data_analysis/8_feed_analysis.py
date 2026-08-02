# data_analysis/8_feed_analysis.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
from components.metric_card_class import MetricCardMYSystem  # 自定义卡片
from plotly.subplots import make_subplots # 创建子图
from data_processing import data_loader # 引入数据处理模块
 
st.set_page_config(page_title="饲料分析", page_icon="🌾", layout="wide")

st.title("🌾 饲料分析")

# ==================== 数据加载函数 ====================
@st.cache_data
def load_feed_data():
    """加载饲料数据"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=12, freq='ME')
    
    df = pd.DataFrame({
        '日期': dates.strftime('%Y年%m月'),
        '玉米价格': np.random.normal(2800, 200, 12),
        '豆粕价格': np.random.normal(3800, 300, 12),
        '小麦价格': np.random.normal(2500, 150, 12),
        '鱼粉价格': np.random.normal(12000, 500, 12),
        '饲料产量': np.random.normal(50000, 5000, 12),
        '饲料销量': np.random.normal(48000, 4000, 12),
    })
    return df

# ==================== 数据源选择 ====================
st.subheader("📁 数据源选择")

col1, col2 = st.columns([2, 3])

with col1:
    data_source = st.radio(
        "选择数据源",
        ["模拟数据", "上传Excel文件"],
        horizontal=False,
        key="feed_data_source"
    )

with col2:
    if data_source == "模拟数据":
        st.info("📊 使用模拟数据展示")
        if st.button("🔄 刷新模拟数据"):
            st.cache_data.clear()
            st.rerun()
        df = load_feed_data()
    else:
        uploaded_file = st.file_uploader(
            "选择Excel文件",
            type=['xlsx', 'xls'],
            key="feed_uploader"
        )
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.success(f"✅ 成功加载 {len(df)} 行数据，{len(df.columns)} 列")
        else:
            df = load_feed_data()
            st.info("💡 请上传Excel文件，或切换回「模拟数据」")

# st.divider()

# ==================== 分析配置 ====================
st.subheader("⚙️ 分析配置")

# 第一行：价格品种选择
col1, col2 = st.columns(2)

with col1:
    price_cols = [col for col in df.columns if '价格' in col or '报价数值' in col]
    selected_prices = st.multiselect(
        "选择要显示的价格品种",
        options=price_cols,
        default=price_cols[:2] if len(price_cols) >= 2 else price_cols,
        key="price_select"
    )

with col2:
    # 时间范围选择
    if '日期' in df.columns:
        date_options = df['日期'].tolist()
        if len(date_options) > 0:
            start_date, end_date = st.select_slider(
                "选择时间范围",
                options=date_options,
                value=(date_options[0], date_options[-1]),
                key="date_range"
            )

st.divider()

# ==================== 主内容区域 ====================
if df is not None and not df.empty:
    
    # 根据时间范围过滤数据
    if '日期' in df.columns and len(date_options) > 0:
        mask = (df['日期'] >= start_date) & (df['日期'] <= end_date)
        filtered_df = df[mask].copy()
    else:
        filtered_df = df.copy()
    
    if filtered_df.empty:
        st.warning("⚠️ 当前时间范围内没有数据")
        st.stop()
    
    st.subheader("📊 饲料核心指标")
    
    # 计算最新值
    latest = filtered_df.iloc[-1] # 最后一行数据
    
    col1, col2, col3, col4, col5 = st.columns(5)
    feed_index_card = data_loader.load_from_database(table_name = 'feed_index_card', limit = 1000, config_name='mysql_test')

    card1 = MetricCardMYSystem(
        label="全程料比",
        icon="📊",
        current_val=feed_index_card.loc[feed_index_card["label"] == "全程料比", "current_val"].iloc[0],
        prev_val=feed_index_card.loc[feed_index_card["label"] == "全程料比", "pre_val"].iloc[0],
        last_year_val=feed_index_card.loc[feed_index_card["label"] == "全程料比", "last_year_val"].iloc[0],
        target=feed_index_card.loc[feed_index_card["label"] == "全程料比", "target"].iloc[0],
        unit=feed_index_card.loc[feed_index_card["label"] == "全程料比", "unit"].iloc[0],
        decimal=feed_index_card.loc[feed_index_card["label"] == "全程料比", "digit_num"].iloc[0],
        background_color="#c584aa"
    )

    card2 = MetricCardMYSystem(
        label="头均饲料成本",
        icon="📊",
        current_val=feed_index_card.loc[feed_index_card["label"] == "头均饲料成本", "current_val"].iloc[0],
        prev_val=feed_index_card.loc[feed_index_card["label"] == "头均饲料成本", "pre_val"].iloc[0],
        last_year_val=feed_index_card.loc[feed_index_card["label"] == "头均饲料成本", "last_year_val"].iloc[0],
        target=feed_index_card.loc[feed_index_card["label"] == "头均饲料成本", "target"].iloc[0],
        unit=feed_index_card.loc[feed_index_card["label"] == "头均饲料成本", "unit"].iloc[0],
        decimal=feed_index_card.loc[feed_index_card["label"] == "头均饲料成本", "digit_num"].iloc[0],
    )

    card3 = MetricCardMYSystem(
        label="饲料总成本",
        icon="📊",
        current_val=feed_index_card.loc[feed_index_card["label"] == "饲料总成本", "current_val"].iloc[0] / 10000,
        prev_val=feed_index_card.loc[feed_index_card["label"] == "饲料总成本", "pre_val"].iloc[0] / 10000,
        last_year_val=feed_index_card.loc[feed_index_card["label"] == "饲料总成本", "last_year_val"].iloc[0] / 10000,
        target=feed_index_card.loc[feed_index_card["label"] == "饲料总成本", "target"].iloc[0] / 10000,
        # unit=feed_index_card.loc[feed_index_card["label"] == "饲料总成本", "unit"].iloc[0],
        unit="万元", # 固定单位为万元
        decimal=feed_index_card.loc[feed_index_card["label"] == "饲料总成本", "digit_num"].iloc[0],
    )

    card4 = MetricCardMYSystem(
        label="保育料比",
        icon="📊",
        current_val=feed_index_card.loc[feed_index_card["label"] == "保育料比", "current_val"].iloc[0],
        prev_val=feed_index_card.loc[feed_index_card["label"] == "保育料比", "pre_val"].iloc[0],
        last_year_val=feed_index_card.loc[feed_index_card["label"] == "保育料比", "last_year_val"].iloc[0],
        target=feed_index_card.loc[feed_index_card["label"] == "保育料比", "target"].iloc[0],
        unit=feed_index_card.loc[feed_index_card["label"] == "保育料比", "unit"].iloc[0],
        decimal=feed_index_card.loc[feed_index_card["label"] == "保育料比", "digit_num"].iloc[0]
    )

    card5 = MetricCardMYSystem(
        label="育肥料比",
        icon="📊",
        current_val=feed_index_card.loc[feed_index_card["label"] == "育肥料比", "current_val"].iloc[0],
        prev_val=feed_index_card.loc[feed_index_card["label"] == "育肥料比", "pre_val"].iloc[0],
        last_year_val=feed_index_card.loc[feed_index_card["label"] == "育肥料比", "last_year_val"].iloc[0],
        target=feed_index_card.loc[feed_index_card["label"] == "育肥料比", "target"].iloc[0],
        unit=feed_index_card.loc[feed_index_card["label"] == "育肥料比", "unit"].iloc[0],
        decimal=feed_index_card.loc[feed_index_card["label"] == "育肥料比", "digit_num"].iloc[0]
    )


    # 渲染
    card1.render(col1)
    card2.render(col2)
    card3.render(col3)
    card4.render(col4)
    card5.render(col5)
    st.divider()

# ==================== 效率趋势分析 ====================
st.subheader("📈 效率趋势分析")

# 时间粒度切换按钮
granularity = st.radio(
        "时间粒度",
        ["年度", "月度", "日度"],
        index=0,
        horizontal=True,
        key="granularity1"
)

# ==================== 生成效率数据 ====================
@st.cache_data
def generate_efficiency_data():
    """生成效率趋势模拟数据"""
    np.random.seed(42)
    
    # 年度数据（12个月）
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    
    # 全程料比实际值（从2.45逐步改善到2.30）
    fcr_trend = [2.45 - i * 0.015 + np.random.normal(0, 0.02) for i in range(12)]
    fcr_trend = [round(max(2.20, min(2.55, x)), 3) for x in fcr_trend]
    
    # 料比目标线（恒定2.28）
    fcr_target = [2.28] * 12
    
    # 去年同期料比
    fcr_last_year = [round(x + 0.08 + np.random.normal(0, 0.02), 3) for x in fcr_trend]
    
    # 日增重（从680逐步提升到720）
    adg_trend = [680 + i * 3.5 + np.random.normal(0, 5) for i in range(12)]
    adg_trend = [round(max(650, min(750, x)), 1) for x in adg_trend]
    
    # 成活率（从91%逐步提升到95%）
    survival_trend = [91 + i * 0.35 + np.random.normal(0, 0.3) for i in range(12)]
    survival_trend = [round(max(88, min(96, x)), 1) for x in survival_trend]
    
    annual_df = pd.DataFrame({
        '月份': months,
        '料比实际值': fcr_trend,
        '料比目标值': fcr_target,
        '去年同期料比': fcr_last_year,
        '日增重': adg_trend,
        '成活率': survival_trend
    })
    
    # 月度数据（30天）
    days = [f'{i+1}日' for i in range(30)]
    monthly_mean_fcr = fcr_trend[-1]
    daily_fcr = [round(max(2.15, min(2.50, monthly_mean_fcr + np.random.normal(0, 0.04))), 3) for _ in range(30)]
    daily_adg = [round(max(600, min(780, adg_trend[-1] + np.random.normal(0, 12))), 1) for _ in range(30)]
    daily_survival = [round(max(88, min(97, survival_trend[-1] + np.random.normal(0, 0.8))), 1) for _ in range(30)]
    
    monthly_df = pd.DataFrame({
        '日期': days,
        '料比实际值': daily_fcr,
        '料比目标值': [2.28] * 30,
        '日增重': daily_adg,
        '成活率': daily_survival
    })
    
    return annual_df, monthly_df

annual_df, monthly_df = generate_efficiency_data()

# ==================== 根据粒度选择数据 ====================
if granularity == "年度":
    df_eff = annual_df
    x_col = '月份'
elif granularity == "月度":
    df_eff = monthly_df
    x_col = '日期'
else:  # 日度
    hours = [f'{i}:00' for i in range(24)]
    base_fcr = 2.30
    hourly_fcr = [round(base_fcr + np.sin(i/24 * 2 * np.pi) * 0.06 + np.random.normal(0, 0.015), 3) for i in range(24)]
    hourly_adg = [round(710 + np.sin((i+6)/24 * 2 * np.pi) * 20 + np.random.normal(0, 5), 1) for i in range(24)]
    hourly_survival = [round(94.5 + np.random.normal(0, 0.3), 1) for _ in range(24)]
    
    df_eff = pd.DataFrame({
        '日期': hours,
        '料比实际值': hourly_fcr,
        '料比目标值': [2.28] * 24,
        '日增重': hourly_adg,
        '成活率': hourly_survival
    })
    x_col = '日期'

# ==================== 创建双图布局 ====================
col_main, col_sub = st.columns([1, 1])

with col_main:
    st.subheader("📉 全程料比趋势")
    
    fig_main = go.Figure()
    
    # 实线·蓝色：实际值
    fig_main.add_trace(go.Scatter(
        x=df_eff[x_col],
        y=df_eff['料比实际值'],
        mode='lines+markers',
        name='实际值',
        line=dict(color='#1890ff', width=2.5),
        marker=dict(size=6, color='#1890ff')
    ))
    
    # 虚线·绿色：目标线
    fig_main.add_trace(go.Scatter(
        x=df_eff[x_col],
        y=df_eff['料比目标值'],
        mode='lines',
        name='目标值 (2.28)',
        line=dict(color='#52c41a', width=2, dash='dash')
    ))
    
    # 虚线·灰色：去年同期（仅年度显示）
    if granularity == "年度":
        fig_main.add_trace(go.Scatter(
            x=df_eff[x_col],
            y=df_eff['去年同期料比'],
            mode='lines+markers',
            name='去年同期',
            line=dict(color='#8c8c8c', width=2, dash='dot'),
            marker=dict(size=5, color='#8c8c8c')
        ))
    
    fig_main.update_layout(
        height=350,
        yaxis_title='料肉比',
        xaxis_title=granularity,
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=40, r=20, t=30, b=40),
        template='plotly_white'
    )
    
    st.plotly_chart(fig_main, use_container_width=True)

with col_sub:
    st.subheader("📊 日增重 & 成活率")
    
    fig_sub = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 左轴：日增重（柱状图）
    fig_sub.add_trace(
        go.Bar(
            x=df_eff[x_col],
            y=df_eff['日增重'],
            name='日增重',
            marker_color='#1890ff',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    # 右轴：成活率（折线图）
    fig_sub.add_trace(
        go.Scatter(
            x=df_eff[x_col],
            y=df_eff['成活率'],
            mode='lines+markers',
            name='成活率',
            line=dict(color='#ff6b6b', width=2.5),
            marker=dict(size=6, color='#ff6b6b')
        ),
        secondary_y=True
    )
    
    fig_sub.update_layout(
        height=350,
        xaxis_title=granularity,
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=40, r=20, t=30, b=40),
        template='plotly_white'
    )
    
    fig_sub.update_yaxes(title_text="日增重 (g/天)", secondary_y=False)
    fig_sub.update_yaxes(title_text="成活率 (%)", secondary_y=True)
    
    st.plotly_chart(fig_sub, use_container_width=True)

# ==================== 效率数据明细 ====================
with st.expander("📋 效率数据明细", expanded=False):
    st.dataframe(df_eff, use_container_width=True)

st.caption("💡 点击顶部 [年度] [月度] [日度] 切换时间粒度")



# ==================== ③ 成本分解区（金额→技术双层视图） ====================
st.markdown("---")
st.subheader("💰 成本分解区")

col_cost_left, col_cost_right = st.columns([1, 1])

with col_cost_left:
    st.markdown("##### 🍩 上层：成本金额环形图")
    
    # 环形图数据
    cost_data = {
        '成本项': ['饲料成本', '人工成本', '兽药疫苗', '折旧管理', '死亡损耗'],
        '占比': [63, 15, 8, 10, 4],
        '金额': [3.42, 0.81, 0.44, 0.54, 0.22],
        '颜色': ['#ff4d4f', '#1890ff', '#52c41a', '#8c8c8c', '#cf1322']
    }
    cost_df = pd.DataFrame(cost_data)
    
    # 创建环形图
    fig_donut = go.Figure()
    
    fig_donut.add_trace(go.Pie(
        labels=cost_df['成本项'],
        values=cost_df['占比'],
        hole=0.55,
        marker=dict(colors=cost_df['颜色'], line=dict(color='white', width=2)),
        textinfo='label+percent',
        textposition='outside',
        hoverinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>占比：%{percent}<br>金额：¥%{value:.2f}亿<extra></extra>',
        pull=[0.08 if i == 0 else 0 for i in range(len(cost_df))],
        sort=False,
        showlegend=False
    ))
    
    # 中心显示总成本
    fig_donut.add_annotation(
        text='总成本<br>¥5.44亿',
        x=0.5, y=0.5,
        font=dict(size=18, color='#1a1a1a'),
        showarrow=False,
        align='center'
    )
    
    fig_donut.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=20, b=20),
        template='plotly_white',
        annotations=[dict(
            text='点击扇区查看分解',
            x=0.5, y=-0.08,
            font=dict(size=11, color='#999'),
            showarrow=False
        )]
    )
    
    st.plotly_chart(fig_donut, use_container_width=True)
    
    # 扇区图例
    legend_cols = st.columns(5)
    for i, row in cost_df.iterrows():
        with legend_cols[i]:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:4px;">
                <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{row['颜色']};"></span>
                <span style="font-size:12px;color:#666;">{row['成本项']}</span>
            </div>
            """, unsafe_allow_html=True)

with col_cost_right:
    st.markdown("##### 🌊 下层：成本偏差瀑布图（饲料成本三层分解）")
    
    # 瀑布图数据
    waterfall_data = {
        '项目': ['目标基准', '+ 料比偏差', '+ 重量偏差', '+ 单价偏差', '实际成本'],
        '数值': [2.88, 0.22, 0.10, 0.12, 3.32],
        '颜色': ['#8c8c8c', '#ff4d4f', '#ff4d4f', '#ff4d4f', '#595959'],
        '测量': ['absolute', 'relative', 'relative', 'relative', 'total']
    }
    waterfall_df = pd.DataFrame(waterfall_data)
    
    # 创建瀑布图
    fig_waterfall = go.Figure()
    
    fig_waterfall.add_trace(go.Waterfall(
        name='成本偏差',
        orientation='v',
        measure=waterfall_df['测量'],
        x=waterfall_df['项目'],
        y=waterfall_df['数值'],
        text=[f'¥{v:.2f}亿' for v in waterfall_df['数值']],
        textposition='outside',
        connector={'line': {'color': '#d9d9d9', 'width': 2}},
        increasing={'marker': {'color': '#ff4d4f'}},
        decreasing={'marker': {'color': '#52c41a'}},
        totals={'marker': {'color': '#595959'}},
        hovertemplate='<b>%{x}</b><br>金额：¥%{y:.2f}亿<extra></extra>',
        textfont=dict(size=12)
    ))
    
    # 添加差值标注
    fig_waterfall.add_annotation(
        x=3,
        y=3.3,
        text='总偏差 ¥0.44亿',
        font=dict(size=14, color='#ff4d4f'),
        showarrow=False,
        bgcolor='rgba(255,241,240,0.8)',
        bordercolor='#ff4d4f',
        borderwidth=1,
        borderpad=4
    )
    
    fig_waterfall.update_layout(
        height=380,
        yaxis_title='金额（亿元）',
        margin=dict(l=40, r=20, t=30, b=40),
        template='plotly_white',
        showlegend=False
    )
    
    st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # 偏差来源说明
    st.markdown("""
    <div style="display:flex;gap:20px;font-size:12px;color:#666;flex-wrap:wrap;">
        <span>🔴 料比偏差：+¥0.22亿（最大偏差项）</span>
        <span>🟠 重量偏差：+¥0.10亿</span>
        <span>🟡 单价偏差：+¥0.12亿</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 悬停查看详情 · 点击环形图扇区可切换下层瀑布图对应成本项")

# ==================== ④ 场线对标区（红绿灯预警排名） ====================
st.subheader("🏆 场线对标区 — 红绿灯预警排名")

# 场线数据
farm_data = pd.DataFrame({
    '排名': [1, 2, 3, 4, 5, 6, 7],
    '场线': ['7号场', '6号场', '1号场', '3号场', '8号场', '4号场', '2号场'],
    '料比': [2.25, 2.28, 2.30, 2.35, 2.38, 2.42, 2.45],
    '灯': ['🟢', '🟢', '🟡', '🟡', '🔴', '🔴', '🔴'],
    '趋势': ['↓ 改善', '→ 持平', '↓ 改善', '↑ 恶化', '↑ 恶化', '↑ 恶化', '↑ 恶化'],
    '趋势颜色': ['#52c41a', '#8c8c8c', '#52c41a', '#ff4d4f', '#ff4d4f', '#ff4d4f', '#ff4d4f'],
    '成活率': [96, 95, 93, 91, 89, 88, 88],
    '成活率颜色': ['#52c41a', '#52c41a', '#fa8c16', '#ff4d4f', '#ff4d4f', '#ff4d4f', '#ff4d4f'],
    '蓝耳状态': ['全面净化 ✅', '一阶段 🔵', '一阶段 🔵', '初阶段 🟠', '初阶段 🟠', '初阶段 🟠', '未启动 🔴']
})

# 生成热力条形排名图
fig_farm = go.Figure()

# 添加热力条形
bar_colors = ['#52c41a' if x <= 2.28 else '#fa8c16' if x <= 2.33 else '#ff4d4f' for x in farm_data['料比']]

fig_farm.add_trace(go.Bar(
    y=farm_data['场线'],
    x=farm_data['料比'],
    orientation='h',
    marker=dict(
        color=bar_colors,
        line=dict(color='white', width=2),
        cornerradius=4
    ),
    text=[f"{x:.2f}" for x in farm_data['料比']],
    textposition='outside',
    textfont=dict(size=13, color='#1a1a1a'),
    hovertemplate='<b>%{y}</b><br>料比：%{x:.2f}<br>排名：第%{customdata}名<extra></extra>',
    customdata=farm_data['排名'],
    width=0.8
))

# 添加目标线
fig_farm.add_vline(x=2.28, line_dash="dash", line_color="#52c41a", 
                   annotation_text="目标线 2.28", annotation_position="bottom right")

fig_farm.update_layout(
    height=320,
    xaxis_title='料比',
    yaxis_title='',
    xaxis=dict(range=[2.10, 2.60], tickfont=dict(size=12)),
    template='plotly_white',
    showlegend=False,
    margin=dict(l=10, r=60, t=30, b=30),
    plot_bgcolor='#fafafa'
)

st.plotly_chart(fig_farm, use_container_width=True)

# 场线数据表格（样式美化）
st.markdown("##### 📋 场线详细数据")

# 创建带样式的DataFrame显示
styled_df = farm_data.copy()
styled_df['排名'] = styled_df['排名'].apply(lambda x: f"#{x}")
styled_df['料比'] = styled_df['料比'].apply(lambda x: f"{x:.2f}")
styled_df['成活率'] = styled_df['成活率'].apply(lambda x: f"{x}%")

st.dataframe(
    styled_df,
    column_config={
        '排名': '排名',
        '场线': '场线名称',
        '料比': '料比',
        '灯': '状态',
        '趋势': '趋势',
        '成活率': '成活率',
        '蓝耳状态': '蓝耳状态'
    },
    hide_index=True,
    use_container_width=True
)

# 快速判断卡片
st.markdown("##### 🎯 总裁快速判断")

col_judge1, col_judge2, col_judge3 = st.columns(3)

with col_judge1:
    red_count = len(farm_data[farm_data['灯'] == '🔴'])
    st.metric(
        label="🔴 红灯场线数量",
        value=f"{red_count} / {len(farm_data)}",
        delta="43% 场线严重偏离" if red_count > 2 else "正常范围",
        delta_color="inverse" if red_count > 2 else "normal"
    )

with col_judge2:
    improving = len(farm_data[farm_data['趋势'].str.contains('改善')])
    st.metric(
        label="📈 正在改善的场线",
        value=f"{improving} 条",
        delta=f"{improving/len(farm_data)*100:.0f}% 正在改善"
    )

with col_judge3:
    purified = len(farm_data[farm_data['蓝耳状态'].str.contains('全面净化|一阶段')])
    st.metric(
        label="🧬 蓝耳净化推进中",
        value=f"{purified} / {len(farm_data)}",
        delta=f"{purified/len(farm_data)*100:.0f}% 已启动" if purified > 0 else "需要加速推进",
        delta_color="inverse" if purified < 3 else "normal"
    )

st.markdown("---")
st.caption("💡 点击场线行可下钻查看详情 · 点击列头可排序")

# ==================== ⑤ 利益联动区（指标→奖金传导可视化） ====================
st.subheader("🔗 利益联动区 — 指标→奖金传导可视化")

st.markdown("""
<div style="background:#f0f7ff;padding:12px 16px;border-radius:8px;border-left:4px solid #1890ff;margin-bottom:16px;">
    <span style="font-weight:600;">💡 核心逻辑：</span>
    料比改善 + 成活率提升 → 成本降低 → 利润增加 → 奖金池增长 → 员工收入翻倍
</div>
""", unsafe_allow_html=True)

col_slider1, col_slider2 = st.columns(2)

with col_slider1:
    fcr_improvement = st.slider(
        "📊 料比改善量",
        min_value=0.00,
        max_value=0.20,
        value=0.10,
        step=0.01,
        help="拖动滑块查看料比改善对奖金的影响"
    )

with col_slider2:
    survival_improvement = st.slider(
        "📈 成活率提升量",
        min_value=0,
        max_value=10,
        value=4,
        step=1,
        help="拖动滑块查看成活率提升对奖金的影响"
    )

# 计算传导效果
fcr_saving = fcr_improvement * 2.2
survival_saving = survival_improvement * 0.115
total_saving = fcr_saving + survival_saving
bonus_pool = total_saving * 0.3
personal_bonus = 6000 + (total_saving / 0.22) * 7000
personal_bonus = min(personal_bonus, 20000)  # 上限2万

# 桑基图风格传导展示
st.markdown("##### 🌊 传导流向图")

col_flow1, col_flow2, col_flow3, col_flow4, col_flow5 = st.columns(5)

with col_flow1:
    st.markdown("""
    <div style="background:#e8f4fd;border-radius:12px;padding:16px;text-align:center;border:2px solid #1890ff;">
        <div style="font-size:28px;font-weight:bold;color:#1890ff;">↓{:.2f}</div>
        <div style="font-size:12px;color:#666;">料比改善</div>
        <div style="font-size:11px;color:#999;">+ ↑{}% 成活率</div>
    </div>
    """.format(fcr_improvement, survival_improvement), unsafe_allow_html=True)

with col_flow2:
    st.markdown("""
    <div style="background:#fff7e6;border-radius:12px;padding:16px;text-align:center;border:2px solid #fa8c16;">
        <div style="font-size:28px;font-weight:bold;color:#fa8c16;">→ ¥{:.2f}亿</div>
        <div style="font-size:12px;color:#666;">成本节省</div>
        <div style="font-size:11px;color:#999;">饲料+存活</div>
    </div>
    """.format(total_saving), unsafe_allow_html=True)

with col_flow3:
    st.markdown("""
    <div style="background:#f6ffed;border-radius:12px;padding:16px;text-align:center;border:2px solid #52c41a;">
        <div style="font-size:28px;font-weight:bold;color:#52c41a;">→ ¥{:.2f}亿</div>
        <div style="font-size:12px;color:#666;">奖金池增量</div>
        <div style="font-size:11px;color:#999;">利润×30%</div>
    </div>
    """.format(bonus_pool), unsafe_allow_html=True)

with col_flow4:
    st.markdown("""
    <div style="background:#f0f0f0;border-radius:12px;padding:16px;text-align:center;border:2px solid #8c8c8c;">
        <div style="font-size:28px;font-weight:bold;color:#595959;">→ ¥{:.0f}</div>
        <div style="font-size:12px;color:#666;">饲养员奖金</div>
        <div style="font-size:11px;color:#999;">基础+改善</div>
    </div>
    """.format(personal_bonus), unsafe_allow_html=True)

with col_flow5:
    delta_bonus = personal_bonus - 6000
    st.markdown("""
    <div style="background:#fff1f0;border-radius:12px;padding:16px;text-align:center;border:2px solid #ff4d4f;">
        <div style="font-size:28px;font-weight:bold;color:#ff4d4f;">+{:.0f}%</div>
        <div style="font-size:12px;color:#666;">奖金增幅</div>
        <div style="font-size:11px;color:#999;">¥6,000 → ¥{:.0f}</div>
    </div>
    """.format(delta_bonus/6000*100 if delta_bonus > 0 else 0, personal_bonus), unsafe_allow_html=True)

# 传导链文字说明
st.markdown(f"""
<div style="background:#fafafa;border-radius:8px;padding:12px 16px;margin-top:12px;font-size:13px;color:#666;">
    <b>🔗 传导链：</b>
    料比改善 <b>{fcr_improvement:.2f}</b> → 饲料成本节省 <b>¥{fcr_saving:.2f}亿</b>
    &nbsp;+&nbsp; 成活率提升 <b>{survival_improvement}%</b> → 死猪成本节省 <b>¥{survival_saving:.2f}亿</b>
    &nbsp;→&nbsp; 总节省 <b>¥{total_saving:.2f}亿</b>
    &nbsp;→&nbsp; 奖金池 <b>¥{bonus_pool:.2f}亿</b>
    &nbsp;→&nbsp; 饲养员 <b>¥{personal_bonus:.0f}</b>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 拖动滑块实时重算 · 料比改善+成活率提升叠加效应")

# ==================== ⑥ 预警诊断区 ====================
st.subheader("⚠️ 预警诊断区 — 异常自动追溯根因")

st.markdown("""
<div style="background:#fff1f0;border-radius:8px;padding:8px 16px;border:1px solid #ffccc7;margin-bottom:12px;">
    <span style="font-weight:600;color:#cf1322;">🔔 实时预警推送</span>
    <span style="color:#999;font-size:12px;margin-left:12px;">系统自动检测偏离阈值的指标，红色为严重问题</span>
</div>
""", unsafe_allow_html=True)

# 预警数据
alerts = [
    {'级别': '🔴 严重', '描述': '料比偏离目标超过0.10，当前2.45', '场线': '📍 2号场', '时间': '🕐 09:15'},
    {'级别': '🔴 严重', '描述': '成活率低于薪酬基准线93%，当前88%', '场线': '📍 2号场、4号场', '时间': '🕐 08:30'},
    {'级别': '🟡 关注', '描述': '料比偏离目标0.05-0.10，当前2.35', '场线': '📍 3号场', '时间': '🕐 09:00'},
    {'级别': '🟡 关注', '描述': '饲料成本占比超过65%，当前67%', '场线': '📍 全场汇总', '时间': '🕐 10:00'},
    {'级别': '🟢 改善', '描述': '7号场料比连续30天低于目标值2.28', '场线': '📍 7号场', '时间': '🕐 自动检测'},
]

# 显示预警条
for alert in alerts:
    if '🔴' in alert['级别']:
        st.error(f"**{alert['级别']}** | {alert['描述']} | {alert['场线']} | {alert['时间']}")
    elif '🟡' in alert['级别']:
        st.warning(f"**{alert['级别']}** | {alert['描述']} | {alert['场线']} | {alert['时间']}")
    else:
        st.success(f"**{alert['级别']}** | {alert['描述']} | {alert['场线']} | {alert['时间']}")

# 预警规则说明
with st.expander("📋 完整预警规则表（8条规则）"):
    st.markdown("""
    | 编号 | 级别 | 触发条件 | 阈值 | 根因归类 | 建议动作 |
    |------|------|----------|------|----------|----------|
    | 规则1 | 🔴严重 | 单场线料比偏离目标 | >0.10 | 健康问题 | 启动蓝耳净化专项 |
    | 规则2 | 🟡关注 | 单场线料比偏离目标 | 0.05-0.10 | 管理问题 | 场长5日整改饲喂方案 |
    | 规则3 | 🔴严重 | 单场线成活率低于基准线 | <93% | 健康+管理 | 立即启动疾病排查 |
    | 规则4 | 🟡关注 | 全场饲料成本占比偏高 | >65% | 采购问题 | 评估配方/采购策略 |
    | 规则5 | 🔴严重 | 全场料比整体偏离目标 | >0.10 | 系统性问题 | 片区级整体推进 |
    | 规则6 | 🟡关注 | 单场线料比趋势恶化 | 连续7天上升 | 突发问题 | 24小时内排查上报 |
    | 规则7 | 🟡关注 | 日增重不达标 | 70日龄<28kg | 饲喂问题 | 调整饲喂方案 |
    | 规则8 | 🟢改善 | 单场线料比持续优于目标 | 连续30天≤2.28 | 标杆场线 | 复盘推广标杆做法 |
    """)

# 诊断链展开示例
with st.expander("🔍 点击查看诊断链 - 2号场料比偏高根因追溯"):
    st.markdown("""
    **诊断链（从利润层到技术层）：**
    """)                     
col1, col2 = st.columns([1, 3])   

with col1:          
        df = data_loader.load_from_database(table_name = 'mytable', limit = 1000, config_name='mysql_test')
        st.dataframe(df)

        
with col2:          
        st.markdown("""
        **根因分析：**
        """)    