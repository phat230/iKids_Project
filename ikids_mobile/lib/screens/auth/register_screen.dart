import 'package:flutter/material.dart'; // Bắt buộc phải có
import '../../services/api_service.dart'; // Import Service để gọi API

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  final _nameController = TextEditingController(); // Thêm controller cho tên
  final _otpController = TextEditingController();
  bool _isOtpStep = false; 

  void _register() async {
    try {
      // Gọi API register từ ApiService đã gộp
      await ApiService().register({
        "name": _nameController.text, 
        "email": _emailController.text,
        "password": _passController.text,
        "role": "student"
      });
      setState(() => _isOtpStep = true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  void _verifyOtp() async {
    try {
      await ApiService().verifyOtp(_emailController.text, _otpController.text);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Kích hoạt thành công!")));
        Navigator.pop(context);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("OTP không chính xác!")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Đăng ký tài khoản")),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: _isOtpStep ? [
            const Text("Nhập mã OTP đã gửi về email/số điện thoại"),
            TextField(controller: _otpController, decoration: const InputDecoration(labelText: "Nhập mã OTP")),
            const SizedBox(height: 20),
            ElevatedButton(onPressed: _verifyOtp, child: const Text("Xác thực"))
          ] : [
            TextField(controller: _nameController, decoration: const InputDecoration(labelText: "Họ và tên")),
            TextField(controller: _emailController, decoration: const InputDecoration(labelText: "Email")),
            TextField(controller: _passController, decoration: const InputDecoration(labelText: "Mật khẩu"), obscureText: true),
            const SizedBox(height: 20),
            ElevatedButton(onPressed: _register, child: const Text("Đăng ký")),
          ],
        ),
      ),
    );
  }
}