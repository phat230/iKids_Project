import 'package:flutter/material.dart';

class TeacherDashboard extends StatelessWidget {
  const TeacherDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Giáo viên Dashboard")),
      body: const Center(child: Text("Chào mừng Giáo viên")),
    );
  }
}