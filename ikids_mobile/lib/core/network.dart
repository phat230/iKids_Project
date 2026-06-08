// lib/core/network.dart
import 'package:http/http.dart' as http;

class NetworkHelper {
  static Future<http.Response> safeRequest(Future<http.Response> request) async {
    try {
      return await request.timeout(const Duration(seconds: 30));
    } catch (e) {
      // Ở đây bạn có thể log lỗi vào Firebase hoặc Sentry
      throw Exception("Lỗi kết nối server: $e");
    }
  }
}