# data_analysis/10_price_forecast.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="猪价预测系统",
    page_icon="🔮",
    layout="wide"
)

st.title("🔮 猪价预测系统")
st.markdown("> 基于历史数据，使用多种算法预测未来猪价走势")

# ==================== 数据加载 ====================
FILE_PATH = r"H:\mzjxuhuaigu\SQL\Python脚本\5-养猪网数据存储\合并标记_20260722_153225.xlsx"

@st.cache_data
def load_data(file_path):
    """加载猪价数据"""
    try:
        if not os.path.exists(file_path):
            st.error(f"❌ 文件不存在: {file_path}")
            return None
        
        df = pd.read_excel(file_path, sheet_name='保留_最新数据')
        st.success(f"✅ 成功加载数据，共 {df.shape[0]} 行，{df.shape[1]} 列")
        return df
    except Exception as e:
        st.error(f"❌ 加载数据失败: {e}")
        return None

# ==================== 数据预处理 ====================
def prepare_price_data(df):
    """准备价格时间序列数据"""
    if '日期' not in df.columns:
        st.error("❌ 数据中缺少'日期'列")
        return None, None
    
    exclude_cols = ['日期', '品种', '编码', '平均值', '标准差', '最大值', '最小值', 
                    '创建时间', '创建人', '是否保留', '数据来源']
    price_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not price_cols:
        st.error("❌ 未找到价格数据列")
        return None, None
    
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期')
    
    # 计算全国均价（简单版本，按日期计算所有省份的平均值）
    if '品种' in df.columns:
        # 按日期和品种分组，计算每个品种的各省均价
        variety_avg = df.groupby(['日期', '品种'])[price_cols].mean().reset_index()
        # 按日期分组，计算所有品种的平均值
        national_avg = variety_avg.groupby('日期')[price_cols].mean().reset_index()
        # 计算每行的全国均价（所有省份的平均值）
        national_avg['全国均价'] = national_avg[price_cols].mean(axis=1)
        # 创建映射字典
        national_avg_dict = national_avg.set_index('日期')['全国均价'].to_dict()
        df['全国均价'] = df['日期'].map(national_avg_dict)
    else:
        # 没有品种列，直接计算所有省份的平均值
        df['全国均价'] = df[price_cols].mean(axis=1, skipna=True)
    
    return df, price_cols

# ==================== 获取价格序列 ====================
def get_price_series(df_prepared, selected_variety, selected_provinces, price_cols):
    """根据选择的品种和省份获取价格序列"""
    
    # ===== 情况1：选择"全国均价" =====
    if selected_variety == '全国均价':
        price_df = df_prepared.groupby('日期')['全国均价'].first().reset_index()
        price_series = price_df.set_index('日期')['全国均价']
        price_type = "全国均价"
        all_provinces = price_cols
        return price_series, price_series.index, price_type, all_provinces
    
    # ===== 情况2：选择具体品种 =====
    if '品种' in df_prepared.columns:
        variety_data = df_prepared[df_prepared['品种'] == selected_variety]
    else:
        variety_data = df_prepared
    
    all_provinces = [col for col in price_cols if col in variety_data.columns]
    
    # 确定要使用的省份列
    if selected_provinces:
        available_cols = [col for col in selected_provinces if col in variety_data.columns]
        if not available_cols:
            available_cols = all_provinces
    else:
        available_cols = all_provinces
    
    # 按日期分组，计算每天的平均价格
    price_series = []
    dates_list = []
    
    for date, group in variety_data.groupby('日期'):
        # 计算该天所有选定省份的平均值
        daily_prices = group[available_cols].mean(axis=1, skipna=True)
        if not daily_prices.empty:
            avg_price = daily_prices.mean()
            if not pd.isna(avg_price):
                price_series.append(avg_price)
                dates_list.append(date)
    
    # 创建 Series
    if price_series:
        price_series = pd.Series(price_series, index=dates_list, name='价格')
        price_type = f"{selected_variety} 全国均价" if not selected_provinces else f"{selected_variety} ({len(available_cols)}省均价)"
    else:
        price_series = pd.Series()
        price_type = "无数据"
        all_provinces = []
    
    return price_series, price_series.index, price_type, all_provinces

# ==================== 预测算法 ====================
def simple_moving_average(data, window=7):
    """简单移动平均"""
    return data.rolling(window=window).mean()

def exponential_smoothing(data, alpha=0.3):
    """指数平滑"""
    result = [data.iloc[0]]
    for i in range(1, len(data)):
        result.append(alpha * data.iloc[i] + (1 - alpha) * result[-1])
    return pd.Series(result, index=data.index)

def linear_regression_forecast(data, forecast_days=7):
    """线性回归预测"""
    from sklearn.linear_model import LinearRegression
    
    if len(data) < 10:
        return None
    
    X = np.arange(len(data)).reshape(-1, 1)
    y = data.values.reshape(-1, 1)
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_X = np.arange(len(data), len(data) + forecast_days).reshape(-1, 1)
    forecast = model.predict(future_X).flatten()
    
    return forecast

def arima_forecast(data, forecast_days=7):
    """ARIMA预测"""
    try:
        from statsmodels.tsa.arima.model import ARIMA
        
        model = ARIMA(data, order=(1, 1, 1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=forecast_days)
        return forecast
    except ImportError:
        return None
    except Exception:
        return None

def prophet_forecast(data, dates, forecast_days=7):
    """Prophet预测"""
    try:
        from prophet import Prophet
        
        df_prophet = pd.DataFrame({
            'ds': dates,
            'y': data
        })
        
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(df_prophet)
        
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)
        
        return forecast
    except ImportError:
        return None
    except Exception:
        return None

# ==================== 评估指标 ====================
def calculate_metrics(actual, predicted):
    """计算预测评估指标"""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    
    min_len = min(len(actual), len(predicted))
    actual = actual[-min_len:]
    predicted = predicted[:min_len]
    
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    
    return {
        'MAE': f"{mae:.3f}",
        'RMSE': f"{rmse:.3f}",
        'MAPE': f"{mape:.2f}%"
    }

# ==================== 主界面 ====================
# 加载数据
df = load_data(FILE_PATH)

if df is not None:
    df_prepared, price_cols = prepare_price_data(df)
    
    if df_prepared is not None and price_cols:
        
        # ==================== 预测配置 ====================
        st.markdown("---")
        st.subheader("⚙️ 预测配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            variety_options = ['全国均价'] + (df_prepared['品种'].unique().tolist() if '品种' in df_prepared.columns else [])
            selected_variety = st.selectbox(
                "🐖 选择品种",
                variety_options,
                index=0
            )
            
            if selected_variety != '全国均价' and '品种' in df_prepared.columns:
                variety_data = df_prepared[df_prepared['品种'] == selected_variety]
                all_provinces = [col for col in price_cols if col in variety_data.columns]
            else:
                all_provinces = price_cols
            
            selected_provinces = st.multiselect(
                "📍 选择省份（多选，不选则使用全国均价）",
                options=all_provinces,
                default=[],
                help="选择多个省份将计算平均值进行预测"
            )
        
        with col2:
            forecast_days = st.slider(
                "📅 预测天数",
                min_value=1,
                max_value=30,
                value=7
            )
            
            train_ratio = st.slider(
                "📊 训练数据比例",
                min_value=0.5,
                max_value=0.95,
                value=0.8,
                step=0.05
            )
            
            st.write("🧠 选择预测算法")
            
            col_algo1, col_algo2 = st.columns(2)
            algorithms = []
            
            with col_algo1:
                if st.checkbox("移动平均", value=True):
                    algorithms.append("移动平均")
                if st.checkbox("线性回归", value=True):
                    algorithms.append("线性回归")
                if st.checkbox("ARIMA", value=False):
                    algorithms.append("ARIMA")
            with col_algo2:
                if st.checkbox("指数平滑", value=False):
                    algorithms.append("指数平滑")
                if st.checkbox("Prophet", value=False):
                    algorithms.append("Prophet")
        
        if "移动平均" in algorithms:
            col_extra1, col_extra2 = st.columns(2)
            with col_extra1:
                ma_window = st.number_input("移动平均窗口", min_value=3, max_value=30, value=7, step=1)
            with col_extra2:
                alpha = st.slider("指数平滑系数", 0.05, 0.95, 0.3, 0.05)
        
        st.markdown("---")
        
        # ==================== 获取价格数据 ====================
        price_series, dates, price_type, all_provinces = get_price_series(
            df_prepared, selected_variety, selected_provinces, price_cols
        )
        
        if len(price_series) < 10:
            st.warning("⚠️ 数据量不足，至少需要10个数据点")
            st.stop()
        
        st.info(f"📌 当前预测数据: {selected_variety} | {price_type} | {len(price_series)} 个数据点")
        if selected_provinces:
            st.caption(f"选中省份: {', '.join(selected_provinces[:10])}{'...' if len(selected_provinces) > 10 else ''}")
        
        # ==================== 数据概览卡片 ====================
        st.subheader("📊 历史数据概览")
        
        latest_date = price_series.index[-1]
        latest_price = price_series.iloc[-1]
        max_price = price_series.max()
        max_date = price_series.idxmax()
        min_price = price_series.min()
        min_date = price_series.idxmin()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 数据点数", f"{len(price_series):,}")
            st.caption(f"📅 {price_series.index[0].strftime('%Y-%m-%d')} ~ {latest_date.strftime('%Y-%m-%d')}")
        
        with col2:
            st.metric("🆕 最新价格", f"{latest_price:.2f}")
            st.caption(f"📅 {latest_date.strftime('%Y-%m-%d')}")
        
        with col3:
            st.metric("📈 最高价格", f"{max_price:.2f}")
            st.caption(f"📅 {max_date.strftime('%Y-%m-%d')}")
        
        with col4:
            st.metric("📉 最低价格", f"{min_price:.2f}")
            st.caption(f"📅 {min_date.strftime('%Y-%m-%d')}")
        
        st.markdown("---")
        
        # ==================== 历史趋势图 ====================
        st.subheader("📈 历史价格趋势")
        
        fig_hist = go.Figure()
        
        fig_hist.add_trace(go.Scatter(
            x=dates,
            y=price_series,
            mode='lines+markers',
            name=price_type,
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=4),
            hovertemplate='日期: %{x|%Y%m%d}<br>价格: %{y:.2f}<extra></extra>'
        ))
        
        # 标注最高点和最低点
        fig_hist.add_trace(go.Scatter(
            x=[max_date],
            y=[max_price],
            mode='markers',
            name=f'最高: {max_price:.2f}',
            marker=dict(color='red', size=12, symbol='triangle-up'),
            hovertemplate=f'最高价: {max_price:.2f}<br>日期: {max_date.strftime("%Y-%m-%d")}<extra></extra>'
        ))
        
        fig_hist.add_trace(go.Scatter(
            x=[min_date],
            y=[min_price],
            mode='markers',
            name=f'最低: {min_price:.2f}',
            marker=dict(color='green', size=12, symbol='triangle-down'),
            hovertemplate=f'最低价: {min_price:.2f}<br>日期: {min_date.strftime("%Y-%m-%d")}<extra></extra>'
        ))
        
        fig_hist.update_layout(
            title=f"{selected_variety} {price_type}历史趋势",
            xaxis_title="日期",
            yaxis_title="价格 (元/公斤)",
            height=400,
            hovermode='x unified',
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=50, r=30, t=50, b=40)
        )
        
        fig_hist.update_xaxes(tickformat="%Y%m", tickangle=0)
        
        st.plotly_chart(fig_hist, use_container_width=True)
        
        st.markdown("---")
        
        # ==================== 预测 ====================
        st.subheader("🔮 价格预测")
        
        if not algorithms:
            st.warning("⚠️ 请至少选择一种预测算法")
            st.stop()
        
        train_size = int(len(price_series) * train_ratio)
        train_data = price_series[:train_size]
        test_data = price_series[train_size:]
        
        predictions = {}
        metrics = {}
        
        with st.spinner("正在计算预测..."):
            if "移动平均" in algorithms:
                ma_forecast = simple_moving_average(price_series, window=ma_window)
                predictions['移动平均'] = ma_forecast
                if len(test_data) > 0:
                    metrics['移动平均'] = calculate_metrics(test_data, ma_forecast.iloc[train_size:])
            
            if "指数平滑" in algorithms:
                es_forecast = exponential_smoothing(price_series, alpha=alpha)
                predictions['指数平滑'] = es_forecast
                if len(test_data) > 0:
                    metrics['指数平滑'] = calculate_metrics(test_data, es_forecast.iloc[train_size:])
            
            if "线性回归" in algorithms:
                lr_forecast = linear_regression_forecast(price_series, forecast_days)
                if lr_forecast is not None:
                    predictions['线性回归'] = lr_forecast
                    if len(test_data) > 3:
                        test_forecast = linear_regression_forecast(price_series[:train_size], len(test_data))
                        if test_forecast is not None:
                            metrics['线性回归'] = calculate_metrics(test_data, test_forecast)
            
            if "ARIMA" in algorithms:
                arima_forecast_result = arima_forecast(price_series, forecast_days)
                if arima_forecast_result is not None:
                    predictions['ARIMA'] = arima_forecast_result
                    if len(test_data) > 3:
                        test_forecast = arima_forecast(price_series[:train_size], len(test_data))
                        if test_forecast is not None:
                            metrics['ARIMA'] = calculate_metrics(test_data, test_forecast)
            
            if "Prophet" in algorithms:
                prophet_result = prophet_forecast(price_series, dates, forecast_days)
                if prophet_result is not None:
                    predictions['Prophet'] = prophet_result
        
        if predictions:
            fig_pred = go.Figure()
            
            fig_pred.add_trace(go.Scatter(
                x=dates,
                y=price_series,
                mode='lines',
                name='历史数据',
                line=dict(color='#2E86AB', width=2),
                hovertemplate='日期: %{x|%Y%m%d}<br>价格: %{y:.2f}<extra></extra>'
            ))
            
            colors = ['#E74C3C', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C']
            color_idx = 0
            
            for name, pred in predictions.items():
                if name == 'Prophet' and pred is not None:
                    future_dates = pred['ds'].tail(forecast_days)
                    future_prices = pred['yhat'].tail(forecast_days)
                    fig_pred.add_trace(go.Scatter(
                        x=future_dates,
                        y=future_prices,
                        mode='lines+markers',
                        name=f'{name}',
                        line=dict(color=colors[color_idx % len(colors)], dash='dash'),
                        marker=dict(size=8),
                        hovertemplate='日期: %{x|%Y%m%d}<br>预测值: %{y:.2f}<extra></extra>'
                    ))
                elif isinstance(pred, (np.ndarray, list)):
                    # future_dates = [dates.iloc[-1] + timedelta(days=i+1) for i in range(len(pred))]
                    future_dates = [dates[-1] + timedelta(days=i+1) for i in range(len(pred))]
                    fig_pred.add_trace(go.Scatter(
                        x=future_dates,
                        y=pred,
                        mode='lines+markers',
                        name=f'{name}',
                        line=dict(color=colors[color_idx % len(colors)], dash='dash'),
                        marker=dict(size=8),
                        hovertemplate='日期: %{x|%Y%m%d}<br>预测值: %{y:.2f}<extra></extra>'
                    ))
                else:
                    if len(pred) > len(price_series):
                        future_dates = [dates.iloc[-1] + timedelta(days=i+1) for i in range(len(pred) - len(price_series))]
                        future_prices = pred.iloc[-len(future_dates):]
                        fig_pred.add_trace(go.Scatter(
                            x=future_dates,
                            y=future_prices,
                            mode='lines+markers',
                            name=f'{name}',
                            line=dict(color=colors[color_idx % len(colors)], dash='dash'),
                            marker=dict(size=8),
                            hovertemplate='日期: %{x|%Y%m%d}<br>预测值: %{y:.2f}<extra></extra>'
                        ))
                color_idx += 1
            
            fig_pred.update_layout(
                title="价格预测对比",
                xaxis_title="日期",
                yaxis_title="价格 (元/公斤)",
                height=500,
                hovermode='x unified',
                template='plotly_white',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(l=50, r=30, t=50, b=40)
            )
            
            fig_pred.update_xaxes(tickformat="%Y%m", tickangle=0)
            
            st.plotly_chart(fig_pred, use_container_width=True)
            
            # ==================== 预测结果表格 ====================
            st.subheader("📋 预测结果明细")
            
            future_dates_list = [dates[-1] + timedelta(days=i+1) for i in range(forecast_days)]

            result_df = pd.DataFrame({
                '日期': [d.strftime('%Y%m%d') for d in future_dates_list]
            })
            
            for name, pred in predictions.items():
                if name == 'Prophet' and pred is not None:
                    values = pred['yhat'].tail(forecast_days).values
                elif isinstance(pred, (np.ndarray, list)):
                    values = pred[:forecast_days]
                else:
                    values = pred.iloc[-forecast_days:].values if len(pred) >= forecast_days else None
                
                if values is not None and len(values) == forecast_days:
                    result_df[name] = [round(v, 2) for v in values]
            
            st.dataframe(result_df, use_container_width=True, hide_index=True)
            
            # ==================== 评估指标 ====================
            if metrics:
                st.subheader("📊 模型评估指标")
                st.info("💡 MAPE < 10% 表示预测精度良好")
                metric_df = pd.DataFrame(metrics).T
                st.dataframe(metric_df, use_container_width=True)
            
            # ==================== 导出预测结果 ====================
            st.subheader("💾 导出预测结果")
            
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 下载预测结果 (CSV)",
                data=csv,
                file_name=f"猪价预测_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("⚠️ 预测失败，请检查数据或更换算法")
        
        # ==================== 使用说明 ====================
        with st.expander("📖 使用说明"):
            st.markdown("""
            ### 价格类型说明
            
            | 选择方式 | 价格类型 | 说明 |
            |---------|---------|------|
            | 品种=全国均价 | 全国均价 | 所有品种、所有省份的平均值 |
            | 品种=外三元 + 不选省份 | 外三元全国均价 | 外三元品种下所有省份的平均值 |
            | 品种=外三元 + 选省份 | 外三元(X省均价) | 外三元品种下选中省份的平均值 |
            
            ### 数据卡片说明
            
            | 卡片 | 说明 |
            |------|------|
            | 📋 数据点数 | 历史数据的总数量，下方显示起止日期 |
            | 🆕 最新价格 | 最新一天的价格，下方显示具体日期 |
            | 📈 最高价格 | 历史最高价格，下方显示发生日期 |
            | 📉 最低价格 | 历史最低价格，下方显示发生日期 |
            
            ### 预测算法说明
            
            | 算法 | 原理 | 适用场景 |
            |------|------|----------|
            | **移动平均** | 计算最近N期的平均值 | 数据平稳，无明显趋势 |
            | **指数平滑** | 加权平均，近期权重更大 | 有轻微趋势变化 |
            | **线性回归** | 拟合直线趋势 | 有明显线性趋势 |
            | **ARIMA** | 自回归移动平均 | 有周期性和趋势 |
            | **Prophet** | Facebook时间序列预测 | 有季节性和节假日效应 |
            
            ### 使用建议
            
            1. **数据量要求**：建议至少30个数据点
            2. **算法选择**：多种算法对比，选择MAPE最小的
            3. **预测周期**：短期预测（7天以内）准确性更高
            
            ### 注意事项
            
            - 预测结果仅供参考，实际价格受多种因素影响
            - 市场波动、政策变化等可能导致预测偏差
            - 建议结合基本面分析综合判断
            """)
    
    else:
        st.error("❌ 数据预处理失败，请检查数据格式")

else:
    st.error("❌ 无法加载数据，请检查文件路径")
    st.info(f"当前查找路径: {FILE_PATH}")