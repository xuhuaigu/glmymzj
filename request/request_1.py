import streamlit as st

st.title("树形多选组件")

# 数据
tree_data = {
    "广西": {
        "南宁": [],
        "桂林": ["象山区", "秀峰区", "七星区"],
        "柳州": ["城中区", "鱼峰区"],
    },
    "广东": {
        "广州": ["天河区", "越秀区", "海珠区"],
        "深圳": ["南山区", "福田区", "罗湖区"],
    },
}

# 使用session_state存储选择状态
if 'tree_selected' not in st.session_state:
    st.session_state.tree_selected = {}

# 使用st.expander实现树形结构
for province, cities in tree_data.items():
    with st.expander(f"📍 {province}"):
        col1, col2 = st.columns([1, 4])
        with col1:
            # 全选该省
            select_all = st.checkbox("全选", key=f"all_{province}")
        with col2:
            # 显示城市
            for city, areas in cities.items():
                if areas:
                    # 有区县的城市
                    selected_areas = st.multiselect(
                        f"  {city}",
                        options=areas,
                        key=f"areas_{province}_{city}",
                        label_visibility="collapsed"
                    )
                    if select_all:
                        st.session_state[f"areas_{province}_{city}"] = areas
                else:
                    # 没有区县的城市
                    is_selected = st.checkbox(
                        f"  {city}",
                        key=f"city_{province}_{city}",
                        value=select_all
                    )
                    if is_selected:
                        st.session_state.tree_selected[f"{province}_{city}"] = True

# 显示结果
st.divider()
st.subheader("已选择")
selected_items = []
for key, value in st.session_state.items():
    if key.startswith("areas_") and value:
        parts = key.split("_")
        selected_items.append(f"{parts[1]}-{parts[2]}")
    elif key.startswith("city_") and value:
        parts = key.split("_")
        selected_items.append(f"{parts[1]}-{parts[2]}")

if selected_items:
    st.write(selected_items)