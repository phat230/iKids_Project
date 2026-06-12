import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../services/api_service.dart';
import '../notification/notification_screen.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  int _selectedIndex = 0;
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage(); 
  
  dynamic _data;
  bool _isLoadingData = true;

  @override
  void initState() {
    super.initState();
    _loadAdminData();
  }

  Future<void> _loadAdminData() async {
    try {
      final data = await _apiService.getAuthorized('/api/auth/admin/stats');
      setState(() {
        _data = data;
        _isLoadingData = false;
      });
    } catch (e) {
      setState(() => _isLoadingData = false);
    }
  }

  Future<void> _handleLogout() async {
    await _storage.deleteAll();
    await _apiService.logout();
    if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
  }

  Widget _buildHomeTab() {
    return _isLoadingData 
      ? const Center(child: CircularProgressIndicator()) 
      : _data == null 
        ? const Center(child: Text("Không thể tải dữ liệu Admin", style: TextStyle(color: Colors.red)))
        : Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.admin_panel_settings, size: 80, color: Colors.redAccent),
                const SizedBox(height: 20),
                Card(child: ListTile(leading: const Icon(Icons.school, color: Colors.blue), title: const Text("Tổng số học sinh"), trailing: Text("${_data['total_students']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)))),
                Card(child: ListTile(leading: const Icon(Icons.person, color: Colors.green), title: const Text("Tổng số giáo viên"), trailing: Text("${_data['total_teachers']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)))),
                Card(child: ListTile(leading: const Icon(Icons.monetization_on, color: Colors.orange), title: const Text("Doanh thu tháng này"), trailing: Text("${_data['revenue_this_month']}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)))),
              ],
            ),
          );
  }

  Widget _buildProfileTab() {
    return Center(
      child: ElevatedButton.icon(
        style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
        icon: const Icon(Icons.logout),
        label: const Text("Đăng xuất Admin"),
        onPressed: _handleLogout,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> tabs = [_buildHomeTab(), const NotificationScreen(), _buildProfileTab()];
    return Scaffold(
      appBar: AppBar(title: const Text("Ban Giám Đốc", style: TextStyle(fontWeight: FontWeight.bold)), backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
      body: tabs[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.redAccent,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: "Tổng quan"),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: "Thông báo"),
          BottomNavigationBarItem(icon: Icon(Icons.admin_panel_settings), label: "Hệ thống"),
        ],
      ),
    );
  }
}