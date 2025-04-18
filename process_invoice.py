import re
from google.cloud import vision
import io
import os
import logging

# Thiết lập logging cơ bản
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_invoice_data(image_path):
    """
    Trích xuất số hóa đơn và tổng tiền từ ảnh hóa đơn sử dụng Google Cloud Vision API.
    Hỗ trợ nhiều định dạng và bố cục hóa đơn tiếng Việt.
    
    Args:
        image_path (str): Đường dẫn đến file ảnh hóa đơn.
    Returns:
        dict: Chứa số hóa đơn và tổng tiền.
    """
    try:
        # Khởi tạo client của Google Cloud Vision
        client = vision.ImageAnnotatorClient()

        # Đọc file ảnh
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Thực hiện OCR với DOCUMENT_TEXT_DETECTION để nhận diện văn bản có cấu trúc
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(f'Lỗi từ Google Cloud Vision: {response.error.message}')

        # Lấy toàn bộ văn bản từ kết quả OCR
        full_text = response.full_text_annotation.text

        # Log kết quả OCR đầy đủ để phân tích
        logger.info(f"Văn bản OCR đầy đủ:\n{full_text}")

        # Tách văn bản thành dòng để xử lý theo dòng
        lines = full_text.split('\n')
        
        # PHẦN 1: TRÍCH XUẤT SỐ HÓA ĐƠN ==================================================
        invoice_number = extract_invoice_number(full_text, lines)
        
        # PHẦN 2: TRÍCH XUẤT TỔNG TIỀN ===================================================
        total_amount = extract_total_amount(full_text, lines)

        # PHẦN 3: TRÍCH XUẤT THÔNG TIN THỜI GIAN =========================================
        date_info = extract_date_info(full_text, lines)

        return {
            'invoice_number': invoice_number,
            'total_amount': total_amount,
            'date_info': date_info,
            'full_text': full_text
        }
    
    except Exception as e:
        logger.error(f"Lỗi khi xử lý ảnh: {str(e)}")
        return {
            'invoice_number': "Không thể trích xuất số hóa đơn",
            'total_amount': "Không thể trích xuất tổng tiền",
            'date_info': "Không thể trích xuất thông tin thời gian",
            'full_text': f"Lỗi: {str(e)}"
        }

def extract_invoice_number(full_text, lines):
    """Trích xuất số hóa đơn với nhiều mẫu khác nhau"""
    
    # Danh sách các mẫu regex để tìm số hóa đơn
    invoice_number_patterns = [
        # Mẫu 1: Ưu tiên mã hóa đơn dài (6 chữ số trở lên) sau "Số:", "Số HĐ:", v.v.
        r'(?:Số|Số\s*HĐ|Số\s*HD|Số\s*hóa\s*đơn|Số\s*hoá\s*đơn|Mã\s*HĐ|Mã\s*HD)\s*[:#=\.]?\s*(\d{6,})',
        
        # Mẫu 2: Các kiểu định dạng chuẩn với "Số HĐ", "Số HD", etc.
        r'(?:Số\s*HĐ|Số\s*HD|Số\s*hóa\s*đơn|Số\s*hoá\s*đơn|Mã\s*HĐ|Mã\s*HD)\s*[:#=\.]?\s*([A-Za-z0-9-\/]+)',
        
        # Mẫu 3: "HÓA ĐƠN THANH TOÁN" và sau đó là số
        r'HÓA\s*ĐƠN\s*THANH\s*TOÁN\s*(?:.*\n){0,2}.*?(?:Số|No|Mã)\s*[:#=\.]?\s*([A-Za-z0-9-\/]+)',
        
        # Mẫu 4: "HD" hoặc "HĐ" và sau đó là số
        r'(?:HD|HĐ|H\.Đ|H\.D)[:#=\.\s]*([A-Za-z0-9-\/]+)',
        
        # Mẫu 5: Tiếng Anh - Invoice number
        r'(?:Invoice\s*(?:Number|No\.?|ID)|Bill\s*No\.?)\s*[:#=]?\s*([A-Za-z0-9-\/]+)',
    ]
    
    # Tìm kiếm qua các mẫu đã định nghĩa
    for pattern in invoice_number_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Kiểm tra để loại bỏ số nhà trong địa chỉ
            nearby_text = get_text_around(full_text, candidate, 50).lower()
            if not any(keyword in nearby_text for keyword in ["đường", "phố", "quận", "huyện", "thành phố"]):
                return candidate
    
    # Tìm kiếm theo từng dòng với mẫu cụ thể
    for line in lines:
        if re.search(r'(Số\s*HĐ|Số\s*HD|Số\s*hoá\s*đơn|Số\s*hóa\s*đơn)', line, re.IGNORECASE):
            match = re.search(r'(\d{6,})', line)
            if match:
                return match.group(1).strip()
    
    # Nếu không tìm thấy theo các mẫu tiêu chuẩn, tìm kiếm nâng cao
    return find_invoice_number_advanced(full_text, lines)

def find_invoice_number_advanced(full_text, lines):
    """Phương pháp tìm số hóa đơn nâng cao"""
    
    # Tìm các chuỗi ngắn có dạng số hoặc chữ và số
    potential_numbers = re.findall(r'\b[A-Za-z0-9-\/]{3,10}\b', full_text)
    
    # Kiểm tra các chuỗi tìm được trong 10 dòng đầu tiên (thường số hóa đơn ở phần đầu)
    top_lines = '\n'.join(lines[:10])
    for num in potential_numbers:
        # Nếu số xuất hiện ở 10 dòng đầu và có dạng hợp lệ
        if num in top_lines and re.match(r'^[A-Za-z0-9-\/]+$', num):
            nearby_text = get_text_around(top_lines, num, 20)
            # Nếu gần số này có từ khóa liên quan đến hóa đơn
            if any(keyword in nearby_text.lower() for keyword in ["hd", "hđ", "số", "Số", "hoá đơn", "hóa đơn", "thanh toán", "bill"]):
                return num
    
    return "Không tìm thấy số hóa đơn"

def extract_total_amount(full_text, lines):
    """Trích xuất tổng tiền với nhiều mẫu khác nhau"""
    
    # Danh sách các mẫu regex để tìm tổng tiền
    total_amount_patterns = [
        # Mẫu 1: Các biến thể của "Tổng cộng", "Tổng tiền", "Thành tiền"
        r'(?:Tổng\s*(?:cộng|tiền|thanh\s*toán)|T\.\s*(?:CỘNG|Cộng)|Thành\s*tiền)\s*[:=]?\s*([\d\., ]+)',
        
        # Mẫu 2: "TIỀN MẶT" hoặc các biến thể
        r'(?:TIỀN\s*MẶT|TIEN\s*MAT|Tiền\s*mặt)\s*[:=]?\s*([\d\., ]+)',
        
        # Mẫu 3: "TỔNG TIỀN" và các biến thể
        r'(?:TỔNG\s*TIỀN|Tổng\s*tiền|TONG\s*TIEN)\s*[:=]?\s*([\d\., ]+)',
        
        # Mẫu 4: Tiếng Anh - Total, Grand Total, Amount
        r'(?:Total|Grand\s*Total|Amount|Sum|Total\s*Amount)\s*[:=]?\s*(?:VND|VNĐ|₫|đ)?\s*([\d\., ]+)',
        
        # Mẫu 5: Số tiền lớn nhất với đơn vị tiền tệ
        r'([\d\., ]+)(?:\s*(?:VND|VNĐ|₫|đ|đồng))',
        
        # Mẫu 6: "SỐ TIỀN" hoặc "THANH TOÁN"
        r'(?:SỐ\s*TIỀN|THANH\s*TOÁN)\s*[:=]?\s*([\d\., ]+)'
    ]
    
    # Phương pháp 1: Dùng regex để tìm tổng tiền
    for pattern in total_amount_patterns:
        matches = re.finditer(pattern, full_text, re.IGNORECASE)
        for match in matches:
            amount = match.group(1).strip()
            # Xử lý định dạng số
            amount = clean_amount(amount)
            # Kiểm tra xem kết quả có hợp lệ không
            if is_valid_amount(amount):
                return amount
            
    # Tìm "Tổng:" theo sau là số (có thể có dấu phẩy)
    total_pattern = r'Tổng:\s*([\d\.,]+)'
    match = re.search(total_pattern, full_text)
    if match:
        return clean_amount(match.group(1).strip())
    
    # Phương pháp 2: Tìm kiếm theo dòng với từ khóa cụ thể
    return find_total_by_keywords(lines)
    

def find_total_by_keywords(lines):
    """Tìm tổng tiền dựa trên từ khóa theo dòng"""
    
    # Danh sách các từ khóa liên quan đến tổng tiền
    amount_keywords = [
        "tổng cộng", "tổng tiền", "tiền mặt", "thanh toán", "Tổng"
        "T.CONG","t.cong", "t.tiền", "thành tiền", "tổng", "total", "T.CONG"
    ]
    
    potential_amounts = []
    
    # Ưu tiên các dòng có từ khóa về tổng tiền
    for line in lines:
        line_lower = line.lower()
        
        # Kiểm tra nếu dòng chứa từ khóa
        if any(keyword in line_lower for keyword in amount_keywords):
            # Trích xuất tất cả số từ dòng này
            numbers = re.findall(r'[\d\., ]+', line)
            if numbers:
                # Lấy số lớn nhất trên dòng (thường là tổng tiền)
                largest = max([clean_amount(num) for num in numbers], 
                             key=lambda x: float(x.replace(".", "").replace(",", "")) if x.replace(".", "").replace(",", "").isdigit() else 0)
                potential_amounts.append((largest, 10))  # Độ ưu tiên cao
    
    # Tìm tất cả các số có dạng tiền tệ trong văn bản
    for i, line in enumerate(lines):
        if i < len(lines) - 1:  # Không phải dòng cuối
            # Tìm các số lớn (có thể là tổng tiền)
            numbers = re.findall(r'[\d\., ]+', line)
            for num in numbers:
                cleaned = clean_amount(num)
                if is_valid_amount(cleaned) and float(cleaned.replace(".", "").replace(",", "")) > 1000:
                    # Kiểm tra xem dòng tiếp theo có chứa từ "đồng" hay không
                    if "đồng" in lines[i+1].lower():
                        potential_amounts.append((cleaned, 5))  # Độ ưu tiên trung bình
    
    # Tìm số lớn nhất có dạng tiền tệ trong các dòng cuối
    last_lines = lines[-5:] if len(lines) > 5 else lines
    for line in last_lines:
        numbers = re.findall(r'[\d\., ]+', line)
        for num in numbers:
            cleaned = clean_amount(num)
            if is_valid_amount(cleaned) and float(cleaned.replace(".", "").replace(",", "")) > 10000:
                potential_amounts.append((cleaned, 3))  # Độ ưu tiên thấp
    
    # Sắp xếp theo độ ưu tiên và lấy số tiền ưu tiên cao nhất
    if potential_amounts:
        potential_amounts.sort(key=lambda x: x[1], reverse=True)
        return potential_amounts[0][0]
    
    return "Không tìm thấy tổng tiền"

def extract_date_info(full_text, lines):
    """Trích xuất thông tin thời gian từ hóa đơn"""
    
    # Các mẫu regex cho ngày tháng
    date_patterns = [
        # DD/MM/YYYY hoặc DD-MM-YYYY
        r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        
        # Mẫu "Ngày... tháng... năm..." trong tiếng Việt
        r'Ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{2,4})',
        
        # Mẫu "Ngày" và sau đó là ngày
        r'Ngày\s*[:]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
    ]
    
    # Tìm theo mẫu date
    for pattern in date_patterns:
        match = re.search(pattern, full_text)
        if match:
            return match.group(0)
    
    # Tìm theo từng dòng
    for line in lines:
        if "ngày" in line.lower() and re.search(r'\d{1,2}', line):
            return line
    
    return "Không tìm thấy thông tin thời gian"

def clean_amount(amount_str):
    """Làm sạch và định dạng số tiền"""
    # Loại bỏ khoảng trắng
    amount_str = amount_str.strip().replace(" ", "")
    
    # Chỉ giữ lại số và dấu phân cách
    amount_str = ''.join(c for c in amount_str if c.isdigit() or c in '.,')
    
    # Đảm bảo định dạng nhất quán
    # Nếu có dấu '.' và ',' trong chuỗi
    if '.' in amount_str and ',' in amount_str:
        # Kiểm tra vị trí của dấu '.' và ','
        dot_pos = amount_str.rfind('.')
        comma_pos = amount_str.rfind(',')
        
        if dot_pos > comma_pos:
            # Định dạng 1,234.56 - dấu '.' là phân cách thập phân
            amount_str = amount_str.replace(',', '')
        else:
            # Định dạng 1.234,56 - dấu ',' là phân cách thập phân
            amount_str = amount_str.replace('.', '').replace(',', '.')
    
    # Nếu chỉ có dấu ','
    elif ',' in amount_str:
        if amount_str.count(',') == 1 and len(amount_str.split(',')[1]) <= 2:
            # Có thể là dấu thập phân, ví dụ: 123,45
            amount_str = amount_str.replace(',', '.')
        else:
            # Dấu phân cách hàng nghìn, ví dụ: 1,234,567
            amount_str = amount_str.replace(',', '')
    
    return amount_str

def is_valid_amount(amount_str):
    """Kiểm tra xem chuỗi có phải là số tiền hợp lệ không"""
    # Loại bỏ dấu '.' và ',' để kiểm tra
    clean_str = amount_str.replace('.', '').replace(',', '')
    
    # Kiểm tra xem có phải là số nguyên không
    if not clean_str.isdigit():
        return False
    
    # Kiểm tra độ dài - số tiền thường > 2 chữ số và < 10 chữ số
    if len(clean_str) < 2 or len(clean_str) > 10:
        return False
    
    return True

def get_text_around(text, target, window_size=20):
    """Lấy văn bản xung quanh một chuỗi mục tiêu"""
    pos = text.find(target)
    if pos == -1:
        return ""
    
    start = max(0, pos - window_size)
    end = min(len(text), pos + len(target) + window_size)
    
    return text[start:end]