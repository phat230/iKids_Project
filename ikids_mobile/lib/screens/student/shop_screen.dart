import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../../services/api_service.dart';
import '../../core/config.dart';

class ShopScreen extends StatefulWidget {
  const ShopScreen({super.key});

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> {
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage();
  
  String? _userId;
  double _balance = 0.0; 
  List<dynamic> _allProducts = []; 
  
  bool _isLoading = true;
  int _currentPage = 0;
  final int _itemsPerPage = 15;

final String apiPrefix = '/api/tv3';

  @override
  void initState() {
    super.initState();
    _fetchStoreData();
  }

  // --- TẢI DỮ LIỆU TỪ BACKEND ---
  Future<void> _fetchStoreData() async {
    try {
      _userId = await _storage.read(key: 'user_id');
      if (_userId == null) throw Exception("Không tìm thấy thông tin tài khoản");

      // 1. Gọi API lấy ví tiền của Học sinh
      final profile = await _apiService.getAuthorized('$apiPrefix/gamification/profile/$_userId');
      
      // 2. Gọi API lấy danh sách Sản phẩm
      final products = await _apiService.getAuthorized('$apiPrefix/products');

      setState(() {
        _balance = (profile['balance'] ?? 0).toDouble();
        _allProducts = products ?? [];
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Lỗi tải cửa hàng: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  // --- XỬ LÝ MUA HÀNG VÀ XIN BA MẸ ---
  Future<void> _handleAction(Map<String, dynamic> product) async {
    double price = (product['price'] ?? 0).toDouble();
    String productId = product['id'] ?? product['_id'];
    String productName = product['name'] ?? "Sản phẩm";
    String? token = await _storage.read(key: 'jwt_token');

    // 1. TRƯỜNG HỢP: ĐỦ TIỀN -> MUA NGAY
    if (_balance >= price) {
      try {
        final response = await http.post(
          Uri.parse('${AppConfig.apiUrl}$apiPrefix/products/purchase'),
          headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
          body: jsonEncode({"user_id": _userId, "product_id": productId}),
        );
        
        if (response.statusCode == 200) {
          setState(() => _balance -= price); // Trừ tiền trên giao diện
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("🎉 Mua thành công! Hãy gặp thầy cô nhận quà nhé."), backgroundColor: Colors.green),
          );
        } else {
          final err = jsonDecode(response.body);
          throw Exception(err['detail']);
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e"), backgroundColor: Colors.red));
      }
    } 
    // 2. TRƯỜNG HỢP: THIẾU TIỀN -> XIN BA MẸ
    else {
      try {
        final response = await http.post(
          Uri.parse('${AppConfig.apiUrl}$apiPrefix/store/request-purchase'),
          headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
          body: jsonEncode({
            "student_id": _userId,
            "product_id": productId,
            "product_name": productName,
            "price": price
          }),
        );

        if (response.statusCode == 200) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("📩 Đã gửi yêu cầu mua [$productName] tới Ba Mẹ!"), backgroundColor: Colors.blue),
          );
        } else {
          final err = jsonDecode(response.body);
          throw Exception(err['detail']);
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e"), backgroundColor: Colors.red));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    int totalPages = (_allProducts.length / _itemsPerPage).ceil();
    int startIndex = _currentPage * _itemsPerPage;
    int endIndex = startIndex + _itemsPerPage;
    if (endIndex > _allProducts.length) endIndex = _allProducts.length;

    List<dynamic> currentProducts = _allProducts.isEmpty ? [] : _allProducts.sublist(startIndex, endIndex);

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text("🛍️ Cửa Hàng iKids", style: TextStyle(fontSize: 18)),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10.0),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(15)),
                child: _isLoading 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : Text("🪙 ${_balance.toStringAsFixed(0)} VNĐ", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              ),
            ),
          )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.green))
        : currentProducts.isEmpty
          ? const Center(child: Text("Cửa hàng đang cập nhật sản phẩm mới 🎈", style: TextStyle(fontSize: 16)))
          : Column(
              children: [
                Expanded(
                  child: GridView.builder(
                    padding: const EdgeInsets.all(10),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: 0.55,
                    ),
                    itemCount: currentProducts.length,
                    itemBuilder: (context, index) {
                      final item = currentProducts[index];
                      double price = (item['price'] ?? 0).toDouble();
                      bool canAfford = _balance >= price;

                      // Xử lý link ảnh
                      String imgUrl = item['image_url'] ?? "";
                      if (!imgUrl.startsWith("http")) {
                        imgUrl = "${AppConfig.apiUrl}/$imgUrl";
                      }

                      return Card(
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Expanded(
                              flex: 4,
                              child: ClipRRect(
                                borderRadius: const BorderRadius.vertical(top: Radius.circular(10)),
                                child: Image.network(
                                  imgUrl, 
                                  fit: BoxFit.cover, 
                                  errorBuilder: (c, e, s) => const Icon(Icons.inventory_2, size: 50, color: Colors.grey)
                                ),
                              ),
                            ),
                            Expanded(
                              flex: 4,
                              child: Padding(
                                padding: const EdgeInsets.all(6.0),
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      item['name'] ?? "Sản phẩm",
                                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                      textAlign: TextAlign.center,
                                    ),
                                    Text(
                                      "${price.toStringAsFixed(0)} đ",
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.orange),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 4.0, vertical: 4.0),
                              child: ElevatedButton(
                                onPressed: () => _handleAction(item),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: canAfford ? Colors.green : Colors.blueAccent,
                                  foregroundColor: Colors.white,
                                  padding: EdgeInsets.zero,
                                  minimumSize: const Size(double.infinity, 30),
                                ),
                                child: Text(canAfford ? "🛒 Mua" : "🙏 Xin ba mẹ", style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                              ),
                            )
                          ],
                        ),
                      );
                    },
                  ),
                ),
                if (totalPages > 1)
                  Container(
                    padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 20),
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 5, offset: Offset(0, -2))],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        ElevatedButton.icon(
                          onPressed: _currentPage > 0 ? () => setState(() => _currentPage--) : null,
                          icon: const Icon(Icons.arrow_back_ios, size: 12),
                          label: const Text("Trước", style: TextStyle(fontSize: 12)),
                        ),
                        Text("Trang ${_currentPage + 1} / $totalPages", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        ElevatedButton(
                          onPressed: _currentPage < totalPages - 1 ? () => setState(() => _currentPage++) : null,
                          child: const Row(mainAxisSize: MainAxisSize.min, children: [Text("Sau ", style: TextStyle(fontSize: 12)), Icon(Icons.arrow_forward_ios, size: 12)]),
                        ),
                      ],
                    ),
                  )
              ],
            ),
    );
  }
}