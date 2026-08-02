# spider_zhuwang/test_page.py
"""
生猪爬虫测试页面
用于测试爬虫的各项功能
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spider_zhuwang.pig_spider import PigPriceSpider

st.set_page_config(
    page_title="生猪爬虫测试",
    page_icon="🐖",
    layout="wide"
)

st.title("🐖 生猪价格爬虫测试")
st.markdown("> 测试爬虫的下载、合并、异常检测等功能")

# 初始化爬虫
@st.cache_resource
def get_spider():
    return PigPriceSpider()

spider = get_spider()

# ==================== 侧边栏 ====================
st.sidebar.header("⚙️ 测试配置")

test_mode = st.sidebar.selectbox(
    "选择测试模式",
    ["📥 单日下载", "📦 批量下载", "🔗 获取链接测试", "📊 合并数据", "🔍 异常检测", "📋 查看最新文件"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"📁 保存目录: {spider.save_dir}")

# ==================== 单日下载 ====================
if test_mode == "📥 单日下载":
    st.subheader("📥 单日数据下载")
    
    url = st.text_input(
        "详情页URL",
        value="https://hangqing.zhuwang.com.cn/shengzhu/20260727/647340.html",
        placeholder="输入生猪价格详情页URL"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        merge_option = st.radio(
            "合并选项",
            ["自动查找最新合并文件", "指定合并文件", "不合并（仅下载）"]
        )
    
    with col2:
        if merge_option == "指定合并文件":
            merge_path = st.text_input(
                "合并文件路径",
                placeholder="输入完整的文件路径"
            )
        else:
            merge_path = None
    
    if st.button("🚀 开始下载", type="primary", use_container_width=True):
        if not url:
            st.error("请输入URL")
        else:
            with st.spinner("正在下载数据..."):
                try:
                    if merge_option == "自动查找最新合并文件":
                        merge_path = spider.get_latest_merge_file()
                        if merge_path:
                            st.info(f"使用最新合并文件: {os.path.basename(merge_path)}")
                    elif merge_option == "不合并（仅下载）":
                        merge_path = None
                    
                    result = spider.download_single(url, merge_path=merge_path)
                    
                    if result:
                        st.success(f"✅ 下载成功！")
                        st.info(f"📁 文件路径: {result}")
                        
                        # 预览数据
                        if os.path.exists(result):
                            df = pd.read_excel(result)
                            st.subheader("📊 数据预览")
                            st.dataframe(df.head(10), use_container_width=True)
                            st.caption(f"共 {len(df)} 行")
                    else:
                        st.error("❌ 下载失败")
                except Exception as e:
                    st.error(f"下载出错: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# ==================== 批量下载 ====================
elif test_mode == "📦 批量下载":
    st.subheader("📦 批量数据下载")
    
    # 方式1：从列表页自动获取
    st.markdown("#### 方式一：从列表页自动获取")
    
    list_url = st.text_input(
        "列表页URL",
        value="https://hangqing.zhuwang.com.cn/shengzhu/list-63-1.html",
        placeholder="输入列表页URL",
        key="list_url_input"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input("最大页数", min_value=1, max_value=50, value=2, key="max_pages_input")
    with col2:
        merge_option_batch = st.radio(
            "合并选项",
            ["自动查找最新合并文件", "不合并"],
            horizontal=True,
            key="merge_option_batch"
        )
    
    # 先测试获取链接
    if st.button("🔍 测试获取链接", use_container_width=True, key="test_get_links"):
        if not list_url:
            st.error("请输入列表页URL")
        else:
            with st.spinner("正在获取链接..."):
                try:
                    urls = spider.get_links_from_list_page(list_url, max_pages=max_pages)
                    if urls:
                        st.success(f"✅ 成功获取 {len(urls)} 个链接")
                        st.write("前10个链接预览:")
                        st.write(urls[:10])
                        
                        # 显示链接统计
                        st.info(f"📊 链接统计: 共 {len(urls)} 个链接")
                    else:
                        st.error("❌ 未获取到任何链接，请检查列表页结构")
                except Exception as e:
                    st.error(f"获取链接失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # 批量下载按钮
    if st.button("🚀 开始批量下载", type="primary", use_container_width=True, key="batch_download_btn"):
        if not list_url:
            st.error("请输入列表页URL")
        else:
            with st.spinner("正在批量下载数据..."):
                try:
                    merge_path = spider.get_latest_merge_file() if merge_option_batch == "自动查找最新合并文件" else None
                    if merge_path:
                        st.info(f"使用最新合并文件: {os.path.basename(merge_path)}")
                    
                    result = spider.download_from_list_page(
                        list_url, 
                        max_pages=max_pages,
                        merge_path=merge_path
                    )
                    
                    if result is not None:
                        st.success(f"✅ 批量下载完成！")
                        st.dataframe(result.head(10), use_container_width=True)
                        st.caption(f"共 {len(result)} 行")
                    else:
                        st.error("❌ 下载失败，请检查日志")
                except Exception as e:
                    st.error(f"下载出错: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # 方式2：手动输入URL列表
    st.markdown("#### 方式二：手动输入URL列表")
    
    urls_text = st.text_area(
        "输入详情页URL（每行一个）",
        placeholder="https://hangqing.zhuwang.com.cn/shengzhu/20260727/647340.html\nhttps://hangqing.zhuwang.com.cn/shengzhu/20260726/647339.html",
        height=150,
        key="manual_urls_input"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        merge_option_manual = st.radio(
            "合并选项",
            ["自动查找最新合并文件", "不合并"],
            horizontal=True,
            key="merge_option_manual"
        )
    
    with col2:
        if st.button("📥 批量下载手动输入的URL", type="primary", use_container_width=True, key="manual_download_btn"):
            urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
            if not urls:
                st.warning("请输入至少一个URL")
            else:
                with st.spinner(f"正在批量下载 {len(urls)} 个链接..."):
                    try:
                        merge_path = spider.get_latest_merge_file() if merge_option_manual == "自动查找最新合并文件" else None
                        if merge_path:
                            st.info(f"使用最新合并文件: {os.path.basename(merge_path)}")
                        
                        result = spider.download_batch(urls, merge_path=merge_path)
                        
                        if result is not None:
                            st.success(f"✅ 批量下载完成！共 {len(result)} 行")
                            st.dataframe(result.head(10), use_container_width=True)
                            st.caption(f"共 {len(result)} 行")
                        else:
                            st.error("❌ 下载失败")
                    except Exception as e:
                        st.error(f"下载出错: {e}")
                        import traceback
                        st.code(traceback.format_exc())

# ==================== 获取链接测试 ====================
elif test_mode == "🔗 获取链接测试":
    st.subheader("🔗 列表页链接获取测试")
    
    st.info("此模式专门测试从列表页获取详情页链接的功能")
    
    test_list_url = st.text_input(
        "列表页URL",
        value="https://hangqing.zhuwang.com.cn/shengzhu/list-63-1.html",
        placeholder="输入列表页URL",
        key="test_list_url"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        test_max_pages = st.number_input("测试页数", min_value=1, max_value=10, value=2, key="test_max_pages")
    with col2:
        show_full_list = st.checkbox("显示完整链接列表", value=False, key="show_full_list")
    
    if st.button("🔍 开始测试", type="primary", use_container_width=True, key="start_link_test"):
        if not test_list_url:
            st.error("请输入列表页URL")
        else:
            with st.spinner("正在获取链接..."):
                try:
                    urls = spider.get_links_from_list_page(test_list_url, max_pages=test_max_pages)
                    
                    if urls:
                        st.success(f"✅ 成功获取 {len(urls)} 个链接")
                        
                        # 显示统计信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总链接数", len(urls))
                        with col2:
                            # 提取日期
                            import re
                            dates = []
                            for url in urls:
                                match = re.search(r'/(\d{8})/', url)
                                if match:
                                    dates.append(match.group(1))
                            if dates:
                                st.metric("日期范围", f"{min(dates)} ~ {max(dates)}")
                        with col3:
                            st.metric("唯一日期数", len(set(dates)) if dates else 0)
                        
                        # 显示链接列表
                        if show_full_list:
                            st.subheader("📋 完整链接列表")
                            st.write(urls)
                        else:
                            st.subheader("📋 链接预览（前20个）")
                            st.write(urls[:20])
                            if len(urls) > 20:
                                st.caption(f"... 还有 {len(urls) - 20} 个链接未显示")
                        
                        # 导出链接
                        if urls:
                            import io
                            df_urls = pd.DataFrame({'链接': urls})
                            csv = df_urls.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 下载链接列表 (CSV)",
                                data=csv,
                                file_name=f"urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_urls"
                            )
                    else:
                        st.error("❌ 未获取到任何链接")
                        st.info("可能原因：\n1. 列表页结构发生变化\n2. 列表页需要登录或验证\n3. 网络连接问题")
                        
                        # 显示页面内容调试
                        try:
                            import requests
                            response = requests.get(test_list_url, headers=spider.headers, timeout=30)
                            st.subheader("🔧 页面内容调试")
                            st.text(f"状态码: {response.status_code}")
                            st.text(f"内容长度: {len(response.text)}")
                            if len(response.text) < 500:
                                st.text("页面内容:")
                                st.code(response.text[:500])
                        except Exception as e:
                            st.error(f"无法获取页面内容: {e}")
                            
                except Exception as e:
                    st.error(f"测试失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# ==================== 合并数据 ====================
elif test_mode == "📊 合并数据":
    st.subheader("📊 数据合并与历史标记")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**原始数据文件 (A)**")
        file_a = st.text_input(
            "文件A路径",
            placeholder="输入原始数据文件路径",
            key="file_a_input"
        )
    
    with col2:
        st.write("**新增数据文件 (B)**")
        file_b = st.text_input(
            "文件B路径",
            placeholder="输入新增数据文件路径",
            key="file_b_input"
        )
    
    if st.button("🔄 开始合并", type="primary", use_container_width=True, key="merge_btn"):
        if not file_a or not file_b:
            st.error("请输入两个文件的路径")
        else:
            if not os.path.exists(file_a):
                st.error(f"文件A不存在: {file_a}")
            elif not os.path.exists(file_b):
                st.error(f"文件B不存在: {file_b}")
            else:
                with st.spinner("正在合并数据..."):
                    try:
                        result = spider.merge_and_mark_historical(file_a, file_b)
                        if result:
                            st.success(f"✅ 合并完成！")
                            st.info(f"📁 合并文件: {result}")
                            
                            # 预览数据
                            df = pd.read_excel(result, sheet_name='保留_最新数据')
                            st.subheader("📊 合并结果预览")
                            st.dataframe(df.head(10), use_container_width=True)
                            st.caption(f"共 {len(df)} 行")
                            
                            # 显示统计信息
                            stats_df = pd.read_excel(result, sheet_name='统计信息')
                            st.subheader("📊 统计信息")
                            st.dataframe(stats_df, use_container_width=True)
                    except Exception as e:
                        st.error(f"合并出错: {e}")
                        import traceback
                        st.code(traceback.format_exc())

# ==================== 异常检测 ====================
# spider_zhuwang/test_page.py
# 替换异常检测部分的代码

elif test_mode == "🔍 异常检测":
    st.subheader("🔍 3σ异常值检测")
    
    # ✅ 从目录读取Excel文件
    import glob
    data_dir = r"H:\mzjxuhuaigu\SQL\Python脚本\5-养猪网数据存储"
    
    # 获取所有Excel文件
    excel_files = glob.glob(os.path.join(data_dir, "*.xlsx"))
    excel_files.extend(glob.glob(os.path.join(data_dir, "*.xls")))
    
    # 按修改时间排序
    excel_files.sort(key=os.path.getmtime, reverse=True)
    
    if excel_files:
        # 提取文件名
        file_options = {os.path.basename(f): f for f in excel_files}
        selected_file_name = st.selectbox(
            "选择要检测的Excel文件",
            options=list(file_options.keys()),
            help="从目录中选择要检测的Excel文件"
        )
        
        if selected_file_name:
            file_path = file_options[selected_file_name]
            st.info(f"📁 文件: {file_path}")
            
            # 显示文件信息
            file_size = os.path.getsize(file_path) / 1024 / 1024
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            col1, col2 = st.columns(2)
            with col1:
                st.metric("文件大小", f"{file_size:.2f} MB")
            with col2:
                st.metric("最后修改", mod_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            # Sheet选择（如果有多个Sheet）
            try:
                xls = pd.ExcelFile(file_path)
                sheet_names = xls.sheet_names
                if '保留_最新数据' in sheet_names:
                    default_sheet = '保留_最新数据'
                else:
                    default_sheet = sheet_names[0] if sheet_names else None
                
                selected_sheet = st.selectbox(
                    "选择Sheet",
                    options=sheet_names,
                    index=sheet_names.index(default_sheet) if default_sheet in sheet_names else 0,
                    help="选择要检测的Sheet"
                )
            except:
                selected_sheet = '保留_最新数据'
            
            if st.button("🔍 开始检测", type="primary", use_container_width=True):
                with st.spinner("正在检测异常值..."):
                    try:
                        result = spider.mark_anomalies_by_3sigma(
                            file_path, 
                            sheet_name=selected_sheet
                        )
                        if result:
                            st.success(f"✅ 异常检测完成！")
                            
                            # 显示异常值汇总
                            try:
                                df = pd.read_excel(file_path, sheet_name='异常值汇总')
                                if df is not None and not df.empty:
                                    st.subheader("📊 异常值汇总")
                                    st.dataframe(df, use_container_width=True)
                                    st.caption(f"共 {len(df)} 个异常值")
                                else:
                                    st.info("未发现异常值")
                            except:
                                st.info("未发现异常值或异常值汇总表不存在")
                    except Exception as e:
                        st.error(f"检测出错: {e}")
                        import traceback
                        st.code(traceback.format_exc())
    else:
        st.warning(f"未找到Excel文件（目录: {data_dir}）")

# ==================== 查看最新文件 ====================
elif test_mode == "📋 查看最新文件":
    st.subheader("📋 查看最新合并文件")
    
    if st.button("🔄 刷新", use_container_width=True, key="refresh_btn"):
        latest = spider.get_latest_merge_file()
        if latest:
            st.success(f"✅ 最新文件: {os.path.basename(latest)}")
            st.info(f"📁 完整路径: {latest}")
            
            # 显示文件信息
            file_size = os.path.getsize(latest) / 1024 / 1024
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("文件大小", f"{file_size:.2f} MB")
            with col2:
                st.metric("最后修改", mod_time.strftime('%Y-%m-%d %H:%M:%S'))
            with col3:
                # 获取文件中的记录数
                try:
                    df = pd.read_excel(latest, sheet_name='保留_最新数据')
                    st.metric("数据记录数", f"{len(df):,}")
                except:
                    st.metric("数据记录数", "N/A")
            
            # 预览数据
            try:
                df = pd.read_excel(latest, sheet_name='保留_最新数据')
                st.subheader("📊 数据预览")
                st.dataframe(df.head(10), use_container_width=True)
                st.caption(f"共 {len(df)} 行")
                
                # 显示日期范围
                if '日期' in df.columns:
                    df['日期'] = pd.to_datetime(df['日期'])
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("最早日期", df['日期'].min().strftime('%Y-%m-%d'))
                    with col2:
                        st.metric("最新日期", df['日期'].max().strftime('%Y-%m-%d'))
            except Exception as e:
                st.warning(f"预览数据失败: {e}")
        else:
            st.warning("未找到合并标记文件")

st.markdown("---")
st.caption(f"🐖 生猪价格爬虫 | 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")