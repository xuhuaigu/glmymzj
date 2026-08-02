# data_processing/data_export.py
import streamlit as st  # 确保在最顶部导入
import pandas as pd
import io
from typing import Optional

class DataExporter:
    """数据导出器"""
    
    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df
    
    def set_data(self, df: pd.DataFrame):
        """设置数据"""
        self.df = df
        return self
    
    def to_csv(self, index: bool = False) -> bytes:
        """导出为CSV"""
        return self.df.to_csv(index=index).encode('utf-8')
    
    def to_excel(self, sheet_name: str = "Sheet1") -> bytes:
        """导出为Excel"""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            self.df.to_excel(writer, sheet_name=sheet_name, index=False)
        return output.getvalue()
    
    def to_json(self, orient: str = 'records') -> str:
        """导出为JSON"""
        return self.df.to_json(orient=orient, force_ascii=False)
    
    def to_parquet(self) -> bytes:
        """导出为Parquet"""
        output = io.BytesIO()
        self.df.to_parquet(output, index=False)
        return output.getvalue()
    
    def export_report(self, file_name: str = "exported_data_", page_key: str = "default"):
        """导出完整报告
        
        Args:
            page_key: 页面唯一标识，用于区分不同页面的按钮
            file_name: 导出文件名称
        """
        # 使用全局导入的 st，不要重新赋值
        st.subheader("📥 导出数据")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.download_button(
                label="📄 导出CSV",
                data=self.to_csv(),
                file_name=f"{file_name}_{page_key}.csv",
                mime="text/csv",
                key=f"{page_key}_export_csv"
            )
        
        with col2:
            st.download_button(
                label="📊 导出Excel",
                data=self.to_excel(),
                file_name=f"{file_name}_{page_key}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{page_key}_export_excel"
            )
        
        with col3:
            st.download_button(
                label="🔧 导出JSON",
                data=self.to_json(),
                file_name=f"{file_name}_{page_key}.json",
                mime="application/json",
                key=f"{page_key}_export_json"
            )
        
        with col4:
            st.download_button(
                label="📦 导出Parquet",
                data=self.to_parquet(),
                file_name=f"{file_name}_{page_key}.parquet",
                mime="application/octet-stream",
                key=f"{page_key}_export_parquet"
            )

# 创建全局实例
data_exporter = DataExporter()