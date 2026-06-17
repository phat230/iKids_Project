// lib/main.dart
import 'package:flutter/material.dart';
import 'routes/app_router.dart';

void main() {
  runApp(const IKidsApp());
}

class IKidsApp extends StatelessWidget {
  const IKidsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'iKids Learning',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueAccent),
        useMaterial3: true,
      ),
      // Màn hình khởi đầu là Login
      initialRoute: '/', 
      // Dùng AppRouter để quản lý các trang
      onGenerateRoute: AppRouter.generateRoute,
    );
  }
}