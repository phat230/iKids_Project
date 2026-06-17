// lib/core/config.dart
class AppConfig {
  // Địa chỉ Backend thực tế trên Render
  static const String baseUrl = "https://ikids-project.onrender.com"; 
  
  // ✅ TRẢ LẠI BIẾN apiUrl ĐỂ CODE CŨ TRONG SCREENS KHÔNG BỊ LỖI
  static const String apiUrl = baseUrl; 
  
  // Thời gian chờ tối đa (giây)
  static const int connectTimeout = 30; 
  
  // ================= CÁC MODULE API CHÍNH =================
  static const String apiAuth = "$baseUrl/api/auth";
  static const String apiTv1 = "$baseUrl/api/tv1";       
  static const String apiTv2 = "$baseUrl/api/tv2";       
  static const String apiTv3 = "$baseUrl/api/tv3";       
  static const String apiFinance = "$baseUrl/api/finance"; 
  
  // ================= CÁC ENDPOINT DÙNG CHUNG =================
  static const String loginEndpoint = "$apiAuth/login";
  static const String registerEndpoint = "$apiAuth/register";
}