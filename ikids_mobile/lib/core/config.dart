// lib/core/config.dart
class AppConfig {
  // ✅ Địa chỉ Backend thực tế trên Render
  static const String baseUrl = "https://ikids-project.onrender.com"; 
  
  // Thời gian chờ tối đa (giây)
  static const int connectTimeout = 30; 
  
  // ================= CÁC MODULE API CHÍNH =================
  // Cấu hình các tiền tố phân hệ khớp 100% với cấu trúc Backend
  static const String apiAuth = "$baseUrl/api/auth";
  static const String apiTv1 = "$baseUrl/api/tv1";       // Quản lý vận hành (Lịch, Lớp, Giáo viên)
  static const String apiTv2 = "$baseUrl/api/tv2";       // Quản lý học thuật (Video, Quiz, Điểm)
  static const String apiTv3 = "$baseUrl/api/tv3";       // Cửa hàng, kỷ niệm, nạp tiền
  static const String apiFinance = "$baseUrl/api/finance"; // Quản lý tài chính
  
  // ================= CÁC ENDPOINT DÙNG CHUNG =================
  static const String loginEndpoint = "$apiAuth/login";
  static const String registerEndpoint = "$apiAuth/register";
}