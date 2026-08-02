# -*- coding: utf-8 -*-
# 文件路径: H:\mzjxuhuaigu\SQL\programmzj\tworepository\data_analysis\9_yangzhuwang_analysis.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import glob
import platform
from datetime import datetime

# ==================== 现代配色方案 ====================
COLORS = {
    'blue': '#4A90D9',
    'green': '#34C759',
    'orange': '#FF9500',
    'purple': '#AF52DE',
    'pink': '#FF2D55',
    'teal': '#5AC8FA',
    'red': '#FF3B30',
    'yellow': '#FFCC00',
    'mint': '#00C7BE',
    'indigo': '#5856D6',
    'gray': '#8E8E93',
    'light_blue': '#007AFF',
}

COLOR_PALETTE = [
    '#4A90D9', '#34C759', '#FF9500', '#AF52DE', '#FF2D55',
    '#5AC8FA', '#FF3B30', '#FFCC00', '#00C7BE', '#5856D6'
]

# 默认文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE_PATH = os.path.join(os.path.dirname(current_dir), 'data_save', 'yangzhuwang_shengzhu', '合并标记_20260801_171825.xlsx')
# 获取目录下所有Excel文件
def get_excel_files(directory):
    """获取指定目录下的所有Excel文件"""
    excel_files = glob.glob(os.path.join(directory, "*.xlsx"))
    excel_files.extend(glob.glob(os.path.join(directory, "*.xls")))
    # 按修改时间排序，最新的在前
    excel_files.sort(key=os.path.getmtime, reverse=True)
    return excel_files

# 获取文件目录
file_dir = os.path.dirname(DEFAULT_FILE_PATH)

# 获取所有Excel文件
all_excel_files = get_excel_files(file_dir)

# 如果没有文件，使用默认路径
if not all_excel_files:
    all_excel_files = [DEFAULT_FILE_PATH]

# ==================== 文件选择下拉框 ====================
# 提取文件名
file_options = {os.path.basename(f): f for f in all_excel_files}

# 检查默认文件是否在列表中
default_key = os.path.basename(DEFAULT_FILE_PATH)
if default_key not in file_options and all_excel_files:
    default_key = os.path.basename(all_excel_files[0])

selected_file_name = st.selectbox(
    "📁 选择数据文件",
    options=list(file_options.keys()),
    index=list(file_options.keys()).index(default_key) if default_key in file_options else 0,
    help="从目录中选择要分析的数据文件"
)

# 获取选中的文件路径
FILE_PATH = file_options[selected_file_name]


@st.cache_data
def load_data(file_path):
    """加载Excel数据，优先使用'保留_最新数据' sheet"""
    try:
        if not os.path.exists(file_path):
            st.error(f"❌ 文件不存在: {file_path}")
            return None
        
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        
        if '保留_最新数据' in sheet_names:
            df = pd.read_excel(file_path, sheet_name='保留_最新数据', header=0)
            st.success(f"✅ 成功加载 '保留_最新数据' sheet，共 {df.shape[0]} 行，{df.shape[1]} 列")
            return df
        else:
            df = pd.read_excel(file_path, sheet_name=0, header=0)
            st.success(f"✅ 成功加载第一个 sheet '{sheet_names[0]}'，共 {df.shape[0]} 行，{df.shape[1]} 列")
            return df
            
    except Exception as e:
        st.error(f"❌ 读取Excel文件失败: {e}")
        return None


def prepare_data(df):
    """数据预处理：转换日期格式，提取数值列等"""
    if df is None:
        return None, []
    
    data = df.copy()
    
    if '日期' in data.columns:
        data['日期'] = pd.to_datetime(data['日期'])
    
    exclude_cols = ['日期', '品种', '编码', '平均值', '标准差', '最大值', '最小值', 
                    '创建时间', '创建人', '是否保留', '数据来源', 'A', 'B', 'C', 'D', 'E', 'F']
    
    numeric_cols = []
    for col in data.columns:
        if col not in exclude_cols:
            try:
                pd.to_numeric(data[col], errors='raise')
                numeric_cols.append(col)
            except:
                pass
    
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
    
    return data, numeric_cols


# ==================== 设置页面 ====================
st.set_page_config(
    page_title="猪价数据分析系统",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 主界面 ====================
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <h1 style="margin: 0;">🐷 全国猪价数据分析系统</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# 加载数据
df = load_data(FILE_PATH)

if df is not None:
    data, numeric_cols = prepare_data(df)
    
    if data is not None and len(numeric_cols) > 0:
        
        # ==================== 筛选控制区 ====================
        st.subheader("🎯 数据筛选")
        
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            if '品种' in data.columns:
                varieties = data['品种'].unique().tolist()
                selected_varieties = st.multiselect(
                    "🐖 选择品种",
                    varieties,
                    default=varieties[:2] if len(varieties) > 1 else varieties
                )
            else:
                selected_varieties = []
        
        with col2:
            if '日期' in data.columns:
                min_date = data['日期'].min()
                max_date = data['日期'].max()
                date_range = st.date_input(
                    "📅 选择日期范围",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                if len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date, end_date = min_date, max_date
            else:
                start_date, end_date = None, None
        
        with col3:
            province_list = sorted(numeric_cols)
            default_provinces = ['上海市', '广东省', '四川省', '河南省', '山东省']
            default_selected = [p for p in default_provinces if p in province_list][:5]
            
            selected_provinces = st.multiselect(
                "📍 选择对比省份",
                province_list,
                default=default_selected if default_selected else province_list[:5]
            )
        
        st.caption(f"📊 当前数据: {data.shape[0]} 条记录 | 识别到 {len(numeric_cols)} 个省份/地区")
        st.markdown("---")
        
        # ==================== 数据筛选执行 ====================
        filtered_data = data.copy()
        
        if selected_varieties and '品种' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['品种'].isin(selected_varieties)]
        
        if '日期' in filtered_data.columns and start_date and end_date:
            filtered_data = filtered_data[
                (filtered_data['日期'] >= pd.to_datetime(start_date)) & 
                (filtered_data['日期'] <= pd.to_datetime(end_date))
            ]
        
        if filtered_data.empty:
            st.warning("⚠️ 没有匹配的数据，请调整筛选条件")
            st.stop()
        
        # ==================== 数据概览 ====================
        st.subheader("📈 数据概览")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📋 总记录数", filtered_data.shape[0])
        with col2:
            if '品种' in filtered_data.columns:
                st.metric("🐖 品种数量", filtered_data['品种'].nunique())
        with col3:
            if '日期' in filtered_data.columns:
                days = (filtered_data['日期'].max() - filtered_data['日期'].min()).days
                st.metric("📅 日期跨度", f"{days} 天")
        with col4:
            st.metric("📍 省份数量", len(numeric_cols))
        
        st.markdown("---")
        
        # ==================== 全国均价趋势 ====================
        st.subheader("📊 全国均价趋势分析")
        
        if '日期' in filtered_data.columns:
            daily_avg = filtered_data.groupby('日期')[numeric_cols].mean().mean(axis=1)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=daily_avg.index,
                y=daily_avg.values,
                mode='lines+markers',
                name='全国均价',
                line=dict(color=COLORS['blue'], width=2),
                marker=dict(size=5, color=COLORS['blue'], opacity=0.8),
                hovertemplate='日期: %{x|%Y%m%d}<br>均价: %{y:.2f} 元/公斤<extra></extra>'
            ))
            
            fig.add_trace(go.Scatter(
                x=daily_avg.index,
                y=daily_avg.values,
                mode='none',
                name='价格区间',
                fill='tozeroy',
                fillcolor='rgba(74, 144, 217, 0.15)',
                showlegend=False,
                hovertemplate='<extra></extra>'
            ))
            
            fig.update_layout(
                title=dict(text='全国猪价均价趋势', font=dict(size=18, color='#1a1a1a', family='Arial')),
                xaxis_title=dict(text='日期', font=dict(size=14, color='#666')),
                yaxis_title=dict(text='均价 (元/公斤)', font=dict(size=14, color='#666')),
                height=400,
                hovermode='x unified',
                template='plotly_white',
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1,
                    font=dict(size=12)
                ),
                margin=dict(l=50, r=30, t=60, b=40),
                plot_bgcolor='#f8f9fa',
                paper_bgcolor='white'
            )
            
            fig.update_xaxes(
                tickangle=0,
                tickfont=dict(size=12),
                gridcolor='#e9ecef',
                showgrid=True,
                tickformat="%Y%m"
            )
            fig.update_yaxes(tickfont=dict(size=12), gridcolor='#e9ecef', showgrid=True)
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ==================== 按品种分析 ====================
        st.subheader("🐖 各品种价格趋势分析")
        
        if '品种' in filtered_data.columns and '日期' in filtered_data.columns:
            variety_trend = filtered_data.groupby(['日期', '品种'])[numeric_cols].mean().reset_index()
            
            fig = go.Figure()
            
            for i, variety in enumerate(variety_trend['品种'].unique()):
                variety_data = variety_trend[variety_trend['品种'] == variety]
                daily_avg = variety_data[numeric_cols].mean(axis=1)
                color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
                
                fig.add_trace(go.Scatter(
                    x=variety_data['日期'],
                    y=daily_avg,
                    mode='lines+markers',
                    name=variety,
                    line=dict(color=color, width=2),
                    marker=dict(size=5, color=color, opacity=0.8),
                    hovertemplate=f'{variety}<br>日期: %{{x|%Y%m%d}}<br>价格: %{{y:.2f}} 元/公斤<extra></extra>'
                ))
            
            fig.update_layout(
                title=dict(text='各品种猪价趋势对比', font=dict(size=18, color='#1a1a1a', family='Arial')),
                xaxis_title=dict(text='日期', font=dict(size=14, color='#666')),
                yaxis_title=dict(text='平均价格 (元/公斤)', font=dict(size=14, color='#666')),
                height=400,
                hovermode='x unified',
                template='plotly_white',
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1,
                    font=dict(size=12)
                ),
                margin=dict(l=50, r=30, t=60, b=40),
                plot_bgcolor='#f8f9fa',
                paper_bgcolor='white'
            )
            
            fig.update_xaxes(
                tickangle=0,
                tickfont=dict(size=12),
                gridcolor='#e9ecef',
                showgrid=True,
                tickformat="%Y%m%d" # 修改日期显示格式
            )
            fig.update_yaxes(tickfont=dict(size=12), gridcolor='#e9ecef', showgrid=True)
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ==================== 省份价格对比 ====================
        st.subheader("📍 省份价格对比分析")
        
        if selected_provinces and '日期' in filtered_data.columns and '品种' in filtered_data.columns:
            compare_varieties = selected_varieties if selected_varieties else filtered_data['品种'].unique().tolist()
            
            n_varieties = len(compare_varieties)
            
            if n_varieties > 0:
                if n_varieties > 1:
                    fig = make_subplots(
                        rows=n_varieties, 
                        cols=1,
                        subplot_titles=[f'{v}' for v in compare_varieties],
                        shared_xaxes=True,
                        vertical_spacing=0.08
                    )
                    
                    for idx, variety in enumerate(compare_varieties):
                        variety_data = filtered_data[filtered_data['品种'] == variety]
                        if variety_data.empty:
                            continue
                        
                        for j, province in enumerate(selected_provinces):
                            if province in variety_data.columns:
                                color = COLOR_PALETTE[j % len(COLOR_PALETTE)]
                                fig.add_trace(
                                    go.Scatter(
                                        x=variety_data['日期'],
                                        y=variety_data[province],
                                        mode='lines+markers',
                                        name=province,
                                        line=dict(color=color, width=1.8),
                                        marker=dict(size=4, color=color, opacity=0.8),
                                        hovertemplate=f'{province}<br>日期: %{{x|%Y%m%d}}<br>价格: %{{y:.2f}} 元/公斤<extra></extra>',
                                        legendgroup=province,
                                        showlegend=(idx == 0)
                                    ),
                                    row=idx+1, col=1
                                )
                    
                    fig.update_layout(
                        height=350 * n_varieties,
                        hovermode='x unified',
                        template='plotly_white',
                        legend=dict(
                            orientation='h',
                            yanchor='bottom',
                            y=1.02,
                            xanchor='right',
                            x=1,
                            font=dict(size=11)
                        ),
                        margin=dict(l=50, r=30, t=60, b=40),
                        plot_bgcolor='#f8f9fa',
                        paper_bgcolor='white'
                    )
                    
                    fig.update_xaxes(
                        tickangle=0,
                        gridcolor='#e9ecef',
                        showgrid=True,
                        tickformat="%Y%m"
                    )
                    fig.update_yaxes(gridcolor='#e9ecef', showgrid=True)
                    
                else:
                    fig = go.Figure()
                    variety = compare_varieties[0]
                    variety_data = filtered_data[filtered_data['品种'] == variety]
                    
                    for j, province in enumerate(selected_provinces):
                        if province in variety_data.columns:
                            color = COLOR_PALETTE[j % len(COLOR_PALETTE)]
                            fig.add_trace(go.Scatter(
                                x=variety_data['日期'],
                                y=variety_data[province],
                                mode='lines+markers',
                                name=province,
                                line=dict(color=color, width=2),
                                marker=dict(size=5, color=color, opacity=0.8),
                                hovertemplate=f'{province}<br>日期: %{{x|%Y%m%d}}<br>价格: %{{y:.2f}} 元/公斤<extra></extra>'
                            ))
                    
                    fig.update_layout(
                        title=dict(text=f'{variety} - 各省价格对比', font=dict(size=18, color='#1a1a1a', family='Arial')),
                        xaxis_title=dict(text='日期', font=dict(size=14, color='#666')),
                        yaxis_title=dict(text='价格 (元/公斤)', font=dict(size=14, color='#666')),
                        height=400,
                        hovermode='x unified',
                        template='plotly_white',
                        legend=dict(
                            orientation='h',
                            yanchor='bottom',
                            y=1.02,
                            xanchor='right',
                            x=1,
                            font=dict(size=12)
                        ),
                        margin=dict(l=50, r=30, t=60, b=40),
                        plot_bgcolor='#f8f9fa',
                        paper_bgcolor='white'
                    )
                    
                    fig.update_xaxes(
                        tickangle=0,
                        gridcolor='#e9ecef',
                        showgrid=True,
                        tickformat="%Y%m"
                    )
                    fig.update_yaxes(gridcolor='#e9ecef', showgrid=True)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 请在上方选择至少2个省份进行对比分析")
        else:
            st.info("💡 请在上方选择至少2个省份进行对比分析")
        
        st.markdown("---")
        
        # ==================== 最新日期的价格排名 ====================
        st.subheader("🏆 最新日期各省价格排名")
        
        if '日期' in filtered_data.columns:
            latest_date = filtered_data['日期'].max()
            latest_data = filtered_data[filtered_data['日期'] == latest_date]
            
            if not latest_data.empty:
                varieties_in_latest = latest_data['品种'].unique().tolist()
                selected_variety_for_rank = st.selectbox(
                    "选择品种查看排名",
                    varieties_in_latest,
                    index=0 if varieties_in_latest else None,
                    key="rank_select"
                )
                
                if selected_variety_for_rank:
                    variety_data = latest_data[latest_data['品种'] == selected_variety_for_rank]
                    
                    province_prices = {}
                    for province in numeric_cols:
                        if province in variety_data.columns:
                            val = variety_data[province].iloc[0]
                            if pd.notna(val):
                                province_prices[province] = val
                    
                    if province_prices:
                        sorted_prices = sorted(province_prices.items(), key=lambda x: x[1], reverse=True)
                        df_rank = pd.DataFrame(sorted_prices, columns=['省份', '价格'])
                        
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.dataframe(df_rank, use_container_width=True, height=600)
                        
                        with col2:
                            fig = go.Figure()
                            
                            colors = ['#4A90D9' if i < 3 else '#AF52DE' if i < 5 else '#8E8E93' for i in range(len(df_rank))]
                            
                            fig.add_trace(go.Bar(
                                y=df_rank['省份'],
                                x=df_rank['价格'],
                                orientation='h',
                                marker=dict(
                                    color=colors,
                                    line=dict(color='white', width=1)
                                ),
                                text=df_rank['价格'].round(2),
                                textposition='outside',
                                textfont=dict(size=11, color='#333'),
                                hovertemplate='省份: %{y}<br>价格: %{x:.2f} 元/公斤<extra></extra>'
                            ))
                            
                            avg_price = df_rank['价格'].mean()
                            fig.add_vline(
                                x=avg_price,
                                line_dash="dash",
                                line_color="#FF3B30",
                                line_width=1.5,
                                annotation_text=f'均价: {avg_price:.2f}',
                                annotation_position="bottom right",
                                annotation_font=dict(size=12, color='#FF3B30')
                            )
                            
                            fig.update_layout(
                                title=dict(
                                    text=f'{selected_variety_for_rank} - {latest_date.strftime("%Y-%m-%d")} 各省价格排名',
                                    font=dict(size=16, color='#1a1a1a', family='Arial')
                                ),
                                xaxis_title=dict(text='价格 (元/公斤)', font=dict(size=14, color='#666')),
                                yaxis_title=dict(text='省份', font=dict(size=14, color='#666')),
                                height=600,
                                template='plotly_white',
                                margin=dict(l=60, r=80, t=60, b=40),
                                plot_bgcolor='#f8f9fa',
                                paper_bgcolor='white'
                            )
                            
                            fig.update_xaxes(gridcolor='#e9ecef', showgrid=True)
                            fig.update_yaxes(gridcolor='#e9ecef', showgrid=True)
                            
                            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ==================== 热力图（最新一天） ====================
        st.subheader("🔥 最新日期各省价格分布")
        
        if '日期' in filtered_data.columns:
            latest_date = filtered_data['日期'].max()
            latest_data = filtered_data[filtered_data['日期'] == latest_date]
            
            if not latest_data.empty:
                varieties_in_latest = latest_data['品种'].unique().tolist()
                selected_heatmap_variety = st.selectbox(
                    "选择品种查看热力图",
                    varieties_in_latest,
                    index=0 if varieties_in_latest else None,
                    key="heatmap_select"
                )
                
                if selected_heatmap_variety:
                    variety_data = latest_data[latest_data['品种'] == selected_heatmap_variety]
                    
                    heatmap_data = []
                    for province in numeric_cols:
                        if province in variety_data.columns:
                            val = variety_data[province].iloc[0]
                            if pd.notna(val):
                                heatmap_data.append({'省份': province, '价格': val})
                    
                    if heatmap_data:
                        df_heat = pd.DataFrame(heatmap_data).sort_values('价格', ascending=False)
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=df_heat['省份'],
                            y=df_heat['价格'],
                            marker=dict(
                                color=df_heat['价格'],
                                colorscale='Blues',
                                colorbar=dict(
                                    title='价格<br>(元/公斤)',
                                    tickfont=dict(size=11),
                                    len=0.6
                                ),
                                line=dict(color='white', width=1)
                            ),
                            text=df_heat['价格'].round(2),
                            textposition='outside',
                            textfont=dict(size=11, color='#333'),
                            hovertemplate='省份: %{x}<br>价格: %{y:.2f} 元/公斤<extra></extra>'
                        ))
                        
                        avg_price = df_heat['价格'].mean()
                        fig.add_hline(
                            y=avg_price,
                            line_dash="dash",
                            line_color="#FF3B30",
                            line_width=1.5,
                            annotation_text=f'均价: {avg_price:.2f}',
                            annotation_position="top right",
                            annotation_font=dict(size=12, color='#FF3B30')
                        )
                        
                        fig.update_layout(
                            title=dict(
                                text=f'{selected_heatmap_variety} - {latest_date.strftime("%Y-%m-%d")} 各省价格分布',
                                font=dict(size=16, color='#1a1a1a', family='Arial')
                            ),
                            xaxis_title=dict(text='省份', font=dict(size=14, color='#666')),
                            yaxis_title=dict(text='价格 (元/公斤)', font=dict(size=14, color='#666')),
                            height=450,
                            template='plotly_white',
                            margin=dict(l=50, r=50, t=60, b=40),
                            plot_bgcolor='#f8f9fa',
                            paper_bgcolor='white'
                        )
                        
                        fig.update_xaxes(tickangle=45, gridcolor='#e9ecef', showgrid=True)
                        fig.update_yaxes(gridcolor='#e9ecef', showgrid=True)
                        
                        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ==================== 数据统计摘要 ====================
        with st.expander("📊 数据统计摘要", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("各品种记录数")
                if '品种' in filtered_data.columns:
                    st.dataframe(filtered_data['品种'].value_counts().reset_index())
            
            with col2:
                st.subheader("数值列统计")
                st.dataframe(filtered_data[numeric_cols].describe())
        
        # ==================== 原始数据预览 ====================
        with st.expander("📋 查看原始数据", expanded=False):
            st.dataframe(filtered_data, use_container_width=True)
        
        # ==================== 数据导出 ====================
        with st.expander("💾 数据导出", expanded=False):
            csv = filtered_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 下载筛选后的数据 (CSV)",
                data=csv,
                file_name=f"filtered_pig_price_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    else:
        st.error("❌ 无法处理数据，请检查数据格式")

else:
    st.error("❌ 无法加载数据，请检查文件路径")
    st.info(f"当前查找路径: {FILE_PATH}")

st.markdown("---")
st.caption(f"🐷 猪价数据分析系统 | 数据来源: {os.path.basename(FILE_PATH)} | 更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
