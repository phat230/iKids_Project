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
  String _lang = "vi"; // Ngôn ngữ mặc định

  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController();
  bool _isEditingProfile = false;
  bool _isLoadingProfile = true;

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "greeting": "Xin chào",
      "balance": "Số dư ví:",
      "utilities": "Tiện ích cho Phụ huynh",
      "developing": "Tính năng đang phát triển",
      "menu_result": "Điểm số",
      "menu_schedule": "Lịch & Đăng ký",
      "menu_finance": "Học phí & Ví",
      "menu_child": "Quản lý con em",
      "menu_store": "Cửa hàng",
      "menu_leave": "Xin phép nghỉ",
      "menu_memory": "Góc kỷ niệm",
      "tab_home": "Trang chủ",
      "tab_noti": "Thông báo",
      "tab_prof": "Cá nhân",
      "prof_name": "Họ và tên (*)",
      "prof_phone": "Số điện thoại",
      "btn_cancel": "Hủy",
      "btn_save": "Lưu",
      "btn_edit": "Chỉnh sửa",
      "lbl_not_updated": "Chưa cập nhật",
      "msg_success": "Cập nhật thành công!",
      "msg_err": "Lỗi kết nối!",
      "btn_pwd": "Đổi mật khẩu",
      "btn_logout": "Đăng xuất",
      "pwd_title": "Đổi Mật Khẩu",
      "pwd_old": "Mật khẩu hiện tại",
      "pwd_new": "Mật khẩu mới",
      "pwd_confirm": "Xác nhận mật khẩu mới",
      "pwd_err_empty": "Vui lòng điền đủ thông tin!",
      "pwd_err_match": "Mật khẩu xác nhận không khớp!",
      "pwd_success": "Đổi mật khẩu thành công!",
    },
    "en": {
      "greeting": "Hello",
      "balance": "Wallet Balance:",
      "utilities": "Parent Utilities",
      "developing": "Feature in development",
      "menu_result": "Results",
      "menu_schedule": "Schedule & Enroll",
      "menu_finance": "Tuition & Wallet",
      "menu_child": "Manage Children",
      "menu_store": "Store",
      "menu_leave": "Leave Request",
      "menu_memory": "Memories",
      "tab_home": "Home",
      "tab_noti": "Inbox",
      "tab_prof": "Profile",
      "prof_name": "Full Name (*)",
      "prof_phone": "Phone Number",
      "btn_cancel": "Cancel",
      "btn_save": "Save",
      "btn_edit": "Edit",
      "lbl_not_updated": "Not updated",
      "msg_success": "Updated successfully!",
      "msg_err": "Connection error!",
      "btn_pwd": "Change Password",
      "btn_logout": "Logout",
      "pwd_title": "Change Password",
      "pwd_old": "Current Password",
      "pwd_new": "New Password",
      "pwd_confirm": "Confirm New Password",
      "pwd_err_empty": "Please fill in all fields!",
      "pwd_err_match": "Passwords do not match!",
      "pwd_success": "Password changed successfully!",
    }
  };

  // ĐÃ SỬA: Biến Menu thành Getter động để tự dịch khi đổi ngôn ngữ
  List<Map<String, dynamic>> get _menuItems {
    final labels = _locales[_lang]!;
    return [
      {"title": labels["menu_result"], "icon": Icons.analytics, "color": Colors.amber, "screen": const ParentResultScreen()},
      {"title": labels["menu_schedule"], "icon": Icons.calendar_today, "color": Colors.blue, "screen": const EnrollClassScreen()},
      {"title": labels["menu_finance"], "icon": Icons.account_balance_wallet, "color": Colors.green, "screen": const ParentDepositScreen()},
      {"title": labels["menu_child"], "icon": Icons.family_restroom, "color": Colors.teal, "screen": const ParentChildManagementScreen()},
      {"title": labels["menu_store"], "icon": Icons.storefront, "color": Colors.purple, "screen": const ParentShopScreen()},
      {"title": labels["menu_leave"], "icon": Icons.edit_document, "color": Colors.redAccent, "screen": const ParentContactScreen()},
      {"title": labels["menu_memory"], "icon": Icons.photo_library, "color": Colors.pink, "screen": const ParentMemoriesScreen()},
    ];
  }

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    // ✅ ĐỌC NGÔN NGỮ TỪ BỘ NHỚ LÚC KHỞI TẠO
    String? savedLang = await _storage.read(key: 'app_lang');
    if (savedLang != null) setState(() => _lang = savedLang);
    await _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    try {
      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final decoded = jsonDecode(userInfo);
        _userId = decoded["id"]?.toString() ?? decoded["_id"]?.toString() ?? "";
        
        setState(() {
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? "Parent";
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
    final labels = _locales[_lang]!;
    if (_nameController.text.trim().isEmpty) return;
    setState(() => _isLoadingProfile = true);
    var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/profile/update/$_userId'));
    request.fields['full_name'] = _nameController.text.trim();
    try {
      var response = await request.send();
      if (response.statusCode == 200) {
        String? userInfoStr = await _storage.read(key: 'user_info');
        if (userInfoStr != null) {
          Map<String, dynamic> userInfo = jsonDecode(userInfoStr);
          userInfo['full_name'] = _nameController.text.trim();
          userInfo['phone_number'] = _phoneController.text.trim();
          await _storage.write(key: 'user_info', value: jsonEncode(userInfo));
        }
        setState(() => _isEditingProfile = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_success"]!), backgroundColor: Colors.green));
      }
    } catch(e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_err"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoadingProfile = false);
    }
  }

  // ================= BỔ SUNG: HỘP THOẠI ĐỔI MẬT KHẨU =================
  void _showChangePasswordDialog() {
    final labels = _locales[_lang]!;
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
              title: Row(
                children: [
                  const Icon(Icons.lock_reset, color: Colors.orange),
                  const SizedBox(width: 10),
                  Text(labels["pwd_title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(controller: oldPassCtrl, decoration: InputDecoration(labelText: labels["pwd_old"]), obscureText: true),
                    const SizedBox(height: 10),
                    TextField(controller: newPassCtrl, decoration: InputDecoration(labelText: labels["pwd_new"]), obscureText: true),
                    const SizedBox(height: 10),
                    TextField(controller: confirmPassCtrl, decoration: InputDecoration(labelText: labels["pwd_confirm"]), obscureText: true),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: isChanging ? null : () => Navigator.pop(dialogContext),
                  child: Text(labels["btn_cancel"]!, style: const TextStyle(color: Colors.grey)),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                  onPressed: isChanging ? null : () async {
                    if (oldPassCtrl.text.isEmpty || newPassCtrl.text.isEmpty || confirmPassCtrl.text.isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["pwd_err_empty"]!), backgroundColor: Colors.red));
                      return;
                    }
                    if (newPassCtrl.text != confirmPassCtrl.text) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["pwd_err_match"]!), backgroundColor: Colors.red));
                      return;
                    }

                    setStateDialog(() => isChanging = true);
                    try {
                      bool success = await _apiService.changePassword(oldPassCtrl.text, newPassCtrl.text);
                      if (success) {
                        if (mounted) Navigator.pop(dialogContext);
                        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["pwd_success"]!), backgroundColor: Colors.green));
                      }
                    } catch (e) {
                      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst("Exception: ", "")), backgroundColor: Colors.red));
                      setStateDialog(() => isChanging = false);
                    }
                  },
                  child: isChanging 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) 
                    : Text(labels["btn_save"]!),
                ),
              ],
            );
          }
        );
      }
    );
  }
  // ====================================================================

  Widget _buildHomeTab(Map<String, String> labels) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.only(top: 30, bottom: 20, left: 20, right: 20),
          decoration: const BoxDecoration(
            color: Colors.green,
            borderRadius: BorderRadius.only(bottomLeft: Radius.circular(30), bottomRight: Radius.circular(30)),
            boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 10, offset: Offset(0, 5))]
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("${labels['greeting']}, ${_nameController.text.split(' ').last}! 👨‍👩‍👧", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
                    const SizedBox(height: 5),
                    Text("${labels['balance']} ${_userBalance.toStringAsFixed(0)} VNĐ", style: const TextStyle(fontSize: 16, color: Colors.yellowAccent, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              // Nút chuyển đổi đa ngôn ngữ đồng bộ
              GestureDetector(
                onTap: () async {
                  setState(() => _lang = _lang == "vi" ? "en" : "vi");
                  await _storage.write(key: 'app_lang', value: _lang);
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(20), border: Border.all(color: Colors.white.withOpacity(0.5))),
                  child: Row(
                    children: [
                      const Icon(Icons.language, color: Colors.white, size: 16),
                      const SizedBox(width: 6),
                      Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                    ],
                  ),
                ),
              )
            ],
          ),
        ),
        const SizedBox(height: 15),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Text(labels["utilities"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
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
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["developing"]!)));
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
                      Text(item['title'], textAlign: TextAlign.center, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: item['color'])),
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

  Widget _buildProfileTab(Map<String, String> labels) {
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
                      TextField(controller: _nameController, decoration: InputDecoration(labelText: labels["prof_name"])),
                      TextField(controller: _phoneController, decoration: InputDecoration(labelText: labels["prof_phone"])),
                      const SizedBox(height: 25),
                      Row(
                        children: [
                          Expanded(child: OutlinedButton(onPressed: () => setState(() => _isEditingProfile = false), child: Text(labels["btn_cancel"]!))),
                          const SizedBox(width: 10),
                          Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white), onPressed: _updateProfile, child: Text(labels["btn_save"]!))),
                        ],
                      ),
                    ],
                  )
                : Column(
                    children: [
                      ListTile(leading: const Icon(Icons.person, color: Colors.green), title: Text(_nameController.text.isEmpty ? labels["lbl_not_updated"]! : _nameController.text, style: const TextStyle(fontWeight: FontWeight.bold))),
                      const Divider(height: 1),
                      ListTile(leading: const Icon(Icons.phone, color: Colors.green), title: Text(_phoneController.text.isEmpty ? labels["lbl_not_updated"]! : _phoneController.text)),
                      const SizedBox(height: 20),
                      SizedBox(width: double.infinity, child: OutlinedButton.icon(style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.green)), onPressed: () => setState(() => _isEditingProfile = true), icon: const Icon(Icons.edit, color: Colors.green), label: Text(labels["btn_edit"]!, style: const TextStyle(color: Colors.green)))),
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
                  title: Text(labels["btn_pwd"]!),
                  trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                  onTap: _showChangePasswordDialog,
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.red),
                  title: Text(labels["btn_logout"]!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
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
    final labels = _locales[_lang]!;
    final List<Widget> tabs = [_buildHomeTab(labels), const NotificationScreen(), _buildProfileTab(labels)];
    
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(child: tabs[_selectedIndex]),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.green,
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.home), label: labels["tab_home"]),
          BottomNavigationBarItem(icon: const Icon(Icons.notifications), label: labels["tab_noti"]),
          BottomNavigationBarItem(icon: const Icon(Icons.person), label: labels["tab_prof"]),
        ],
      ),
    );
  }
}