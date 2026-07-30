# Gói Bàn Giao Thương Mại

Dự án: AI Pulmonary Diagnostic Suite
Mục đích: Xác định ranh giới thương mại, mô hình sở hữu, và điều khoản hỗ trợ khi bàn giao cho khách hàng.

## 1. Mục đích tài liệu

Tài liệu này là phần bổ trợ về thương mại và pháp lý cho bộ bàn giao kỹ thuật. Mục tiêu là:

- Làm rõ phần nào nằm trong phạm vi bàn giao và phần nào không.
- Bảo vệ hai bên khỏi phát sinh phạm vi ngoài kế hoạch và chi phí triển khai không dự kiến.
- Giữ lại cơ hội doanh thu từ nâng cấp, bảo trì, và hỗ trợ vận hành.

Đây là mẫu tài liệu hỗ trợ hợp đồng và cần được bộ phận pháp lý rà soát trước khi ký.

## 2. Phạm vi công việc (SOW)

### 2.1 Phần trong phạm vi

- Ứng dụng web dựa trên Streamlit cho triage ảnh phổi và giải thích mô hình.
- Triển khai cục bộ hoặc trên hạ tầng cloud do khách hàng sở hữu bằng mã nguồn và artifact mô hình đã cung cấp.
- Suy luận mô hình bằng các trọng số `.tflite` và `.keras`.
- Tải ảnh theo lô và xuất kết quả triage ra `.xlsx` và `.txt`.
- Hướng dẫn vận hành cơ bản cho cài đặt, khởi chạy, và kiểm tra.
- Tạo toy dataset để kiểm thử cục bộ và chạy CI.

### 2.2 Phần ngoài phạm vi

Các hạng mục sau chỉ được thực hiện nếu được mua thêm thông qua yêu cầu thay đổi hoặc SOW riêng:

- Tích hợp PACS, RIS, EMR, hoặc DICOM của bệnh viện.
- Quản lý định danh chuẩn production, SSO, hoặc RBAC.
- Chứng nhận HIPAA, GDPR, hoặc chứng nhận pháp lý địa phương.
- Thẩm định lâm sàng, nộp hồ sơ pháp lý, hoặc đăng ký thiết bị y tế.
- Quản lý người dùng đa tenant tập trung và thanh toán.
- Huấn luyện lại mô hình liên tục trên dữ liệu lâm sàng của khách hàng.
- Vận hành production 24/7, hỗ trợ on-call, và xử lý sự cố.
- Thanh toán hóa đơn cloud, sở hữu tài khoản cloud, và quản trị chi phí cloud.

### 2.3 Kiểm soát thay đổi

- Mọi yêu cầu nằm ngoài phạm vi phải được ghi nhận thành yêu cầu thay đổi.
- Mỗi yêu cầu thay đổi phải nêu rõ tác động đến tiến độ, chi phí, phụ thuộc, và rủi ro.
- Chỉ triển khai sau khi hai bên chấp thuận bằng văn bản.

## 3. Sở hữu trí tuệ và cấp phép

### 3.1 Mô hình sở hữu

- Khách hàng nhận quyền sử dụng phần mềm đối với gói ứng dụng đã bàn giao.
- Nhà cung cấp giữ quyền sở hữu đối với pipeline huấn luyện, phương pháp huấn luyện, và know-how có thể tái sử dụng, trừ khi có thỏa thuận chuyển giao bằng văn bản.
- Trọng số mô hình được cấp phép để sử dụng cho giải pháp này và có thể bị giới hạn trong môi trường khách hàng đã quy định trong hợp đồng.

### 3.2 Định hướng cấp phép khuyến nghị

- Cấp cho khách hàng quyền sử dụng không độc quyền, không chuyển nhượng, có thể là vĩnh viễn hoặc theo thời hạn, đối với ứng dụng đã triển khai.
- Chỉ cung cấp mã nguồn cho lớp ứng dụng cần thiết để vận hành và bảo trì, không cung cấp toàn bộ stack nghiên cứu hoặc huấn luyện nếu chưa được thanh toán riêng.
- Coi việc huấn luyện lại mô hình, thiết kế lại kiến trúc, và hỗ trợ thêm modality mới là công việc mở rộng có tính phí.

### 3.3 Điều khoản tái sử dụng

- Nhà cung cấp giữ quyền tái sử dụng các thành phần dùng chung, pattern chung, và thư viện có sẵn miễn là không lộ dữ liệu mật của khách hàng.
- Dữ liệu, nhãn, và cấu hình vận hành đặc thù của khách hàng vẫn là tài sản mật của khách hàng.

## 4. SLA và điều khoản hỗ trợ

### 4.1 Thời gian hỗ trợ bảo hành

- Bao gồm một khoảng hỗ trợ sau bàn giao có giới hạn, thường từ 30 đến 90 ngày.
- Trong giai đoạn này, nhà cung cấp sửa các lỗi tái hiện được trên baseline mã nguồn đã bàn giao.
- Các yêu cầu nâng cấp, mở rộng phạm vi, và lỗi do môi trường riêng không nằm trong phạm vi bảo hành nếu không có thỏa thuận khác.

### 4.2 Mô hình bảo trì có phí

Sau giai đoạn bảo hành, hỗ trợ nên chuyển sang mô hình bảo trì trả phí:

- Gói retainer theo tháng cho hỗ trợ liên tục và thay đổi nhỏ.
- Tính phí theo thời gian và nhân lực cho các nâng cấp lớn hoặc cập nhật mô hình.
- SOW riêng cho tối ưu hạ tầng, hardening triển khai, hoặc tích hợp quy trình lâm sàng.

### 4.3 Mức dịch vụ

- Thời gian phản hồi và mục tiêu xử lý chỉ nên áp dụng cho gói hỗ trợ trả phí.
- Phân loại mức độ nghiêm trọng cần tách rõ giữa ngừng nền tảng, suy giảm vận hành, và yêu cầu tính năng.

## 5. Kiểm soát rủi ro thương mại

### 5.1 Bảo vệ chi phí

- Chi phí cloud của khách hàng được tính vào tài khoản cloud do khách hàng sở hữu.
- Chi phí lưu trữ, compute, và network egress do khách hàng quản lý không thuộc trách nhiệm của nhà cung cấp.
- Mọi môi trường bổ sung, sandbox, hoặc cụm staging do khách hàng yêu cầu đều có thể tính phí nếu hợp đồng không bao gồm.

### 5.2 Bảo vệ khỏi scope creep

- Những yêu cầu làm thay đổi workflow lâm sàng, quản trị dữ liệu, hoặc độ sâu tích hợp phải được coi là phạm vi mới.
- Phản hồi từ bản demo không tự động trở thành cam kết bàn giao.
- Tiêu chí nghiệm thu phải rõ ràng và đo được.

### 5.3 Lộ trình tăng doanh thu

- Modality mới, nâng cấp explainability, hardening triển khai, và tối ưu hiệu năng nên được định vị là dịch vụ cao cấp.
- Bảo trì, cập nhật mô hình, và tối ưu cloud là các nguồn doanh thu định kỳ.

## 6. Tiêu chí nghiệm thu

Xem dự án là nghiệm thu khi xác minh được các điểm sau:

- Ứng dụng khởi chạy thành công trong môi trường đã thống nhất.
- Artifact mô hình được tải và suy luận chạy không lỗi runtime.
- Chức năng xuất kết quả hoạt động như mô tả.
- Đội kỹ thuật khách hàng nhận được gói bàn giao, hướng dẫn vận hành, và ghi chú bàn giao.
- Các giới hạn đã biết và phần ngoài phạm vi được xác nhận bằng văn bản.

## 7. Ghi chú ký kết

- Đây là mẫu tài liệu bàn giao và nên được đính kèm với gói hợp đồng thương mại.
- Ngôn ngữ pháp lý cuối cùng cần được đồng bộ với master services agreement hoặc purchase order.
