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

  // Ánh xạ Quyền gửi thông báo (RBAC) giống hệt Web
  final Map<String, Map<String, String>> _roleTargetsMap = {
    "admin": {"operator": "Nhân viên vận hành", "teacher": "Giáo viên"},
    "operator": {"admin": "Ban Giám Đốc", "teacher": "Giáo viên", "student": "Học sinh", "parent": "Phụ huynh"},
    "teacher": {"operator": "Nhân viên vận hành", "student": "Học sinh", "parent": "Phụ huynh"},
    "student": {"teacher": "Giáo viên", "operator": "Nhân viên vận hành"},
    "parent": {"teacher": "Giáo viên", "operator": "Nhân viên vận hành"}
  };

  final Map<String, String> _notiTypes = {
    "message": "💬 Tin nhắn trao đổi",
    "schedule": "📅 Lịch học",
    "finance": "💰 Tài chính & Học phí",
    "request": "📝 Đơn từ & Yêu cầu",
    "system": "⚙️ Hệ thống"
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
      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final Map<String, dynamic> decodedUser = jsonDecode(userInfo);
        _userId = decodedUser["id"]?.toString() ?? decodedUser["_id"]?.toString() ?? "";
        _userRole = decodedUser["role"]?.toString().toLowerCase() ?? "student";
        _userName = decodedUser["full_name"]?.toString() ?? decodedUser["name"]?.toString() ?? "Người dùng";
        
        // Gán giá trị mặc định cho dropdown
        if (_roleTargetsMap.containsKey(_userRole) && _roleTargetsMap[_userRole]!.isNotEmpty) {
          _selectedTargetRole = _roleTargetsMap[_userRole]!.keys.first;
        }

        await Future.wait([_fetchInbox(), _fetchSent()]);
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi tải thông tin tài khoản!")));
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
    if (_titleController.text.trim().isEmpty || _contentController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng điền đủ tiêu đề và nội dung!"), backgroundColor: Colors.red));
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

      if (mounted) Navigator.pop(context); // Tắt loading

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("🎉 Gửi thông báo thành công!"), backgroundColor: Colors.green));
        _titleController.clear();
        _contentController.clear();
        _receiverIdController.clear();
        await _fetchSent(); // Cập nhật lại list đã gửi
      } else {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi gửi thông báo!"), backgroundColor: Colors.red));
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Mất kết nối mạng!"), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: const Text("📨 Hộp Thư & Thông Báo", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          backgroundColor: Colors.blueAccent,
          foregroundColor: Colors.white,
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            indicatorWeight: 3,
            tabs: [
              Tab(icon: Icon(Icons.inbox), text: "Hộp thư đến"),
              Tab(icon: Icon(Icons.edit_note), text: "Soạn tin"),
              Tab(icon: Icon(Icons.send), text: "Đã gửi"),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _buildInboxTab(),
                  _buildComposeTab(),
                  _buildSentTab(),
                ],
              ),
      ),
    );
  }

  // ==================== 1. TAB HỘP THƯ ĐẾN ====================
  Widget _buildInboxTab() {
    if (_inboxNotis.isEmpty) {
      return RefreshIndicator(
        onRefresh: _initData,
        child: ListView(children: const [SizedBox(height: 200), Center(child: Text("Hộp thư của bạn đang trống."))]),
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
                noti['title'] ?? 'Không có tiêu đề',
                style: TextStyle(fontWeight: isRead ? FontWeight.normal : FontWeight.bold, fontSize: 15),
              ),
              subtitle: Text("Từ: ${noti['sender_name']} (${noti['sender_role']})\n$timeStr", style: const TextStyle(fontSize: 12)),
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

  // ==================== 2. TAB SOẠN THÔNG BÁO ====================
  Widget _buildComposeTab() {
    final allowedTargets = _roleTargetsMap[_userRole] ?? {};

    if (allowedTargets.isEmpty) {
      return const Center(child: Text("Vai trò của bạn không có quyền gửi thông báo."));
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
              const Text("Gửi đến bộ phận:", style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 5),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(border: Border.all(color: Colors.grey), borderRadius: BorderRadius.circular(8)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedTargetRole,
                    items: allowedTargets.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList(),
                    onChanged: (val) => setState(() => _selectedTargetRole = val),
                  ),
                ),
              ),
              const SizedBox(height: 15),

              const Text("Loại thông báo:", style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 5),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(border: Border.all(color: Colors.grey), borderRadius: BorderRadius.circular(8)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedNotiType,
                    items: _notiTypes.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList(),
                    onChanged: (val) => setState(() => _selectedNotiType = val!),
                  ),
                ),
              ),
              const SizedBox(height: 15),

              if (_userRole == 'admin' || _userRole == 'operator') ...[
                TextField(
                  controller: _receiverIdController,
                  decoration: const InputDecoration(labelText: "ID Người nhận (Để trống để gửi toàn bộ)", border: OutlineInputBorder()),
                ),
                const SizedBox(height: 15),
              ] else ...[
                Text("ℹ️ Yêu cầu sẽ được gửi đến toàn bộ ${allowedTargets[_selectedTargetRole]}", style: const TextStyle(color: Colors.blue, fontStyle: FontStyle.italic)),
                const SizedBox(height: 15),
              ],

              TextField(
                controller: _titleController,
                decoration: const InputDecoration(labelText: "Tiêu đề (*)", border: OutlineInputBorder()),
              ),
              const SizedBox(height: 15),

              TextField(
                controller: _contentController,
                maxLines: 5,
                decoration: const InputDecoration(labelText: "Nội dung chi tiết (*)", border: OutlineInputBorder(), alignLabelWithHint: true),
              ),
              const SizedBox(height: 20),

              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.send),
                  label: const Text("Gửi Thông Báo", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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

  // ==================== 3. TAB ĐÃ GỬI ====================
  Widget _buildSentTab() {
    if (_sentNotis.isEmpty) {
      return RefreshIndicator(
        onRefresh: _initData,
        child: ListView(children: const [SizedBox(height: 200), Center(child: Text("Bạn chưa gửi thông báo nào."))]),
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
          String targetDisplay = _roleTargetsMap[_userRole]?[targetRoleRaw] ?? targetRoleRaw.toUpperCase();

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
                      Text("📩 Tới: $targetDisplay", style: const TextStyle(color: Colors.grey, fontSize: 12)),
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