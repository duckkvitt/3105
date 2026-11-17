# Thử trên iPhone XS Max — iOS 18.7.12

Bản chuẩn bị: **3105 Diagnostic R1**, phát triển từ nguồn 3105 main commit `a72617ed4c764a65d8aac1e91aca95231e72a2cb` của YangJiii. Giữ giấy phép GPL-3.0 và ghi công trong repository.

Đây là bước chẩn đoán phục vụ mục tiêu hỗ trợ đầy đủ ứng dụng 3105 trên 18.7.11/18.7.12. **Chưa có kết quả build Xcode hoặc kiểm thử iPhone. Chưa có IPA được tạo trong workspace Windows.**

## Bản R1 kiểm tra điều gì?

- Mở một màn hình chẩn đoán riêng trên nền ứng dụng 3105.
- Người dùng nhập bundle ID của một ứng dụng đã cài và thuộc quyền quản lý của mình.
- Thử đường truy cập container MCM hiện có, sau đó thực sự đọc danh sách thư mục gốc. Không tự duyệt các ứng dụng khác.
- Báo cáo gồm model, phiên bản/build iOS, bundle ID và trạng thái từng bước. Không đưa đường dẫn container, tên file, nội dung tệp hay thông báo lỗi native thô vào báo cáo.
- Không chạy kernel, không ghi file đích và không áp dụng/khôi phục patch. Thành công chỉ xác nhận quyền đọc container trong phiên thử đó; chưa xác nhận quyền ghi hay toàn bộ chức năng 3105.
- Hỗ trợ chạy phép thử đúng 18.7.11 hoặc 18.7.12; không đổi danh sách iOS đã xác minh của ứng dụng gốc.

## Build bằng Windows qua GitHub Actions

Bạn cần tài khoản GitHub. Không cần Mac, token hoặc chứng chỉ ký để build IPA unsigned. Chưa có repository hay workflow nào được đẩy lên/chạy thay bạn trong phiên này.

1. Mở https://github.com/YangJiiii/3105 và chọn **Fork** để tạo bản sao trong tài khoản của bạn.
2. Giải nén `3105_XSM_iOS18.7.12_R1_overlay.zip` trên Windows.
3. Trong repository vừa fork, chọn **Add file → Upload files**. Kéo toàn bộ các thư mục/file trong ZIP vào gốc repository, giữ đúng đường dẫn và commit vào nhánh mặc định. Overlay chứa các file đã sửa; mã nguồn còn lại lấy từ fork.
4. Chọn tab **Actions** và bật workflow cho repository fork nếu GitHub yêu cầu.
5. Chọn **Build 3105 iOS 18.7 Diagnostic → Run workflow**.
6. Khi job thành công, tải artifact `3105-iOS187-Diagnostic-R1-unsigned`. Giải nén để lấy IPA, `build_report.json` và `SHA256SUMS.txt`.
7. Nếu job thất bại, tải artifact `3105-iOS187-Xcode-log` và cung cấp log để sửa lỗi build. Không coi việc đã chuẩn bị workflow là bằng chứng build thành công.

Nếu không thấy nút Run workflow, kiểm tra `.github/workflows/ios187-diagnostic.yml` đã nằm trên nhánh mặc định. Thư mục `.github` phải được tải lên cùng các file khác.

Tham khảo thao tác chạy thủ công: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow

## Ký và cài trên iPhone

IPA tải từ Actions chưa ký, không cài trực tiếp được. Theo tài liệu 3105 gốc, đường truy cập dữ liệu cần chứng chỉ doanh nghiệp và giữ nguyên bundle ID/CodeDirectory identifier `com.apple.mobile.MobileHouseArrest`; đổi ID để cài được sẽ làm phép thử mất ý nghĩa. Build thành công không cung cấp chứng chỉ ký.

Nếu dùng ESign với bộ chứng chỉ phù hợp đã có, ký IPA và giữ nguyên ID nêu trên. Không gửi chứng chỉ, khóa riêng hoặc mật khẩu ký cho người khác. Bản thử dùng cùng bundle ID với 3105 cũ nên có thể thay thế ứng dụng đang cài; xuất các gói/dữ liệu cần giữ trước khi cài. Việc thay thế app phụ thuộc cách ký và công cụ cài, không được bảo đảm giữ nguyên dữ liệu.

Tài liệu yêu cầu cài đặt gốc: https://github.com/YangJiiii/3105/blob/main/README.vi.md#lưu-ý-cài-đặt

## Chạy phép thử

1. Mở **3105 Test 18.7**. Kiểm tra màn hình ghi đúng phiên bản/build iOS của máy.
2. Nhập bundle ID của ứng dụng thử do bạn quản lý. Dùng một ứng dụng thử riêng, không chứa dữ liệu quan trọng, để kiểm tra quyền đọc trước.
3. Bấm **Kiểm tra quyền đọc**.
4. Bấm **Chia sẻ báo cáo** và gửi lại phần JSON.

Các kết quả chính:

| Trường `stage` | Ý nghĩa |
| --- | --- |
| `read_access_confirmed_write_unverified` | Container đọc được; chưa thử quyền ghi hoặc patch. |
| `container_activation_denied` | Đường MCM hiện tại không lấy được quyền; cần đối chiếu ID/cách ký và cơ chế truy cập. Chưa đủ để kết luận iOS đã vá. |
| `container_read_denied` | Đã nhận đường dẫn/quyền activation nhưng đọc thực tế thất bại. |
| `signing_bundle_id_changed` | Cách ký đã đổi bundle ID bắt buộc. |
| `unexpected_or_self_container` | Đường dẫn không phải container ứng dụng đích phù hợp. |
| `invalid_or_self_bundle_id` | ID không hợp lệ hoặc trỏ về chính bản thử. |
| `outside_diagnostic_os_range` | Máy không chạy 18.7.11/18.7.12. |

## Trạng thái công việc còn lại

Cần build bằng Xcode trên Actions, ký/cài bằng cấu hình phù hợp và lấy báo cáo thực tế từ XS Max 18.7.12. Sau đó mới quyết định giữ đường truy cập hiện có hay cần backend khác. Phải kiểm tra quyền ghi, sao lưu và khôi phục trước khi mở các thao tác patch; 18.7.11 cũng cần kết quả thử riêng.
