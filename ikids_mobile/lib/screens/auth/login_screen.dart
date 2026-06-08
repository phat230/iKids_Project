import 'package:flutter/material.dart'; 
import '../../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  // 1. Khai báo các Controller và Service bên trong Class State
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  final _apiService = ApiService();
  bool _isLoading = false;

  // 2. Hàm xử lý Logic Đăng nhập
  void _login() async {
    // Kiểm tra dữ liệu đầu vào (Validation) trước khi gọi API
    if (_emailController.text.isEmpty || _passController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Vui lòng điền đầy đủ email và mật khẩu!")),
      );
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      final data = await _apiService.login(_emailController.text, _passController.text);
      
      // An toàn với null-check
      final userInfo = data['user_info'];
      if (userInfo == null) {
        throw Exception("Dữ liệu phản hồi không hợp lệ.");
      }
      
      String role = userInfo['role'] ?? 'student'; // Mặc định là student nếu không có role
      
      if (!mounted) return;

      // Điều hướng dựa trên role (Đã cập nhật đủ 5 role)
      switch (role) {
        case 'admin':
          Navigator.pushReplacementNamed(context, '/admin');
          break;
        case 'teacher':
          Navigator.pushReplacementNamed(context, '/teacher');
          break;
        case 'operator':
          Navigator.pushReplacementNamed(context, '/operator');
          break;
        case 'parent':
          Navigator.pushReplacementNamed(context, '/parent');
          break;
        case 'student':
        default:
          Navigator.pushReplacementNamed(context, '/student');
          break;
      }
      
    } catch (e) {
      // Phân loại thông báo lỗi để người dùng dễ hiểu
      String errorMsg = e.toString().contains("403") 
          ? "Tài khoản chưa được kích hoạt hoặc bị khóa." 
          : e.toString().replaceFirst("Exception: ", "");
          
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Lỗi: $errorMsg")),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    // Giải phóng bộ nhớ của các controller khi hủy widget
    _emailController.dispose();
    _passController.dispose();
    super.dispose();
  }

  // 3. Hàm xây dựng Giao diện (UI)
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _emailController, 
              decoration: const InputDecoration(labelText: "Email"),
              keyboardType: TextInputType.emailAddress,
            ),
            TextField(
              controller: _passController, 
              decoration: const InputDecoration(labelText: "Mật khẩu"), 
              obscureText: true,
            ),
            const SizedBox(height: 20),
            _isLoading 
              ? const CircularProgressIndicator() 
              : ElevatedButton(
                  onPressed: _login, 
                  child: const Text("Đăng nhập"),
                ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/register'), 
              child: const Text("Đăng ký"),
            ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/forgot-password'), 
              child: const Text("Quên mật khẩu?"),
            ),
          ],
        ),
      ),
    );
  }
}