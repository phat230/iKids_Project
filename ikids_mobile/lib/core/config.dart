// lib/core/config.dart
class AppConfig {
  // 10.0.2.2 là IP đặc biệt của Android Emulator để truy cập máy tính host
  static const String apiUrl = "http://10.0.2.2:8000"; 
  
  static const int connectTimeout = 30; // giây
  
  // Các endpoint dùng chung
  static const String loginEndpoint = "/auth/login";
}