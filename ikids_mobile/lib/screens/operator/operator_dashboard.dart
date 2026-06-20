import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import '../../services/api_service.dart';
import '../notification/notification_screen.dart';

class OperatorDashboard extends StatefulWidget {
  const OperatorDashboard({super.key});

  @override
  State<OperatorDashboard> createState() => _OperatorDashboardState();
}

class _OperatorDashboardState extends State<OperatorDashboard> {
  int _selectedIndex = 0;
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage(); 
  
  String _userId = "";
  String _lang = "vi"; // Ngôn ngữ mặc định
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  bool _isLoadingProfile = true;

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "default_name": "Vận hành iKids",
      "greeting": "Nhân viên",
      "subtitle": "Chào mừng bạn trở lại trạm điều hành!",
      "tools_header": "CÔNG CỤ QUẢN LÝ",
      "menu_class": "Quản lý Lớp học",
      "menu_class_sub": "Tạo lớp mới, xếp danh sách học viên",
      "menu_schedule": "Xếp lịch & Thông báo",
      "menu_schedule_sub": "Sắp xếp TKB, gửi SMS tự động",
      "menu_finance": "Giao dịch & Tài chính",
      "menu_finance_sub": "Duyệt ví tiền, xuất báo cáo",
      "menu_store": "Cửa hàng Đổi thưởng",
      "menu_store_sub": "Quản lý kho quà tặng iKids",
      "menu_cms": "Quản lý Trang chủ (CMS)",
      "menu_cms_sub": "Đăng tin tức, sửa phần giới thiệu",
      "btn_logout": "Đăng xuất khỏi ca trực",
      "tab_dashboard": "Điều khiển",
      "tab_noti": "Thông báo",
      "tab_profile": "Hồ sơ"
    },
    "en": {
      "default_name": "iKids Operator",
      "greeting": "Operator",
      "subtitle": "Welcome back to the operations station!",
      "tools_header": "MANAGEMENT TOOLS",
      "menu_class": "Class Management",
      "menu_class_sub": "Create classes, arrange student lists",
      "menu_schedule": "Schedule & Notify",
      "menu_schedule_sub": "Arrange timetables, send auto SMS",
      "menu_finance": "Finance & Transactions",
      "menu_finance_sub": "Approve wallets, export reports",
      "menu_store": "Reward Store",
      "menu_store_sub": "Manage iKids gift inventory",
      "menu_cms": "Homepage CMS",
      "menu_cms_sub": "Post news, edit about us section",
      "btn_logout": "Log out of shift",
      "tab_dashboard": "Dashboard",
      "tab_noti": "Inbox",
      "tab_profile": "Profile"
    }
  };

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    // Đọc ngôn ngữ được lưu trên hệ thống từ lúc Đăng nhập
    String? savedLang = await _storage.read(key: 'app_lang');
    if (savedLang != null) {
      setState(() => _lang = savedLang);
    }
    await _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    final labels = _locales[_lang]!;
    try {
      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final decoded = jsonDecode(userInfo);
        _userId = decoded["id"]?.toString() ?? decoded["_id"]?.toString() ?? "";
        setState(() {
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? labels["default_name"]!;
          _phoneController.text = decoded["phone_number"] ?? decoded["phone"] ?? "";
        });
      }
    } finally {
      if (mounted) setState(() => _isLoadingProfile = false);
    }
  }

  Future<void> _handleLogout() async {
    await _storage.deleteAll();
    await _apiService.logout();
    if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
  }

  // --- TAB 1: BẢNG ĐIỀU KHIỂN CHÍNH ---
  Widget _buildHomeTab() {
    final labels = _locales[_lang]!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header xin chào
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(25),
          decoration: const BoxDecoration(
            color: Colors.orange,
            borderRadius: BorderRadius.only(bottomLeft: Radius.circular(30), bottomRight: Radius.circular(30)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("${labels['greeting']} ${_nameController.text.split(' ').last} ⚙️", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
                    const SizedBox(height: 5),
                    Text(labels["subtitle"]!, style: const TextStyle(color: Colors.white70)),
                  ],
                ),
              ),
              // Nút chuyển đổi ngôn ngữ
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
        
        // Danh sách công cụ
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(labels["tools_header"]!, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.orange)),
              const SizedBox(height: 15),
              
              _buildMenuCard(
                labels["menu_class"]!, 
                labels["menu_class_sub"]!, 
                Icons.class_, 
                Colors.indigo, 
                () => Navigator.pushNamed(context, '/operator-class')
              ),
              
              _buildMenuCard(
                labels["menu_schedule"]!, 
                labels["menu_schedule_sub"]!, 
                Icons.calendar_month, 
                Colors.purple, 
                () => Navigator.pushNamed(context, '/operator-schedule')
              ),
              
              _buildMenuCard(
                labels["menu_finance"]!, 
                labels["menu_finance_sub"]!, 
                Icons.account_balance_wallet, 
                Colors.green, 
                () => Navigator.pushNamed(context, '/operator-finance')
              ),
              
              _buildMenuCard(
                labels["menu_store"]!, 
                labels["menu_store_sub"]!, 
                Icons.storefront, 
                Colors.blue, 
                () => Navigator.pushNamed(context, '/operator-store')
              ),

              // ✅ THÊM NÚT QUẢN LÝ CMS TRANG CHỦ
              _buildMenuCard(
                labels["menu_cms"]!, 
                labels["menu_cms_sub"]!, 
                Icons.web, 
                Colors.teal, 
                () => Navigator.pushNamed(context, '/operator-cms')
              ),
            ],
          ),
        ),
      ],
    );
  }

  // --- COMPONENT THẺ MENU ---
  Widget _buildMenuCard(String title, String subtitle, IconData icon, Color color, VoidCallback onTap) {
    return Card(
      margin: const EdgeInsets.only(bottom: 15),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(15),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: color.withOpacity(0.15), shape: BoxShape.circle),
                child: Icon(icon, color: color, size: 28),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(height: 4),
                    Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.grey)
            ],
          ),
        ),
      ),
    );
  }

  // --- TAB 3: TRANG CÁ NHÂN ---
  Widget _buildProfileTab() {
    final labels = _locales[_lang]!;
    if (_isLoadingProfile) return const Center(child: CircularProgressIndicator(color: Colors.orange));
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const CircleAvatar(radius: 50, backgroundColor: Colors.orange, child: Icon(Icons.settings, size: 60, color: Colors.white)),
          const SizedBox(height: 25),
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            child: ListTile(
              leading: const Icon(Icons.logout, color: Colors.red), 
              title: Text(labels["btn_logout"]!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)), 
              onTap: _handleLogout
            ),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;
    final List<Widget> tabs = [_buildHomeTab(), const NotificationScreen(), _buildProfileTab()];
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: SafeArea(child: tabs[_selectedIndex]),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.orange,
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.dashboard), label: labels["tab_dashboard"]),
          BottomNavigationBarItem(icon: const Icon(Icons.notifications), label: labels["tab_noti"]),
          BottomNavigationBarItem(icon: const Icon(Icons.person), label: labels["tab_profile"]),
        ],
      ),
    );
  }
}