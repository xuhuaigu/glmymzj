import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid

def get_visitor_id():
    """
    生成一个稳定的访客标识（基于 session）
    即使获取不到 IP，也能区分不同访客
    """
    try:
        if "visitor_id" in st.session_state:
            return st.session_state.visitor_id
        
        visitor_id = str(uuid.uuid4())[:8]
        st.session_state.visitor_id = visitor_id
        return visitor_id
    except:
        return "unknown"

def get_client_ip():
    """
    使用 Streamlit 官方方法获取访客 IP
    st.context.ip_address 在 Streamlit 1.45.0+ 可用
    本地调试时返回 None
    """
    try:
        # 方法1：官方推荐方式 (Streamlit 1.45.0+)
        if hasattr(st, 'context') and hasattr(st.context, 'ip_address'):
            ip = st.context.ip_address
            if ip:
                return ip
        
        # 方法2：兼容旧版本，从 headers 中解析
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            headers = st.context.headers
            # 尝试 X-Forwarded-For
            forwarded = headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            # 尝试 X-Real-IP
            real_ip = headers.get("X-Real-IP")
            if real_ip:
                return real_ip
        
        # 方法3：尝试旧版 st.request
        if hasattr(st, 'request') and hasattr(st.request, 'headers'):
            headers = st.request.headers
            forwarded = headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            real_ip = headers.get("X-Real-IP")
            if real_ip:
                return real_ip
        
        return None
    except Exception:
        return None

def get_client_info():
    """
    获取客户端信息：IP、User-Agent
    返回一个字典
    """
    info = {
        "ip": "unknown",
        "user_agent": "unknown"
    }
    
    try:
        # 获取 IP（使用官方方法）
        ip = get_client_ip()
        if ip:
            info["ip"] = ip
        else:
            # 本地环境使用 session ID 作为标识
            info["ip"] = get_visitor_id()
        
        # 获取 User-Agent
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            headers = st.context.headers
            if "User-Agent" in headers:
                info["user_agent"] = headers["User-Agent"]
        elif hasattr(st, 'request') and hasattr(st.request, 'headers'):
            headers = st.request.headers
            if "User-Agent" in headers:
                info["user_agent"] = headers["User-Agent"]
                
    except Exception as e:
        pass
    
    return info

def log_visitor():
    """
    记录访客信息到 CSV
    """
    # 获取来源参数
    query_params = st.query_params
    source = query_params.get("source", "direct")
    page = query_params.get("page", "首页")
    
    # 获取客户端信息
    client_info = get_client_info()
    
    # 构建记录
    new_record = {
        "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "访客ID": client_info["ip"],
        "IP": client_info["ip"],
        "来源": source,
        "页面": page,
        "User-Agent": client_info["user_agent"][:100] if client_info["user_agent"] != "unknown" else "unknown"
    }
    
    # 保存到 CSV
    log_file = "visitor_log.csv"
    
    try:
        if os.path.exists(log_file):
            df = pd.read_csv(log_file)
        else:
            df = pd.DataFrame(columns=["时间", "访客ID", "IP", "来源", "页面", "User-Agent"])
        
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        df.to_csv(log_file, index=False)
        return True
    except Exception as e:
        st.error(f"记录访客失败: {e}")
        return False

# ========== 主页面 ==========
def main():
    st.set_page_config(page_title="访客统计看板", layout="wide")
    
    # 在页面加载时记录访问
    log_visitor()
    
    st.title("📊 访客统计看板")
    
    # 显示当前会话信息（调试用）
    with st.expander("🔍 当前会话信息（调试）"):
        # 显示 IP 获取状态
        ip = get_client_ip()
        if ip:
            st.success(f"✅ 成功获取 IP: {ip}")
        else:
            st.info("💡 本地开发环境，IP 为 None（部署后可正常获取）")
        
        # 显示请求头
        try:
            if hasattr(st, 'context') and hasattr(st.context, 'headers'):
                st.json(dict(st.context.headers))
            else:
                st.info("当前环境不支持 st.context.headers")
        except:
            st.info("无法获取请求头信息")
        
        st.write(f"**当前访客标识**: {get_visitor_id()}")
    
    # 读取并显示日志
    log_file = "visitor_log.csv"
    
    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        
        if not df.empty:
            # 统计指标
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("总访问量", len(df))
            
            # 统计独立访客（基于访客ID）
            unique_visitors = df["访客ID"].nunique()
            col2.metric("独立访客", unique_visitors)
            
            col3.metric("最新访问", df["时间"].max() if not df.empty else "无")
            col4.metric("来源渠道数", df["来源"].nunique())
            
            # 显示数据表格
            st.subheader("📋 访客详情")
            st.dataframe(df, use_container_width=True)
            
            # 可视化
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 访问来源分布")
                source_counts = df["来源"].value_counts()
                if not source_counts.empty:
                    st.bar_chart(source_counts)
                else:
                    st.info("暂无数据")
            
            with col2:
                st.subheader("🕒 每日访问趋势")
                df["日期"] = pd.to_datetime(df["时间"]).dt.date
                daily_count = df.groupby("日期").size()
                if not daily_count.empty:
                    st.line_chart(daily_count)
                else:
                    st.info("暂无数据")
            
            # 显示近7天访问量
            st.subheader("📅 近7天访问量")
            df["日期"] = pd.to_datetime(df["时间"]).dt.date
            last_7_days = df[df["日期"] >= (pd.Timestamp.now() - pd.Timedelta(days=7)).date()]
            if not last_7_days.empty:
                week_count = last_7_days.groupby("日期").size().sort_index()
                st.bar_chart(week_count)
            else:
                st.info("近7天暂无访问")
        else:
            st.info("暂无访问记录")
    else:
        st.info("暂无访问记录，等待第一个访客...")
        
        # 创建空日志文件
        empty_df = pd.DataFrame(columns=["时间", "访客ID", "IP", "来源", "页面", "User-Agent"])
        empty_df.to_csv(log_file, index=False)

if __name__ == "__main__":
    main()