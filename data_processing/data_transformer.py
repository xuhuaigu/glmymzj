# data_processing/data_transformer.py
import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Optional, Union

class DataTransformer:
    """数据转换器"""
    
    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df
    
    def set_data(self, df: pd.DataFrame):
        """设置数据"""
        self.df = df.copy()
        return self
    
    def create_date_features(self, date_column: str) -> pd.DataFrame:
        """创建日期特征"""
        if date_column not in self.df.columns:
            st.warning(f"列 '{date_column}' 不存在")
            return self.df
        
        # 确保日期列是 datetime 类型
        self.df[date_column] = pd.to_datetime(self.df[date_column])
        
        # 添加日期特征
        self.df['年'] = self.df[date_column].dt.year
        self.df['月'] = self.df[date_column].dt.month
        self.df['日'] = self.df[date_column].dt.day
        self.df['季度'] = self.df[date_column].dt.quarter
        self.df['周'] = self.df[date_column].dt.isocalendar().week
        self.df['星期几'] = self.df[date_column].dt.dayofweek
        self.df['星期名称'] = self.df[date_column].dt.day_name()
        self.df['是否周末'] = (self.df[date_column].dt.dayofweek >= 5).astype(int)
        
        st.success(f"已从 '{date_column}' 创建日期特征")
        return self.df
    
    def create_lag_features(self, column: str, lags: List[int]) -> pd.DataFrame:
        """创建滞后特征"""
        if column not in self.df.columns:
            st.warning(f"列 '{column}' 不存在")
            return self.df
        
        for lag in lags:
            self.df[f'{column}_lag_{lag}'] = self.df[column].shift(lag)
        
        st.success(f"为 '{column}' 创建了滞后特征: {lags}")
        return self.df
    
    def create_rolling_features(self, column: str, windows: List[int], 
                                 stats: List[str] = ['mean', 'std']) -> pd.DataFrame:
        """创建滚动统计特征"""
        if column not in self.df.columns:
            st.warning(f"列 '{column}' 不存在")
            return self.df
        
        for window in windows:
            for stat in stats:
                if stat == 'mean':
                    self.df[f'{column}_rolling_{window}_mean'] = self.df[column].rolling(window).mean()
                elif stat == 'std':
                    self.df[f'{column}_rolling_{window}_std'] = self.df[column].rolling(window).std()
                elif stat == 'min':
                    self.df[f'{column}_rolling_{window}_min'] = self.df[column].rolling(window).min()
                elif stat == 'max':
                    self.df[f'{column}_rolling_{window}_max'] = self.df[column].rolling(window).max()
        
        st.success(f"为 '{column}' 创建了滚动特征")
        return self.df
    
    def normalize_columns(self, columns: List[str], method: str = 'minmax') -> pd.DataFrame:
        """标准化/归一化列"""
        try:
            from sklearn.preprocessing import MinMaxScaler, StandardScaler
        except ImportError:
            st.error("请安装 scikit-learn: pip install scikit-learn")
            return self.df
        
        for col in columns:
            if col not in self.df.columns:
                continue
            
            data = self.df[col].values.reshape(-1, 1)
            
            if method == 'minmax':
                scaler = MinMaxScaler()
                self.df[f'{col}_normalized'] = scaler.fit_transform(data).flatten()
            elif method == 'standard':
                scaler = StandardScaler()
                self.df[f'{col}_normalized'] = scaler.fit_transform(data).flatten()
        
        st.success(f"已对 {len(columns)} 列应用 {method} 归一化")
        return self.df
    
    def bin_continuous_variable(self, column: str, bins: int, 
                                  labels: Optional[List[str]] = None) -> pd.DataFrame:
        """将连续变量离散化"""
        if column not in self.df.columns:
            st.warning(f"列 '{column}' 不存在")
            return self.df
        
        self.df[f'{column}_binned'] = pd.cut(self.df[column], bins=bins, labels=labels)
        st.success(f"已将 '{column}' 离散化为 {bins} 个区间")
        return self.df
    
    def encode_categorical(self, columns: List[str], method: str = 'onehot') -> pd.DataFrame:
        """编码分类变量"""
        if method == 'onehot':
            # 只对存在的列进行 one-hot 编码
            existing_cols = [col for col in columns if col in self.df.columns]
            if existing_cols:
                self.df = pd.get_dummies(self.df, columns=existing_cols, prefix=existing_cols)
                st.success(f"已对 {len(existing_cols)} 列应用 one-hot 编码")
            else:
                st.warning("没有找到指定的列")
                
        elif method == 'label':
            try:
                from sklearn.preprocessing import LabelEncoder
                for col in columns:
                    if col in self.df.columns and self.df[col].dtype == 'object':
                        le = LabelEncoder()
                        self.df[f'{col}_encoded'] = le.fit_transform(self.df[col].astype(str))
                st.success(f"已对 {len(columns)} 列应用 label 编码")
            except ImportError:
                st.error("请安装 scikit-learn: pip install scikit-learn")
        
        return self.df
    
    def aggregate_data(self, group_by: List[str], agg_dict: dict) -> pd.DataFrame:
        """聚合数据"""
        # 检查分组列是否存在
        existing_groups = [col for col in group_by if col in self.df.columns]
        if not existing_groups:
            st.warning("没有找到指定的分组列")
            return self.df
        
        self.df = self.df.groupby(existing_groups).agg(agg_dict).reset_index()
        st.success(f"已按 {existing_groups} 进行聚合")
        return self.df
    
    def pivot_table(self, index: List[str], columns: str, values: str, 
                     aggfunc: str = 'mean') -> pd.DataFrame:
        """创建透视表"""
        # 检查必要的列是否存在
        if columns not in self.df.columns:
            st.warning(f"列 '{columns}' 不存在")
            return self.df
        
        if values not in self.df.columns:
            st.warning(f"列 '{values}' 不存在")
            return self.df
        
        existing_index = [col for col in index if col in self.df.columns]
        if not existing_index:
            st.warning("没有找到指定的索引列")
            return self.df
        
        self.df = self.df.pivot_table(
            index=existing_index, 
            columns=columns, 
            values=values, 
            aggfunc=aggfunc
        ).reset_index()
        
        st.success("已创建透视表")
        return self.df
    
    def get_transformed_data(self) -> Optional[pd.DataFrame]:
        """获取转换后的数据"""
        return self.df

# 创建全局实例
data_transformer = DataTransformer()