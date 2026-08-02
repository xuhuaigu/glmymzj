# data_processing/data_analyzer.py
import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Optional, Dict

class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df
    
    def set_data(self, df: pd.DataFrame):
        """设置数据"""
        self.df = df
        return self
    
    def get_basic_stats(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """获取基本统计信息"""
        if columns:
            df_subset = self.df[columns]
        else:
            df_subset = self.df.select_dtypes(include=[np.number])
        
        stats = df_subset.describe().T
        stats['缺失值'] = df_subset.isnull().sum()
        stats['缺失比例(%)'] = (df_subset.isnull().sum() / len(df_subset) * 100)
        stats['偏度'] = df_subset.skew()
        stats['峰度'] = df_subset.kurtosis()
        
        return stats
    
    def get_correlation_matrix(self, method: str = 'pearson') -> pd.DataFrame:
        """获取相关系数矩阵"""
        numeric_df = self.df.select_dtypes(include=[np.number])
        return numeric_df.corr(method=method)
    
    def find_high_correlations(self, threshold: float = 0.7) -> List[tuple]:
        """找出高相关性的变量对"""
        corr_matrix = self.get_correlation_matrix()
        
        high_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) >= threshold:
                    high_corr.append({
                        '变量1': corr_matrix.columns[i],
                        '变量2': corr_matrix.columns[j],
                        '相关系数': corr_matrix.iloc[i, j]
                    })
        
        return sorted(high_corr, key=lambda x: abs(x['相关系数']), reverse=True)
    
    def get_column_insights(self, column: str) -> Dict:
        """获取单个列的洞察"""
        if column not in self.df.columns:
            return {}
        
        col_data = self.df[column].dropna()
        insights = {
            '列名': column,
            '数据类型': str(self.df[column].dtype),
            '唯一值数': self.df[column].nunique(),
            '缺失值数': self.df[column].isnull().sum(),
            '缺失比例': f"{self.df[column].isnull().sum() / len(self.df) * 100:.2f}%"
        }
        
        # 数值列的特殊统计
        if pd.api.types.is_numeric_dtype(self.df[column]):
            insights.update({
                '最小值': col_data.min(),
                '最大值': col_data.max(),
                '均值': col_data.mean(),
                '中位数': col_data.median(),
                '标准差': col_data.std(),
                '偏度': col_data.skew(),
                '峰度': col_data.kurtosis()
            })
        else:
            # 分类列的特殊统计
            value_counts = col_data.value_counts()
            insights.update({
                '最常见值': value_counts.index[0] if len(value_counts) > 0 else None,
                '最常见值频数': value_counts.iloc[0] if len(value_counts) > 0 else 0,
                '最常见值比例': f"{value_counts.iloc[0] / len(col_data) * 100:.2f}%" if len(value_counts) > 0 else "0%"
            })
        
        return insights
    
    def get_groupby_stats(self, group_by: str, agg_column: str, 
                           agg_funcs: List[str] = ['mean', 'sum', 'count']) -> pd.DataFrame:
        """获取分组统计"""
        agg_dict = {agg_column: agg_funcs}
        return self.df.groupby(group_by).agg(agg_dict).reset_index()
    
    def detect_outliers_iqr(self, column: str, threshold: float = 1.5) -> Dict:
        """使用IQR方法检测异常值"""
        Q1 = self.df[column].quantile(0.25)
        Q3 = self.df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        outliers = self.df[(self.df[column] < lower_bound) | (self.df[column] > upper_bound)]
        
        return {
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'outliers_count': len(outliers),
            'outliers_ratio': f"{len(outliers) / len(self.df) * 100:.2f}%",
            'outliers_values': outliers[column].tolist()
        }
    
    def get_time_series_decomposition(self, date_column: str, value_column: str) -> Dict:
        """时间序列分解（趋势、季节性、残差）"""
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        # 确保数据按日期排序
        df_sorted = self.df.sort_values(date_column)
        df_sorted = df_sorted.set_index(date_column)
        
        # 执行分解
        result = seasonal_decompose(df_sorted[value_column], model='additive', period=7)
        
        return {
            'trend': result.trend,
            'seasonal': result.seasonal,
            'residual': result.resid,
            'observed': result.observed
        }

# 创建全局实例
data_analyzer = DataAnalyzer()