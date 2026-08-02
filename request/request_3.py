import streamlit as st

st.title("测试页面")

from data_processing import data_loader
from datetime import datetime

# 1. 选择模式
mode = st.selectbox(
    "请选择模式?",
    ["CQ", "DWD", 'DWS', 'DIM', 'ADS'],
    index=0, 
    placeholder="选择模式？",
)
# 2. 指定配置名称
tables = data_loader.get_database_tables(config_name='oracle_test', schema=mode)
option = st.selectbox(
    "请选择数据库表?",
    tables[0:10],
    index=None,
    placeholder="选择表名？",
)
st.write("You selected:", option)
df = data_loader.load_from_database(mode + '.' + option, config_name='oracle_test')

# ==================== 数据统计 ====================
with st.expander("📊 数据统计", expanded=True):
    st.dataframe(df.describe(), use_container_width=True)

# ==================== 数据明细 ====================
with st.expander("📋 数据明细表", expanded=True):
    st.dataframe(df[0:100], use_container_width=False)  # False: 不换行; True: 换行
    
    # 导出按钮
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 下载数据",
        data=csv,
        file_name=f"饲料数据_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )