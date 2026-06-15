// lib/core/config.dart
class AppConfig {
  // Bắt buộc dùng 10.0.2.2 cho Máy ảo Android (Emulator)
  static const String apiUrl = "https://ikids-project.onrender.com"; 
  
  static const int connectTimeout = 30; // giây
  
  // Các endpoint dùng chung
  static const String loginEndpoint = "/auth/login";
}