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

// --- Import các trang Chức năng Admin & Operator ---
import '../screens/admin/admin_staff_management_screen.dart';
import '../screens/operator/operator_finance_screen.dart';
import '../screens/operator/operator_store_screen.dart';
import '../screens/operator/operator_class_screen.dart';
import '../screens/operator/operator_schedule_screen.dart';

// --- Import các trang Chức năng Giáo viên ---
import '../screens/teacher/teacher_journal_screen.dart';
import '../screens/teacher/teacher_create_quiz_screen.dart';
import '../screens/teacher/teacher_schedule_screen.dart';
import '../screens/teacher/teacher_grading_screen.dart';
import '../screens/teacher/teacher_assignment_screen.dart';

class AppRouter {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      // 1. Nhóm Auth
      case '/':
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      case '/register':
        return MaterialPageRoute(builder: (_) => const RegisterScreen());
      case '/forgot-password':
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

      // 3. Nhóm Chức năng Hệ thống (Admin & Operator)
      case '/admin-staff':
        return MaterialPageRoute(builder: (_) => const AdminStaffManagementScreen());
      case '/operator-finance':
        return MaterialPageRoute(builder: (_) => const OperatorFinanceScreen());
      case '/operator-store':
        return MaterialPageRoute(builder: (_) => const OperatorStoreScreen());
      case '/operator-class':
        return MaterialPageRoute(builder: (_) => const OperatorClassScreen());
      case '/operator-schedule':
        return MaterialPageRoute(builder: (_) => const OperatorScheduleScreen());

      // 4. Nhóm Chức năng Giáo viên
      case '/teacher-journal':
        return MaterialPageRoute(builder: (_) => const TeacherJournalScreen());
      case '/teacher-create-quiz':
        return MaterialPageRoute(builder: (_) => const TeacherCreateQuizScreen());
      case '/teacher-schedule':
        return MaterialPageRoute(builder: (_) => const TeacherScheduleScreen());
      case '/teacher-grading':
        return MaterialPageRoute(builder: (_) => const TeacherGradingScreen());
      case '/teacher-assignment':
        return MaterialPageRoute(builder: (_) => const TeacherAssignmentScreen());

      // 5. Fallback (Trang không tồn tại)
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