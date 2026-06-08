// lib/routes/app_router.dart
import 'package:flutter/material.dart';

// --- Import các trang Auth ---
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/forgot_password_screen.dart';

// --- Import các trang Dashboard ---
import '../screens/admin/admin_dashboard.dart';
import '../screens/student/student_dashboard.dart';
import '../screens/teacher/teacher_dashboard.dart';
import '../screens/parent/parent_dashboard.dart';
import '../screens/operator/operator_dashboard.dart';

class AppRouter {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      // 1. Nhóm Auth
      case '/':
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      case '/register':
        return MaterialPageRoute(builder: (_) => const RegisterScreen());
      case '/forgot-password':
        // Bỏ const ở đây vì constructor của ForgotPasswordScreen hiện tại không phải là const
        return MaterialPageRoute(builder: (_) => const ForgotPasswordScreen());

      // 2. Nhóm Dashboard theo Role
      case '/admin':
        return MaterialPageRoute(builder: (_) => const AdminDashboard());
      case '/student':
        return MaterialPageRoute(builder: (_) => const StudentDashboard());
      case '/teacher':
        return MaterialPageRoute(builder: (_) => const TeacherDashboard());
      case '/parent':
        return MaterialPageRoute(builder: (_) => const ParentDashboard());
      case '/operator':
        return MaterialPageRoute(builder: (_) => const OperatorDashboard());

      // 3. Fallback (Trang không tồn tại)
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            appBar: AppBar(title: const Text('Lỗi điều hướng')),
            body: Center(
              child: Text('Trang ${settings.name} không tồn tại'),
            ),
          ),
        );
    }
  }
}