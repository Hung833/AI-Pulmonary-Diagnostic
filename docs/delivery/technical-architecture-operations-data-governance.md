# Hướng Dẫn Kiến Trúc Kỹ Thuật, Vận Hành, Và Quản Trị Dữ Liệu

Dự án: AI Pulmonary Diagnostic Suite
Mục đích: Giải thích kiến trúc sản phẩm, kỳ vọng triển khai, tính minh bạch của mô hình, và tài liệu hóa các script tiện ích cho bàn giao kỹ thuật.

## 1. Mục đích tài liệu

Đây là tài liệu kỹ thuật đi kèm với gói bàn giao thương mại. Tài liệu dành cho đội kỹ thuật khách hàng, DevOps, và nhóm đánh giá kỹ thuật cần hiểu hệ thống hoạt động như thế nào, triển khai ra sao, và những giả định vận hành nào đang được áp dụng.

## 2. Tổng quan kiến trúc

### 2.1 Mục tiêu hệ thống

Ứng dụng là một hệ thống hỗ trợ chẩn đoán dựa trên web cho triage ảnh X-quang ngực. Hệ thống kết hợp suy luận nhanh với lớp giải thích mô hình tùy chọn để hỗ trợ bác sĩ xem xét các ca nghi ngờ viêm phổi.

### 2.2 Thiết kế hai động cơ

- Động cơ triage nhanh: mô hình TensorFlow Lite gọn nhẹ để phân loại theo lô với độ trễ thấp.
- Động cơ AI giải thích: mô hình Keras đầy đủ dùng để tạo heatmap Grad-CAM phục vụ diễn giải trực quan.

Thiết kế hai động cơ tách phần sàng lọc nhanh khỏi phần giải thích, giúp tăng tính hữu dụng và làm sản phẩm dễ được định vị như một giải pháp AI y tế có giá trị cao.

### 2.3 Các thành phần runtime chính

- Giao diện Streamlit cho upload, triage, trực quan hóa, và xuất báo cáo.
- Đường suy luận TensorFlow Lite cho phân loại nhanh.
- Đường giải thích dựa trên Keras cho rendering Grad-CAM.
- Pandas và chức năng xuất Excel cho báo cáo.

## 3. Hướng dẫn triển khai và vận hành

### 3.1 Giả định triển khai

- Khách hàng sở hữu môi trường runtime mục tiêu.
- Khách hàng cung cấp compute, storage, và network.
- File mô hình và mã ứng dụng được triển khai cùng nhau trong môi trường đích.
- Môi trường triển khai có thể là local, VM, hoặc AWS tùy theo thỏa thuận.

### 3.2 Mô hình vận hành AWS khuyến nghị

Khi triển khai trên AWS, nên dùng hạ tầng do khách hàng sở hữu để chi phí cloud thuộc trách nhiệm của khách hàng:

- Host ứng dụng trên EC2, ECS, hoặc dịch vụ tương đương do khách hàng quản lý.
- Lưu artifact mô hình trong object storage do khách hàng kiểm soát.
- Bật logging và monitoring theo tài khoản AWS của khách hàng nếu cần.

### 3.3 Ranh giới vận hành

- Nhà cung cấp chỉ cung cấp hướng dẫn triển khai, không vận hành cloud dài hạn trừ khi có hợp đồng riêng.
- Mọi hóa đơn AWS, chi phí egress, hoặc chi phí scale đều không thuộc trách nhiệm của nhà cung cấp.
- Hardening production, autoscaling, HA, backup policy, và security baseline là công việc tính phí nếu vượt quá mức bàn giao chuẩn.

### 3.4 Bộ runbook tối thiểu

Bộ bàn giao nên có tối thiểu:

- Điều kiện tiên quyết cài đặt.
- Quy trình khởi động và dừng.
- Yêu cầu về định dạng file đầu vào.
- Các giới hạn và chế độ lỗi đã biết.
- Các bước kiểm tra sau triển khai.

## 4. Model Card

### 4.1 Mục đích mô hình

Mô hình dùng để hỗ trợ quyết định trong phát hiện viêm phổi từ ảnh X-quang ngực. Nó không thay thế đánh giá lâm sàng của bác sĩ.

### 4.2 Chỉ số chính

- Kích thước tập huấn luyện xấp xỉ: hơn 5.800 ảnh.
- Trọng tâm hiệu năng: ưu tiên recall cao để giảm false negative.
- Chỉ số mục tiêu được mô tả trong dự án: khoảng 92% recall.

### 4.3 Mục đích sử dụng

- Sàng lọc và ưu tiên các ảnh X-quang ngực.
- Hỗ trợ con người xem xét, không phải chẩn đoán tự động.

### 4.4 Giới hạn

- Hiệu năng có thể thay đổi theo máy chụp, quy trình bệnh viện, và quần thể bệnh nhân.
- Kết quả mô hình không nên được xem là chẩn đoán y khoa cuối cùng.
- Cần thẩm định độc lập trước khi dùng cho production được quản lý hoặc triển khai lâm sàng.

### 4.5 Tuyên bố an toàn

Sản phẩm này là công cụ hỗ trợ quyết định lâm sàng. Nó không được dùng như thay thế cho chẩn đoán của bác sĩ có chuyên môn.

## 5. Data Card

### 5.1 Tóm tắt dữ liệu huấn luyện

- Nguồn: tập dữ liệu X-quang ngực được tổ chức theo nhãn pneumonia và normal.
- Cấu trúc dữ liệu: train, validation, và test.
- Dự án cũng có toy dataset generator để phục vụ phát triển nhẹ và kiểm thử CI.

### 5.2 Ghi chú xử lý dữ liệu

- Không mặc định rằng tập dữ liệu này đã đủ cho chứng nhận pháp lý.
- Mọi tập dữ liệu riêng của khách hàng dùng để huấn luyện lại phải tuân theo chính sách đồng ý, riêng tư, và lưu giữ dữ liệu của khách hàng.
- Lineage dữ liệu và tiền xử lý nên được ghi nhận trước khi đưa vào production.

### 5.3 Bias và đại diện dữ liệu

- Thành phần dữ liệu có thể chưa đại diện đầy đủ cho mọi nhóm nhân khẩu học hoặc loại thiết bị.
- Cần thêm bước xác thực riêng cho từng site triển khai.

## 6. Tài liệu hóa script tiện ích: create_toy_dataset.py

Script này thuộc nhóm công cụ cho developer và CI, không phải runtime lâm sàng. Nó tạo ra một toy dataset nhỏ, có tính tái lập, từ các thư mục ảnh gốc.

### 6.1 Mục đích

- Tạo bộ test nhẹ cho phát triển cục bộ.
- Hỗ trợ CI/CD chạy nhanh mà không phải di chuyển toàn bộ dataset.
- Giảm chi phí lưu trữ, băng thông, và tiền xử lý cho workflow kiểm thử.

### 6.2 Tính năng cốt lõi

- Tự động phát hiện các thư mục nhãn như `NORMAL` và `PNEUMONIA` trong cây dữ liệu.
- Kiểm tra đường dẫn nguồn và đích trước khi sao chép file.
- Dùng `ThreadPoolExecutor` để copy song song, phù hợp với tác vụ I/O-bound.
- Giữ metadata file nhờ `shutil.copy2`.

### 6.3 Điều khiển tính tái lập

- `sample_size = 60` giới hạn bộ toy dataset ở kích thước nhỏ và ổn định.
- `RANDOM_SEED = 2026` đảm bảo lần chạy nào cũng chọn cùng một tập con ngẫu nhiên.
- Tái lập là yếu tố quan trọng cho unit test, CI pipeline, và khả năng kiểm toán.

### 6.4 Hành vi vận hành

- Script quét dưới thư mục `dataset/` của dự án.
- Nếu có nhiều ứng viên, script ưu tiên thư mục nằm dưới `train/`.
- Kết quả được ghi vào `toy_dataset/<ten-lop>/`.
- Nếu thiếu thư mục nhãn, script dừng sớm với thông báo lỗi rõ ràng.

### 6.5 Ghi chú bảo mật

- Script chuẩn hóa đường dẫn trước khi dùng để giảm rủi ro path traversal.
- Chỉ sao chép các file có đuôi ảnh đã cho phép.
- Nếu mở rộng trong tương lai để nhận input người dùng, cần giữ nguyên mẫu kiểm tra này.

### 6.6 Cách đưa vào bàn giao

- Đưa script này vào developer guide.
- Nhắc tới nó trong phần cấu hình CI/CD để đội kỹ thuật biết cách tạo bộ dữ liệu test tối thiểu.
- Không đưa toy dataset vào bộ bằng chứng lâm sàng vì nó chỉ phục vụ kiểm thử kỹ thuật.

## 7. Checklist bàn giao

- Gói ứng dụng chạy được trong môi trường đích.
- File mô hình có sẵn và load thành công.
- Đội kỹ thuật khách hàng có tài liệu triển khai.
- Phạm vi thương mại và điều khoản hỗ trợ được tách tài liệu riêng.
- Các script tiện ích như `create_toy_dataset.py` được tài liệu hóa để đảm bảo phát triển có thể tái lập.
