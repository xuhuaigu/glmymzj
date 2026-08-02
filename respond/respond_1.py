import streamlit as st
import pymysql
from sqlalchemy import text

pymysql.install_as_MySQLdb()

st.markdown("# 数据新增源码 🎉")

conn = st.connection('mysql', type='sql')

# ========== 插入数据部分 ==========
st.subheader("🐻 添加新数据")

with st.form("insert_form"):
    name = st.text_input("姓名")
    pet = st.text_input("宠物类型（狗/猫/鸟等）")
    submitted = st.form_submit_button("提交")
    
    if submitted and name and pet:
        try:
            with conn.session as session:
                # ✅ 正确写法：SQLAlchemy 2.x 使用 :参数名 作为占位符
                session.execute(
                    text('INSERT INTO mytable (name, pet) VALUES (:name, :pet)'),
                    {"name": name, "pet": pet}  # 注意：这里是字典，不是元组
                )
                session.commit()
                st.success(f"✅ 成功插入：{name} - {pet}")
                st.rerun()
        except Exception as e:
            st.error(f"❌ 插入失败: {e}")

# ========== 查询并显示所有数据 ==========
st.subheader("当前数据列表")

df = conn.query('SELECT * FROM mytable;', ttl=0)

if len(df) > 0:
    for row in df.itertuples():
        st.write(f"{row.name} has a :{row.pet}:")
else:
    st.info("暂无数据，请添加")