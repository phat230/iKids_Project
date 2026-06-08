import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class StudentDashboard extends StatelessWidget {
  const StudentDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Học sinh Dashboard"),
        backgroundColor: Colors.blueAccent,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Đăng xuất',
            onPressed: () async {
              await ApiService().logout(); // Xóa token
              if (context.mounted) {
                Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
              }
            },
          )
        ],
      ),
      body: const Center(
        child: Text("Chào mừng bé đến với iKids!", style: TextStyle(fontSize: 20)),
      ),
    );
  }
}