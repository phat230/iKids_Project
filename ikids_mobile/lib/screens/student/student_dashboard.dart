import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart'; // Thêm thư viện quản lý bộ nhớ
import '../../services/api_service.dart';
import 'exercise_screen.dart';
import 'video_screen.dart';
import 'schedule_screen.dart';
import 'result_screen.dart';
import 'memories_screen.dart';
import 'shop_screen.dart';

class StudentDashboard extends StatefulWidget {
  const StudentDashboard({super.key});

  @override
  State<StudentDashboard> createState() => _StudentDashboardState();
}

class _StudentDashboardState extends State<StudentDashboard> {
  int _selectedIndex = 0;
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage(); // Khởi tạo công cụ dọn dẹp bộ nhớ
  
  // Controllers cho form cập nhật thông tin cá nhân
  final _nameController = TextEditingController(text: "Học sinh iKids");
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController();
  bool _isEditingProfile = false;

  // Danh sách 6 chức năng chính dạng Grid
  final List<Map<String, dynamic>> _menuItems = [
    {"title": "Lịch học", "icon": Icons.calendar_month_rounded, "color": Colors.blue, "screen": const ScheduleScreen()},
    {"title": "Bài tập (Quiz)", "icon": Icons.quiz_rounded, "color": Colors.orange, "screen": const ExerciseScreen()},
    {"title": "Video bài học", "icon": Icons.play_circle_fill_rounded, "color": Colors.red, "screen": const VideoScreen()},
    {"title": "Kết quả", "icon": Icons.emoji_events_rounded, "color": Colors.amber, "screen": const ResultScreen()},
    {"title": "Kỷ niệm", "icon": Icons.auto_stories_rounded, "color": Colors.purple, "screen": const MemoriesScreen()},
    {"title": "Cửa hàng", "icon": Icons.shopping_bag_rounded, "color": Colors.green, "screen": const ShopScreen()},
  ];

  Future<void> _handleLogout() async {
    // 1. CHỐT CHẶN: Xóa sạch toàn bộ dữ liệu tài khoản cũ lưu trong máy
    await _storage.deleteAll();
    
    // 2. Gọi API logout nếu cần
    await _apiService.logout();
    
    // 3. Văng ra màn hình đăng nhập
    if (mounted) {
      Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
    }
  }

  // API cập nhật trang cá nhân tương thích Backend Router /profile/update
  void _updateProfile() async {
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Họ và tên không được để trống")));
      return;
    }
    try {
      // Logic gọi hàm cập nhật dữ liệu (Ví dụ kết nối PUT lên backend)
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Cập nhật thông tin thành công!")));
      setState(() => _isEditingProfile = false);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e")));
    }
  }

  // GIAO DIỆN TRANG CHỦ
  Widget _buildHomeTab() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: const BoxDecoration(
            color: Colors.blueAccent,
            borderRadius: BorderRadius.only(bottomLeft: Radius.circular(30), bottomRight: Radius.circular(30)),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Xin chào, Bé ơi! 👋", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              SizedBox(height: 5),
              Text("Hôm nay chúng ta cùng khám phá nhé!", style: TextStyle(fontSize: 16, color: Colors.white70)),
            ],
          ),
        ),
        const SizedBox(height: 15),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 20),
          child: Text("Danh mục học tập", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ),
        Expanded(
          child: GridView.builder(
            padding: const EdgeInsets.all(20),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 15,
              mainAxisSpacing: 15,
              childAspectRatio: 1.15,
            ),
            itemCount: _menuItems.length,
            itemBuilder: (context, index) {
              final item = _menuItems[index];
              return InkWell(
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => item['screen'])),
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

  // GIAO DIỆN TAB CÁ NHÂN (PROFILE)
  Widget _buildProfileTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const CircleAvatar(radius: 45, backgroundColor: Colors.blueAccent, child: Icon(Icons.face, size: 50, color: Colors.white)),
          const SizedBox(height: 15),
          _isEditingProfile
              ? Column(
                  children: [
                    TextField(controller: _nameController, decoration: const InputDecoration(labelText: "Họ và tên")),
                    TextField(controller: _phoneController, decoration: const InputDecoration(labelText: "Số điện thoại"), keyboardType: TextInputType.phone),
                    TextField(controller: _bioController, decoration: const InputDecoration(labelText: "Sở thích / Tiểu sử")),
                    const SizedBox(height: 15),
                    ElevatedButton(onPressed: _updateProfile, child: const Text("Lưu thay đổi")),
                  ],
                )
              : Column(
                  children: [
                    Text(_nameController.text, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 5),
                    Text("SĐT: ${_phoneController.text.isEmpty ? 'Chưa cập nhật' : _phoneController.text}"),
                    Text("Sở thích: ${_bioController.text.isEmpty ? 'Chưa cập nhật' : _bioController.text}", style: const TextStyle(color: Colors.grey)),
                    const SizedBox(height: 15),
                    OutlinedButton.icon(
                      onPressed: () => setState(() => _isEditingProfile = true),
                      icon: const Icon(Icons.edit),
                      label: const Text("Sửa thông tin"),
                    ),
                  ],
                ),
          const Divider(height: 40),
          ListTile(
            leading: const Icon(Icons.lock, color: Colors.orange),
            title: const Text("Đổi mật khẩu"),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text("Đăng xuất"),
            onTap: _handleLogout,
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> tabs = [
      _buildHomeTab(),
      const Center(child: Text("Hộp thư thông báo trống 🔔", style: TextStyle(fontSize: 16))),
      _buildProfileTab(),
    ];

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(child: tabs[_selectedIndex]),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.blueAccent,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: "Trang chủ"),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: "Thông báo"),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: "Cá nhân"),
        ],
      ),
    );
  }
}