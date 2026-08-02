# spider_zhuwang/corn_test_page.py
"""
玉米爬虫测试页面
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spider_zhuwang.corn_spider import CornPriceSpider

st.set_page_config(
    page_title="玉米爬虫测试",
    page_icon="🌽",
    layout="wide"
)

st.title("🌽 玉米价格爬虫测试")
st.markdown("> 测试玉米价格数据爬虫的批量爬取功能")

# ==================== 初始化爬虫 ====================
@st.cache_resource
def get_corn_spider():
    """获取玉米爬虫实例"""
    return CornPriceSpider(creator='mzj')

spider = get_corn_spider()

# ==================== 侧边栏 ====================
st.sidebar.header("⚙️ 测试配置")

test_mode = st.sidebar.selectbox(
    "选择测试模式",
    ["📥 从列表页批量爬取", "📋 查看最新文件", "🔧 单URL测试"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"📁 保存目录: {spider.save_dir}")

# ==================== 从列表页批量爬取 ====================
if test_mode == "📥 从列表页批量爬取":
    st.subheader("📥 从列表页批量爬取玉米价格数据")
    
    st.info("""
    **使用说明：**
    1. 输入列表页URL（默认：玉米列表页）
    2. 设置最大爬取页数
    3. 选择合并文件（下拉选择已有文件，或选择"创建新文件"）
    4. 点击「开始爬取」
    """)
    
    list_url = st.text_input(
        "列表页URL",
        value="https://hangqing.zhuwang.com.cn/yumi/list-68-1.html",
        placeholder="输入玉米价格列表页URL"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input("最大爬取页数", min_value=1, max_value=50, value=2)
    
    with col2:
        # 获取已有文件列表
        existing_files = spider.get_all_files()
        
        merge_options = ["🆕 创建新文件"] + [os.path.basename(f) for f in existing_files]
        
        selected_file = st.selectbox(
            "选择合并文件",
            options=merge_options,
            help="选择要合并的已有文件，或选择创建新文件"
        )
        
        if selected_file == "🆕 创建新文件":
            merge_file_path = None
            st.info("将创建新的Excel文件")
        else:
            # 找到对应的完整路径
            for f in existing_files:
                if os.path.basename(f) == selected_file:
                    merge_file_path = f
                    break
            st.info(f"将合并到: {selected_file}")
    
    # 文件命名（仅当创建新文件时有效）
    filename = None
    if selected_file == "🆕 创建新文件":
        filename = st.text_input(
            "输出文件名（可选）",
            placeholder="留空则自动生成",
            help="例如: 玉米价格_20260728.xlsx"
        )
        if filename and not filename.endswith('.xlsx'):
            filename += '.xlsx'
    
    # 显示当前爬虫状态
    st.caption(f"📊 当前数据状态: {'已有数据' if spider.data else '无数据'}")
    
    if st.button("🚀 开始爬取", type="primary", use_container_width=True):
        if not list_url:
            st.error("请输入列表页URL")
        else:
            with st.spinner("正在爬取玉米价格数据..."):
                try:
                    # 先提取URL
                    st.info(f"正在从列表页提取链接: {list_url}")
                    detail_urls = spider.extract_urls_from_list_page(list_url, max_pages)
                    
                    if not detail_urls:
                        st.error("❌ 未提取到任何详情页URL")
                    else:
                        st.success(f"✅ 提取到 {len(detail_urls)} 个详情页URL")
                        
                        # 爬取数据
                        st.info(f"正在爬取 {len(detail_urls)} 个详情页...")
                        spider._fetch_multiple_urls(detail_urls)
                        
                        if not spider.data:
                            st.error("❌ 没有爬取到任何数据")
                        else:
                            st.success(f"✅ 成功爬取 {len(spider.data)} 条数据")
                            
                            # 转换为DataFrame，合并文件
                            spider.to_dataframe(merge_file=merge_file_path)
                            
                            # 保存到Excel
                            if merge_file_path:
                                success = spider.save_to_excel(merge_file=merge_file_path)
                            else:
                                if filename:
                                    success = spider.save_to_excel(filename=filename)
                                else:
                                    success = spider.save_to_excel()
                            
                            if success and spider.df is not None:
                                st.success(f"✅ 数据保存成功！")
                                
                                # 显示数据预览
                                st.subheader("📊 数据预览")
                                st.dataframe(spider.df.head(10), use_container_width=True)
                                st.caption(f"共 {len(spider.df)} 条记录")
                                
                                # 显示统计信息
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("总记录数", len(spider.df))
                                with col2:
                                    if '省份' in spider.df.columns:
                                        st.metric("省份数", spider.df['省份'].nunique())
                                with col3:
                                    if '数据状态' in spider.df.columns:
                                        keep_count = len(spider.df[spider.df['数据状态'] == '保留'])
                                        st.metric("保留记录", keep_count)
                                with col4:
                                    if '数据状态' in spider.df.columns:
                                        history_count = len(spider.df[spider.df['数据状态'] == '历史'])
                                        st.metric("历史记录", history_count)
                            else:
                                st.error("❌ 数据保存失败")
                                
                except Exception as e:
                    st.error(f"爬取出错: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# ==================== 查看最新文件 ====================
elif test_mode == "📋 查看最新文件":
    st.subheader("📋 查看最新玉米价格文件")
    
    if st.button("🔄 刷新", use_container_width=True):
        # 获取所有文件
        all_files = spider.get_all_files()
        
        if all_files:
            st.success(f"✅ 找到 {len(all_files)} 个玉米价格文件")
            
            # 显示文件列表
            for f in all_files:
                file_size = os.path.getsize(f) / 1024 / 1024
                mod_time = datetime.fromtimestamp(os.path.getmtime(f))
                
                with st.expander(f"📁 {os.path.basename(f)}", expanded=(f == all_files[0])):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("文件大小", f"{file_size:.2f} MB")
                    with col2:
                        st.metric("最后修改", mod_time.strftime('%Y-%m-%d %H:%M:%S'))
                    with col3:
                        try:
                            # 统计各Sheet数据量
                            xls = pd.ExcelFile(f)
                            sheet_counts = {}
                            for sheet in xls.sheet_names:
                                df = pd.read_excel(f, sheet_name=sheet)
                                sheet_counts[sheet] = len(df)
                            st.metric("Sheet数", len(xls.sheet_names))
                        except:
                            st.metric("Sheet数", "N/A")
                    
                    # 预览数据
                    try:
                        df = pd.read_excel(f, sheet_name='保留_最新数据')
                        st.dataframe(df.head(10), use_container_width=True)
                        st.caption(f"「保留_最新数据」共 {len(df)} 条记录")
                    except:
                        try:
                            df = pd.read_excel(f, sheet_name=0)
                            st.dataframe(df.head(10), use_container_width=True)
                            st.caption(f"共 {len(df)} 条记录")
                        except:
                            pass
        else:
            st.warning(f"未找到玉米价格文件（目录: {spider.save_dir}）")

# ==================== 单URL测试 ====================
elif test_mode == "🔧 单URL测试":
    st.subheader("🔧 单URL测试")
    
    st.info("""
    **测试单个URL的数据爬取**
    用于调试和验证单个页面是否能正常解析
    """)
    
    test_url = st.text_input(
        "测试URL",
        value="https://hangqing.zhuwang.com.cn/yumi/20260728/647384.html",
        placeholder="输入玉米价格详情页URL"
    )
    
    if st.button("🔍 测试爬取", type="primary", use_container_width=True):
        if not test_url:
            st.error("请输入测试URL")
        else:
            with st.spinner("正在测试爬取..."):
                try:
                    # 自动检测数据类型
                    data_type, province_name = spider.detect_data_type(test_url)
                    st.info(f"检测到数据类型: {data_type}, 省份: {province_name}")
                    
                    # 爬取数据
                    if data_type == 'national':
                        data = spider.fetch_national_data(test_url)
                    else:
                        data = spider.fetch_province_data(test_url, province_name)
                    
                    if data:
                        st.success(f"✅ 成功爬取 {len(data)} 条数据")
                        
                        # 显示数据预览
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.error("❌ 未获取到数据")
                        
                except Exception as e:
                    st.error(f"测试失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())

st.markdown("---")
st.caption(f"🌽 玉米价格爬虫 | 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")