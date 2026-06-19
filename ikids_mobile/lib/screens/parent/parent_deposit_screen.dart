import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class ParentDepositScreen extends StatefulWidget {
  const ParentDepositScreen({super.key});

  @override
  State<ParentDepositScreen> createState() => _ParentDepositScreenState();
}

class _ParentDepositScreenState extends State<ParentDepositScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi"; // Ngôn ngữ mặc định
  String _userId = "";
  String _token = "";
  double _balance = 0.0;

  // Controllers
  final _amountController = TextEditingController(text: "50000");
  final _issueAmountController = TextEditingController();
  final _issueDescController = TextEditingController();

  double _currentAmount = 50000;
  String _memo = "";

  // ================= BỘ TỪ ĐIỂN SONG NGỮ HOÀN CHỈNH =================
  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "💳 Nạp Tiền & Quản Lý Ví",
      "lbl_balance": "Số dư ví hiện tại",
      "sub_bank_info": "1. Thông tin chuyển khoản",
      "input_amount": "Số tiền muốn nạp (VNĐ)",
      "bank_details": "Ngân hàng: BIDV\nSố tài khoản: 64110001073247\nChủ TK: NGUYEN DUC PHAT",
      "warn_memo": "Nội dung chuyển khoản bắt buộc:",
      "btn_done": "Tôi đã chuyển khoản xong",
      "toast_logged": "Đã ghi nhận! Hệ thống đang chờ ngân hàng xác nhận.",
      "qr_title": "2. Quét mã QR (Nhanh)",
      "qr_caption": "Mở ứng dụng Ngân hàng để quét mã này",
      "expander_title": "❓ Đã chuyển nhưng chưa nhận được tiền?",
      "expander_desc": "Gửi yêu cầu để Admin kiểm tra và cộng tiền thủ công:",
      "input_confirm_amount": "Số tiền đã chuyển (VNĐ)",
      "input_desc": "Mô tả sự cố",
      "placeholder_desc": "VD: Đã chuyển khoản 15 phút trước nhưng chưa nhận được...",
      "btn_submit_report": "💥 Gửi Yêu Cầu Hỗ Trợ",
      "success_report": "✅ Đã gửi yêu cầu thành công!",
      "err_empty_desc": "⚠️ Vui lòng nhập mô tả sự cố.",
      "err_conn": "⚠️ Lỗi kết nối mạng!"
    },
    "en": {
      "title": "💳 Wallet Top-up",
      "lbl_balance": "Current Wallet Balance",
      "sub_bank_info": "1. Bank Transfer Information",
      "input_amount": "Deposit Amount (VND)",
      "bank_details": "Bank: BIDV\nAccount No: 64110001073247\nHolder: NGUYEN DUC PHAT",
      "warn_memo": "Mandatory Transfer Content:",
      "btn_done": "I Have Transferred",
      "toast_logged": "Recorded! Awaiting bank confirmation.",
      "qr_title": "2. Scan QR Code (Instant)",
      "qr_caption": "Open Mobile Banking app to scan",
      "expander_title": "❓ Transferred but balance not updated?",
      "expander_desc": "Submit a ticket for manual verification:",
      "input_confirm_amount": "Transferred Amount (VND)",
      "input_desc": "Issue Description",
      "placeholder_desc": "e.g., Transferred 15 mins ago but no update...",
      "btn_submit_report": "💥 Submit Support Ticket",
      "success_report": "✅ Ticket submitted successfully!",
      "err_empty_desc": "⚠️ Issue description cannot be empty.",
      "err_conn": "⚠️ Network connection error!"
    }
  };

  @override
  void initState() {
    super.initState();
    _initData();
  }

  Future<void> _initData() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    try {
      // ✅ ĐỌC NGÔN NGỮ TỪ BỘ NHỚ LÚC KHỞI TẠO
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      _token = await _storage.read(key: 'jwt_token') ?? "";
      _userId = await _storage.read(key: 'user_id') ?? "";

      if (_userId.isNotEmpty) {
        // Tạo nội dung chuyển khoản tự động
        String suffix = _userId.length >= 6 ? _userId.substring(_userId.length - 6).toUpperCase() : _userId.toUpperCase();
        _memo = "IKIDS NAP $suffix";

        // Lấy số dư ví
        final res = await http.get(
          Uri.parse('${AppConfig.apiUrl}/api/tv3/gamification/profile/$_userId'),
          headers: {"Authorization": "Bearer $_token"}
        );
        if (res.statusCode == 200) {
          _balance = (jsonDecode(res.body)['balance'] ?? 0).toDouble();
        }
      }
    } catch (e) {
      debugPrint("Lỗi load số dư: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // Cập nhật số tiền nạp để vẽ lại QR
  void _updateAmount(String val) {
    setState(() {
      _currentAmount = double.tryParse(val) ?? 0.0;
    });
  }

  // Hàm gửi báo cáo sự cố (Gọi chung API Contact của module TV3)
  Future<void> _submitIssueReport() async {
    final labels = _labels[_lang]!;
    if (_issueDescController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels['err_empty_desc']!), backgroundColor: Colors.red));
      return;
    }

    showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator(color: Colors.green)));

    try {
      final payload = {
        "sender_id": _userId,
        "receiver_id": "admin",
        "subject": "SỰ CỐ NẠP TIỀN", // Cố định tiếng Việt để Backend nhận dạng luồng
        "content": _issueDescController.text.trim(),
        "amount": double.tryParse(_issueAmountController.text) ?? 0.0
      };

      final res = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/contact/submit'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload),
      ).timeout(const Duration(seconds: 15));

      if (mounted) Navigator.pop(context);

      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["success_report"]!), backgroundColor: Colors.green));
        _issueDescController.clear();
        _issueAmountController.clear();
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["err_conn"]!), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;
    
    // Tự động generate link VietQR
    String qrUrl = "https://img.vietqr.io/image/BIDV-64110001073247-compact.png?amount=${_currentAmount.toInt()}&addInfo=${Uri.encodeComponent(_memo)}&accountName=NGUYEN%20DUC%20PHAT";

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          // ✅ ĐÃ THÊM: NÚT CHUYỂN ĐỔI NGÔN NGỮ ĐỒNG BỘ
          TextButton(
            onPressed: () async {
              setState(() => _lang = _lang == "vi" ? "en" : "vi");
              await _storage.write(key: 'app_lang', value: _lang);
            },
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.green))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // --- 1. BANNER SỐ DƯ ---
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: LinearBinding.linearGradient(Colors.green[600]!, Colors.green[400]!),
                      borderRadius: BorderRadius.circular(15),
                      boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 4))]
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_balance"]!, style: const TextStyle(color: Colors.white70, fontSize: 14)),
                        const SizedBox(height: 5),
                        Text("${_balance.toStringAsFixed(0)} VNĐ", style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // --- 2. THÔNG TIN CHUYỂN KHOẢN ---
                  Text(labels["sub_bank_info"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.indigo)),
                  const SizedBox(height: 10),
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(15),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          TextField(
                            controller: _amountController,
                            keyboardType: TextInputType.number,
                            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                            decoration: InputDecoration(
                              labelText: labels["input_amount"],
                              border: const OutlineInputBorder(),
                              suffixText: "VNĐ"
                            ),
                            onChanged: _updateAmount,
                          ),
                          const SizedBox(height: 15),
                          
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(8)),
                            child: Text(labels["bank_details"]!, style: const TextStyle(fontSize: 13, height: 1.5)),
                          ),
                          const SizedBox(height: 15),

                          Text(labels["warn_memo"]!, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red)),
                          const SizedBox(height: 5),
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(color: Colors.grey[200], borderRadius: BorderRadius.circular(8)),
                            child: Text(_memo, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2), textAlign: TextAlign.center),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // --- 3. MÃ QR NHANH ---
                  Text(labels["qr_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.indigo)),
                  const SizedBox(height: 10),
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          Image.network(qrUrl, height: 250, fit: BoxFit.contain),
                          const SizedBox(height: 15),
                          Text(labels["qr_caption"]!, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                          const SizedBox(height: 15),
                          SizedBox(
                            width: double.infinity,
                            height: 45,
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                              onPressed: () {
                                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["toast_logged"]!), backgroundColor: Colors.blue));
                              },
                              child: Text(labels["btn_done"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
                            ),
                          )
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 25),

                  // --- 4. BÁO CÁO SỰ CỐ ---
                  Card(
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.red[200]!)),
                    child: ExpansionTile(
                      collapsedIconColor: Colors.red,
                      iconColor: Colors.red,
                      title: Text(labels["expander_title"]!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 13)),
                      childrenPadding: const EdgeInsets.all(15),
                      children: [
                        Text(labels["expander_desc"]!, style: const TextStyle(fontSize: 12, color: Colors.black87)),
                        const SizedBox(height: 15),
                        TextField(
                          controller: _issueAmountController,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(labelText: labels["input_confirm_amount"], border: const OutlineInputBorder(), isDense: true),
                        ),
                        const SizedBox(height: 10),
                        TextField(
                          controller: _issueDescController,
                          maxLines: 3,
                          decoration: InputDecoration(labelText: labels["input_desc"], hintText: labels["placeholder_desc"], border: const OutlineInputBorder()),
                        ),
                        const SizedBox(height: 15),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
                            onPressed: _submitIssueReport,
                            child: Text(labels["btn_submit_report"]!),
                          ),
                        )
                      ],
                    ),
                  )
                ],
              ),
            ),
    );
  }
}

// Bổ trợ làm Gradient mượt cho Banner Số dư
class LinearBinding {
  static LinearGradient linearGradient(Color c1, Color c2) {
    return LinearGradient(colors: [c1, c2], begin: Alignment.topLeft, end: Alignment.bottomRight);
  }
}