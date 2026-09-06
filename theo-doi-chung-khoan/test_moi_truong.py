# Demo nhỏ để mỗi thành viên tự kiểm tra đã cài môi trường/Streamlit thành công.
# Chạy: streamlit run test_moi_truong.py
import streamlit as st

st.set_page_config(page_title="Setup Check - Nhóm 11", page_icon="📈")
st.title("📈 Xin chào nhóm 11 !!!!")
st.write("Nếu bạn thấy trang này thì môi trường Streamlit đã sẵn sàng 🎉")

name = st.text_input("Nhập tên của bạn để điểm danh:")
if st.button("Tôi đã cài xong môi trường 🚀"):
    if name:
        st.success(f"Chúc mừng {name}, bạn đã sẵn sàng code app theo dõi chứng khoán!")
    else:
        st.success("Chúc mừng, bạn đã sẵn sàng code app theo dõi chứng khoán!")
    st.balloons()
