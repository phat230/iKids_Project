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
  
  // Lưu trạng thái học sinh được chọn cho TỪNG sản phẩm riêng biệt
  final Map<String, String> _selectedChildPerProduct = {};

  // ================= BỘ TỪ ĐIỂN SONG NGỮ HOÀN CHỈNH =================
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
      // ✅ ĐỌC NGÔN NGỮ TỪ BỘ NHỚ LÚC KHỞI TẠO
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      _token = await _storage.read(key: 'jwt_token') ?? "";
      _parentId = await _storage.read(key: 'user_id') ?? "";

      if (_token.isEmpty || _parentId.isEmpty) return;

      final headers = {
        "Authorization": "Bearer $_token",
        "parent-id": _parentId,
        "Content-Type": "application/json"
      };

      // 1. Lấy số dư ví (Profile Gamification)
      final profileRes = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/gamification/profile/$_parentId'), headers: headers);
      if (profileRes.statusCode == 200) {
        _balance = (jsonDecode(utf8.decode(profileRes.bodyBytes))['balance'] ?? 0).toDouble();
      }

      // 2. Lấy danh sách con em
      final childrenRes = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/parent/my-children'), headers: headers);
      if (childrenRes.statusCode == 200) {
        _children = jsonDecode(utf8.decode(childrenRes.bodyBytes));
      }

      // 3. Lấy danh sách sản phẩm
      final productsRes = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/products'), headers: headers);
      if (productsRes.statusCode == 200) {
        _products = jsonDecode(utf8.decode(productsRes.bodyBytes));
        
        // Khởi tạo mặc định chọn bé đầu tiên cho tất cả sản phẩm
        if (_children.isNotEmpty) {
          String firstChildId = _children[0]['id'];
          for (var p in _products) {
            String pId = p['id'] ?? p['_id'];
            _selectedChildPerProduct[pId] = firstChildId;
          }
        }
      }

    } catch (e) {
      debugPrint("Lỗi tải Cửa hàng: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // Hàm xử lý Mua / Tặng quà
  Future<void> _purchaseProduct(Map<String, dynamic> product) async {
    final labels = _labels[_lang]!;
    double price = (product['price'] ?? 0).toDouble();
    String productId = product['id'] ?? product['_id'];
    String? targetChildId = _selectedChildPerProduct[productId];

    if (targetChildId == null) return;

    if (_balance < price) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_err_balance"]!), backgroundColor: Colors.red));
      return;
    }

    showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator(color: Colors.green)));

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/products/purchase'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode({
          "user_id": _parentId, 
          "product_id": productId,
          "target_student_id": targetChildId 
        }),
      ).timeout(const Duration(seconds: 15));

      if (mounted) Navigator.pop(context); 

      if (response.statusCode == 200) {
        final childName = _children.firstWhere((c) => c['id'] == targetChildId)['name'] ?? labels['lbl_be'];
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("🎉 ${labels['msg_success']} **$childName**!"), backgroundColor: Colors.green));
        _initData(); 
      } else {
        final error = jsonDecode(utf8.decode(response.bodyBytes));
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("❌ ${error['detail'] ?? labels['err_purchase']!}"), backgroundColor: Colors.red));
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["err_network"]!), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _initData),
          // ✅ NÚT CHUYỂN ĐỔI NGÔN NGỮ ĐỒNG BỘ
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
        : _children.isEmpty 
            ? Center(child: Padding(padding: const EdgeInsets.all(20), child: Text(labels["warn_no_child"]!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red, fontSize: 16))))
            : Column(
                children: [
                  // --- Banner Số dư ví ---
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(15),
                    color: Colors.green[50],
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text("💳 ${labels['sidebar_balance']}:", style: TextStyle(color: Colors.green[800], fontSize: 16, fontWeight: FontWeight.bold)),
                        Text("${_balance.toStringAsFixed(0)} VNĐ", style: const TextStyle(color: Colors.green, fontSize: 18, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),

                  // --- Lưới Sản Phẩm ---
                  Expanded(
                    child: _products.isEmpty 
                      ? Center(child: Text(labels["info_updating"]!))
                      : GridView.builder(
                          padding: const EdgeInsets.all(12),
                          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 2, 
                            crossAxisSpacing: 12, 
                            mainAxisSpacing: 12, 
                            childAspectRatio: 0.55 
                          ),
                          itemCount: _products.length,
                          itemBuilder: (context, index) {
                            final product = _products[index];
                            String pId = product['id'] ?? product['_id'];
                            
                            // Xử lý tên đa ngôn ngữ thông minh
                            String pName = labels["lbl_default_product"]!;
                            if (product['name'] is Map) {
                              pName = product['name'][_lang] ?? product['name']['vi'] ?? labels["lbl_default_product"]!;
                            } else if (product['name'] is String) {
                              pName = product['name'];
                            }

                            // Xử lý link ảnh
                            String imgPath = product['image_url'] ?? "";
                            String fullImgUrl = imgPath.startsWith("static/") ? '${AppConfig.apiUrl}/$imgPath' : (imgPath.isEmpty ? "https://via.placeholder.com/150" : imgPath);

                            return Card(
                              elevation: 2,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              clipBehavior: Clip.antiAlias,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  // Ảnh sản phẩm
                                  Expanded(
                                    child: Image.network(
                                      fullImgUrl, 
                                      fit: BoxFit.cover,
                                      errorBuilder: (_, __, ___) => Container(color: Colors.grey[300], child: const Icon(Icons.broken_image, color: Colors.grey, size: 40)),
                                    ),
                                  ),
                                  
                                  Padding(
                                    padding: const EdgeInsets.all(8.0),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(pName, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                        const SizedBox(height: 4),
                                        Text("${labels['lbl_price']}: ${product['price']} VNĐ", style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold, fontSize: 12)),
                                        const SizedBox(height: 8),
                                        
                                        // Dropdown chọn bé
                                        Text("${labels['lbl_gift_to']}:", style: const TextStyle(fontSize: 10, color: Colors.grey)),
                                        Container(
                                          height: 30,
                                          padding: const EdgeInsets.symmetric(horizontal: 8),
                                          decoration: BoxDecoration(border: Border.all(color: Colors.grey[300]!), borderRadius: BorderRadius.circular(5)),
                                          child: DropdownButtonHideUnderline(
                                            child: DropdownButton<String>(
                                              isExpanded: true,
                                              value: _selectedChildPerProduct[pId],
                                              iconSize: 16,
                                              style: const TextStyle(fontSize: 11, color: Colors.black),
                                              items: _children.map((c) {
                                                String cName = c['full_name'] ?? c['name'] ?? "${labels['lbl_be']} (${c['id'].toString().substring(c['id'].toString().length - 4)})";
                                                return DropdownMenuItem<String>(value: c['id'].toString(), child: Text(cName, overflow: TextOverflow.ellipsis));
                                              }).toList(),
                                              onChanged: (val) {
                                                if (val != null) setState(() => _selectedChildPerProduct[pId] = val);
                                              },
                                            ),
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        
                                        // Nút mua
                                        SizedBox(
                                          width: double.infinity,
                                          height: 32,
                                          child: ElevatedButton(
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor: Colors.green, 
                                              foregroundColor: Colors.white,
                                              padding: EdgeInsets.zero,
                                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6))
                                            ),
                                            onPressed: () => _purchaseProduct(product),
                                            child: Text(labels["btn_confirm"]!, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
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
                  )
                ],
              ),
    );
  }
}