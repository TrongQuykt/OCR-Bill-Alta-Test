import streamlit as st
from process_invoice import extract_invoice_data
import os
import tempfile
import logging

# Các hàm phụ trợ
def generate_csv(result):
    """Tạo file CSV từ kết quả"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Trường', 'Giá trị'])
    writer.writerow(['Số hóa đơn', result['invoice_number']])
    writer.writerow(['Tổng tiền', result['total_amount']])
    
    return output.getvalue()

def create_history_dataframe():
    """Tạo DataFrame từ lịch sử"""
    import pandas as pd
    
    # Tạo DataFrame từ lịch sử
    df = pd.DataFrame(st.session_state.history)
    
    # Thêm cột trạng thái
    df['status'] = df.apply(
        lambda row: 
            "✅ Thành công" if "không tìm thấy" not in row['invoice_number'].lower() and "không tìm thấy" not in row['total_amount'].lower()
            else "⚠️ Một phần" if not ("không tìm thấy" in row['invoice_number'].lower() and "không tìm thấy" in row['total_amount'].lower())
            else "❌ Thất bại",
        axis=1
    )
    
    return df

def convert_df_to_csv(df):
    """Chuyển đổi DataFrame thành CSV"""
    return df.to_csv(index=False).encode('utf-8')

def clear_history():
    """Xóa lịch sử"""
    st.session_state.history = []
    st.experimental_rerun()

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thiết lập cấu hình trang
st.set_page_config(
    page_title="Trích Xuất Hóa Đơn Thông Minh",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
    <style>
    .main {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        color: #f1f5f9;
    }
    .stButton>button {
        background-color: #10b981;
        color: #ffffff;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stFileUploader {
        border: 2px dashed #64748b;
        border-radius: 10px;
        padding: 20px;
        background-color: #334155;
        color: #f1f5f9;
    }
    .stSpinner {
        color: #10b981;
    }
    .result-box {
        background-color: #334155;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        margin-top: 20px;
        color: #f1f5f9;
    }
    .title {
        color: #ffffff;
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        color: #cbd5e1;
        font-size: 1.2em;
        text-align: center;
        margin-bottom: 30px;
    }
    .success-message {
        background-color: #064e3b;
        color: #6ee7b7;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
    .error-message {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
    .data-item {
        background-color: #283548;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #10b981;
    }
    .data-label {
        font-weight: bold;
        color: #cbd5e1;
    }
    .data-value {
        font-size: 1.1em;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Thiết lập tiêu đề
st.markdown('<div class="title">Trích Xuất Thông Tin Hóa Đơn</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Tải lên ảnh hóa đơn để trích xuất số hóa đơn và tổng tiền.</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("ℹ️ Thông Tin")
    st.markdown("""
    - **Định dạng hỗ trợ**: PNG, JPG, JPEG
    - **Kích thước tối đa**: 10MB
    - **Thời gian xử lý**: ~5-10 giây
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Hướng dẫn sử dụng**")
    st.markdown("""
    1. Tải lên ảnh hóa đơn rõ nét.
    2. Chờ hệ thống xử lý và trích xuất thông tin.
    3. Xem kết quả bao gồm số hóa đơn và tổng tiền.
    """, unsafe_allow_html=True)

# Tạo tabs
tab1, tab2 = st.tabs(["📤 Tải lên hóa đơn", "📊 Lịch sử"])

with tab1:
    # Widget tải file
    uploaded_file = st.file_uploader("📤 Chọn ảnh hóa đơn", type=["png", "jpg", "jpeg"])

    # Kiểm soát xử lý
    process_btn = st.button("🔍 Xử lý hóa đơn", type="primary", disabled=uploaded_file is None)

    if uploaded_file is not None:
        # Hiển thị ảnh đã tải lên
        st.image(uploaded_file, caption="Ảnh hóa đơn đã tải lên", use_column_width=True)
        
        if process_btn:
            # Lưu file tạm thời
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(uploaded_file.getbuffer())
            
            # Xử lý ảnh và trích xuất thông tin
            with st.spinner("⏳ Đang xử lý hóa đơn..."):
                try:
                    result = extract_invoice_data(temp_file_path)
                    
                    # Kiểm tra kết quả trích xuất
                    extraction_success = (result['invoice_number'] != "Không tìm thấy số hóa đơn" and 
                                         result['total_amount'] != "Không tìm thấy tổng tiền")
                    
                    if extraction_success:
                        st.markdown('<div class="success-message">✅ Xử lý hoàn tất!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-message">⚠️ Không tìm thấy đầy đủ thông tin.</div>', unsafe_allow_html=True)
                    
                    # Hiển thị kết quả
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.subheader("Kết quả trích xuất")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f'<div class="data-item"><span class="data-label">Số hóa đơn:</span><br/><span class="data-value">{result["invoice_number"]}</span></div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown(f'<div class="data-item"><span class="data-label">Tổng tiền:</span><br/><span class="data-value">{result["total_amount"]}</span></div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Phần xem toàn bộ văn bản đã trích xuất
                    with st.expander("📜 Xem toàn bộ văn bản trích xuất", expanded=False):
                        st.text_area("Văn bản đầy đủ", result['full_text'], height=200, disabled=True)
                    
                    # Lưu kết quả vào session state để hiển thị trong tab lịch sử
                    if 'history' not in st.session_state:
                        st.session_state.history = []
                    
                    st.session_state.history.append({
                        'invoice_number': result['invoice_number'],
                        'total_amount': result['total_amount'],
                        'timestamp': "Hôm nay"
                    })
                    
                    # Nút tải xuống
                    st.download_button(
                        label="💾 Tải xuống kết quả (CSV)",
                        data=generate_csv(result),
                        file_name=f"invoice_{result['invoice_number']}.csv",
                        mime="text/csv"
                    )

                except Exception as e:
                    logger.error(f"Lỗi khi xử lý: {str(e)}")
                    st.markdown(f'<div class="error-message">❌ Lỗi khi xử lý: {str(e)}</div>', unsafe_allow_html=True)

                finally:
                    # Xóa file tạm
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
    else:
        st.info("📌 Vui lòng tải lên ảnh hóa đơn để bắt đầu.", icon="ℹ️")

with tab2:
    st.header("📊 Lịch sử trích xuất")
    
    # Hiển thị lịch sử nếu có
    if 'history' in st.session_state and st.session_state.history:
        # Tạo DataFrame từ lịch sử
        history_df = create_history_dataframe()
        
        # Hiển thị bảng lịch sử
        st.dataframe(
            history_df,
            column_config={
                "invoice_number": "Số hóa đơn",
                "total_amount": "Tổng tiền",
                "timestamp": "Thời gian",
                "status": "Trạng thái"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Nút xóa lịch sử
        st.button("🗑️ Xóa lịch sử", on_click=clear_history)
    else:
        st.info("📌 Chưa có dữ liệu lịch sử.", icon="ℹ️")

# Footer
st.markdown("---")
st.markdown('<div style="text-align: center; color: #cbd5e1;">Powered by Streamlit</div>', unsafe_allow_html=True)