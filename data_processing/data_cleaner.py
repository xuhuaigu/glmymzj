# data_processing/data_cleaner.py
import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Optional, Union

class DataCleaner:
    """数据清洗器"""
    
    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df
    
    def set_data(self, df: pd.DataFrame):
        """设置数据"""
        self.df = df.copy()
        return self
    
    def remove_duplicates(self, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """删除重复行"""
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset)
        after = len(self.df)
        st.info(f"删除了 {before - after} 行重复数据")
        return self.df
    
    def handle_missing_values(self, strategy: str = 'drop', 
                               fill_value: Optional[any] = None,
                               columns: Optional[List[str]] = None) -> pd.DataFrame:
        """处理缺失值"""
        target_cols = columns if columns else self.df.columns
        
        for col in target_cols:
            if col not in self.df.columns:
                continue
                
            missing_before = self.df[col].isnull().sum()
            
            if strategy == 'drop':
                self.df = self.df.dropna(subset=[col])
            elif strategy == 'fill_mean':
                self.df[col] = self.df[col].fillna(self.df[col].mean())
            elif strategy == 'fill_median':
                self.df[col] = self.df[col].fillna(self.df[col].median())
            elif strategy == 'fill_mode':
                self.df[col] = self.df[col].fillna(self.df[col].mode()[0] if not self.df[col].mode().empty else 0)
            elif strategy == 'fill_forward':
                self.df[col] = self.df[col].fillna(method='ffill')
            elif strategy == 'fill_backward':
                self.df[col] = self.df[col].fillna(method='bfill')
            elif strategy == 'fill_value' and fill_value is not None:
                self.df[col] = self.df[col].fillna(fill_value)
            elif strategy == 'interpolate':
                self.df[col] = self.df[col].interpolate()
            
            missing_after = self.df[col].isnull().sum()
            if missing_before > missing_after:
                st.info(f"列 '{col}': 处理了 {missing_before - missing_after} 个缺失值")
        
        return self.df
    
    def remove_outliers(self, columns: List[str], method: str = 'iqr', 
                        threshold: float = 1.5) -> pd.DataFrame:
        """删除异常值"""
        before = len(self.df)
        
        for col in columns:
            if col not in self.df.columns:
                continue
            
            if method == 'iqr':
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                self.df = self.df[(self.df[col] >= lower_bound) & (self.df[col] <= upper_bound)]
            
            elif method == 'zscore':
                from scipy import stats
                z_scores = np.abs(stats.zscore(self.df[col].dropna()))
                self.df = self.df[z_scores < threshold]
        
        after = len(self.df)
        st.info(f"删除了 {before - after} 行异常值")
        return self.df
    
    def convert_data_types(self, type_mappings: dict) -> pd.DataFrame:
        """转换数据类型"""
        for col, dtype in type_mappings.items():
            if col in self.df.columns:
                try:
                    self.df[col] = self.df[col].astype(dtype)
                    st.success(f"列 '{col}' 已转换为 {dtype}")
                except Exception as e:
                    st.warning(f"转换列 '{col}' 失败: {e}")
        return self.df
    
    def rename_columns(self, rename_dict: dict) -> pd.DataFrame:
        """重命名列"""
        self.df = self.df.rename(columns=rename_dict)
        return self.df
    
    def filter_data(self, query: str) -> pd.DataFrame:
        """过滤数据"""
        before = len(self.df)
        self.df = self.df.query(query)
        after = len(self.df)
        st.info(f"过滤后剩余 {after} 行（删除了 {before - after} 行）")
        return self.df
    
    def get_cleaning_report(self) -> pd.DataFrame:
        """获取清洗报告"""
        if self.df is None:
            return pd.DataFrame()
        
        report = pd.DataFrame({
            '列名': self.df.columns,
            '数据类型': self.df.dtypes.values,
            '非空值数': self.df.count().values,
            '空值数': self.df.isnull().sum().values,
            '空值比例(%)': (self.df.isnull().sum() / len(self.df) * 100).values,
            '唯一值数': self.df.nunique().values,
            '内存(MB)': (self.df.memory_usage(deep=True) / 1024 / 1024).values
        })
        return report

# 创建全局实例
data_cleaner = DataCleaner()