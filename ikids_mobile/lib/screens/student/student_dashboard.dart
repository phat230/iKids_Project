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
  String _lang = "vi"; // Ngôn ngữ mặc định

  // Controllers cho Profile Form
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController(); 
  final _fbController = TextEditingController(); 
  bool _isEditingProfile = false;
  bool _isLoadingProfile = true;

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "greeting": "Xin chào",
      "subtitle": "Hôm nay chúng ta cùng khám phá nhé!",
      "category": "Danh mục học tập",
      "tab_home": "Trang chủ",
      "tab_noti": "Thông báo",
      "tab_profile": "Cá nhân",
      "menu_schedule": "Lịch học",
      "menu_quiz": "Bài tập (Quiz)",
      "menu_video": "Video bài học",
      "menu_result": "Kết quả",
      "menu_memory": "Kỷ niệm",
      "menu_shop": "Cửa hàng",
      "prof_rank": "🏆 Hạng:",
      "prof_exp": "⭐ EXP Tích lũy:",
      "prof_role": "🔑 Vai trò:",
      "prof_basic": "👤 Thông tin cơ bản",
      "prof_name": "Họ và tên (*)",
      "prof_phone": "Số điện thoại",
      "prof_hobby": "Sở thích cá nhân",
      "prof_not_updated": "Chưa cập nhật",
      "btn_edit_pic": "Đổi ảnh đại diện",
      "btn_edit_prof": "Chỉnh sửa hồ sơ",
      "btn_cancel": "Hủy",
      "btn_save": "Lưu thay đổi",
      "btn_pwd": "Đổi mật khẩu",
      "btn_logout": "Đăng xuất",
      "pwd_title": "Đổi Mật Khẩu",
      "pwd_old": "Mật khẩu hiện tại",
      "pwd_new": "Mật khẩu mới",
      "pwd_confirm": "Xác nhận mật khẩu mới",
      "msg_success": "Cập nhật thành công!",
      "msg_empty": "Vui lòng điền đủ thông tin!",
      "msg_match": "Mật khẩu xác nhận không khớp!",
      "msg_err_conn": "Lỗi kết nối tới server."
    },
    "en": {
      "greeting": "Hello",
      "subtitle": "Let's explore today's lessons!",
      "category": "Learning Categories",
      "tab_home": "Home",
      "tab_noti": "Inbox",
      "tab_profile": "Profile",
      "menu_schedule": "Schedule",
      "menu_quiz": "Quizzes",
      "menu_video": "Video Lessons",
      "menu_result": "Results",
      "menu_memory": "Memories",
      "menu_shop": "Reward Store",
      "prof_rank": "🏆 Rank:",
      "prof_exp": "⭐ Total EXP:",
      "prof_role": "🔑 Role:",
      "prof_basic": "👤 Basic Information",
      "prof_name": "Full Name (*)",
      "prof_phone": "Phone Number",
      "prof_hobby": "Personal Hobbies",
      "prof_not_updated": "Not updated",
      "btn_edit_pic": "Change Avatar",
      "btn_edit_prof": "Edit Profile",
      "btn_cancel": "Cancel",
      "btn_save": "Save Changes",
      "btn_pwd": "Change Password",
      "btn_logout": "Logout",
      "pwd_title": "Change Password",
      "pwd_old": "Current Password",
      "pwd_new": "New Password",
      "pwd_confirm": "Confirm New Password",
      "msg_success": "Updated successfully!",
      "msg_empty": "Please fill in all fields!",
      "msg_match": "Passwords do not match!",
      "msg_err_conn": "Server connection error."
    }
  };

  List<Map<String, dynamic>> get _menuItems {
    final labels = _locales[_lang]!;
    return [
      {"title": labels["menu_schedule"], "icon": Icons.calendar_month_rounded, "color": Colors.blue, "screen": const ScheduleScreen()},
      {"title": labels["menu_quiz"], "icon": Icons.quiz_rounded, "color": Colors.orange, "screen": const ExerciseScreen()},
      {"title": labels["menu_video"], "icon": Icons.play_circle_fill_rounded, "color": Colors.red, "screen": const VideoScreen()},
      {"title": labels["menu_result"], "icon": Icons.emoji_events_rounded, "color": Colors.amber, "screen": const ResultScreen()},
      {"title": labels["menu_memory"], "icon": Icons.auto_stories_rounded, "color": Colors.purple, "screen": const MemoriesScreen()},
      {"title": labels["menu_shop"], "icon": Icons.shopping_bag_rounded, "color": Colors.green, "screen": const ShopScreen()},
    ];
  }

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
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
        _userRole = decoded["role"]?.toString() ?? "student";
        
        setState(() {
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? "Student";
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
    if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
  }

  void _updateProfile() async {
    final labels = _locales[_lang]!;
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_empty"]!), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isLoadingProfile = true);
    
    var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/profile/update/$_userId'));
    request.fields['full_name'] = _nameController.text.trim();
    
    try {
      var response = await request.send();
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("🎉 ${labels["msg_success"]}"), backgroundColor: Colors.green));
        
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
        throw Exception("Server Error");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_err_conn"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoadingProfile = false);
    }
  }

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
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_empty"]!), backgroundColor: Colors.red));
                      return;
                    }
                    if (newPassCtrl.text != confirmPassCtrl.text) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_match"]!), backgroundColor: Colors.red));
                      return;
                    }

                    setStateDialog(() => isChanging = true);
                    try {
                      bool success = await _apiService.changePassword(oldPassCtrl.text, newPassCtrl.text);
                      if (success) {
                        if (mounted) Navigator.pop(dialogContext);
                        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_success"]!), backgroundColor: Colors.green));
                      }
                    } catch (e) {
                      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst("Exception: ", "")), backgroundColor: Colors.red));
                      setStateDialog(() => isChanging = false);
                    }
                  },
                  child: isChanging 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) 
                    : const Text("OK"),
                ),
              ],
            );
          }
        );
      }
    );
  }

  Widget _buildHomeTab(Map<String, String> labels) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.only(top: 30, bottom: 20, left: 20, right: 20),
          decoration: const BoxDecoration(
            color: Colors.blueAccent,
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
                    Text("${labels['greeting']}, ${_nameController.text.split(' ').last}! 👋", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
                    const SizedBox(height: 5),
                    Text(labels['subtitle']!, style: const TextStyle(fontSize: 16, color: Colors.white70)),
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
          child: Text(labels["category"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
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

  Widget _buildProfileTab(Map<String, String> labels) {
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
              label: Text(labels["btn_edit_pic"]!),
            ),
          const SizedBox(height: 15),

          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(15)),
            child: Column(
              children: [
                Text("${labels['prof_rank']} $_userRank", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blue[800])),
                const SizedBox(height: 5),
                Text("${labels['prof_exp']} $_userExp", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange[800])),
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
                      Text(labels["prof_basic"]!, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                      TextField(controller: _nameController, decoration: InputDecoration(labelText: labels["prof_name"])),
                      TextField(controller: _phoneController, decoration: InputDecoration(labelText: labels["prof_phone"]), keyboardType: TextInputType.phone),
                      const SizedBox(height: 15),
                      TextField(controller: _bioController, decoration: InputDecoration(labelText: labels["prof_hobby"])),
                      
                      const SizedBox(height: 25),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () => setState(() => _isEditingProfile = false),
                              child: Text(labels["btn_cancel"]!, style: const TextStyle(color: Colors.grey)),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent, foregroundColor: Colors.white),
                              onPressed: _updateProfile,
                              child: Text(labels["btn_save"]!),
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
                        title: Text(_nameController.text.isEmpty ? labels["prof_not_updated"]! : _nameController.text, style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text(labels["prof_name"]!.replaceAll(" (*)", "")),
                      ),
                      const Divider(height: 1),
                      ListTile(
                        leading: const Icon(Icons.phone, color: Colors.green),
                        title: Text(_phoneController.text.isEmpty ? labels["prof_not_updated"]! : _phoneController.text),
                        subtitle: Text(labels["prof_phone"]!),
                      ),
                      const Divider(height: 1),
                      ListTile(
                        leading: const Icon(Icons.star, color: Colors.orange),
                        title: Text(_bioController.text.isEmpty ? labels["prof_not_updated"]! : _bioController.text),
                        subtitle: Text(labels["prof_hobby"]!),
                      ),
                      
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.blueAccent)),
                          onPressed: () => setState(() => _isEditingProfile = true),
                          icon: const Icon(Icons.edit, color: Colors.blueAccent),
                          label: Text(labels["btn_edit_prof"]!, style: const TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold)),
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
    final List<Widget> tabs = [
      _buildHomeTab(labels),
      const NotificationScreen(),
      _buildProfileTab(labels),
    ];

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(child: tabs[_selectedIndex]),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.blueAccent,
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.home), label: labels["tab_home"]),
          BottomNavigationBarItem(icon: const Icon(Icons.notifications), label: labels["tab_noti"]),
          BottomNavigationBarItem(icon: const Icon(Icons.person), label: labels["tab_profile"]),
        ],
      ),
    );
  }
}