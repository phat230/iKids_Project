import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../services/api_service.dart';
import '../../core/config.dart';
import 'exercise_screen.dart';
import 'video_screen.dart';
import 'schedule_screen.dart';
import 'result_screen.dart';
import 'memories_screen.dart';
import 'shop_screen.dart';
import '../notification/notification_screen.dart';

class StudentDashboard extends StatefulWidget {
  const StudentDashboard({super.key});

  @override
  State<StudentDashboard> createState() => _StudentDashboardState();
}

class _StudentDashboardState extends State<StudentDashboard> {
  int _selectedIndex = 0;
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage(); 
  
  // Thông tin user
  String _userId = "";
  String _userRole = "student";
  String _userRank = "Beginner";
  int _userExp = 0;
  double _userBalance = 0;

  // Controllers cho Profile Form
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController(); 
  final _fbController = TextEditingController(); 
  bool _isEditingProfile = false;
  bool _isLoadingProfile = true;

  final List<Map<String, dynamic>> _menuItems = [
    {"title": "Lịch học", "icon": Icons.calendar_month_rounded, "color": Colors.blue, "screen": const ScheduleScreen()},
    {"title": "Bài tập (Quiz)", "icon": Icons.quiz_rounded, "color": Colors.orange, "screen": const ExerciseScreen()},
    {"title": "Video bài học", "icon": Icons.play_circle_fill_rounded, "color": Colors.red, "screen": const VideoScreen()},
    {"title": "Kết quả", "icon": Icons.emoji_events_rounded, "color": Colors.amber, "screen": const ResultScreen()},
    {"title": "Kỷ niệm", "icon": Icons.auto_stories_rounded, "color": Colors.purple, "screen": const MemoriesScreen()},
    {"title": "Cửa hàng", "icon": Icons.shopping_bag_rounded, "color": Colors.green, "screen": const ShopScreen()},
  ];

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
  }

  // Lấy dữ liệu Profile từ DB
  Future<void> _loadUserProfile() async {
    try {
      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final decoded = jsonDecode(userInfo);
        _userId = decoded["id"]?.toString() ?? decoded["_id"]?.toString() ?? "";
        _userRole = decoded["role"]?.toString() ?? "student";
        
        setState(() {
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? "Người dùng iKids";
          _phoneController.text = decoded["phone_number"] ?? decoded["phone"] ?? "";
          _bioController.text = decoded["bio"] ?? "";
          _fbController.text = decoded["facebook_url"] ?? "";
        });

        if (_userId.isNotEmpty) {
          final res = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/gamification/profile/$_userId'));
          if (res.statusCode == 200) {
            final gameData = jsonDecode(res.body);
            setState(() {
              _userExp = gameData['exp'] ?? 0;
              _userRank = gameData['rank'] ?? 'Beginner';
              _userBalance = (gameData['balance'] ?? 0).toDouble();
            });
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
    if (mounted) {
      Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
    }
  }

  // Hàm gọi API cập nhật Profile
  void _updateProfile() async {
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Họ và tên không được để trống"), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isLoadingProfile = true);
    
    var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/profile/update/$_userId'));
    request.fields['full_name'] = _nameController.text.trim();
    
    try {
      var response = await request.send();
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("🎉 Cập nhật thông tin thành công!"), backgroundColor: Colors.green));
        
        String? userInfoStr = await _storage.read(key: 'user_info');
        if (userInfoStr != null) {
          Map<String, dynamic> userInfo = jsonDecode(userInfoStr);
          userInfo['full_name'] = _nameController.text.trim();
          userInfo['phone_number'] = _phoneController.text.trim();
          userInfo['bio'] = _bioController.text.trim();
          userInfo['facebook_url'] = _fbController.text.trim();
          await _storage.write(key: 'user_info', value: jsonEncode(userInfo));
        }
        
        setState(() => _isEditingProfile = false);
      } else {
        throw Exception("Lỗi server");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi: Không thể kết nối tới server."), backgroundColor: Colors.red));
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
            color: Colors.blueAccent,
            borderRadius: BorderRadius.only(bottomLeft: Radius.circular(30), bottomRight: Radius.circular(30)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Xin chào, ${_nameController.text.split(' ').last}! 👋", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 5),
              const Text("Hôm nay chúng ta cùng khám phá nhé!", style: TextStyle(fontSize: 16, color: Colors.white70)),
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
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, crossAxisSpacing: 15, mainAxisSpacing: 15, childAspectRatio: 1.15),
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

  Widget _buildProfileTab() {
    if (_isLoadingProfile) return const Center(child: CircularProgressIndicator());

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const CircleAvatar(radius: 50, backgroundColor: Colors.blueAccent, child: Icon(Icons.person, size: 60, color: Colors.white)),
          const SizedBox(height: 10),
          
          if (_isEditingProfile)
            TextButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.camera_alt, color: Colors.blueAccent),
              label: const Text("Đổi ảnh đại diện"),
            ),
          const SizedBox(height: 15),

          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(15)),
            child: Column(
              children: [
                if (_userRole == 'student') ...[
                  Text("🏆 Hạng: $_userRank", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blue[800])),
                  const SizedBox(height: 5),
                  Text("⭐ EXP Tích lũy: $_userExp", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange[800])),
                ] else if (_userRole == 'parent') ...[
                  Text("💰 Số dư ví: ${_userBalance.toStringAsFixed(0)} VNĐ", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.green)),
                ] else ...[
                  Text("🔑 Vai trò: ${_userRole.toUpperCase()}", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blue[800])),
                ]
              ],
            ),
          ),
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
                      const Text("👤 Thông tin cơ bản", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                      TextField(controller: _nameController, decoration: const InputDecoration(labelText: "Họ và tên (*)")),
                      TextField(controller: _phoneController, decoration: const InputDecoration(labelText: "Số điện thoại"), keyboardType: TextInputType.phone),
                      const SizedBox(height: 15),
                      
                      if (_userRole == 'teacher' || _userRole == 'admin' || _userRole == 'operator') ...[
                        const Text("🌐 Mạng xã hội & Khác", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                        TextField(controller: _fbController, decoration: const InputDecoration(labelText: "Link Facebook")),
                        TextField(controller: _bioController, decoration: const InputDecoration(labelText: "Phương châm giảng dạy")),
                      ] else ...[
                        TextField(controller: _bioController, decoration: const InputDecoration(labelText: "Sở thích cá nhân")),
                      ],
                      
                      const SizedBox(height: 25),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () => setState(() => _isEditingProfile = false),
                              child: const Text("Hủy", style: TextStyle(color: Colors.grey)),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent, foregroundColor: Colors.white),
                              onPressed: _updateProfile,
                              child: const Text("Lưu thay đổi"),
                            ),
                          ),
                        ],
                      ),
                    ],
                  )
                : Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.person, color: Colors.blueAccent),
                        title: Text(_nameController.text.isEmpty ? "Chưa cập nhật" : _nameController.text, style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: const Text("Họ và Tên"),
                      ),
                      const Divider(height: 1),
                      ListTile(
                        leading: const Icon(Icons.phone, color: Colors.green),
                        title: Text(_phoneController.text.isEmpty ? "Chưa cập nhật" : _phoneController.text),
                        subtitle: const Text("Số điện thoại"),
                      ),
                      const Divider(height: 1),
                      
                      if (_userRole == 'teacher' || _userRole == 'admin' || _userRole == 'operator') ...[
                        ListTile(
                          leading: const Icon(Icons.facebook, color: Colors.blue),
                          title: Text(_fbController.text.isEmpty ? "Chưa có liên kết" : "Đã liên kết FB"),
                          subtitle: const Text("Mạng xã hội"),
                        ),
                        const Divider(height: 1),
                        ListTile(
                          leading: const Icon(Icons.favorite, color: Colors.redAccent),
                          title: Text(_bioController.text.isEmpty ? "Chưa cập nhật" : _bioController.text),
                          subtitle: const Text("Phương châm giảng dạy"),
                        ),
                      ] else ...[
                        ListTile(
                          leading: const Icon(Icons.star, color: Colors.orange),
                          title: Text(_bioController.text.isEmpty ? "Chưa cập nhật" : _bioController.text),
                          subtitle: const Text("Sở thích"),
                        ),
                      ],
                      
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.blueAccent)),
                          onPressed: () => setState(() => _isEditingProfile = true),
                          icon: const Icon(Icons.edit, color: Colors.blueAccent),
                          label: const Text("Chỉnh sửa hồ sơ", style: TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
          ),

          const SizedBox(height: 20),
          
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.lock, color: Colors.orange),
                  title: const Text("Đổi mật khẩu"),
                  trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                  onTap: _showChangePasswordDialog, // GỌI HÀM ĐỔI MẬT KHẨU TẠI ĐÂY
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
    final List<Widget> tabs = [
      _buildHomeTab(),
      const NotificationScreen(),
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