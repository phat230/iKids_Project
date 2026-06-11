// lib/core/config.dart
class AppConfig {
  // Bắt buộc dùng 10.0.2.2 cho Máy ảo Android (Emulator)
  static const String apiUrl = "http://10.0.2.2:8000"; 
  
  static const int connectTimeout = 30; // giây
  
  // Các endpoint dùng chung
  static const String loginEndpoint = "/auth/login";
}