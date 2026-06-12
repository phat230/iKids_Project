import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../services/api_service.dart';
import '../../core/config.dart';
import '../notification/notification_screen.dart';

// --- IMPORT TẤT CẢ CÁC MÀN HÌNH CỦA PHỤ HUYNH CHÚNG TA ĐÃ TẠO ---
import 'parent_result_screen.dart';
import 'enroll_class_screen.dart';
import 'parent_shop_screen.dart';
import 'parent_contact_screen.dart';
import 'parent_deposit_screen.dart';
import 'parent_memories_screen.dart';
import 'parent_child_management_screen.dart';

class ParentDashboard extends StatefulWidget {
  const ParentDashboard({super.key});

  @override
  State<ParentDashboard> createState() => _ParentDashboardState();
}

class _ParentDashboardState extends State<ParentDashboard> {
  int _selectedIndex = 0;
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage(); 
  
  String _userId = "";
  double _userBalance = 0;

  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController();
  bool _isEditingProfile = false;
  bool _isLoadingProfile = true;

  // ĐÃ LIÊN KẾT ĐẦY ĐỦ TẤT CẢ 7 MÀN HÌNH VÀO MENU
  final List<Map<String, dynamic>> _menuItems = [
    {"title": "Điểm số", "icon": Icons.analytics, "color": Colors.amber, "screen": const ParentResultScreen()},
    {"title": "Lịch & Đăng ký", "icon": Icons.calendar_today, "color": Colors.blue, "screen": const EnrollClassScreen()},
    {"title": "Học phí & Ví", "icon": Icons.account_balance_wallet, "color": Colors.green, "screen": const ParentDepositScreen()},
    {"title": "Quản lý con em", "icon": Icons.family_restroom, "color": Colors.teal, "screen": const ParentChildManagementScreen()},
    {"title": "Cửa hàng", "icon": Icons.storefront, "color": Colors.purple, "screen": const ParentShopScreen()},
    {"title": "Xin phép nghỉ", "icon": Icons.edit_document, "color": Colors.redAccent, "screen": const ParentContactScreen()},
    {"title": "Góc kỷ niệm", "icon": Icons.photo_library, "color": Colors.pink, "screen": const ParentMemoriesScreen()},
  ];

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    try {
      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final decoded = jsonDecode(userInfo);
        _userId = decoded["id"]?.toString() ?? decoded["_id"]?.toString() ?? "";
        
        setState(() {
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? "Phụ huynh iKids";
          _phoneController.text = decoded["phone_number"] ?? decoded["phone"] ?? "";
          _bioController.text = decoded["bio"] ?? "";
        });

        if (_userId.isNotEmpty) {
          final res = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/gamification/profile/$_userId'));
          if (res.statusCode == 200) {
            setState(() => _userBalance = (jsonDecode(res.body)['balance'] ?? 0).toDouble());
          }
        }
      }
    } catch (e) {
      debugPrint("Lỗi load profile: $e");
    } finally {
      if (mounted) setState(() => _isLoadingProfile = false);
    }
  }

  Future<void> _handleLogout() async {
    await _storage.deleteAll();
    await _apiService.logout();
    if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
  }

  void _updateProfile() async {
    if (_nameController.text.trim().isEmpty) return;
    setState(() => _isLoadingProfile = true);
    var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/profile/update/$_userId'));
    request.fields['full_name'] = _nameController.text.trim();
    try {
      var response = await request.send();
      if (response.statusCode == 200) {
        // Cập nhật lại Cache cục bộ để hiển thị ngay
        String? userInfoStr = await _storage.read(key: 'user_info');
        if (userInfoStr != null) {
          Map<String, dynamic> userInfo = jsonDecode(userInfoStr);
          userInfo['full_name'] = _nameController.text.trim();
          userInfo['phone_number'] = _phoneController.text.trim();
          await _storage.write(key: 'user_info', value: jsonEncode(userInfo));
        }
        setState(() => _isEditingProfile = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Cập nhật thành công!"), backgroundColor: Colors.green));
      }
    } catch(e) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi kết nối!"), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoadingProfile = false);
    }
  }

  // ================= BỔ SUNG: HỘP THOẠI ĐỔI MẬT KHẨU =================
  void _showChangePasswordDialog() {
    final oldPassCtrl = TextEditingController();
    final newPassCtrl = TextEditingController();
    final confirmPassCtrl = TextEditingController();
    bool isChanging = false;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              title: const Row(
                children: [
                  Icon(Icons.lock_reset, color: Colors.orange),
                  SizedBox(width: 10),
                  Text("Đổi Mật Khẩu", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(controller: oldPassCtrl, decoration: const InputDecoration(labelText: "Mật khẩu hiện tại"), obscureText: true),
                    const SizedBox(height: 10),
                    TextField(controller: newPassCtrl, decoration: const InputDecoration(labelText: "Mật khẩu mới"), obscureText: true),
                    const SizedBox(height: 10),
                    TextField(controller: confirmPassCtrl, decoration: const InputDecoration(labelText: "Xác nhận mật khẩu mới"), obscureText: true),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: isChanging ? null : () => Navigator.pop(dialogContext),
                  child: const Text("Hủy", style: TextStyle(color: Colors.grey)),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                  onPressed: isChanging ? null : () async {
                    if (oldPassCtrl.text.isEmpty || newPassCtrl.text.isEmpty || confirmPassCtrl.text.isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng điền đủ thông tin!"), backgroundColor: Colors.red));
                      return;
                    }
                    if (newPassCtrl.text != confirmPassCtrl.text) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Mật khẩu xác nhận không khớp!"), backgroundColor: Colors.red));
                      return;
                    }

                    setStateDialog(() => isChanging = true);
                    try {
                      bool success = await _apiService.changePassword(oldPassCtrl.text, newPassCtrl.text);
                      if (success) {
                        if (mounted) Navigator.pop(dialogContext);
                        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đổi mật khẩu thành công!"), backgroundColor: Colors.green));
                      }
                    } catch (e) {
                      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst("Exception: ", "")), backgroundColor: Colors.red));
                      setStateDialog(() => isChanging = false);
                    }
                  },
                  child: isChanging 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) 
                    : const Text("Xác nhận"),
                ),
              ],
            );
          }
        );
      }
    );
  }
  // ====================================================================

  Widget _buildHomeTab() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: const BoxDecoration(
            color: Colors.green,
            borderRadius: BorderRadius.only(bottomLeft: Radius.circular(30), bottomRight: Radius.circular(30)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Xin chào, ${_nameController.text.split(' ').last}! 👨‍👩‍👧", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 5),
              Text("Số dư ví: ${_userBalance.toStringAsFixed(0)} VNĐ", style: const TextStyle(fontSize: 16, color: Colors.yellowAccent, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        const SizedBox(height: 15),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 20),
          child: Text("Tiện ích cho Phụ huynh", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ),
        Expanded(
          child: GridView.builder(
            padding: const EdgeInsets.all(20),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, crossAxisSpacing: 15, mainAxisSpacing: 15, childAspectRatio: 1.15),
            itemCount: _menuItems.length,
            itemBuilder: (context, index) {
              final item = _menuItems[index];
              return InkWell(
                onTap: () {
                  if (item['screen'] != null) {
                    Navigator.push(context, MaterialPageRoute(builder: (_) => item['screen']));
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Tính năng đang phát triển")));
                  }
                },
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  decoration: BoxDecoration(
                    color: item['color'].withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: item['color'].withOpacity(0.3), width: 2),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(item['icon'], size: 45, color: item['color']),
                      const SizedBox(height: 8),
                      Text(item['title'], style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: item['color'])),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildProfileTab() {
    if (_isLoadingProfile) return const Center(child: CircularProgressIndicator());
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const CircleAvatar(radius: 50, backgroundColor: Colors.green, child: Icon(Icons.person, size: 60, color: Colors.white)),
          const SizedBox(height: 25),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(15),
              boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 10, offset: Offset(0, 5))]
            ),
            child: _isEditingProfile
                ? Column(
                    children: [
                      TextField(controller: _nameController, decoration: const InputDecoration(labelText: "Họ và tên (*)")),
                      TextField(controller: _phoneController, decoration: const InputDecoration(labelText: "Số điện thoại")),
                      const SizedBox(height: 25),
                      Row(
                        children: [
                          Expanded(child: OutlinedButton(onPressed: () => setState(() => _isEditingProfile = false), child: const Text("Hủy"))),
                          const SizedBox(width: 10),
                          Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white), onPressed: _updateProfile, child: const Text("Lưu"))),
                        ],
                      ),
                    ],
                  )
                : Column(
                    children: [
                      ListTile(leading: const Icon(Icons.person, color: Colors.green), title: Text(_nameController.text.isEmpty ? "Chưa cập nhật" : _nameController.text, style: const TextStyle(fontWeight: FontWeight.bold))),
                      const Divider(height: 1),
                      ListTile(leading: const Icon(Icons.phone, color: Colors.green), title: Text(_phoneController.text.isEmpty ? "Chưa cập nhật" : _phoneController.text)),
                      const SizedBox(height: 20),
                      SizedBox(width: double.infinity, child: OutlinedButton.icon(style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.green)), onPressed: () => setState(() => _isEditingProfile = true), icon: const Icon(Icons.edit, color: Colors.green), label: const Text("Chỉnh sửa", style: TextStyle(color: Colors.green)))),
                    ],
                  ),
          ),
          const SizedBox(height: 20),
          
          // --- DANH SÁCH CÁC THIẾT LẬP HỆ THỐNG ---
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.lock, color: Colors.orange),
                  title: const Text("Đổi mật khẩu"),
                  trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                  onTap: _showChangePasswordDialog,
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.red),
                  title: const Text("Đăng xuất", style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                  onTap: _handleLogout,
                ),
              ],
            ),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> tabs = [_buildHomeTab(), const NotificationScreen(), _buildProfileTab()];
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(child: tabs[_selectedIndex]),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.green,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: "Trang chủ"),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: "Thông báo"),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: "Cá nhân"),
        ],
      ),
    );
  }
}