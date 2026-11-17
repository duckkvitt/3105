#if IOS187_DIAGNOSTICS
import SwiftUI
import UIKit

// Separate entry point: the diagnostic build never initializes the normal app
// stores, runs detectSupport, imports a patch, or starts the kernel chain.
@main
struct IOS187DiagnosticsApp: App {
    var body: some Scene {
        WindowGroup {
            IOS187DiagnosticsView()
        }
    }
}

struct IOS187DiagnosticReport: Encodable {
    let diagnosticVersion = "3105-ios187-readonly-r1"
    let timestamp = ISO8601DateFormatter().string(from: Date())
    let machine = AppInfo.machineName
    let expectedMachine = "iPhone11,6"
    let iosVersion = AppInfo.osVersion
    let iosBuild = AppInfo.osBuild
    let signingBundleID = Bundle.main.bundleIdentifier ?? "unknown"
    var targetBundleID: String
    var bridgeAvailable = false
    var containerActivated = false
    var directoryReadable = false
    var stage = "not_started"
    var errorDomain: String?
    var errorCode: Int?
    let kernelExecution = "disabled"
    let writeTest = "not_run"
    let patchApplyRestore = "not_run"

    var text: String {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        guard let data = try? encoder.encode(self),
              let result = String(data: data, encoding: .utf8) else {
            return "Could not encode diagnostic report."
        }
        return result
    }
}

enum IOS187ReadOnlyDiagnostic {
    static var isExpectedTestDevice: Bool {
        AppInfo.machineName == "iPhone11,6"
    }

    static var isTargetOS: Bool {
        let version = AppInfo.versionTuple
        return version.major == 18 && version.minor == 7 && [11, 12].contains(version.patch)
    }

    static func run(bundleID: String) -> IOS187DiagnosticReport {
        var report = IOS187DiagnosticReport(targetBundleID: bundleID)
        guard isTargetOS else {
            report.stage = "outside_diagnostic_os_range"
            return report
        }
        guard bundleID.utf8.count <= 255,
              bundleID.range(of: "^[A-Za-z0-9_-]+(\\.[A-Za-z0-9_-]+)+$", options: .regularExpression) != nil,
              bundleID != Bundle.main.bundleIdentifier else {
            report.stage = "invalid_or_self_bundle_id"
            return report
        }
        guard Bundle.main.bundleIdentifier == "com.apple.mobile.MobileHouseArrest" else {
            report.stage = "signing_bundle_id_changed"
            return report
        }
#if targetEnvironment(simulator)
        report.stage = "physical_device_required"
        return report
#else
        report.bridgeAvailable = MCMBridgeAvailable()
        guard report.bridgeAvailable else {
            report.stage = "mcm_bridge_unavailable"
            return report
        }

        // Use the existing app-container route, with no kernel fallback and
        // no automatic enumeration of the user's other applications.
        var activationError: NSString?
        guard let path = MCMActivateContainerPath(2, bundleID, false, &activationError) else {
            // Raw native error messages can contain absolute container paths.
            report.stage = "container_activation_denied"
            return report
        }
        report.containerActivated = true
        let url = URL(fileURLWithPath: path).standardizedFileURL
        let canonicalPath = normalizedPath(url.path)
        let canonicalURL = URL(fileURLWithPath: canonicalPath)
        guard canonicalURL.deletingLastPathComponent().path == "/var/mobile/Containers/Data/Application",
              UUID(uuidString: canonicalURL.lastPathComponent) != nil,
              canonicalPath != normalizedPath(NSHomeDirectory()) else {
            report.stage = "unexpected_or_self_container"
            return report
        }
        do {
            // Listing is the actual access check. Names and contents are not
            // included in the report; this probe never creates or edits files.
            _ = try FileManager.default.contentsOfDirectory(atPath: url.path)
            report.directoryReadable = true
            report.stage = "read_access_confirmed_write_unverified"
        } catch {
            let failure = error as NSError
            report.stage = "container_read_denied"
            report.errorDomain = failure.domain
            report.errorCode = failure.code
        }
        return report
#endif
    }

    private static func normalizedPath(_ path: String) -> String {
        let result = URL(fileURLWithPath: path).standardizedFileURL.path
        return result.hasPrefix("/private/var/") ? String(result.dropFirst(8)) : result
    }
}

struct IOS187DiagnosticsView: View {
    @State private var bundleID = ""
    @State private var running = false
    @State private var report: IOS187DiagnosticReport?

    var body: some View {
        NavigationStack {
            Form {
                Section("Thiết bị thử") {
                    LabeledContent("Model", value: AppInfo.machineName)
                    LabeledContent("iOS", value: "\(AppInfo.osVersion) (\(AppInfo.osBuild))")
                    if !IOS187ReadOnlyDiagnostic.isExpectedTestDevice {
                        Text("Máy thử đã chọn là iPhone XS Max (iPhone11,6); tiếp tục được nhưng kết quả không thuộc đúng mẫu máy đã yêu cầu.")
                            .font(.footnote)
                            .foregroundStyle(.orange)
                    }
                    Text("Bản chẩn đoán R1 dành cho iOS 18.7.11 và 18.7.12. Chưa xác nhận hỗ trợ áp dụng patch.")
                        .font(.footnote)
                }
                Section {
                    TextField("Bundle ID của app thử, ví dụ com.example.myapp", text: $bundleID)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .disabled(running)
                    Button {
                        startDiagnostic()
                    } label: {
                        HStack {
                            Text("Kiểm tra quyền đọc")
                            if running { ProgressView() }
                        }
                    }
                    .disabled(running || bundleID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !IOS187ReadOnlyDiagnostic.isTargetOS)
                } header: {
                    Text("Ứng dụng bạn quản lý")
                } footer: {
                    Text("Nhập bundle ID của ứng dụng đã cài trên máy. Phép thử chỉ đọc danh sách thư mục gốc; báo cáo không chứa tên file hoặc nội dung dữ liệu.")
                }
                if let report {
                    Section("Kết quả") {
                        Text(report.directoryReadable ? "Đọc được container. Quyền ghi và áp dụng/khôi phục patch vẫn cần kiểm tra riêng." : "Chưa xác nhận được quyền đọc. Xem trường stage trong báo cáo.")
                        ShareLink(item: report.text) {
                            Label("Chia sẻ báo cáo", systemImage: "square.and.arrow.up")
                        }
                        Text(report.text)
                            .font(.caption.monospaced())
                            .textSelection(.enabled)
                    }
                }
                Section {
                    Text("Bản này tắt chạy kernel và không thay đổi file trong ứng dụng đích. Kết quả đọc thành công chưa chứng minh 3105 hỗ trợ đầy đủ phiên bản iOS này.")
                        .font(.footnote)
                    Link("Mã nguồn 3105 của YangJiii (GPL-3.0)", destination: URL(string: "https://github.com/YangJiiii/3105")!)
                }
            }
            .navigationTitle("3105 • Chẩn đoán R1")
        }
    }

    private func startDiagnostic() {
        let target = bundleID.trimmingCharacters(in: .whitespacesAndNewlines)
        running = true
        report = nil
        DispatchQueue.global(qos: .userInitiated).async {
            let result = IOS187ReadOnlyDiagnostic.run(bundleID: target)
            DispatchQueue.main.async {
                report = result
                running = false
            }
        }
    }
}
#endif
