import streamlit as st
import pandas as pd
from shengYiShe import MaltodextrinScraper
import time
from datetime import datetime
import os
import io
from data_processing import data_exporter

# 页面配置
st.set_page_config(
    page_title="大宗商品报价采集器",
    page_icon="📊",
    layout="wide"
)

st.title("📊 大宗商品报价采集器")
st.markdown("从 100ppi.com 爬取各类大宗商品最新报价数据")

# ==================== 初始化 ====================
if 'all_category_links' not in st.session_state:
    st.session_state.all_category_links = {}  # {分类名称: [(产品名称, URL), ...]}
if 'selected_products' not in st.session_state:
    st.session_state.selected_products = []  # [(产品名称, URL, 分类), ...]
if 'data' not in st.session_state:
    st.session_state.data = []
if 'scraping' not in st.session_state:
    st.session_state.scraping = False
if 'progress' not in st.session_state:
    st.session_state.progress = (0, 0, 0, 0)  # (当前物料序号, 总物料数, 当前页, 总页数)

# ==================== 产品链接提取（正文上方） ====================
st.subheader("🔗 产品列表")

# 分类选择
categories = ['能源', '有色', '钢铁', '化工', '橡塑', '纺织', '建材', '农副']
selected_categories = st.multiselect(
    "选择要提取的分类",
    options=categories,
    default=categories,  # ✅ 默认全选
    help="选择要提取的分类，默认提取所有分类"
)

col_extract, col_status = st.columns([1, 3])

with col_extract:
    extract_btn = st.button("🔄 提取产品链接", type="primary", use_container_width=True)

with col_status:
    if extract_btn:
        with st.spinner("正在提取产品链接..."):
            scraper = MaltodextrinScraper(base_url='https://www.100ppi.com')
            
            if selected_categories:
                all_links = scraper.extract_all_links(selected_categories)
            else:
                all_links = scraper.extract_all_links()
            
            st.session_state.all_category_links = all_links
            
            total_products = sum(len(links) for links in all_links.values())
            st.success(f"✅ 成功提取 {len(all_links)} 个分类，共 {total_products} 个产品")
    
    # 显示各分类统计
    if st.session_state.all_category_links:
        cols = st.columns(len(st.session_state.all_category_links))
        for idx, (category, links) in enumerate(st.session_state.all_category_links.items()):
            with cols[idx]:
                st.info(f"📁 {category}: {len(links)} 个")

st.divider()

# ==================== 参数配置 ====================
st.subheader("⚙️ 参数配置")

# 第一行：产品选择 + 爬取页数 + 开始按钮
col1, col2, col3 = st.columns([3, 2, 1])

with col1:
    # 按分类分组显示的多选
    if st.session_state.all_category_links:
        # 构建带分类标签的产品列表
        all_products = []
        product_to_category = {}
        for category, links in st.session_state.all_category_links.items():
            for name, url in links:
                display_name = f"[{category}] {name}"
                all_products.append(display_name)
                product_to_category[display_name] = (name, url, category)
        # 全选复选框
        select_all = st.checkbox("全选所有物料", value=False)
        

        selected_display_names = st.multiselect(
            "选择物料（可多选）",
            options=all_products,
            default=all_products if select_all else [],
            help="可以选择不同分类的多个物料，系统将依次爬取"
        )
 

        # 转换为 (产品名称, URL, 分类) 列表
        st.session_state.selected_products = [
            product_to_category[name] for name in selected_display_names
        ]
    else:
        st.info("👈 请先点击「提取产品链接」获取产品列表")
        selected_display_names = []

with col2:
    max_pages = st.slider("每个物料爬取页数", min_value=1, max_value=10, value=10, 
                          help="网站最多10页数据")

with col3:
    st.write("")  # 占位
    st.write("")  # 占位
    start_btn = st.button("🚀 开始爬取", type="primary", use_container_width=True,
                         disabled=len(selected_display_names) == 0)

# 第二行：清空按钮 + 当前选择状态
col4, col5, col6 = st.columns([3, 2, 1])
with col6:
    clear_btn = st.button("🗑️ 清空数据", use_container_width=True)

st.divider()

# ==================== 状态显示 ====================
status_placeholder = st.empty()
progress_placeholder = st.empty()

# 显示当前选中的产品
if selected_display_names:
    # 按分类统计
    category_counts = {}
    for name in selected_display_names:
        category = name.split(']')[0].replace('[', '') if ']' in name else '未知'
        category_counts[category] = category_counts.get(category, 0) + 1
    
    summary_text = f"📌 已选择 {len(selected_display_names)} 个物料："
    for category, count in category_counts.items():
        summary_text += f" {category}({count})"
    st.info(summary_text)
else:
    st.info("📌 请至少选择一个物料")

# 清空数据
if clear_btn:
    st.session_state.data = []
    st.session_state.progress = (0, 0, 0, 0)
    st.rerun()

# 开始爬取
if start_btn and not st.session_state.scraping and selected_display_names:
    st.session_state.scraping = True
    st.session_state.data = []
    # ✅ 在这里添加，记录开始时间
    start_time = time.time()
    scraper = MaltodextrinScraper(base_url='https://www.100ppi.com')
    
    # 获取选中的 (产品名称, URL, 分类) 列表
    selected_items = st.session_state.selected_products
    
    total_products = len(selected_items)
    all_data = []
    
    # 进度回调
    def update_progress(product_idx, total_products, product_name, page_count):
        st.session_state.progress = (product_idx, total_products, 0, 0)
        progress_text = f"正在爬取 [{product_idx}/{total_products}] {product_name}，本页 {page_count} 条"
        progress_placeholder.progress(
            product_idx / total_products,
            text=progress_text
        )
    
    # 执行爬取
    try:
        for idx, (product_name, product_url, category) in enumerate(selected_items, 1):
            # 更新状态
            status_placeholder.info(f"🔄 正在爬取 [{idx}/{total_products}] [{category}] {product_name} ...")
            
            # 爬取当前物料
            scraper.clear()
            
            # 使用进度回调
            def page_progress_callback(current, total, count, idx=idx, product_name=product_name):
                update_progress(idx, total_products, product_name, count)
            
            scraper.scrape(
                product_url=product_url,
                max_pages=max_pages,
                progress_callback=page_progress_callback
            )
            raw_data = scraper.get_data()
            
            if raw_data:
                # ✅ 添加创建人、创建时间、物料名称、物料分类
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for row in raw_data:
                    row['创建人'] = 'mzj'
                    row['创建时间'] = current_time
                    row['物料名称'] = product_name
                    row['物料分类'] = category  # ✅ 新增物料分类字段
                all_data.extend(raw_data)
                status_placeholder.success(f"✅ [{idx}/{total_products}] [{category}] {product_name} 完成，获取 {len(raw_data)} 条数据")
            else:
                status_placeholder.warning(f"⚠️ [{idx}/{total_products}] [{category}] {product_name} 未获取到数据")
            
            # 每个物料之间增加延迟
            if idx < total_products:
                time.sleep(2)

        # ✅ 计算用时
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        time_str = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"

        if all_data:
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"
            
            st.session_state.data = all_data
            st.session_state.last_elapsed_time = time_str  # ✅ 保存到 session_state
            
            status_placeholder.success(f"✅ 全部爬取完成！共获取 {len(all_data)} 条数据，用时 {time_str}")
        else:
            st.session_state.data = all_data
            st.session_state.last_elapsed_time = "未获取到数据"  # ✅ 保存到 session_state
            status_placeholder.error("❌ 未获取到任何数据")
            
    except Exception as e:
        status_placeholder.error(f"❌ 发生错误：{str(e)}")
    
    finally:
        st.session_state.scraping = False
        st.rerun()

# 显示爬取进度
if st.session_state.scraping:
    product_idx, total_products, _, _ = st.session_state.progress
    if total_products > 0:
        progress_text = f"正在爬取 [{product_idx}/{total_products}]"
        progress_placeholder.progress(
            product_idx / total_products,
            text=progress_text
        )

# ==================== 数据显示 ====================
tab1, tab2, tab3 = st.tabs(["📋 数据表格", "📊 统计分析", "💾 导出数据"])
with tab1:
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        # ✅ 调整列顺序：物料分类 → 物料名称 → 其他 → 创建人 → 创建时间
        base_cols = [c for c in df.columns if c not in ['物料分类', '物料名称', '创建人', '创建时间']]
        cols = ['物料分类', '物料名称'] + base_cols + ['创建人', '创建时间']
        # 只保留存在的列
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        st.dataframe(df, use_container_width=True, height=400)
        
        st.caption(f"共 {len(df)} 条记录")
        st.divider()
        
        # ✅ 按分类统计
        st.subheader("📊 各分类数据量统计")
        category_counts = df['物料分类'].value_counts()
        st.dataframe(category_counts, use_container_width=True, height=150)
        
        st.subheader("📊 各物料数据量统计")
        product_counts = df['物料名称'].value_counts()
        st.dataframe(product_counts, use_container_width=True, height=200)
    else:
        st.info("请选择物料并点击「开始爬取」按钮获取数据")

with tab2:
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("总数据条数", len(df))
        with col2:
            categories = df['物料分类'].nunique()
            st.metric("分类数量", categories)
        with col3:
            products = df['物料名称'].nunique()
            st.metric("物料种类数", products)
        with col4:
            traders = df['交易商'].nunique()
            st.metric("交易商数量", traders)
        with col5:
            places = df['交货地'].nunique()
            st.metric("交货地数量", places)
        
        st.divider()
        
        # ✅ 各分类数据量分布
        st.subheader("📊 各分类数据量分布")
        category_counts = df['物料分类'].value_counts()
        st.bar_chart(category_counts)
        
        # 各物料数据量分布
        st.subheader("📊 各物料数据量分布")
        product_counts = df['物料名称'].value_counts().head(20)
        st.bar_chart(product_counts)
        
        # 交货地分布
        st.subheader("📍 交货地分布")
        place_counts = df['交货地'].value_counts().head(10)
        st.bar_chart(place_counts)
        
        # 报价类型分布
        st.subheader("📌 报价类型分布")
        price_type_counts = df['报价类型'].value_counts()
        st.dataframe(price_type_counts, use_container_width=True)
        
        # 创建人统计
        st.subheader("👤 创建人统计")
        creator_counts = df['创建人'].value_counts()
        st.dataframe(creator_counts, use_container_width=True)
    else:
        st.info("暂无数据")

with tab3:
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        # 调整列顺序
        base_cols = [c for c in df.columns if c not in ['物料分类', '物料名称', '创建人', '创建时间']]
        cols = ['物料分类', '物料名称'] + base_cols + ['创建人', '创建时间']
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        # 固定保存路径
        import os
        from datetime import datetime

        # 获取当前文件所在目录
        _CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        # 项目根目录
        _PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
        # 默认保存目录
        DEFAULT_SAVE_DIR = os.path.join(_PROJECT_ROOT, 'data_save', 'shengyishe')
        save_dir = DEFAULT_SAVE_DIR
        
        os.makedirs(save_dir, exist_ok=True)
        
        # 显示当前保存路径
        st.caption(f"📁 文件保存目录：`{save_dir}`")
        
        # 生成文件名前缀
        categories = df['物料分类'].unique()
        category_str = '_'.join(categories[:3])
        if len(categories) > 3:
            category_str += f'_等{len(categories)}种'
        file_prefix = f"{category_str}_报价_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        st.divider()
        
        # ----- 导出功能（直接保存到本地） -----
        st.subheader("📥 导出数据到本地")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 保存 CSV", use_container_width=True):
                csv_path = os.path.join(save_dir, f"{file_prefix}.csv")
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                st.success(f"✅ 已保存: {os.path.basename(csv_path)}")
        
        with col2:
            if st.button("📊 保存 Excel", use_container_width=True):
                excel_path = os.path.join(save_dir, f"{file_prefix}.xlsx")
                df.to_excel(excel_path, index=False, sheet_name='报价数据')
                st.success(f"✅ 已保存: {os.path.basename(excel_path)}")
        
        with col3:
            if st.button("📥 保存 JSON", use_container_width=True):
                json_path = os.path.join(save_dir, f"{file_prefix}.json")
                df.to_json(json_path, orient='records', force_ascii=False, indent=2)
                st.success(f"✅ 已保存: {os.path.basename(json_path)}")
        
        st.divider()
        
        # 一次性保存所有格式
        if st.button("💾 保存所有格式 (CSV + Excel + JSON)", type="primary", use_container_width=True):
            # CSV
            csv_path = os.path.join(save_dir, f"{file_prefix}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # Excel
            excel_path = os.path.join(save_dir, f"{file_prefix}.xlsx")
            df.to_excel(excel_path, index=False, sheet_name='报价数据')
            
            # JSON
            json_path = os.path.join(save_dir, f"{file_prefix}.json")
            df.to_json(json_path, orient='records', force_ascii=False, indent=2)
            
            st.success(f"✅ 所有文件已保存到：{save_dir}")
            st.info(f"📄 {file_prefix}.csv\n📊 {file_prefix}.xlsx\n📥 {file_prefix}.json")
        
        # 显示最近保存的文件
        with st.expander("📋 查看已保存的文件", expanded=False):
            try:
                files = os.listdir(save_dir)
                excel_files = sorted([f for f in files if f.endswith('.xlsx')], reverse=True)[:10]
                if excel_files:
                    for f in excel_files:
                        file_path = os.path.join(save_dir, f)
                        file_size = os.path.getsize(file_path) / 1024
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        st.write(f"- {f} ({file_size:.1f} KB) - {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.info("暂无已保存的文件")
            except Exception as e:
                st.warning(f"读取文件列表失败: {e}")
        
        # 打开文件夹按钮
        if st.button("📂 打开保存文件夹", use_container_width=True):
            try:
                os.startfile(save_dir)
            except:
                st.warning("无法自动打开文件夹，请手动打开路径")
        
    else:
        st.info("暂无数据可导出")

# 在参数配置和数据显示之间（放在 st.divider() 后面）
st.divider()

# ✅ 显示上次爬取用时（页面刷新后仍然保留）
if 'last_elapsed_time' in st.session_state and st.session_state.last_elapsed_time:
    st.info(f"⏱️ 上次爬取用时：{st.session_state.last_elapsed_time}")
else:
    st.info("⏱️ 尚未爬取数据")


# ==================== 数据合并功能 ====================
st.divider()
st.subheader("🔗 数据合并")

st.markdown("合并两个Excel文件，去重后生成新文件")

# 文件选择
col_a, col_b, col_merge_btn = st.columns([3, 3, 1])

# 获取当前文件所在目录
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
# 默认保存目录
DEFAULT_SAVE_DIR = os.path.join(_PROJECT_ROOT, 'data_save', 'shengyishe')
# 默认路径
default_dir = DEFAULT_SAVE_DIR

with col_a:
    # 获取目录下所有Excel文件
    import os
    excel_files = []
    if os.path.exists(default_dir):
        excel_files = [f for f in os.listdir(default_dir) if f.endswith(('.xlsx', '.xls'))]
    
    file_a = st.selectbox(
        "选择A文件（原数据）",
        options=[""] + excel_files,
        key="merge_file_a",
        help="选择要合并的第一个文件"
    )

with col_b:
    file_b = st.selectbox(
        "选择B文件（新增数据）",
        options=[""] + excel_files,
        key="merge_file_b",
        help="选择要合并的第二个文件"
    )

with col_merge_btn:
    st.write("")  # 占位
    st.write("")  # 占位
    merge_btn = st.button(
        "🔄 合并文件",
        type="primary",
        use_container_width=True,
        key="merge_btn",
        disabled=not (file_a and file_b)
    )

# 合并结果展示
if merge_btn and file_a and file_b:
    try:
        file_a_path = os.path.join(default_dir, file_a)
        file_b_path = os.path.join(default_dir, file_b)
        
        # ✅ 使用 pandas 读取两个文件
        import pandas as pd

        # 读取文件A
        sheet_names_a = pd.ExcelFile(file_a_path).sheet_names
        sheet_name_a = '合并去重数据' if '合并去重数据' in sheet_names_a else sheet_names_a[0]
        df_a = pd.read_excel(file_a_path, sheet_name=sheet_name_a)

        # 读取文件B
        sheet_names_b = pd.ExcelFile(file_b_path).sheet_names
        sheet_name_b = '合并去重数据' if '合并去重数据' in sheet_names_b else sheet_names_b[0]
        df_b = pd.read_excel(file_b_path, sheet_name=sheet_name_b)
        
        # 确定去重依据的字段（排除创建人和创建时间）
        exclude_cols = ['创建人', '创建时间']
        duplicate_cols = [col for col in df_a.columns if col not in exclude_cols]
        
        # 合并两个DataFrame
        df_combined = pd.concat([df_a, df_b], ignore_index=True)
        
        # 去重（不根据创建人和创建时间）
        df_unique = df_combined.drop_duplicates(subset=duplicate_cols, keep='first')
        
        # ✅ 生成输出文件名
        base_name = os.path.splitext(os.path.basename(file_a))[0]
        result_file = os.path.join(default_dir, f"{base_name}_合并结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        # ✅ 使用 pandas 保存到默认路径
        with pd.ExcelWriter(result_file, engine='openpyxl') as writer:
            df_a.to_excel(writer, sheet_name='原数据', index=False)
            df_b.to_excel(writer, sheet_name='新增数据', index=False)
            df_unique.to_excel(writer, sheet_name='合并去重数据', index=False)
        
        # 显示成功信息
        st.success(f"✅ 合并完成！文件已保存到：{result_file}")
        
        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("A文件数据量", len(df_a))
        with col2:
            st.metric("B文件数据量", len(df_b))
        with col3:
            st.metric("合并去重后", len(df_unique))
        with col4:
            duplicate_count = len(df_a) + len(df_b) - len(df_unique)
            st.metric("去除重复", duplicate_count, delta=f"-{duplicate_count}" if duplicate_count > 0 else "0")
        
        # 显示合并后的数据预览
        st.subheader("📋 合并去重后数据预览（前20条）")
        st.dataframe(df_unique.head(20), use_container_width=True)
        
        # ✅ 显示文件路径和打开文件夹按钮
        st.info(f"📁 合并结果已保存到：`{result_file}`")
        
        col_open1, col_open2 = st.columns([1, 5])
        with col_open1:
            open_folder_btn = st.button(
                "📂 打开保存文件夹",
                use_container_width=True,
                key="open_merge_folder_btn"
            )
            if open_folder_btn:
                try:
                    os.startfile(default_dir)
                except:
                    st.warning("无法自动打开文件夹，请手动打开路径")
        
    except Exception as e:
        st.error(f"❌ 合并失败：{str(e)}")
else:
    if merge_btn:
        st.warning("请选择A文件和B文件")