// lib/core/network.dart
import 'package:http/http.dart' as http;

class NetworkHelper {
  static Future<http.Response> safeRequest(Future<http.Response> request) async {
    try {
      // Tự động ngắt kết nối nếu quá 30 giây không phản hồi
      return await request.timeout(const Duration(seconds: 30));
    } catch (e) {
      // Log lỗi ra console hoặc ném ra exception để UI bắt và hiển thị
      throw Exception("Lỗi kết nối server: $e");
    }
  }
}