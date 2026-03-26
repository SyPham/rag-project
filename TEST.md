# Page 1

KHU DÂN CƯ VIỆT SING

DANH SÁCH THÔNG TIN ĐẤT

Số hồ sơ | Họ và tên         | Số thửa | Diện tích (m2) | Ghi chú
-------------------------------------------------------------------
001       | Nguyễn Văn A      | D2      | 3760           | Đất ở
002       | Trần Thị B        | D3      | 2048           | Đất nông nghiệp
003       | Lê Văn C          | D4      | 1520           | Đất ở
004       | Phạm Thị D        | D5      | 2980           | Đất thương mại
005       | Hoàng Văn E       | D6      | 4100           | Đất ở

TỔNG DIỆN TÍCH: 14408 m2

# Page 2

KHU DÂN CƯ VIỆT SING

DANH SÁCH THÔNG TIN ĐẤT

Số hồ sơ | Họ và tên         | Số thửa | Diện tích (m2) | Ghi chú
-------------------------------------------------------------------
001       | Nguyễn Văn A      | D2      | 3760           | Đất ở
002       | Trần Thị B        | D3      | 2048           | Đất nông nghiệp
003       | Lê Văn C          | D4      | 1520           | Đất ở
004       | Phạm Thị D        | D5      | 2980           | Đất thương mại
005       | Hoàng Văn E       | D6      | 4100           | Đất ở

TỔNG DIỆN TÍCH: 14408 m2

# Page 3

KHU DÂN CƯ VIỆT SING

THÔNG TIN BỔ SUNG

Họ và tên         | Năm sinh | Số điện thoại | Địa chỉ
---------------------------------------------------------
Nguyễn Văn A      | 1985     | 0901234567    | Bình Dương
Trần Thị B        | 1990     | 0912345678    | TP.HCM
Lê Văn C          | 1982     | 0987654321    | Đồng Nai
Phạm Thị D        | 1995     | 0978123456    | Bình Phước
Hoàng Văn E       | 1988     | 0933333333    | Long An

# Page 4

KHU DÂN CƯ VIỆT SING

LỊCH SỬ GIAO DỊCH

Họ và tên         | Loại giao dịch | Ngày        | Giá trị (VNĐ)
----------------------------------------------------------------
Nguyễn Văn A      | Mua            | 2020-05-01  | 2,000,000,000
Trần Thị B        | Bán            | 2021-07-12  | 1,500,000,000
Lê Văn C          | Mua            | 2019-03-20  | 1,200,000,000
Phạm Thị D        | Cho thuê       | 2022-01-10  | 50,000,000
Hoàng Văn E       | Mua            | 2023-06-15  | 3,000,000,000

# CÂU HỎI TEST MULTI-PAGE

Nguyễn Văn A sinh năm bao nhiêu?
số điện thoại của Trần Thị B là gì?
Nguyễn Văn A mua đất với giá bao nhiêu?
Nguyễn Văn A mua đất với giá bao nhiêu?
liệt kê tất cả những người mua đất
người nào vừa có diện tích lớn vừa có giao dịch cao?
so sánh diện tích và giá trị giao dịch của Nguyễn Văn A và Hoàng Văn E
so sánh diện tích và giá trị giao dịch của Nguyễn Văn A và Hoàng Văn E
danh sách tất cả thông tin liên quan đến Hoàng Văn E

# Mục đích test
| Feature              | Test được |
| -------------------- | --------- |
| chunking             | ✅         |
| metadata filter      | ✅         |
| cross-page reasoning | ✅         |
| RAG quality          | ✅         |


# Mở rộng thêm

Phân quyền dữ liệu
API trả về stream
multi-query
query rewrite
hybrid search (BM25 + vector)
hybrid search (BM25 + vector)
Chỉ đồng bộ những data mới qua Qdrant
Xóa dữ liệu OCR thì xóa bên Qdrant