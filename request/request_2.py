import streamlit as st
import pandas as pd

st.title("AntV S2 - 多维数据透视表")

s2_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <!-- 替换为这些稳定链接 -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@antv/s2@1.56.0/build/css/index.min.css">
    <script src="https://cdn.jsdelivr.net/npm/@antv/s2@1.56.0/dist/index.min.js"></script>
    <style>
        #container { width: 100%; height: 500px; }
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        const data = [
            { category: '电子产品', subCategory: '手机', sales: 12000, profit: 3000 },
            { category: '电子产品', subCategory: '电脑', sales: 25000, profit: 5000 },
            { category: '服装', subCategory: '男装', sales: 8000, profit: 2000 },
            { category: '服装', subCategory: '女装', sales: 15000, profit: 3500 },
            { category: '食品', subCategory: '零食', sales: 5000, profit: 1000 },
        ];
        
        const s2DataConfig = {
            fields: {
                rows: ['category', 'subCategory'],
                columns: [],
                values: ['sales', 'profit']
            },
            data: data
        };
        
        const s2Options = {
            width: document.getElementById('container').clientWidth,
            height: 500,
            interaction: { enableInteractions: true }
        };
        
        const container = document.getElementById('container');
        const s2 = new S2.PivotSheet(container, s2DataConfig, s2Options);
        s2.render();
    </script>
</body>
</html>
"""

st.components.v1.html(s2_html, height=550)