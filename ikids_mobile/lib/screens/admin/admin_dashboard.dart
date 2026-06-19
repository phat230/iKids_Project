import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';
import '../notification/notification_screen.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  final _storage = const FlutterSecureStorage();
  int _selectedIndex = 0;
  bool _isLoading = true;
  String _lang = "vi"; // Mặc định, sẽ bị ghi đè bởi cấu hình hệ thống
  String _token = "";

  List<dynamic> _pendingRequests = [];
  List<dynamic> _historyRequests = [];
  List<dynamic> _depositIssues = [];

  // ================= BỘ TỪ ĐIỂN SONG NGỮ HOÀN CHỈNH =================
  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Bảng Điều Khiển Quản Trị",
      "metric_tv1_pending": "ĐƠN CHỜ DUYỆT (TV1)",
      "metric_tv1_today": "CA DẠY HÔM NAY",
      "metric_tv2_logs": "NHẬT KÝ ĐÃ NỘP",
      "metric_tv3_issues": "SỰ CỐ NẠP (TV3)",
      "sub_tv1_pending": "Yêu cầu từ Giáo viên",
      "sub_tv1_history": "Lịch sử xét duyệt",
      "sub_tv3": "Sự cố nạp tiền từ Phụ huynh",
      "no_requests": "Không có yêu cầu nào.",
      "no_deposits": "Không có sự cố nạp tiền.",
      "btn_approve": "Duyệt",
      "btn_reject": "Từ chối",
      "btn_check": "Kiểm tra",
      "msg_success": "Thao tác thành công!",
      "msg_error": "Có lỗi xảy ra, thử lại sau.",
      "lbl_reason": "Lý do",
      "lbl_detail": "Chi tiết",
      "lbl_logout": "Đăng xuất tài khoản",
      "sys_management": "QUẢN TRỊ HỆ THỐNG",
      "sys_staff": "Quản lý Nhân sự & Phân quyền",
      "sys_tools": "CÔNG CỤ VẬN HÀNH",
      "sys_class": "Quản lý Lớp học",
      "sys_schedule": "Xếp lịch học",
      "sys_finance": "Quản lý Tài chính & Giao dịch",
      "sys_store": "Quản lý Cửa hàng iKids",
      "tab_home": "Dashboard",
      "tab_noti": "Thông báo",
      "tab_sys": "Chức năng",
    },
    "en": {
      "title": "Admin Dashboard",
      "metric_tv1_pending": "PENDING REQUESTS (TV1)",
      "metric_tv1_today": "CLASSES TODAY",
      "metric_tv2_logs": "JOURNALS SUBMITTED",
      "metric_tv3_issues": "DEPOSIT ISSUES (TV3)",
      "sub_tv1_pending": "Teacher Requests",
      "sub_tv1_history": "Approval History",
      "sub_tv3": "Parent Deposit Issues",
      "no_requests": "No pending requests.",
      "no_deposits": "No deposit issues.",
      "btn_approve": "Approve",
      "btn_reject": "Reject",
      "btn_check": "Check",
      "msg_success": "Operation successful!",
      "msg_error": "Error occurred, try again.",
      "lbl_reason": "Reason",
      "lbl_detail": "Details",
      "lbl_logout": "Logout Account",
      "sys_management": "SYSTEM MANAGEMENT",
      "sys_staff": "Staff & Role Management",
      "sys_tools": "OPERATIONAL TOOLS",
      "sys_class": "Class Management",
      "sys_schedule": "Scheduling",
      "sys_finance": "Finance & Transactions",
      "sys_store": "iKids Store Management",
      "tab_home": "Dashboard",
      "tab_noti": "Inbox",
      "tab_sys": "Settings",
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchDashboardData();
  }

  Future<void> _fetchDashboardData() async {
    setState(() => _isLoading = true);
    try {
      // ✅ ĐỌC NGÔN NGỮ TỪ BỘ NHỚ LÚC KHỞI TẠO
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      _token = await _storage.read(key: 'jwt_token') ?? "";
      final headers = {"Authorization": "Bearer $_token"};

      final resPending = http.get(Uri.parse('${AppConfig.apiTv1}/pending-requests'), headers: headers);
      final resHistory = http.get(Uri.parse('${AppConfig.apiTv1}/request-history'), headers: headers);
      final resDeposit = http.get(Uri.parse('${AppConfig.apiTv3}/admin/deposit-issues'), headers: headers);

      final responses = await Future.wait([resPending, resHistory, resDeposit]);

      setState(() {
        _pendingRequests = responses[0].statusCode == 200 ? jsonDecode(utf8.decode(responses[0].bodyBytes)) : [];
        _historyRequests = responses[1].statusCode == 200 ? jsonDecode(utf8.decode(responses[1].bodyBytes)) : [];
        _depositIssues = responses[2].statusCode == 200 ? jsonDecode(utf8.decode(responses[2].bodyBytes)) : [];
      });
    } catch (e) {
      debugPrint("Lỗi tải Dashboard: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleTV1Request(String reqId, String action) async {
    try {
      final res = await http.post(
        Uri.parse('${AppConfig.apiTv1}/requests/$action/$reqId'),
        headers: {"Authorization": "Bearer $_token"}
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['msg_success']!), backgroundColor: Colors.green));
        _fetchDashboardData();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['msg_error']!), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['msg_error']!), backgroundColor: Colors.red));
    }
  }

  Future<void> _resolveDeposit(String issueId) async {
    try {
      final res = await http.post(
        Uri.parse('${AppConfig.apiTv3}/admin/resolve-deposit/$issueId'),
        headers: {"Authorization": "Bearer $_token"}
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['msg_success']!), backgroundColor: Colors.green));
        _fetchDashboardData();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['msg_error']!), backgroundColor: Colors.red));
    }
  }

  Future<void> _handleLogout() async {
    await _storage.deleteAll();
    if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
  }

  // --- UI COMPONENTS ---
  Widget _buildMetricCard(String title, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.5), width: 1.5),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4)]
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 5),
          Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildHomeTab() {
    final labels = _labels[_lang]!;
    
    return RefreshIndicator(
      onRefresh: _fetchDashboardData,
      color: Colors.redAccent,
      child: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.redAccent))
        : SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            physics: const AlwaysScrollableScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. CHỈ SỐ TỔNG QUAN
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: 1.8,
                  children: [
                    _buildMetricCard(labels["metric_tv1_pending"]!, "${_pendingRequests.length}", Colors.red),
                    _buildMetricCard(labels["metric_tv1_today"]!, "--", Colors.green),
                    _buildMetricCard(labels["metric_tv2_logs"]!, "--", Colors.orange),
                    _buildMetricCard(labels["metric_tv3_issues"]!, "${_depositIssues.length}", Colors.blue),
                  ],
                ),
                
                const SizedBox(height: 30),
                
                // 2. YÊU CẦU TV1 ĐANG CHỜ
                Text(labels["sub_tv1_pending"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.redAccent)),
                const SizedBox(height: 10),
                _pendingRequests.isEmpty 
                  ? Container(padding: const EdgeInsets.all(15), decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10)), child: Text(labels["no_requests"]!))
                  : ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: _pendingRequests.length,
                      itemBuilder: (context, index) {
                        final req = _pendingRequests[index];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 10),
                          child: Padding(
                            padding: const EdgeInsets.all(15),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text("${req['type'] ?? 'Yêu cầu'} - GV: ${req['teacher_name'] ?? 'Unknown'}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                const SizedBox(height: 5),
                                Text("${labels['lbl_detail']}: ${req['details'] ?? req['class_name'] ?? ''}", style: const TextStyle(color: Colors.grey)),
                                Text("${labels['lbl_reason']}: ${req['reason'] ?? ''}"),
                                const SizedBox(height: 10),
                                Row(
                                  children: [
                                    Expanded(child: OutlinedButton(style: OutlinedButton.styleFrom(foregroundColor: Colors.red, side: const BorderSide(color: Colors.red)), onPressed: () => _handleTV1Request(req['id'] ?? req['_id'], 'reject'), child: Text(labels['btn_reject']!))),
                                    const SizedBox(width: 10),
                                    Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white), onPressed: () => _handleTV1Request(req['id'] ?? req['_id'], 'approve'), child: Text(labels['btn_approve']!))),
                                  ],
                                )
                              ],
                            ),
                          ),
                        );
                      },
                    ),

                const SizedBox(height: 30),

                // 3. SỰ CỐ NẠP TIỀN TV3
                Text(labels["sub_tv3"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueAccent)),
                const SizedBox(height: 10),
                _depositIssues.isEmpty 
                  ? Container(padding: const EdgeInsets.all(15), decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10)), child: Text(labels["no_deposits"]!))
                  : ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: _depositIssues.length,
                      itemBuilder: (context, index) {
                        final issue = _depositIssues[index];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 10),
                          child: ListTile(
                            leading: const CircleAvatar(backgroundColor: Colors.blue, child: Icon(Icons.warning, color: Colors.white)),
                            title: Text("${issue['amount'] ?? 0} VNĐ", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
                            subtitle: Text("${labels['lbl_reason']}: ${issue['content']}"),
                            trailing: ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.blue, foregroundColor: Colors.white),
                              onPressed: () => _resolveDeposit(issue['id'] ?? issue['_id']),
                              child: Text(labels['btn_approve']!),
                            ),
                          ),
                        );
                      },
                    ),
                    
                const SizedBox(height: 30),

                // 4. LỊCH SỬ XÉT DUYỆT
                ExpansionTile(
                  title: Text(labels["sub_tv1_history"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
                  collapsedBackgroundColor: Colors.white,
                  backgroundColor: Colors.white,
                  children: _historyRequests.take(5).map((h) {
                    bool isApproved = h['status'] == 'approved';
                    return ListTile(
                      leading: Icon(isApproved ? Icons.check_circle : Icons.cancel, color: isApproved ? Colors.green : Colors.red),
                      title: Text("${h['type']} - GV: ${h['teacher_name']}", style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                      subtitle: Text(h['details'] ?? h['class_name'] ?? '', style: const TextStyle(fontSize: 12)),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
    );
  }

  // --- MENU ĐIỀU KHIỂN HỆ THỐNG CHO ADMIN ---
  Widget _buildSystemTab() {
    final labels = _labels[_lang]!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(labels["sys_management"]!, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.redAccent)),
        const SizedBox(height: 10),
        _buildMenuCard(labels["sys_staff"]!, Icons.admin_panel_settings, Colors.redAccent, () => Navigator.pushNamed(context, '/admin-staff')),
        
        const SizedBox(height: 25),
        Text(labels["sys_tools"]!, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.blueAccent)),
        const SizedBox(height: 10),
        _buildMenuCard(labels["sys_class"]!, Icons.class_, Colors.indigo, () => Navigator.pushNamed(context, '/operator-class')),
        _buildMenuCard(labels["sys_schedule"]!, Icons.calendar_month, Colors.purple, () => Navigator.pushNamed(context, '/operator-schedule')),
        _buildMenuCard(labels["sys_finance"]!, Icons.account_balance_wallet, Colors.orange, () => Navigator.pushNamed(context, '/operator-finance')),
        _buildMenuCard(labels["sys_store"]!, Icons.store, Colors.green, () => Navigator.pushNamed(context, '/operator-store')),
        
        const SizedBox(height: 40),
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.grey[300], 
            foregroundColor: Colors.black87, 
            padding: const EdgeInsets.symmetric(vertical: 15),
            elevation: 0
          ),
          icon: const Icon(Icons.logout),
          label: Text(labels["lbl_logout"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          onPressed: _handleLogout,
        )
      ],
    );
  }

  Widget _buildMenuCard(String title, IconData icon, Color color, VoidCallback onTap) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 1,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(backgroundColor: color.withOpacity(0.15), child: Icon(icon, color: color)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey),
        onTap: onTap,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> tabs = [_buildHomeTab(), const NotificationScreen(), _buildSystemTab()];
    final labels = _labels[_lang]!;

    return Scaffold(
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold)), 
        backgroundColor: Colors.redAccent, 
        foregroundColor: Colors.white,
        actions: [
          // ✅ LƯU NGÔN NGỮ KHI CHUYỂN
          TextButton(
            onPressed: () async {
              setState(() => _lang = _lang == "vi" ? "en" : "vi");
              await _storage.write(key: 'app_lang', value: _lang);
            },
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: tabs[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.redAccent,
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.dashboard), label: labels["tab_home"]),
          BottomNavigationBarItem(icon: const Icon(Icons.notifications), label: labels["tab_noti"]),
          BottomNavigationBarItem(icon: const Icon(Icons.settings), label: labels["tab_sys"]),
        ],
      ),
    );
  }
}