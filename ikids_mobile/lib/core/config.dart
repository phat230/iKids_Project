// lib/core/config.dart
class AppConfig {
  // Địa chỉ Backend thực tế trên Render
  static const String apiUrl = "https://ikids-backend-api.onrender.com";  
  static const String apiUrl = baseUrl; 
  
static const int connectTimeout = 60;  
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