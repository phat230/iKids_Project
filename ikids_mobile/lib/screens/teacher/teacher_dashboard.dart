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

  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController();
  final _fbController = TextEditingController(); 
  bool _isEditingProfile = false;
  bool _isLoadingProfile = true;

  final List<Map<String, dynamic>> _menuItems = [
    {"title": "Lịch dạy", "icon": Icons.calendar_month, "color": Colors.teal},
    {"title": "Chấm điểm", "icon": Icons.grading, "color": Colors.blue},
    {"title": "Giao bài tập", "icon": Icons.assignment, "color": Colors.orange},
    {"title": "Góc kỷ niệm", "icon": Icons.photo_library, "color": Colors.purple},
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
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? "Giáo viên iKids";
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
    if (_nameController.text.trim().isEmpty) return;
    setState(() => _isLoadingProfile = true);
    var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/profile/update/$_userId'));
    request.fields['full_name'] = _nameController.text.trim();
    try {
      var response = await request.send();
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Cập nhật thành công!"), backgroundColor: Colors.green));
        setState(() => _isEditingProfile = false);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi kết nối."), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoadingProfile = false);
    }
  }

  Widget _buildHomeTab() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: const BoxDecoration(
            color: Colors.teal,
            borderRadius: BorderRadius.only(bottomLeft: Radius.circular(30), bottomRight: Radius.circular(30)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Chào Thầy/Cô ${_nameController.text.split(' ').last}! 📚", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 5),
              const Text("Chúc một ngày giảng dạy tràn đầy năng lượng!", style: TextStyle(fontSize: 16, color: Colors.white70)),
            ],
          ),
        ),
        const SizedBox(height: 15),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 20),
          child: Text("Nghiệp vụ giảng dạy", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ),
        Expanded(
          child: GridView.builder(
            padding: const EdgeInsets.all(20),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, crossAxisSpacing: 15, mainAxisSpacing: 15, childAspectRatio: 1.15),
            itemCount: _menuItems.length,
            itemBuilder: (context, index) {
              final item = _menuItems[index];
              return InkWell(
                onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Tính năng đang phát triển"))),
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
                      TextField(controller: _nameController, decoration: const InputDecoration(labelText: "Họ và tên (*)")),
                      TextField(controller: _phoneController, decoration: const InputDecoration(labelText: "Số điện thoại")),
                      TextField(controller: _fbController, decoration: const InputDecoration(labelText: "Link Facebook")),
                      TextField(controller: _bioController, decoration: const InputDecoration(labelText: "Phương châm giảng dạy")),
                      const SizedBox(height: 25),
                      Row(
                        children: [
                          Expanded(child: OutlinedButton(onPressed: () => setState(() => _isEditingProfile = false), child: const Text("Hủy"))),
                          const SizedBox(width: 10),
                          Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white), onPressed: _updateProfile, child: const Text("Lưu"))),
                        ],
                      ),
                    ],
                  )
                : Column(
                    children: [
                      ListTile(leading: const Icon(Icons.person, color: Colors.teal), title: Text(_nameController.text.isEmpty ? "Chưa cập nhật" : _nameController.text, style: const TextStyle(fontWeight: FontWeight.bold)), subtitle: const Text("Họ và Tên")),
                      const Divider(height: 1),
                      ListTile(leading: const Icon(Icons.phone, color: Colors.green), title: Text(_phoneController.text.isEmpty ? "Chưa cập nhật" : _phoneController.text), subtitle: const Text("Số điện thoại")),
                      const Divider(height: 1),
                      ListTile(leading: const Icon(Icons.favorite, color: Colors.redAccent), title: Text(_bioController.text.isEmpty ? "Chưa cập nhật" : _bioController.text), subtitle: const Text("Phương châm giảng dạy")),
                      const SizedBox(height: 20),
                      SizedBox(width: double.infinity, child: OutlinedButton.icon(style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.teal)), onPressed: () => setState(() => _isEditingProfile = true), icon: const Icon(Icons.edit, color: Colors.teal), label: const Text("Chỉnh sửa hồ sơ", style: TextStyle(color: Colors.teal)))),
                    ],
                  ),
          ),
          const SizedBox(height: 20),
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            child: ListTile(leading: const Icon(Icons.logout, color: Colors.red), title: const Text("Đăng xuất", style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)), onTap: _handleLogout),
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
        selectedItemColor: Colors.teal,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: "Trang chủ"),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: "Thông báo"),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: "Cá nhân"),
        ],
      ),
    );
  }
}