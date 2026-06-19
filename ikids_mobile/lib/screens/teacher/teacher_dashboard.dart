import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../services/api_service.dart';
import '../../core/config.dart';
import '../notification/notification_screen.dart';

class TeacherDashboard extends StatefulWidget {
  const TeacherDashboard({super.key});

  @override
  State<TeacherDashboard> createState() => _TeacherDashboardState();
}

class _TeacherDashboardState extends State<TeacherDashboard> {
  int _selectedIndex = 0;
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage(); 
  
  String _userId = "";
  String _userRole = "teacher";
  String _lang = "vi"; // Ngôn ngữ mặc định

  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController();
  final _fbController = TextEditingController(); 
  bool _isEditingProfile = false;
  bool _isLoadingProfile = true;

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "greeting": "Chào Thầy/Cô",
      "wish": "Chúc một ngày giảng dạy tràn đầy năng lượng!",
      "operations": "Nghiệp vụ giảng dạy",
      "tab_home": "Trang chủ",
      "tab_noti": "Thông báo",
      "tab_profile": "Cá nhân",
      "menu_schedule": "Lịch dạy",
      "menu_grading": "Chấm điểm",
      "menu_ai_quiz": "Soạn Đề AI",
      "menu_assignment": "Giao bài tập",
      "menu_journal": "Nhật ký & Điểm danh",
      "prof_name": "Họ và tên (*)",
      "prof_phone": "Số điện thoại",
      "prof_fb": "Link Facebook",
      "prof_bio": "Phương châm giảng dạy",
      "btn_cancel": "Hủy",
      "btn_save": "Lưu",
      "btn_edit": "Chỉnh sửa hồ sơ",
      "btn_logout": "Đăng xuất",
      "msg_not_updated": "Chưa cập nhật",
      "msg_success": "Cập nhật thành công!",
      "msg_fail": "Lưu thất bại. Vui lòng thử lại.",
      "msg_error": "Lỗi kết nối.",
    },
    "en": {
      "greeting": "Hello",
      "wish": "Have an energetic and inspiring teaching day!",
      "operations": "Teaching Operations",
      "tab_home": "Home",
      "tab_noti": "Inbox",
      "tab_profile": "Profile",
      "menu_schedule": "Schedule",
      "menu_grading": "Grading",
      "menu_ai_quiz": "AI Quiz Maker",
      "menu_assignment": "Assignments",
      "menu_journal": "Journal & Attendance",
      "prof_name": "Full Name (*)",
      "prof_phone": "Phone Number",
      "prof_fb": "Facebook Link",
      "prof_bio": "Teaching Philosophy",
      "btn_cancel": "Cancel",
      "btn_save": "Save Changes",
      "btn_edit": "Edit Profile",
      "btn_logout": "Logout",
      "msg_not_updated": "Not updated",
      "msg_success": "Profile updated successfully!",
      "msg_fail": "Save failed. Please try again.",
      "msg_error": "Connection error.",
    }
  };

  // ✅ Khởi tạo Menu động để ngôn ngữ tự động thay đổi theo trạng thái
  List<Map<String, dynamic>> get _menuItems {
    final labels = _locales[_lang]!;
    return [
      {"title": labels["menu_schedule"], "icon": Icons.calendar_month, "color": Colors.teal},
      {"title": labels["menu_grading"], "icon": Icons.grading, "color": Colors.blue},
      {"title": labels["menu_ai_quiz"], "icon": Icons.psychology, "color": Colors.redAccent},
      {"title": labels["menu_assignment"], "icon": Icons.assignment, "color": Colors.orange},
      {"title": labels["menu_journal"], "icon": Icons.book, "color": Colors.purple}, 
    ];
  }

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    // Đọc ngôn ngữ người dùng đã chọn từ màn hình Login
    String? savedLang = await _storage.read(key: 'app_lang');
    if (savedLang != null) {
      setState(() => _lang = savedLang);
    }
    await _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    try {
      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final decoded = jsonDecode(userInfo);
        _userId = decoded["id"]?.toString() ?? decoded["_id"]?.toString() ?? "";
        
        setState(() {
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? "Teacher";
          _phoneController.text = decoded["phone_number"] ?? decoded["phone"] ?? "";
          _bioController.text = decoded["bio"] ?? "";
          _fbController.text = decoded["facebook_url"] ?? "";
        });
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
    
    try {
      String? token = await _storage.read(key: 'jwt_token');
      var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/profile/update/$_userId'));
      
      request.headers['Authorization'] = 'Bearer $token'; 
      request.fields['full_name'] = _nameController.text.trim();
      
      var response = await request.send();
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_success"]!), backgroundColor: Colors.green));
        setState(() => _isEditingProfile = false);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_fail"]!), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_error"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoadingProfile = false);
    }
  }

  // --- GIAO DIỆN TRANG CHỦ ---
  Widget _buildHomeTab(Map<String, String> labels) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.only(top: 30, bottom: 20, left: 20, right: 20),
          decoration: const BoxDecoration(
            color: Colors.teal,
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
                    Text("${labels['greeting']} ${_nameController.text.split(' ').last}! 📚", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
                    const SizedBox(height: 5),
                    Text(labels['wish']!, style: const TextStyle(fontSize: 15, color: Colors.white70)),
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
        const SizedBox(height: 20),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Text(labels["operations"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
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
                  if (index == 0) {
                    Navigator.pushNamed(context, '/teacher-schedule');
                  } else if (index == 1) {
                    Navigator.pushNamed(context, '/teacher-grading');
                  } else if (index == 2) {
                    Navigator.pushNamed(context, '/teacher-create-quiz');
                  } else if (index == 3) {
                    Navigator.pushNamed(context, '/teacher-assignment');
                  } else if (index == 4) {
                    Navigator.pushNamed(context, '/teacher-journal');
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

  // --- GIAO DIỆN TRANG CÁ NHÂN ---
  Widget _buildProfileTab(Map<String, String> labels) {
    if (_isLoadingProfile) return const Center(child: CircularProgressIndicator());
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const CircleAvatar(radius: 50, backgroundColor: Colors.teal, child: Icon(Icons.person, size: 60, color: Colors.white)),
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
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      TextField(controller: _nameController, decoration: InputDecoration(labelText: labels["prof_name"])),
                      TextField(controller: _phoneController, decoration: InputDecoration(labelText: labels["prof_phone"])),
                      TextField(controller: _fbController, decoration: InputDecoration(labelText: labels["prof_fb"])),
                      TextField(controller: _bioController, decoration: InputDecoration(labelText: labels["prof_bio"])),
                      const SizedBox(height: 25),
                      Row(
                        children: [
                          Expanded(child: OutlinedButton(onPressed: () => setState(() => _isEditingProfile = false), child: Text(labels["btn_cancel"]!))),
                          const SizedBox(width: 10),
                          Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white), onPressed: _updateProfile, child: Text(labels["btn_save"]!))),
                        ],
                      ),
                    ],
                  )
                : Column(
                    children: [
                      ListTile(leading: const Icon(Icons.person, color: Colors.teal), title: Text(_nameController.text.isEmpty ? labels["msg_not_updated"]! : _nameController.text, style: const TextStyle(fontWeight: FontWeight.bold)), subtitle: Text(labels["prof_name"]!.replaceAll(" (*)", ""))),
                      const Divider(height: 1),
                      ListTile(leading: const Icon(Icons.phone, color: Colors.green), title: Text(_phoneController.text.isEmpty ? labels["msg_not_updated"]! : _phoneController.text), subtitle: Text(labels["prof_phone"]!)),
                      const Divider(height: 1),
                      ListTile(leading: const Icon(Icons.favorite, color: Colors.redAccent), title: Text(_bioController.text.isEmpty ? labels["msg_not_updated"]! : _bioController.text), subtitle: Text(labels["prof_bio"]!)),
                      const SizedBox(height: 20),
                      SizedBox(width: double.infinity, child: OutlinedButton.icon(style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.teal)), onPressed: () => setState(() => _isEditingProfile = true), icon: const Icon(Icons.edit, color: Colors.teal), label: Text(labels["btn_edit"]!, style: const TextStyle(color: Colors.teal)))),
                    ],
                  ),
          ),
          const SizedBox(height: 20),
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            child: ListTile(leading: const Icon(Icons.logout, color: Colors.red), title: Text(labels["btn_logout"]!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)), onTap: _handleLogout),
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
        selectedItemColor: Colors.teal,
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.home), label: labels["tab_home"]),
          BottomNavigationBarItem(icon: const Icon(Icons.notifications), label: labels["tab_noti"]),
          BottomNavigationBarItem(icon: const Icon(Icons.person), label: labels["tab_profile"]),
        ],
      ),
    );
  }
}