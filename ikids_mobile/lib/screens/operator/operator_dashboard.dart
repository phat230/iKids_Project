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
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  bool _isLoadingProfile = true;

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
          _nameController.text = decoded["full_name"] ?? decoded["name"] ?? "Vận hành iKids";
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Nhân viên ${_nameController.text.split(' ').last} ⚙️", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 5),
              const Text("Chào mừng bạn trở lại trạm điều hành!", style: TextStyle(color: Colors.white70)),
            ],
          ),
        ),
        
        // Danh sách công cụ
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const Text("CÔNG CỤ QUẢN LÝ", style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.orange)),
              const SizedBox(height: 15),
              
              _buildMenuCard(
                "Quản lý Lớp học", 
                "Tạo lớp mới, xếp danh sách học viên", 
                Icons.class_, 
                Colors.indigo, 
                () => Navigator.pushNamed(context, '/operator-class')
              ),
              
              _buildMenuCard(
                "Xếp lịch & Thông báo", 
                "Sắp xếp TKB, gửi SMS tự động", 
                Icons.calendar_month, 
                Colors.purple, 
                () => Navigator.pushNamed(context, '/operator-schedule')
              ),
              
              _buildMenuCard(
                "Giao dịch & Tài chính", 
                "Duyệt ví tiền, xuất báo cáo", 
                Icons.account_balance_wallet, 
                Colors.green, 
                () => Navigator.pushNamed(context, '/operator-finance')
              ),
              
              _buildMenuCard(
                "Cửa hàng Đổi thưởng", 
                "Quản lý kho quà tặng iKids", 
                Icons.storefront, 
                Colors.blue, 
                () => Navigator.pushNamed(context, '/operator-store')
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
              title: const Text("Đăng xuất khỏi ca trực", style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)), 
              onTap: _handleLogout
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
      backgroundColor: Colors.grey[100],
      body: SafeArea(child: tabs[_selectedIndex]),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.orange,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: "Bảng điều khiển"),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: "Thông báo"),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: "Hồ sơ"),
        ],
      ),
    );
  }
}