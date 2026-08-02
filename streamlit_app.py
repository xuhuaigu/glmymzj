import streamlit as st

# ==================== 导入全局配置 ====================
from config import Roles, PageConfig, init_session_state

# ==================== 页面配置 ====================
st.set_page_config(
    page_title=PageConfig.TITLE,
    page_icon=PageConfig.ICON,
    layout=PageConfig.LAYOUT,
    initial_sidebar_state=PageConfig.SIDEBAR_STATE,
    menu_items=PageConfig.MENU_ITEMS # type: ignore
)

# 初始化全局变量
init_session_state()

# 角色列表（从配置中获取）
ROLES = Roles.ALL

# ==================== 登录函数 ====================
def login():
    st.header("登陆界面")
    role = st.selectbox("请选择你的角色", ROLES, key="login_role")
    
    # 数据分析员登录需要密码验证
    if role == Roles.DATA_ANALYST:
        mima = st.text_input("请输入密码", type="password", key="login_password")
        
        if mima == Roles.DATA_ANALYST_PASSWORD:
            st.success("密码正确，请点击登录")
            if st.button("登录", key="login_btn_analyst"):
                st.session_state.role = role
                st.rerun()
        elif mima:
            st.error("密码错误！")
    
    # 其他角色直接登录
    elif role and role != Roles.DATA_ANALYST:
        if st.button("登录", key="login_btn_other"):
            st.session_state.role = role
            st.rerun()

# ==================== 注销函数 ====================
def logout():
    st.session_state.role = None
    st.rerun()

# 获取当前角色
role = st.session_state.role

# ==================== 定义页面 ====================
logout_page = st.Page(logout, title="注销", icon=":material/logout:")
settings = st.Page("settings.py", title="设置", icon=":material/settings:")

# 测试页面
request_1 = st.Page(
    "request/request_1.py",
    title="测试页面1",
    icon=":material/help:",
    default=(role == Roles.TESTER),
)
request_2 = st.Page(
    "request/request_2.py", 
    title="测试页面2", 
    icon=":material/bug_report:",
    # visibility="hidden" if role == Roles.TESTER else "visible",
)
request_3 = st.Page(
    "request/request_3.py", 
    title="测试页面3", 
    icon=":material/bug_report:",
    # visibility="hidden" if role == Roles.TESTER else "visible",
)

# 数据库管理页面
respond_1 = st.Page(
    "respond/respond_1.py",
    title="添加数据",
    icon=":material/healing:",
    default=(role == Roles.DB_ADMIN),
)
respond_2 = st.Page(
    "respond/respond_2.py", 
    title="Respond 2", 
    icon=":material/handyman:"
)
respond_3 = st.Page(
    "respond/respond_3.py", 
    title="数据质量", 
    icon=":material/handyman:"
)

# 系统管理员页面
admin_1 = st.Page(
    "admin/admin_1.py",
    title="Admin 1",
    icon=":material/person_add:",
    default=(role == Roles.SYS_ADMIN),
)
admin_2 = st.Page(
    "admin/admin_2.py", 
    title="Admin 2", 
    icon=":material/security:"
)

# 数据分析页面
data_analysis1 = st.Page(
    "data_analysis/1_data_overview.py",
    title="数据分析",
    icon=":material/pie_chart:",
    default=(role == Roles.SYS_ADMIN or role == Roles.DATA_ANALYST),
)
data_analysis2 = st.Page(
    "data_analysis/2_data_visualization.py",
    title="数据可视化",
    icon=":material/pie_chart:"
)
data_analysis3 = st.Page(
    "data_analysis/3_statistical_analysis.py",
    title="统计分析",
    icon=":material/pie_chart:",
)
data_analysis4 = st.Page(
    "data_analysis/4_correlation_analysis.py",
    title="相关性分析",
    icon=":material/pie_chart:",
)
data_analysis5 = st.Page(
    "data_analysis/5_time_series.py",
    title="时间序列分析",
    icon=":material/pie_chart:",
)
data_analysis6 = st.Page(
    "data_analysis/6_chart_analysis.py",
    title="图表大全",
    icon=":material/pie_chart:",
)

# 生猪养殖数据分析页面
data_analysis7 = st.Page(
    "data_analysis/7_pig_analysis.py",
    title="生猪养殖",
    icon="🐷",
)

# 饲料分析
data_analysis8 = st.Page(
    "data_analysis/8_feed_analysis.py",
    title="饲料分析",
    icon="🌾",
)

# 养猪网数据分析页面
data_analysis9 = st.Page(
    "data_analysis/9_yangzhuwang_analysis.py",
    title="养猪网分析",
    icon="🌾",
)

# 猪价数据预测页面
data_analysis10 = st.Page(
    "data_analysis/10_price_forecast.py",
    title="猪价预测分析",
    icon="🔮"
)

# 爬虫管理页面
spider_list = st.Page(
    "spider_manager/1_spider_list.py",
    title="爬虫任务",
    icon="🕷️",
)
spider_config = st.Page(
    "spider_manager/2_spider_config.py",
    title="爬虫配置",
    icon="⚙️",
)
spider_log = st.Page(
    "spider_manager/3_spider_log.py",
    title="运行日志",
    icon="📋",
)
spider_data_view = st.Page(
    "spider_manager/4_data_view.py",
    title="数据查看",
    icon="📊",
)
glmyjt1 = st.Page(
    "gxglmy/gxglmy1.py",
    title="桂柳牧业",
    icon=":material/pie_chart:",
    default=(role == Roles.GLMY),
)
glmyjt2 = st.Page(
    "gxglmy/gxglmy2.py",
    title="桂柳牧业2",
    icon=":material/pie_chart:",
)

# 养猪网数据爬取界面
spider_zhuwang1 = st.Page(
    "spider_zhuwang/test_page.py",
    title="养猪网--生猪数据",
    icon="🕷️"
) 

# 养猪网数据爬取界面
spider_zhuwang2 = st.Page(
    "spider_zhuwang/corn_test_page.py",
    title="养猪网--玉米数据",
    icon="🕷️"
) 
shengYiShe1 = st.Page(
    "shengYiShe/nongfuchanpin.py",
    title="生意社--所有数据",
    icon="🕷️"
)




# ==================== 页面分组 ====================
account_pages = [logout_page, settings]
request_pages = [request_1, request_2, request_3]
respond_pages = [respond_1, respond_2]

# 管理页面
admin_pages = [
    admin_1, admin_2,
    # data_analysis1, data_analysis2, data_analysis3, data_analysis4, data_analysis5,
    spider_list, spider_config, spider_log, spider_data_view
]

# ==================== 数据分析页面分组 ====================
data_analysis_pages = [
    data_analysis1, data_analysis2, data_analysis3, data_analysis4, data_analysis5, data_analysis6, data_analysis7, data_analysis8,
    spider_data_view
]
# 桂柳牧业页面
glmyjt_pages = [glmyjt1, glmyjt2, data_analysis1, data_analysis2, data_analysis3, data_analysis9, data_analysis10, 
        respond_3, spider_zhuwang1, spider_zhuwang2, shengYiShe1, data_analysis7, data_analysis8]
# ==================== 页面标题和Logo ====================
# st.title("Request manager")
st.logo("images/horizontal_blue.png", icon_image="🕷️")

# ==================== 构建导航 ====================
page_dict = {}

# ✅ 修改：使用 Roles 常量替代字符串
if role in [Roles.TESTER, Roles.SYS_ADMIN]:
    page_dict["测试页面"] = request_pages
if role in [Roles.DB_ADMIN, Roles.SYS_ADMIN]:
    page_dict["数据库管理"] = respond_pages
if role == Roles.SYS_ADMIN:
    page_dict["系统管理"] = admin_pages
if role == Roles.DATA_ANALYST:
    page_dict["数据分析"] = data_analysis_pages
if role == Roles.GLMY:
    page_dict["桂柳牧业"] = glmyjt_pages
# if role == Roles.

# 创建导航
if len(page_dict) > 0:
    pg = st.navigation({"设置": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

# ==================== 侧边栏帮助菜单 ====================
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📞 帮助与反馈")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❓ 获取帮助", use_container_width=True):
            st.markdown("[点击访问帮助中心](https://www.baidu.com)")
    with col2:
        if st.button("🐛 报告问题", use_container_width=True):
            st.markdown("[点击反馈问题](https://github.com/xxx)")


pg.run()