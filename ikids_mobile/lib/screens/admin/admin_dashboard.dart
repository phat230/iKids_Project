import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  final ApiService _apiService = ApiService();
  dynamic _data;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAdminData();
  }

  Future<void> _loadAdminData() async {
    try {
      // Đã sửa lại đúng đường dẫn API Backend
      final data = await _apiService.getAuthorized('/api/auth/admin/stats');
      setState(() {
        _data = data;
        _isLoading = false;
      });
    } catch (e) {
      print("Lỗi load dữ liệu admin: $e");
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Admin Dashboard"),
        backgroundColor: Colors.redAccent,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Đăng xuất',
            onPressed: () async {
              await _apiService.logout();
              if (context.mounted) {
                Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
              }
            },
          )
        ],
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator()) 
          : _data == null 
              ? const Center(child: Text("Không thể tải dữ liệu Admin", style: TextStyle(color: Colors.red)))
              // Hiển thị dữ liệu lấy được từ Backend
              : Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.admin_panel_settings, size: 80, color: Colors.redAccent),
                      const SizedBox(height: 20),
                      Card(
                        child: ListTile(
                          leading: const Icon(Icons.school, color: Colors.blue),
                          title: const Text("Tổng số học sinh"),
                          trailing: Text("${_data['total_students']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                      ),
                      Card(
                        child: ListTile(
                          leading: const Icon(Icons.person, color: Colors.green),
                          title: const Text("Tổng số giáo viên"),
                          trailing: Text("${_data['total_teachers']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                      ),
                      Card(
                        child: ListTile(
                          leading: const Icon(Icons.monetization_on, color: Colors.orange),
                          title: const Text("Doanh thu tháng này"),
                          trailing: Text("${_data['revenue_this_month']}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}