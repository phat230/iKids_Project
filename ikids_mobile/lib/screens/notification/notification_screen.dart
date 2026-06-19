import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";
  
  String _userId = "";
  String _userRole = "";
  String _userName = "";

  List<dynamic> _inboxNotis = [];
  List<dynamic> _sentNotis = [];

  // Controllers cho Tab Soạn thông báo
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final _receiverIdController = TextEditingController();
  
  String? _selectedTargetRole;
  String _selectedNotiType = "message";

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Hộp Thư & Thông Báo",
      "tab_inbox": "Hộp thư đến",
      "tab_compose": "Soạn tin",
      "tab_sent": "Đã gửi",
      "empty_inbox": "Hộp thư của bạn đang trống.",
      "empty_sent": "Bạn chưa gửi thông báo nào.",
      "from": "Từ:",
      "to": "Tới:",
      "no_title": "Không có tiêu đề",
      "no_permission": "Vai trò của bạn không có quyền gửi thông báo.",
      "lbl_target": "Gửi đến bộ phận:",
      "lbl_type": "Loại thông báo:",
      "lbl_receiver_id": "ID Người nhận (Để trống để gửi toàn bộ)",
      "lbl_all_info": "ℹ️ Yêu cầu sẽ được gửi đến toàn bộ",
      "lbl_title_field": "Tiêu đề (*)",
      "lbl_content_field": "Nội dung chi tiết (*)",
      "btn_send": "Gửi Thông Báo",
      "msg_empty_fields": "Vui lòng điền đủ tiêu đề và nội dung!",
      "msg_success": "🎉 Gửi thông báo thành công!",
      "msg_fail": "Lỗi gửi thông báo!",
      "msg_err_conn": "Mất kết nối mạng!",
      
      // Translating Roles
      "role_operator": "Nhân viên vận hành",
      "role_teacher": "Giáo viên",
      "role_admin": "Ban Giám Đốc",
      "role_student": "Học sinh",
      "role_parent": "Phụ huynh",
      
      // Translating Types
      "type_message": "💬 Tin nhắn trao đổi",
      "type_schedule": "📅 Lịch học",
      "type_finance": "💰 Tài chính & Học phí",
      "type_request": "📝 Đơn từ & Yêu cầu",
      "type_system": "⚙️ Hệ thống",
    },
    "en": {
      "title": "Inbox & Notifications",
      "tab_inbox": "Inbox",
      "tab_compose": "Compose",
      "tab_sent": "Sent",
      "empty_inbox": "Your inbox is empty.",
      "empty_sent": "You haven't sent any messages.",
      "from": "From:",
      "to": "To:",
      "no_title": "No subject",
      "no_permission": "Your role does not have permission to send notifications.",
      "lbl_target": "Send to department:",
      "lbl_type": "Notification Type:",
      "lbl_receiver_id": "Receiver ID (Leave blank to send to all)",
      "lbl_all_info": "ℹ️ Message will be sent to all",
      "lbl_title_field": "Title (*)",
      "lbl_content_field": "Detailed Content (*)",
      "btn_send": "Send Notification",
      "msg_empty_fields": "Please fill in title and content!",
      "msg_success": "🎉 Message sent successfully!",
      "msg_fail": "Failed to send message!",
      "msg_err_conn": "Network connection lost!",

      // Translating Roles
      "role_operator": "Operations Staff",
      "role_teacher": "Teacher",
      "role_admin": "Board of Directors",
      "role_student": "Student",
      "role_parent": "Parent",
      
      // Translating Types
      "type_message": "💬 Exchange Message",
      "type_schedule": "📅 Class Schedule",
      "type_finance": "💰 Finance & Tuition",
      "type_request": "📝 Applications & Requests",
      "type_system": "⚙️ System",
    }
  };

  // Ánh xạ Quyền gửi thông báo (RBAC)
  final Map<String, List<String>> _rbacMatrix = {
    "admin": ["operator", "teacher"],
    "operator": ["admin", "teacher", "student", "parent"],
    "teacher": ["operator", "student", "parent"],
    "student": ["teacher", "operator"],
    "parent": ["teacher", "operator"]
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
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final Map<String, dynamic> decodedUser = jsonDecode(userInfo);
        _userId = decodedUser["id"]?.toString() ?? decodedUser["_id"]?.toString() ?? "";
        _userRole = decodedUser["role"]?.toString().toLowerCase() ?? "student";
        _userName = decodedUser["full_name"]?.toString() ?? decodedUser["name"]?.toString() ?? "Người dùng";
        
        if (_rbacMatrix.containsKey(_userRole) && _rbacMatrix[_userRole]!.isNotEmpty) {
          _selectedTargetRole = _rbacMatrix[_userRole]!.first;
        }

        await Future.wait([_fetchInbox(), _fetchSent()]);
      }
    } catch (e) {
      debugPrint("Error init Data: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _fetchInbox() async {
    if (_userId.isEmpty) return;
    try {
      final response = await http.get(Uri.parse('${AppConfig.apiUrl}/api/notifications/receive/$_userId/$_userRole')).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        if (mounted) setState(() => _inboxNotis = jsonDecode(utf8.decode(response.bodyBytes)));
      }
    } catch (e) {
      debugPrint("Lỗi Inbox: $e");
    }
  }

  Future<void> _fetchSent() async {
    if (_userId.isEmpty) return;
    try {
      final response = await http.get(Uri.parse('${AppConfig.apiUrl}/api/notifications/sent/$_userId')).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        if (mounted) setState(() => _sentNotis = jsonDecode(utf8.decode(response.bodyBytes)));
      }
    } catch (e) {
      debugPrint("Lỗi Sent: $e");
    }
  }

  Future<void> _markAsRead(String notiId) async {
    try {
      final response = await http.put(Uri.parse('${AppConfig.apiUrl}/api/notifications/$notiId/read')).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        setState(() {
          final index = _inboxNotis.indexWhere((n) => n['id'] == notiId);
          if (index != -1) _inboxNotis[index]['is_read'] = true;
        });
      }
    } catch (e) {
      debugPrint("Lỗi đánh dấu đã đọc: $e");
    }
  }

  Future<void> _sendNotification() async {
    final labels = _locales[_lang]!;
    if (_titleController.text.trim().isEmpty || _contentController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_empty_fields"]!), backgroundColor: Colors.red));
      return;
    }

    showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator()));

    String receiverIdStr = _receiverIdController.text.trim();
    if (receiverIdStr.isEmpty) receiverIdStr = "all";

    Map<String, dynamic> payload = {
      "sender_id": _userId,
      "sender_role": _userRole,
      "sender_name": _userName,
      "receiver_id": receiverIdStr,
      "receiver_role": _selectedTargetRole,
      "type": _selectedNotiType,
      "title": _titleController.text.trim(),
      "content": _contentController.text.trim()
    };

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/notifications/send'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload),
      ).timeout(const Duration(seconds: 15));

      if (mounted) Navigator.pop(context);

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_success"]!), backgroundColor: Colors.green));
        _titleController.clear();
        _contentController.clear();
        _receiverIdController.clear();
        await _fetchSent();
      } else {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_fail"]!), backgroundColor: Colors.red));
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_err_conn"]!), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: Text("📨 ${labels['title']}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          backgroundColor: Colors.blueAccent,
          foregroundColor: Colors.white,
          bottom: TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            indicatorWeight: 3,
            tabs: [
              Tab(icon: const Icon(Icons.inbox), text: labels["tab_inbox"]),
              Tab(icon: const Icon(Icons.edit_note), text: labels["tab_compose"]),
              Tab(icon: const Icon(Icons.send), text: labels["tab_sent"]),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _buildInboxTab(labels),
                  _buildComposeTab(labels),
                  _buildSentTab(labels),
                ],
              ),
      ),
    );
  }

  Widget _buildInboxTab(Map<String, String> labels) {
    if (_inboxNotis.isEmpty) {
      return RefreshIndicator(
        onRefresh: _initData,
        child: ListView(children: [const SizedBox(height: 200), Center(child: Text(labels["empty_inbox"]!))]),
      );
    }

    return RefreshIndicator(
      onRefresh: _initData,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _inboxNotis.length,
        itemBuilder: (context, index) {
          final noti = _inboxNotis[index];
          bool isRead = noti['is_read'] ?? false;
          String rawTime = noti['created_at'] ?? '';
          String timeStr = rawTime.length >= 16 ? rawTime.substring(0, 16).replaceAll('T', ' ') : "";
          String roleDisplay = labels["role_${noti['sender_role']}"] ?? noti['sender_role'];

          return Card(
            elevation: isRead ? 1 : 3,
            color: isRead ? Colors.white : Colors.blue[50],
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12), 
              side: isRead ? BorderSide.none : const BorderSide(color: Colors.blueAccent, width: 1)
            ),
            child: ExpansionTile(
              leading: CircleAvatar(
                backgroundColor: isRead ? Colors.grey[400] : Colors.blueAccent,
                child: Icon(isRead ? Icons.drafts : Icons.mark_email_unread, color: Colors.white, size: 20),
              ),
              title: Text(
                noti['title'] ?? labels['no_title']!,
                style: TextStyle(fontWeight: isRead ? FontWeight.normal : FontWeight.bold, fontSize: 15),
              ),
              subtitle: Text("${labels['from']} ${noti['sender_name']} ($roleDisplay)\n$timeStr", style: const TextStyle(fontSize: 12)),
              childrenPadding: const EdgeInsets.all(16),
              expandedAlignment: Alignment.topLeft,
              onExpansionChanged: (expanded) {
                if (expanded && !isRead) _markAsRead(noti['id']);
              },
              children: [
                const Divider(),
                Text(noti['content'] ?? '', style: const TextStyle(fontSize: 15, height: 1.4)),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildComposeTab(Map<String, String> labels) {
    final allowedTargets = _rbacMatrix[_userRole] ?? [];

    if (allowedTargets.isEmpty) {
      return Center(child: Text(labels["no_permission"]!));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Card(
        color: Colors.white,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(labels["lbl_target"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 5),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(border: Border.all(color: Colors.grey), borderRadius: BorderRadius.circular(8)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedTargetRole,
                    items: allowedTargets.map((r) => DropdownMenuItem(value: r, child: Text(labels["role_$r"] ?? r))).toList(),
                    onChanged: (val) => setState(() => _selectedTargetRole = val),
                  ),
                ),
              ),
              const SizedBox(height: 15),

              Text(labels["lbl_type"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 5),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(border: Border.all(color: Colors.grey), borderRadius: BorderRadius.circular(8)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedNotiType,
                    items: ["message", "schedule", "finance", "request", "system"]
                        .map((type) => DropdownMenuItem(value: type, child: Text(labels["type_$type"] ?? type))).toList(),
                    onChanged: (val) => setState(() => _selectedNotiType = val!),
                  ),
                ),
              ),
              const SizedBox(height: 15),

              if (_userRole == 'admin' || _userRole == 'operator') ...[
                TextField(
                  controller: _receiverIdController,
                  decoration: InputDecoration(labelText: labels["lbl_receiver_id"], border: const OutlineInputBorder()),
                ),
                const SizedBox(height: 15),
              ] else ...[
                Text("${labels['lbl_all_info']} ${labels['role_$_selectedTargetRole'] ?? _selectedTargetRole}", style: const TextStyle(color: Colors.blue, fontStyle: FontStyle.italic)),
                const SizedBox(height: 15),
              ],

              TextField(
                controller: _titleController,
                decoration: InputDecoration(labelText: labels["lbl_title_field"], border: const OutlineInputBorder()),
              ),
              const SizedBox(height: 15),

              TextField(
                controller: _contentController,
                maxLines: 5,
                decoration: InputDecoration(labelText: labels["lbl_content_field"], border: const OutlineInputBorder(), alignLabelWithHint: true),
              ),
              const SizedBox(height: 20),

              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.send),
                  label: Text(labels["btn_send"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                  onPressed: _sendNotification,
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSentTab(Map<String, String> labels) {
    if (_sentNotis.isEmpty) {
      return RefreshIndicator(
        onRefresh: _initData,
        child: ListView(children: [const SizedBox(height: 200), Center(child: Text(labels["empty_sent"]!))]),
      );
    }

    return RefreshIndicator(
      onRefresh: _initData,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _sentNotis.length,
        itemBuilder: (context, index) {
          final noti = _sentNotis[index];
          String rawTime = noti['created_at'] ?? '';
          String timeStr = rawTime.length >= 16 ? rawTime.substring(0, 16).replaceAll('T', ' ') : "";
          
          String targetRoleRaw = noti['receiver_role'] ?? '';
          String targetDisplay = labels["role_$targetRoleRaw"] ?? targetRoleRaw.toUpperCase();

          return Card(
            elevation: 2,
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(noti['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 8),
                  Text(noti['content'] ?? '', style: const TextStyle(fontSize: 14)),
                  const Divider(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("📩 ${labels['to']} $targetDisplay", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                      Text("🕒 $timeStr", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                    ],
                  )
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}