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
      "default_product": "Sản phẩm",
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
      "default_product": "Product",
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchStoreData();
  }

  Future<void> _fetchStoreData() async {
    if (!mounted) return;

    setState(() => _isLoading = true);

    try {
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) {
        _lang = savedLang;
      }

      _userId = await _storage.read(key: 'user_id');

      if (_userId == null || _userId!.isEmpty) {
        throw Exception(_locales[_lang]!["err_not_found"]);
      }

      final profile = await _apiService.getAuthorized(
        '$apiPrefix/gamification/profile/$_userId',
      );

      final products = await _apiService.getAuthorized(
        '$apiPrefix/products',
      );

      if (!mounted) return;

      setState(() {
        _balance = _toDouble(profile['balance']);
        _allProducts = products is List ? products : [];
        _isLoading = false;
        _currentPage = 0;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() => _isLoading = false);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("${_locales[_lang]!['err_load']} $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  double _toDouble(dynamic value) {
    if (value == null) return 0.0;

    if (value is int) return value.toDouble();

    if (value is double) return value;

    return double.tryParse(value.toString()) ?? 0.0;
  }

  String _getProductId(Map<String, dynamic> product) {
    return (product['id'] ?? product['_id'] ?? "").toString();
  }

  String _getLocalized(dynamic field, String defaultValue) {
    if (field == null) return defaultValue;

    if (field is Map) {
      return field[_lang]?.toString() ??
          field['vi']?.toString() ??
          field['en']?.toString() ??
          defaultValue;
    }

    return field.toString();
  }

  String _getProductImageUrl(dynamic imageUrl) {
    const fallbackUrl =
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png";

    if (imageUrl == null) {
      return fallbackUrl;
    }

    String url = imageUrl.toString().trim();

    if (url.isEmpty ||
        url.toLowerCase().contains("placeholder") ||
        url.toLowerCase().contains("anh_laptop.jpg")) {
      return fallbackUrl;
    }

    // Ảnh Cloudinary hoặc ảnh online
    if (url.startsWith("http://") || url.startsWith("https://")) {
      return url;
    }

    // Ảnh local cũ dạng /static/...
    if (url.startsWith("/")) {
      url = url.substring(1);
    }

    // Ảnh local cũ dạng static/...
    return "${AppConfig.apiUrl}/$url";
  }

  Future<void> _handleAction(Map<String, dynamic> product) async {
    final labels = _locales[_lang]!;

    double price = _toDouble(product['price']);
    String productId = _getProductId(product);
    String productName = _getLocalized(
      product['name'],
      labels["default_product"]!,
    );

    String? token = await _storage.read(key: 'jwt_token');

    if (_userId == null || _userId!.isEmpty) {
      _showSnack(labels["err_not_found"]!, Colors.red);
      return;
    }

    if (productId.isEmpty) {
      _showSnack("Không tìm thấy mã sản phẩm.", Colors.red);
      return;
    }

    if (_balance >= price) {
      try {
        final response = await http.post(
          Uri.parse('${AppConfig.apiUrl}$apiPrefix/products/purchase'),
          headers: {
            'Content-Type': 'application/json',
            if (token != null && token.isNotEmpty)
              'Authorization': 'Bearer $token',
          },
          body: jsonEncode({
            "user_id": _userId,
            "product_id": productId,
          }),
        );

        if (response.statusCode == 200) {
          if (!mounted) return;

          setState(() {
            _balance -= price;
          });

          _showSnack(labels["msg_buy_success"]!, Colors.green);
        } else {
          final err = _decodeJsonSafe(response.body);
          throw Exception(err['detail'] ?? response.body);
        }
      } catch (e) {
        _showSnack("Lỗi: $e", Colors.red);
      }
    } else {
      try {
        final response = await http.post(
          Uri.parse('${AppConfig.apiUrl}$apiPrefix/store/request-purchase'),
          headers: {
            'Content-Type': 'application/json',
            if (token != null && token.isNotEmpty)
              'Authorization': 'Bearer $token',
          },
          body: jsonEncode({
            "student_id": _userId,
            "product_id": productId,
            "product_name": productName,
            "price": price,
          }),
        );

        if (response.statusCode == 200) {
          _showSnack(labels["msg_ask_success"]!, Colors.blue);
        } else {
          final err = _decodeJsonSafe(response.body);
          throw Exception(err['detail'] ?? response.body);
        }
      } catch (e) {
        _showSnack("Lỗi: $e", Colors.red);
      }
    }
  }

  Map<String, dynamic> _decodeJsonSafe(String body) {
    try {
      return jsonDecode(body);
    } catch (_) {
      return {};
    }
  }

  void _showSnack(String message, Color color) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;

    int totalPages = (_allProducts.length / _itemsPerPage).ceil();

    if (totalPages == 0) {
      totalPages = 1;
    }

    if (_currentPage >= totalPages) {
      _currentPage = totalPages - 1;
    }

    int startIndex = _currentPage * _itemsPerPage;
    int endIndex = startIndex + _itemsPerPage;

    if (endIndex > _allProducts.length) {
      endIndex = _allProducts.length;
    }

    List<dynamic> currentProducts = _allProducts.isEmpty
        ? []
        : _allProducts.sublist(startIndex, endIndex);

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(
          labels["title"]!,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10.0),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(15),
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : Text(
                        "🪙 ${_balance.toStringAsFixed(0)} VNĐ",
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
              ),
            ),
          ),
          TextButton(
            onPressed: () async {
              setState(() {
                _lang = _lang == "vi" ? "en" : "vi";
              });

              await _storage.write(key: 'app_lang', value: _lang);
            },
            child: Text(
              _lang.toUpperCase(),
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          )
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Colors.green),
            )
          : currentProducts.isEmpty
              ? RefreshIndicator(
                  onRefresh: _fetchStoreData,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      SizedBox(
                        height: MediaQuery.of(context).size.height * 0.65,
                        child: Center(
                          child: Text(
                            labels["empty_shop"]!,
                            style: const TextStyle(fontSize: 16),
                          ),
                        ),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _fetchStoreData,
                  child: Column(
                    children: [
                      Expanded(
                        child: GridView.builder(
                          padding: const EdgeInsets.all(10),
                          gridDelegate:
                              const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 3,
                            crossAxisSpacing: 10,
                            mainAxisSpacing: 10,
                            childAspectRatio: 0.55,
                          ),
                          itemCount: currentProducts.length,
                          itemBuilder: (context, index) {
                            final item = Map<String, dynamic>.from(
                              currentProducts[index],
                            );

                            double price = _toDouble(item['price']);
                            bool canAfford = _balance >= price;

                            String imgUrl = _getProductImageUrl(
                              item['image_url'],
                            );

                            String productName = _getLocalized(
                              item['name'],
                              labels["default_product"]!,
                            );

                            return Card(
                              elevation: 2,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Expanded(
                                    flex: 4,
                                    child: ClipRRect(
                                      borderRadius:
                                          const BorderRadius.vertical(
                                        top: Radius.circular(10),
                                      ),
                                      child: Image.network(
                                        imgUrl,
                                        fit: BoxFit.cover,
                                        loadingBuilder:
                                            (context, child, loadingProgress) {
                                          if (loadingProgress == null) {
                                            return child;
                                          }

                                          return const Center(
                                            child: SizedBox(
                                              width: 24,
                                              height: 24,
                                              child:
                                                  CircularProgressIndicator(
                                                strokeWidth: 2,
                                              ),
                                            ),
                                          );
                                        },
                                        errorBuilder: (context, error, stack) {
                                          return Container(
                                            color: Colors.grey[200],
                                            child: const Icon(
                                              Icons.inventory_2,
                                              size: 50,
                                              color: Colors.grey,
                                            ),
                                          );
                                        },
                                      ),
                                    ),
                                  ),
                                  Expanded(
                                    flex: 4,
                                    child: Padding(
                                      padding: const EdgeInsets.all(6.0),
                                      child: Column(
                                        mainAxisAlignment:
                                            MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            productName,
                                            style: const TextStyle(
                                              fontSize: 11,
                                              fontWeight: FontWeight.bold,
                                            ),
                                            maxLines: 2,
                                            overflow: TextOverflow.ellipsis,
                                            textAlign: TextAlign.center,
                                          ),
                                          Text(
                                            "${price.toStringAsFixed(0)} đ",
                                            style: const TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.bold,
                                              color: Colors.orange,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  Padding(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 4.0,
                                      vertical: 4.0,
                                    ),
                                    child: ElevatedButton(
                                      onPressed: () => _handleAction(item),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: canAfford
                                            ? Colors.green
                                            : Colors.blueAccent,
                                        foregroundColor: Colors.white,
                                        padding: EdgeInsets.zero,
                                        minimumSize:
                                            const Size(double.infinity, 30),
                                      ),
                                      child: Text(
                                        canAfford
                                            ? labels["btn_buy"]!
                                            : labels["btn_ask"]!,
                                        style: const TextStyle(
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
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
                          padding: const EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 20,
                          ),
                          decoration: const BoxDecoration(
                            color: Colors.white,
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black12,
                                blurRadius: 5,
                                offset: Offset(0, -2),
                              )
                            ],
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              ElevatedButton.icon(
                                onPressed: _currentPage > 0
                                    ? () {
                                        setState(() {
                                          _currentPage--;
                                        });
                                      }
                                    : null,
                                icon: const Icon(
                                  Icons.arrow_back_ios,
                                  size: 12,
                                ),
                                label: Text(
                                  labels["btn_prev"]!,
                                  style: const TextStyle(fontSize: 12),
                                ),
                              ),
                              Text(
                                "${labels['page']} ${_currentPage + 1} / $totalPages",
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                              ElevatedButton(
                                onPressed: _currentPage < totalPages - 1
                                    ? () {
                                        setState(() {
                                          _currentPage++;
                                        });
                                      }
                                    : null,
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                      labels["btn_next"]!,
                                      style: const TextStyle(fontSize: 12),
                                    ),
                                    const Icon(
                                      Icons.arrow_forward_ios,
                                      size: 12,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        )
                    ],
                  ),
                ),
    );
  }
}