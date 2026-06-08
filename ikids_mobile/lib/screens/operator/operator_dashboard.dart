import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class OperatorDashboard extends StatelessWidget {
  const OperatorDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Vận hành Dashboard"),
        backgroundColor: Colors.orange,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Đăng xuất',
            onPressed: () async {
              await ApiService().logout();
              if (context.mounted) {
                Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
              }
            },
          )
        ],
      ),
      body: const Center(
        child: Text("Giao diện dành cho Nhân viên Vận hành", style: TextStyle(fontSize: 18)),
      ),
    );
  }
}