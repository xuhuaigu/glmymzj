import streamlit as st

st.header("Admin 1")
st.write(f"You are logged in as {st.session_state.role}.")

st.page_link("request/request_1.py", label="request_1", icon="🏠")

# 复选框
a = st.checkbox("多选框", ["选项1", "选项2", "选项3", "选项4"])

st.write(a)

# 多选下拉框
options = st.multiselect(
    "请选择选项",
    ["选项1", "选项2", "选项3", "选项4"],
    # default=["选项1", "选项2"],
    placeholder="请选择选项..." # 占位符

)

st.write(f"您选择了: {options}")

# 禁用状态
result = st.multiselect(
    "选择水果（已禁用）",
    ["苹果", "香蕉", "橙子"],
    disabled=True  # 灰色不可用
)

# 原始数据是数字，显示为文字
options = [1, 2, 3]
format_funcs = [f"{x}级" for x in options]
result = st.multiselect(
    "选择等级",
    options,
    format_func=lambda x: f"{x}级"  # 1显示为"1级"
)