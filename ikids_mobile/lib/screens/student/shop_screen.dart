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
  String _lang = "vi"; 

  final String apiPrefix = '/api/tv3';

  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "🛍️ Cửa Hàng iKids",
      "err_not_found": "Không tìm thấy thông tin tài khoản",
      "err_load": "Lỗi tải cửa hàng:",
      "btn_buy": "🛒 Mua",
      "btn_ask": "🙏 Xin ba mẹ",
      "msg_buy_success": "🎉 Mua thành công! Hãy gặp thầy cô nhận quà nhé.",
      "msg_ask_success": "📩 Đã gửi yêu cầu mua tới Ba Mẹ!",
      "empty_shop": "Cửa hàng đang cập nhật sản phẩm mới 🎈",
      "btn_prev": "Trước",
      "btn_next": "Sau",
      "page": "Trang",
    },
    "en": {
      "title": "🛍️ iKids Store",
      "err_not_found": "Account information not found",
      "err_load": "Error loading store:",
      "btn_buy": "🛒 Buy",
      "btn_ask": "🙏 Ask Parents",
      "msg_buy_success": "🎉 Purchase successful! See your teacher for the reward.",
      "msg_ask_success": "📩 Purchase request sent to Parents!",
      "empty_shop": "The store is updating new products 🎈",
      "btn_prev": "Prev",
      "btn_next": "Next",
      "page": "Page",
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchStoreData();
  }

  Future<void> _fetchStoreData() async {
    try {
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      _userId = await _storage.read(key: 'user_id');
      if (_userId == null) throw Exception(_locales[_lang]!["err_not_found"]);

      final profile = await _apiService.getAuthorized('$apiPrefix/gamification/profile/$_userId');
      final products = await _apiService.getAuthorized('$apiPrefix/products');

      setState(() {
        _balance = (profile['balance'] ?? 0).toDouble();
        _allProducts = products ?? [];
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("${_locales[_lang]!['err_load']} $e"), backgroundColor: Colors.red));
    }
  }

  Future<void> _handleAction(Map<String, dynamic> product) async {
    double price = (product['price'] ?? 0).toDouble();
    String productId = product['id'] ?? product['_id'];
    String productName = product['name'] ?? "Sản phẩm";
    String? token = await _storage.read(key: 'jwt_token');

    if (_balance >= price) {
      try {
        final response = await http.post(
          Uri.parse('${AppConfig.apiUrl}$apiPrefix/products/purchase'),
          headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
          body: jsonEncode({"user_id": _userId, "product_id": productId}),
        );
        
        if (response.statusCode == 200) {
          setState(() => _balance -= price);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_locales[_lang]!["msg_buy_success"]!), backgroundColor: Colors.green));
        } else {
          final err = jsonDecode(response.body);
          throw Exception(err['detail']);
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi: $e"), backgroundColor: Colors.red));
      }
    } else {
      try {
        final response = await http.post(
          Uri.parse('${AppConfig.apiUrl}$apiPrefix/store/request-purchase'),
          headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
          body: jsonEncode({"student_id": _userId, "product_id": productId, "product_name": productName, "price": price}),
        );

        if (response.statusCode == 200) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_locales[_lang]!["msg_ask_success"]!), backgroundColor: Colors.blue));
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
    final labels = _locales[_lang]!;
    int totalPages = (_allProducts.length / _itemsPerPage).ceil();
    int startIndex = _currentPage * _itemsPerPage;
    int endIndex = startIndex + _itemsPerPage;
    if (endIndex > _allProducts.length) endIndex = _allProducts.length;

    List<dynamic> currentProducts = _allProducts.isEmpty ? [] : _allProducts.sublist(startIndex, endIndex);

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
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
          ),
          TextButton(
            onPressed: () async {
              setState(() => _lang = _lang == "vi" ? "en" : "vi");
              await _storage.write(key: 'app_lang', value: _lang);
            },
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.green))
        : currentProducts.isEmpty
          ? Center(child: Text(labels["empty_shop"]!, style: const TextStyle(fontSize: 16)))
          : Column(
              children: [
                Expanded(
                  child: GridView.builder(
                    padding: const EdgeInsets.all(10),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3, crossAxisSpacing: 10, mainAxisSpacing: 10, childAspectRatio: 0.55,
                    ),
                    itemCount: currentProducts.length,
                    itemBuilder: (context, index) {
                      final item = currentProducts[index];
                      double price = (item['price'] ?? 0).toDouble();
                      bool canAfford = _balance >= price;
                      String imgUrl = item['image_url'] ?? "";
                      if (!imgUrl.startsWith("http")) imgUrl = "${AppConfig.apiUrl}/$imgUrl";

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
                                child: Image.network(imgUrl, fit: BoxFit.cover, errorBuilder: (c, e, s) => const Icon(Icons.inventory_2, size: 50, color: Colors.grey)),
                              ),
                            ),
                            Expanded(
                              flex: 4,
                              child: Padding(
                                padding: const EdgeInsets.all(6.0),
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(item['name'] ?? "Sản phẩm", style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold), maxLines: 2, overflow: TextOverflow.ellipsis, textAlign: TextAlign.center),
                                    Text("${price.toStringAsFixed(0)} đ", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.orange)),
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
                                  foregroundColor: Colors.white, padding: EdgeInsets.zero, minimumSize: const Size(double.infinity, 30),
                                ),
                                child: Text(canAfford ? labels["btn_buy"]! : labels["btn_ask"]!, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
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
                    decoration: const BoxDecoration(color: Colors.white, boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 5, offset: Offset(0, -2))]),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        ElevatedButton.icon(
                          onPressed: _currentPage > 0 ? () => setState(() => _currentPage--) : null,
                          icon: const Icon(Icons.arrow_back_ios, size: 12),
                          label: Text(labels["btn_prev"]!, style: const TextStyle(fontSize: 12)),
                        ),
                        Text("${labels['page']} ${_currentPage + 1} / $totalPages", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        ElevatedButton(
                          onPressed: _currentPage < totalPages - 1 ? () => setState(() => _currentPage++) : null,
                          child: Row(mainAxisSize: MainAxisSize.min, children: [Text(labels["btn_next"]!, style: const TextStyle(fontSize: 12)), const Icon(Icons.arrow_forward_ios, size: 12)]),
                        ),
                      ],
                    ),
                  )
              ],
            ),
    );
  }
}