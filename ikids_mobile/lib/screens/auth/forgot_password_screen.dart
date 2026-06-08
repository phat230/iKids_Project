import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _emailController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPassController = TextEditingController();
  
  bool _isOtpStep = false; // Trạng thái: false = Đang ở Bước 1, true = Đang ở Bước 2
  bool _isLoading = false;

  // Xử lý Bước 1: Gửi yêu cầu lấy OTP
  void _sendOtp() async {
    if (_emailController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng nhập email!")));
      return;
    }
    
    setState(() => _isLoading = true);
    try {
      bool success = await ApiService().forgotPassword(_emailController.text.trim());
      if (success) {
        setState(() => _isOtpStep = true); // Chuyển giao diện sang bước nhập OTP
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Mã OTP đã được gửi vào email của bạn!"))
          );
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst("Exception: ", ""))));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // Xử lý Bước 2: Xác nhận OTP và lưu Mật khẩu mới
  void _resetPassword() async {
    if (_otpController.text.isEmpty || _newPassController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng nhập đủ OTP và mật khẩu mới!")));
      return;
    }

    setState(() => _isLoading = true);
    try {
      bool success = await ApiService().resetPassword(
        _emailController.text.trim(),
        _otpController.text.trim(),
        _newPassController.text,
      );
      
      if (success && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Đổi mật khẩu thành công! Hãy đăng nhập lại."))
        );
        Navigator.pop(context); // Đổi xong thì thoát về trang Login
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst("Exception: ", ""))));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Khôi phục mật khẩu")),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: _isOtpStep
              ? [ // --- GIAO DIỆN BƯỚC 2: NHẬP OTP ---
                  Text("Mã xác thực đã được gửi tới:\n${_emailController.text}", textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 20),
                  TextField(
                    controller: _otpController,
                    decoration: const InputDecoration(labelText: "Nhập mã OTP (6 số)"),
                    keyboardType: TextInputType.number,
                  ),
                  TextField(
                    controller: _newPassController,
                    decoration: const InputDecoration(labelText: "Nhập Mật khẩu mới"),
                    obscureText: true,
                  ),
                  const SizedBox(height: 20),
                  _isLoading
                      ? const CircularProgressIndicator()
                      : ElevatedButton(onPressed: _resetPassword, child: const Text("Xác nhận đổi mật khẩu")),
                ]
              : [ // --- GIAO DIỆN BƯỚC 1: NHẬP EMAIL ---
                  const Text("Nhập email bạn đã đăng ký để nhận mã khôi phục."),
                  const SizedBox(height: 10),
                  TextField(
                    controller: _emailController,
                    decoration: const InputDecoration(labelText: "Nhập Email của bạn"),
                    keyboardType: TextInputType.emailAddress,
                  ),
                  const SizedBox(height: 20),
                  _isLoading
                      ? const CircularProgressIndicator()
                      : ElevatedButton(onPressed: _sendOtp, child: const Text("Gửi yêu cầu")),
                ],
        ),
      ),
    );
  }
}