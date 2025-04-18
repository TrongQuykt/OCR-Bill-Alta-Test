# Ứng dụng Trích Xuất Thông Tin Hóa Đơn
Ứng dụng Streamlit để trích xuất thông tin từ hóa đơn sử dụng Google Cloud Vision OCR.
- Giao diện người dùng thân thiện với Streamlit
- Trích xuất số hóa đơn từ nhiều định dạng và bố cục khác nhau

# Thiết lập Google Cloud Vision API
- Tạo hoặc sử dụng project trên Google Cloud Console
- Kích hoạt Cloud Vision API
- Tải xuống file credentials JSON
- Đặt biến môi trường GOOGLE_APPLICATION_CREDENTIALS trỏ đến file JSON

# Cài đặt
Đặt biến môi trường GOOGLE_APPLICATION_CREDENTIALS trỏ đến file JSON
```bash
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Users\ADMIN\Desktop\Alta PV\diabetes-433807-40c20e39eff8.json"
```
Kiểm tra phiên bản Streamlit
```bash
pip show streamlit
```
Nếu không thấy thông tin về Streamlit, hãy cài đặt
```bash
pip install streamlit
```
Nếu lệnh streamlit vẫn không hoạt động, bạn có thể chạy Streamlit thông qua Python trực tiếp
```bash
python -m streamlit run app.py
```
# Cải tiến trong tương lai
- Thêm hỗ trợ cho nhiều ngôn ngữ
- Cải thiện khả năng trích xuất với AI học sâu
- Thêm tính năng xử lý hàng loạt hóa đơn

# Liên hệ
## Gmail: vyquy633@gmail.com
## Linkedin: www.linkedin.com/in/vy-trọng-quý-941b71347

# Hình ảnh ứng dụng

![Image](https://github.com/user-attachments/assets/7a22e7c1-52a3-459e-ab51-bff585c3abb3)

![Image](https://github.com/user-attachments/assets/14a39277-8cdf-4e7a-9a8c-8d90b736f653)

![Image](https://github.com/user-attachments/assets/7203185f-01c1-439c-9a01-ee8bcdce3721)

![Image](https://github.com/user-attachments/assets/1c49e22f-d52a-4236-954d-1bff3e17c26e)
