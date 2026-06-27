import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import '../../core/config.dart';

class ParentShopScreen extends StatefulWidget {
  const ParentShopScreen({super.key});

  @override
  State<ParentShopScreen> createState() => _ParentShopScreenState();
}

class _ParentShopScreenState extends State<ParentShopScreen> {
  final _storage = const FlutterSecureStorage();

  bool _isLoading = true;
  String _lang = "vi";
  String _parentId = "";
  String _token = "";
  double _balance = 0.0;

  List<dynamic> _children = [];
  List<dynamic> _products = [];

  final Map<String, String> _selectedChildPerProduct = {};

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "🛍️ Cửa Hàng Quà Tặng iKids",
      "sidebar_balance": "Số dư ví",
      "warn_no_child": "⚠️ Chưa có hồ sơ con em. Vui lòng tạo tài khoản cho bé trước.",
      "info_updating": "ℹ️ Cửa hàng đang cập nhật sản phẩm mới.",
      "lbl_price": "Giá",
      "lbl_gift_to": "Tặng cho",
      "lbl_be": "Bé",
      "btn_confirm": "Tặng ngay",
      "msg_success": "Đã tặng quà thành công cho",
      "msg_err_balance": "❌ Không đủ số dư trong ví!",
      "err_network": "Mất kết nối mạng!",
      "err_purchase": "Lỗi mua hàng",
      "lbl_default_product": "Sản phẩm",
      "err_missing_product": "Không tìm thấy mã sản phẩm.",
      "err_missing_child": "Vui lòng chọn bé nhận quà.",
    },
    "en": {
      "title": "🛍️ iKids Gift Store",
      "sidebar_balance": "Wallet Balance",
      "warn_no_child": "⚠️ No student profiles found. Please register your child first.",
      "info_updating": "ℹ️ The store inventory is currently being updated.",
      "lbl_price": "Price",
      "lbl_gift_to": "Gift to",
      "lbl_be": "Kid",
      "btn_confirm": "Gift Now",
      "msg_success": "Successfully gifted reward to",
      "msg_err_balance": "❌ Insufficient wallet balance!",
      "err_network": "Network connection lost!",
      "err_purchase": "Purchase error",
      "lbl_default_product": "Product",
      "err_missing_product": "Product ID not found.",
      "err_missing_child": "Please select a child to receive the gift.",
    }
  };

  @override
  void initState() {
    super.initState();
    _initData();
  }

  Future<void> _initData() async {
    if (!mounted) return;

    setState(() => _isLoading = true);

    try {
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) {
        _lang = savedLang;
      }

      _token = await _storage.read(key: 'jwt_token') ?? "";
      _parentId = await _storage.read(key: 'user_id') ?? "";

      if (_token.isEmpty || _parentId.isEmpty) {
        throw Exception("Missing token or parent id");
      }

      final headers = {
        "Authorization": "Bearer $_token",
        "parent-id": _parentId,
        "Content-Type": "application/json",
      };

      final profileRes = await http.get(
        Uri.parse('${AppConfig.apiTv3}/gamification/profile/$_parentId'),
        headers: headers,
      );

      final childrenRes = await http.get(
        Uri.parse('${AppConfig.apiTv3}/parent/my-children'),
        headers: headers,
      );

      final productsRes = await http.get(
        Uri.parse('${AppConfig.apiTv3}/products'),
        headers: headers,
      );

      double newBalance = 0.0;
      List<dynamic> newChildren = [];
      List<dynamic> newProducts = [];

      if (profileRes.statusCode == 200) {
        final profileData = jsonDecode(utf8.decode(profileRes.bodyBytes));
        newBalance = _toDouble(profileData['balance']);
      }

      if (childrenRes.statusCode == 200) {
        final childrenData = jsonDecode(utf8.decode(childrenRes.bodyBytes));
        newChildren = childrenData is List ? childrenData : [];
      }

      if (productsRes.statusCode == 200) {
        final productsData = jsonDecode(utf8.decode(productsRes.bodyBytes));
        newProducts = productsData is List ? productsData : [];
      }

      final Map<String, String> newSelectedMap = {};

      if (newChildren.isNotEmpty) {
        final firstChildId = _getChildId(newChildren.first);

        for (final product in newProducts) {
          if (product is Map) {
            final pId = _getProductId(Map<String, dynamic>.from(product));
            if (pId.isNotEmpty) {
              final oldSelected = _selectedChildPerProduct[pId];

              final isOldChildStillExists = newChildren.any(
                (child) => _getChildId(child) == oldSelected,
              );

              newSelectedMap[pId] =
                  isOldChildStillExists ? oldSelected! : firstChildId;
            }
          }
        }
      }

      if (!mounted) return;

      setState(() {
        _balance = newBalance;
        _children = newChildren;
        _products = newProducts;
        _selectedChildPerProduct
          ..clear()
          ..addAll(newSelectedMap);
        _isLoading = false;
      });
    } catch (e) {
      debugPrint("Lỗi tải Cửa hàng phụ huynh: $e");

      if (!mounted) return;

      setState(() => _isLoading = false);

      _showSnack(
        _labels[_lang]!["err_network"]!,
        Colors.red,
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

  String _getChildId(dynamic child) {
    if (child is Map) {
      return (child['id'] ?? child['_id'] ?? "").toString();
    }
    return "";
  }

  String _getChildName(dynamic child) {
    final labels = _labels[_lang]!;

    if (child is Map) {
      final childId = _getChildId(child);
      final fallbackId = childId.length >= 4
          ? childId.substring(childId.length - 4)
          : childId;

      return (child['full_name'] ??
              child['name'] ??
              "${labels['lbl_be']} $fallbackId")
          .toString();
    }

    return labels["lbl_be"]!;
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

    // Ảnh Cloudinary hoặc URL online
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

  Map<String, dynamic> _decodeJsonSafe(String body) {
    try {
      final data = jsonDecode(body);
      if (data is Map<String, dynamic>) {
        return data;
      }
      return {};
    } catch (_) {
      return {};
    }
  }

  Future<void> _purchaseProduct(Map<String, dynamic> product) async {
    final labels = _labels[_lang]!;

    final price = _toDouble(product['price']);
    final productId = _getProductId(product);
    final targetChildId = _selectedChildPerProduct[productId];

    if (productId.isEmpty) {
      _showSnack(labels["err_missing_product"]!, Colors.red);
      return;
    }

    if (targetChildId == null || targetChildId.isEmpty) {
      _showSnack(labels["err_missing_child"]!, Colors.red);
      return;
    }

    if (_balance < price) {
      _showSnack(labels["msg_err_balance"]!, Colors.red);
      return;
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(
        child: CircularProgressIndicator(color: Colors.green),
      ),
    );

    try {
      final response = await http
          .post(
            Uri.parse('${AppConfig.apiTv3}/products/purchase'),
            headers: {
              "Content-Type": "application/json",
              "Authorization": "Bearer $_token",
            },
            body: jsonEncode({
              "user_id": _parentId,
              "product_id": productId,
              "target_student_id": targetChildId,
            }),
          )
          .timeout(const Duration(seconds: 20));

      if (mounted) {
        Navigator.of(context, rootNavigator: true).pop();
      }

      if (response.statusCode == 200) {
        final child = _children.firstWhere(
          (c) => _getChildId(c) == targetChildId,
          orElse: () => {},
        );

        final childName = _getChildName(child);

        _showSnack(
          "🎉 ${labels['msg_success']} $childName!",
          Colors.green,
        );

        await _initData();
      } else {
        final error = _decodeJsonSafe(utf8.decode(response.bodyBytes));
        _showSnack(
          "❌ ${error['detail'] ?? labels['err_purchase']!}",
          Colors.red,
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.of(context, rootNavigator: true).pop();
      }

      _showSnack(labels["err_network"]!, Colors.red);
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
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(
          labels["title"]!,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _initData,
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
          : _children.isEmpty
              ? RefreshIndicator(
                  onRefresh: _initData,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      SizedBox(
                        height: MediaQuery.of(context).size.height * 0.7,
                        child: Center(
                          child: Padding(
                            padding: const EdgeInsets.all(20),
                            child: Text(
                              labels["warn_no_child"]!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                color: Colors.red,
                                fontSize: 16,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(15),
                      color: Colors.green[50],
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            "💳 ${labels['sidebar_balance']}:",
                            style: TextStyle(
                              color: Colors.green[800],
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            "${_balance.toStringAsFixed(0)} VNĐ",
                            style: const TextStyle(
                              color: Colors.green,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),

                    Expanded(
                      child: RefreshIndicator(
                        onRefresh: _initData,
                        child: _products.isEmpty
                            ? ListView(
                                physics:
                                    const AlwaysScrollableScrollPhysics(),
                                children: [
                                  SizedBox(
                                    height:
                                        MediaQuery.of(context).size.height *
                                            0.6,
                                    child: Center(
                                      child: Text(labels["info_updating"]!),
                                    ),
                                  ),
                                ],
                              )
                            : GridView.builder(
                                padding: const EdgeInsets.all(12),
                                physics:
                                    const AlwaysScrollableScrollPhysics(),
                                gridDelegate:
                                    const SliverGridDelegateWithFixedCrossAxisCount(
                                  crossAxisCount: 2,
                                  crossAxisSpacing: 12,
                                  mainAxisSpacing: 12,
                                  childAspectRatio: 0.55,
                                ),
                                itemCount: _products.length,
                                itemBuilder: (context, index) {
                                  final product = Map<String, dynamic>.from(
                                    _products[index],
                                  );

                                  final pId = _getProductId(product);

                                  final pName = _getLocalized(
                                    product['name'],
                                    labels["lbl_default_product"]!,
                                  );

                                  final price = _toDouble(product['price']);

                                  final fullImgUrl = _getProductImageUrl(
                                    product['image_url'],
                                  );

                                  String? selectedChild =
                                      _selectedChildPerProduct[pId];

                                  final childIds =
                                      _children.map(_getChildId).toList();

                                  if (selectedChild == null ||
                                      !childIds.contains(selectedChild)) {
                                    selectedChild = childIds.isNotEmpty
                                        ? childIds.first
                                        : null;
                                  }

                                  return Card(
                                    elevation: 2,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    clipBehavior: Clip.antiAlias,
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.stretch,
                                      children: [
                                        Expanded(
                                          child: Image.network(
                                            fullImgUrl,
                                            fit: BoxFit.cover,
                                            loadingBuilder: (
                                              context,
                                              child,
                                              loadingProgress,
                                            ) {
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
                                            errorBuilder: (_, __, ___) =>
                                                Container(
                                              color: Colors.grey[300],
                                              child: const Icon(
                                                Icons.broken_image,
                                                color: Colors.grey,
                                                size: 40,
                                              ),
                                            ),
                                          ),
                                        ),

                                        Padding(
                                          padding: const EdgeInsets.all(8.0),
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                pName,
                                                maxLines: 2,
                                                overflow:
                                                    TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.bold,
                                                  fontSize: 13,
                                                ),
                                              ),

                                              const SizedBox(height: 4),

                                              Text(
                                                "${labels['lbl_price']}: ${price.toStringAsFixed(0)} VNĐ",
                                                style: const TextStyle(
                                                  color: Colors.blue,
                                                  fontWeight: FontWeight.bold,
                                                  fontSize: 12,
                                                ),
                                              ),

                                              const SizedBox(height: 8),

                                              Text(
                                                "${labels['lbl_gift_to']}:",
                                                style: const TextStyle(
                                                  fontSize: 10,
                                                  color: Colors.grey,
                                                ),
                                              ),

                                              Container(
                                                height: 30,
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                  horizontal: 8,
                                                ),
                                                decoration: BoxDecoration(
                                                  border: Border.all(
                                                    color:
                                                        Colors.grey[300]!,
                                                  ),
                                                  borderRadius:
                                                      BorderRadius.circular(5),
                                                ),
                                                child:
                                                    DropdownButtonHideUnderline(
                                                  child:
                                                      DropdownButton<String>(
                                                    isExpanded: true,
                                                    value: selectedChild,
                                                    iconSize: 16,
                                                    style: const TextStyle(
                                                      fontSize: 11,
                                                      color: Colors.black,
                                                    ),
                                                    items: _children.map((c) {
                                                      final childId =
                                                          _getChildId(c);
                                                      final childName =
                                                          _getChildName(c);

                                                      return DropdownMenuItem<
                                                          String>(
                                                        value: childId,
                                                        child: Text(
                                                          childName,
                                                          overflow:
                                                              TextOverflow
                                                                  .ellipsis,
                                                        ),
                                                      );
                                                    }).toList(),
                                                    onChanged: (val) {
                                                      if (val != null) {
                                                        setState(() {
                                                          _selectedChildPerProduct[
                                                              pId] = val;
                                                        });
                                                      }
                                                    },
                                                  ),
                                                ),
                                              ),

                                              const SizedBox(height: 8),

                                              SizedBox(
                                                width: double.infinity,
                                                height: 32,
                                                child: ElevatedButton(
                                                  style:
                                                      ElevatedButton.styleFrom(
                                                    backgroundColor:
                                                        Colors.green,
                                                    foregroundColor:
                                                        Colors.white,
                                                    padding: EdgeInsets.zero,
                                                    shape:
                                                        RoundedRectangleBorder(
                                                      borderRadius:
                                                          BorderRadius.circular(
                                                        6,
                                                      ),
                                                    ),
                                                  ),
                                                  onPressed: () =>
                                                      _purchaseProduct(
                                                    product,
                                                  ),
                                                  child: Text(
                                                    labels["btn_confirm"]!,
                                                    style: const TextStyle(
                                                      fontSize: 11,
                                                      fontWeight:
                                                          FontWeight.bold,
                                                    ),
                                                  ),
                                                ),
                                              )
                                            ],
                                          ),
                                        )
                                      ],
                                    ),
                                  );
                                },
                              ),
                      ),
                    )
                  ],
                ),
    );
  }
}