# spider_manager/4_data_view.py
import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
from io import BytesIO
import time

sys.path.append(str(Path(__file__).parent.parent))
from spider_manager.spider_core import spider_core

st.title("📊 爬取数据查看")

# 获取所有Excel文件（包括手动放入的文件）
def get_spider_files():
    """获取所有爬虫数据文件（包括手动放入的文件）"""
    data_dir = Path("./spider_data")
    
    # 如果目录不存在，创建它
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        return []
    
    # 获取所有xlsx文件（包括手动放入的）
    files = list(data_dir.glob("*.xlsx"))
    # 获取所有xls文件
    files.extend(list(data_dir.glob("*.xls")))
    
    # 按修改时间排序
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files

# 文件选择
files = get_spider_files()

if files:
    # 文件选择器
    file_options = {f.name: f for f in files}
    selected_file_name = st.selectbox(
        "选择数据文件",
        options=list(file_options.keys()),
        help="选择要查看的数据文件（包括手动放入的文件）"
    )
    
    if selected_file_name:
        selected_file = file_options[selected_file_name]
        
        # 读取数据
        try:
            # 尝试读取Excel文件
            df = pd.read_excel(selected_file, engine='openpyxl')
            
            # 显示文件信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("文件名", selected_file_name)
            with col2:
                st.metric("数据行数", len(df))
            with col3:
                mod_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(selected_file.stat().st_mtime))
                st.metric("最后修改", mod_time)
            
            st.divider()
            
            # 数据预览
            st.subheader("🔍 数据预览")
            preview_rows = st.selectbox("预览行数", [5, 10, 20, 50, 100], index=1)
            st.dataframe(df.head(preview_rows), use_container_width=True)
            
            # 列信息
            st.subheader("📝 列信息")
            dtype_df = pd.DataFrame({
                '列名': df.columns,
                '数据类型': df.dtypes.astype(str).values,
                '非空值数': df.count().values,
                '空值数': df.isnull().sum().values,
                '空值比例(%)': (df.isnull().sum() / len(df) * 100).round(2).values,
                '唯一值数': df.nunique().values
            })
            st.dataframe(dtype_df, use_container_width=True)
            
            # 数据过滤
            with st.expander("🔍 数据过滤", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    # 选择过滤列
                    filter_column = st.selectbox("选择过滤列", df.columns, key="filter_column")
                    if filter_column:
                        unique_values = df[filter_column].dropna().unique()
                        if len(unique_values) <= 50:
                            selected_values = st.multiselect("选择值", unique_values, key="filter_values")
                            if selected_values:
                                df = df[df[filter_column].isin(selected_values)]
                        else:
                            search_text = st.text_input("搜索关键词", key="search_text")
                            if search_text:
                                df = df[df[filter_column].astype(str).str.contains(search_text, case=False)]
            
            # 统计分析（仅对数值列）
            st.subheader("📐 统计分析")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                st.dataframe(df[numeric_cols].describe(), use_container_width=True)
                
                # 数值列分布图
                with st.expander("📊 数值列分布图"):
                    selected_col = st.selectbox("选择列", numeric_cols, key="dist_col")
                    if selected_col:
                        st.bar_chart(df[selected_col].value_counts().head(20))
            else:
                st.info("没有数值列可供统计分析")
            
            # 数据导出
            st.subheader("💾 数据导出")
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📄 下载CSV",
                    data=csv,
                    file_name=selected_file.stem + ".csv",
                    mime="text/csv",
                    key="download_csv"
                )
            with col2:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='data')
                st.download_button(
                    label="📊 下载Excel",
                    data=output.getvalue(),
                    file_name=selected_file.stem + "_filtered.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )
        
        except Exception as e:
            st.error(f"读取文件失败: {e}")
            st.info("请确保文件是有效的Excel格式（.xlsx或.xls）")

else:
    st.info("暂无数据文件，请将Excel文件放入 ./spider_data 目录下")
    
    # 显示目录信息
    with st.expander("📁 如何添加文件"):
        st.markdown(f"""
        ### 添加数据文件步骤：
        
        1. 将您的Excel文件（.xlsx或.xls格式）放入以下目录：
        ```{Path('./spider_data').absolute()}```
        
2. 刷新此页面即可看到文件

### 支持的文件格式：
- .xlsx (Excel 2007+)
- .xls (Excel 97-2003)

### 文件命名建议：
- 使用有意义的文件名，如：`合并处理后的数据.xlsx`
- 中英文都可以
""")

# 创建目录按钮
if st.button("📁 创建数据目录"):
    data_dir = Path("./spider_data")
    data_dir.mkdir(parents=True, exist_ok=True)
    st.success(f"已创建目录: {data_dir.absolute()}")
    st.rerun()