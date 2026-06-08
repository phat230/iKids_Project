import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../core/config.dart';
import '../core/network.dart';

class ApiService {
  final _storage = const FlutterSecureStorage();

  // 1. Hàm Đăng nhập
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiUrl}/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await _storage.write(key: 'jwt_token', value: data['access_token']);
      await _storage.write(key: 'role', value: data['user_info']['role']);
      return data;
    } else {
      final error = jsonDecode(response.body);
      throw Exception(error['detail'] ?? 'Đăng nhập thất bại: ${response.statusCode}');
    }
  }

  // 2. Hàm Đăng ký (Giai đoạn 1)
  Future<Map<String, dynamic>> register(Map<String, dynamic> userData) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiUrl}/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(userData),
    );
    
    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      final error = jsonDecode(response.body);
      throw Exception(error['detail'] ?? 'Đăng ký thất bại');
    }
  }

  // 3. Hàm Xác thực OTP (Giai đoạn 2)
  Future<Map<String, dynamic>> verifyOtp(String email, String otp) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiUrl}/api/auth/verify-registration-otp'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'otp_code': otp}),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      final error = jsonDecode(response.body);
      throw Exception(error['detail'] ?? 'Xác thực OTP thất bại');
    }
  }

  // 4. Hàm Quên mật khẩu (Gửi email lấy OTP)
  Future<bool> forgotPassword(String email) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiUrl}/api/auth/forgot-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
    
    if (response.statusCode == 200) return true;
    
    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'Lỗi khi gửi yêu cầu khôi phục');
  }

  // 4.1 Hàm MỚI: Đặt lại mật khẩu (Gửi OTP và MK mới lên Backend)
  Future<bool> resetPassword(String email, String otp, String newPassword) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiUrl}/api/auth/verify-reset'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'otp': otp,
        'new_password': newPassword
      }),
    );
    
    if (response.statusCode == 200) return true;
    
    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'Lỗi khi đặt lại mật khẩu');
  }

  // 5. Hàm GET có Token (Dùng cho mọi API được bảo mật)
  Future<dynamic> getAuthorized(String endpoint) async {
    String? token = await _storage.read(key: 'jwt_token');
    
    final response = await NetworkHelper.safeRequest(
      http.get(
        Uri.parse('${AppConfig.apiUrl}$endpoint'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Lỗi hệ thống: ${response.statusCode}');
    }
  }
  
  // 6. Hàm Đăng xuất (Dọn dẹp bộ nhớ)
  Future<void> logout() async {
    await _storage.deleteAll();
  }
}