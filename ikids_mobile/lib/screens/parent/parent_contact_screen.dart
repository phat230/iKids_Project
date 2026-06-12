import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart';
import '../../core/config.dart';

class ParentContactScreen extends StatefulWidget {
  const ParentContactScreen({super.key});

  @override
  State<ParentContactScreen> createState() => _ParentContactScreenState();
}

class _ParentContactScreenState extends State<ParentContactScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = false;
  String _lang = "vi";
  String _parentId = "";

  List<dynamic> _historyList = [];

  // Controllers cho form
  final _contentController = TextEditingController();
  DateTime _selectedDate = DateTime.now();
  
  // Ánh xạ Loại yêu cầu
  final Map<String, String> _typeOptions = {
    "Xin nghỉ phép": "req_leave",
    "Hỏi bài tập": "req_homework",
    "Góp ý dịch vụ": "req_feedback",
    "Khác": "req_other"
  };
  String _selectedTypeRaw = "Xin nghỉ phép";

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "📩 Liên Hệ & Xin Nghỉ Phép",
      "tab_new": "📝 Gửi Yêu Cầu",
      "tab_history": "📋 Lịch Sử",
      "lbl_type": "Loại yêu cầu:",
      "lbl_date": "Ngày áp dụng:",
      "lbl_content": "Nội dung chi tiết (*):",
      "placeholder_content": "Ví dụ: Xin cho cháu nghỉ học ngày...",
      "btn_submit": "🚀 Gửi Yêu Cầu",
      "err_empty": "⚠️ Vui lòng nhập nội dung chi tiết!",
      "success_msg": "✅ Đã gửi yêu cầu thành công!",
      "req_leave": "Xin nghỉ phép",
      "req_homework": "Hỏi bài tập",
      "req_feedback": "Góp ý dịch vụ",
      "req_other": "Khác",
      "info_empty": "Chưa có yêu cầu nào được ghi nhận.",
      "lbl_row_type": "Loại:",
      "lbl_row_date": "Ngày:",
      "lbl_row_content": "Nội dung:",
      "status_pending": "Đang xử lý",
      "status_approved": "Đã duyệt",
      "status_rejected": "Từ chối"
    },
    "en": {
      "title": "📩 Contact & Leave",
      "tab_new": "📝 New Request",
      "tab_history": "📋 History",
      "lbl_type": "Request Type:",
      "lbl_date": "Effective Date:",
      "lbl_content": "Detailed Content (*):",
      "placeholder_content": "e.g., Request for child absence on...",
      "btn_submit": "🚀 Submit Request",
      "err_empty": "⚠️ Content cannot be empty!",
      "success_msg": "✅ Request submitted successfully!",
      "req_leave": "Leave Request",
      "req_homework": "Homework Inquiry",
      "req_feedback": "Service Feedback",
      "req_other": "Other",
      "info_empty": "No previous contact logs found.",
      "lbl_row_type": "Type:",
      "lbl_row_date": "Date:",
      "lbl_row_content": "Content:",
      "status_pending": "Pending",
      "status_approved": "Approved",
      "status_rejected": "Rejected"
    }
  };

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    if (!mounted) return;
    setState(() => _isLoading = true);
    try {
      _parentId = await _storage.read(key: 'user_id') ?? "";
      if (_parentId.isEmpty) return;

      final res = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/contact/history/$_parentId')).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        if (mounted) setState(() => _historyList = jsonDecode(utf8.decode(res.bodyBytes)));
      }
    } catch (e) {
      debugPrint("Lỗi tải lịch sử liên hệ: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // Hàm chọn ngày (Mở bộ lịch của điện thoại)
  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() => _selectedDate = picked);
    }
  }

  // Hàm gửi form
  Future<void> _submitForm() async {
    if (_contentController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!["err_empty"]!), backgroundColor: Colors.red));
      return;
    }

    showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator()));

    try {
      final payload = {
        "parent_id": _parentId,
        "type": _selectedTypeRaw, // Giữ chuỗi thô gửi lên DB (Tiếng Việt)
        "date": DateFormat('yyyy-MM-dd').format(_selectedDate),
        "content": _contentController.text.trim(),
        "status": "pending"
      };

      final res = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/contact/submit'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload),
      ).timeout(const Duration(seconds: 10));

      if (mounted) Navigator.pop(context);

      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!["success_msg"]!), backgroundColor: Colors.green));
        _contentController.clear();
        _loadHistory();
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi kết nối mạng!"), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          backgroundColor: Colors.redAccent,
          foregroundColor: Colors.white,
          actions: [
            TextButton(
              onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
              child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            )
          ],
          bottom: TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            indicatorWeight: 3,
            tabs: [
              Tab(text: labels["tab_new"]),
              Tab(text: labels["tab_history"]),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildComposeTab(labels),
            _buildHistoryTab(labels),
          ],
        ),
      ),
    );
  }

  // ================= TAB 1: GỬI YÊU CẦU =================
  Widget _buildComposeTab(Map<String, String> labels) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Card(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(labels["lbl_type"]!, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
              const SizedBox(height: 5),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(border: Border.all(color: Colors.grey[300]!), borderRadius: BorderRadius.circular(8)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedTypeRaw,
                    items: _typeOptions.keys.map((String keyRaw) {
                      String labelKey = _typeOptions[keyRaw]!;
                      return DropdownMenuItem<String>(value: keyRaw, child: Text(labels[labelKey]!));
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _selectedTypeRaw = val);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 20),

              Text(labels["lbl_date"]!, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
              const SizedBox(height: 5),
              InkWell(
                onTap: () => _selectDate(context),
                child: Container(
                  padding: const EdgeInsets.all(15),
                  decoration: BoxDecoration(border: Border.all(color: Colors.grey[300]!), borderRadius: BorderRadius.circular(8)),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(DateFormat('dd/MM/yyyy').format(_selectedDate), style: const TextStyle(fontSize: 16)),
                      const Icon(Icons.calendar_today, color: Colors.redAccent),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              Text(labels["lbl_content"]!, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
              const SizedBox(height: 5),
              TextField(
                controller: _contentController,
                maxLines: 5,
                decoration: InputDecoration(
                  hintText: labels["placeholder_content"],
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  contentPadding: const EdgeInsets.all(12),
                ),
              ),
              const SizedBox(height: 25),

              SizedBox(
                width: double.infinity,
                height: 45,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                  onPressed: _submitForm,
                  child: Text(labels["btn_submit"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  // ================= TAB 2: LỊCH SỬ YÊU CẦU =================
  Widget _buildHistoryTab(Map<String, String> labels) {
    if (_isLoading) return const Center(child: CircularProgressIndicator(color: Colors.redAccent));
    if (_historyList.isEmpty) return Center(child: Text(labels["info_empty"]!));

    return RefreshIndicator(
      color: Colors.redAccent,
      onRefresh: _loadHistory,
      child: ListView.builder(
        padding: const EdgeInsets.all(15),
        itemCount: _historyList.length,
        itemBuilder: (context, index) {
          final item = _historyList[index];
          
          // Trích xuất Type đa ngôn ngữ
          String rawType = item['type'] ?? 'Khác';
          String typeLangKey = _typeOptions[rawType] ?? "req_other";
          String displayType = labels[typeLangKey] ?? rawType;

          // Xử lý Status (Màu và Chữ)
          String rawStatus = (item['status'] ?? 'pending').toLowerCase();
          String displayStatus = labels["status_pending"]!;
          Color statusColor = Colors.blue;
          IconData statusIcon = Icons.pending;

          if (rawStatus == "approved" || rawStatus == "resolved") {
            displayStatus = labels["status_approved"]!;
            statusColor = Colors.green;
            statusIcon = Icons.check_circle;
          } else if (rawStatus == "rejected") {
            displayStatus = labels["status_rejected"]!;
            statusColor = Colors.red;
            statusIcon = Icons.cancel;
          }

          return Card(
            elevation: 2,
            margin: const EdgeInsets.only(bottom: 15),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(displayType, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
                        child: Row(
                          children: [
                            Icon(statusIcon, color: statusColor, size: 14),
                            const SizedBox(width: 4),
                            Text(displayStatus, style: TextStyle(color: statusColor, fontSize: 12, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      )
                    ],
                  ),
                  const Divider(),
                  Text("${labels['lbl_row_date']} ${item['date'] ?? ''}", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  const SizedBox(height: 5),
                  Text(item['content'] ?? '', style: const TextStyle(fontSize: 14)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}