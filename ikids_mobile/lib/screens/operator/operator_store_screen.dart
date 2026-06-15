import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class OperatorStoreScreen extends StatefulWidget {
  const OperatorStoreScreen({super.key});

  @override
  State<OperatorStoreScreen> createState() => _OperatorStoreScreenState();
}

class _OperatorStoreScreenState extends State<OperatorStoreScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";
  String _token = "";
  
  List<dynamic> _products = [];
  List<dynamic> _filteredProducts = [];
  
  // Trạng thái Form
  Map<String, dynamic>? _editingProduct;
  final _nameController = TextEditingController();
  final _descController = TextEditingController();
  final _priceController = TextEditingController();
  final _searchController = TextEditingController();

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Kho hàng iKids",
      "caption": "Thêm mới, chỉnh sửa hoặc gỡ bỏ sản phẩm.",
      "stat_total": "Tổng sản phẩm",
      "stat_max_price": "Giá cao nhất",
      "form_edit_title": "📝 ĐANG CHỈNH SỬA",
      "form_add_title": "➕ THÊM SẢN PHẨM MỚI",
      "input_name": "Tên sản phẩm (*)",
      "input_desc": "Mô tả chi tiết",
      "input_price": "Giá bán (VNĐ)",
      "btn_save": "Lưu cập nhật",
      "btn_add": "Đăng sản phẩm",
      "btn_cancel": "Hủy",
      "msg_success": "Thao tác thành công!",
      "msg_err_empty": "⚠️ Thiếu thông tin bắt buộc hoặc giá không hợp lệ!",
      "sub_catalog": "📦 Danh mục hàng hóa",
      "search_placeholder": "Tìm kiếm sản phẩm...",
      "no_products": "Chưa có sản phẩm nào trong kho.",
      "btn_edit": "Sửa",
      "btn_del": "Xóa",
    },
    "en": {
      "title": "iKids Inventory",
      "caption": "Add, modify, or remove store products.",
      "stat_total": "Total Products",
      "stat_max_price": "Highest Price",
      "form_edit_title": "📝 EDITING PRODUCT",
      "form_add_title": "➕ ADD NEW PRODUCT",
      "input_name": "Product Name (*)",
      "input_desc": "Detailed Description",
      "input_price": "Price (Points/VND)",
      "btn_save": "Save Changes",
      "btn_add": "Publish Product",
      "btn_cancel": "Cancel",
      "msg_success": "Operation successful!",
      "msg_err_empty": "⚠️ Required fields cannot be empty!",
      "sub_catalog": "📦 Inventory Catalog",
      "search_placeholder": "Search rewards...",
      "no_products": "The store database is currently empty.",
      "btn_edit": "Edit",
      "btn_del": "Delete",
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
      _token = await _storage.read(key: 'jwt_token') ?? "";
      if (_token.isEmpty) return;
      await _fetchProducts();
    } catch (e) {
      debugPrint("Lỗi Init Data: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _fetchProducts() async {
    try {
      final res = await http.get(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/products'),
        headers: {"Authorization": "Bearer $_token"}
      );
      if (res.statusCode == 200) {
        _products = jsonDecode(utf8.decode(res.bodyBytes));
        _filteredProducts = List.from(_products);
      }
    } catch (e) {
      debugPrint("Lỗi Fetch Products: $e");
    }
  }

  // Hàm hỗ trợ bóc tách ngôn ngữ từ JSON (Giống get_localized_value trên Python)
  String _getLocalized(dynamic data) {
    if (data == null) return "";
    if (data is Map) {
      return data[_lang] ?? data['vi'] ?? "";
    }
    return data.toString();
  }

  void _filterProducts(String query) {
    setState(() {
      if (query.isEmpty) {
        _filteredProducts = List.from(_products);
      } else {
        _filteredProducts = _products.where((p) {
          String name = _getLocalized(p['name']).toLowerCase();
          return name.contains(query.toLowerCase());
        }).toList();
      }
    });
  }

  void _startEdit(Map<String, dynamic> product) {
    setState(() {
      _editingProduct = product;
      _nameController.text = _getLocalized(product['name']);
      _descController.text = _getLocalized(product['description']);
      _priceController.text = product['price']?.toString() ?? "0";
    });
  }

  void _cancelEdit() {
    setState(() {
      _editingProduct = null;
      _nameController.clear();
      _descController.clear();
      _priceController.clear();
    });
  }

  Future<void> _submitForm() async {
    final name = _nameController.text.trim();
    final desc = _descController.text.trim();
    final price = double.tryParse(_priceController.text) ?? 0;

    if (name.isEmpty || price <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!["msg_err_empty"]!), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isLoading = true);

    try {
      final payload = {
        "name": name,
        "price": price,
        "description": desc,
        "image_url": _editingProduct != null ? _editingProduct!['image_url'] : "static/placeholder.png", // Giữ ảnh cũ hoặc dùng Placeholder
        "updated_at": DateTime.now().toIso8601String()
      };

      http.Response res;
      if (_editingProduct != null) {
        // PUT (Sửa)
        res = await http.put(
          Uri.parse('${AppConfig.apiUrl}/api/tv3/products/${_editingProduct!['id']}'),
          headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
          body: jsonEncode(payload)
        );
      } else {
        // POST (Thêm mới)
        payload["created_at"] = DateTime.now().toIso8601String();
        res = await http.post(
          Uri.parse('${AppConfig.apiUrl}/api/tv3/products'),
          headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
          body: jsonEncode(payload)
        );
      }

      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!["msg_success"]!), backgroundColor: Colors.green));
        _cancelEdit();
        await _fetchProducts();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi Server!"), backgroundColor: Colors.red));
      }
    } catch (e) {
      debugPrint("Lỗi Submit: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteProduct(String id) async {
    setState(() => _isLoading = true);
    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/products/$id'),
        headers: {"Authorization": "Bearer $_token"}
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!["msg_success"]!), backgroundColor: Colors.green));
        await _fetchProducts();
      }
    } catch (e) {
      debugPrint("Lỗi Xóa: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    // Tính toán thống kê
    int totalProducts = _products.length;
    double maxPrice = 0;
    if (_products.isNotEmpty) {
      maxPrice = _products.map((p) => (p['price'] ?? 0).toDouble()).reduce((a, b) => a > b ? a : b);
    }

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        actions: [
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.teal))
        : SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(labels["caption"]!, style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic)),
                const SizedBox(height: 15),

                // --- KHỐI THỐNG KÊ ---
                Row(
                  children: [
                    Expanded(child: _buildStatCard(labels["stat_total"]!, "$totalProducts", Icons.inventory_2, Colors.blue)),
                    const SizedBox(width: 10),
                    Expanded(child: _buildStatCard(labels["stat_max_price"]!, "${maxPrice.toStringAsFixed(0)}đ", Icons.payments, Colors.orange)),
                  ],
                ),
                const SizedBox(height: 20),

                // --- FORM THÊM / SỬA ---
                Card(
                  elevation: 3,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  child: Padding(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _editingProduct != null ? labels["form_edit_title"]! : labels["form_add_title"]!,
                          style: TextStyle(fontWeight: FontWeight.bold, color: _editingProduct != null ? Colors.orange : Colors.teal, fontSize: 16),
                        ),
                        const Divider(),
                        TextField(controller: _nameController, decoration: InputDecoration(labelText: labels["input_name"])),
                        const SizedBox(height: 10),
                        TextField(controller: _priceController, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: labels["input_price"])),
                        const SizedBox(height: 10),
                        TextField(controller: _descController, maxLines: 3, decoration: InputDecoration(labelText: labels["input_desc"])),
                        const SizedBox(height: 20),
                        Row(
                          children: [
                            if (_editingProduct != null) ...[
                              Expanded(child: OutlinedButton(onPressed: _cancelEdit, child: Text(labels["btn_cancel"]!))),
                              const SizedBox(width: 10),
                            ],
                            Expanded(
                              flex: 2,
                              child: ElevatedButton(
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white),
                                onPressed: _submitForm,
                                child: Text(_editingProduct != null ? labels["btn_save"]! : labels["btn_add"]!),
                              ),
                            ),
                          ],
                        )
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 25),

                // --- DANH SÁCH SẢN PHẨM ---
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(labels["sub_catalog"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.teal)),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: _searchController,
                  onChanged: _filterProducts,
                  decoration: InputDecoration(
                    hintText: labels["search_placeholder"],
                    prefixIcon: const Icon(Icons.search),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none)
                  ),
                ),
                const SizedBox(height: 15),

                if (_filteredProducts.isEmpty)
                  Center(child: Padding(padding: const EdgeInsets.all(20.0), child: Text(labels["no_products"]!)))
                else
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _filteredProducts.length,
                    itemBuilder: (context, index) {
                      final p = _filteredProducts[index];
                      String name = _getLocalized(p['name']);
                      String desc = _getLocalized(p['description']);
                      double price = (p['price'] ?? 0).toDouble();
                      String imgUrl = p['image_url']?.toString() ?? "";
                      
                      // Xử lý URL ảnh an toàn
                      if (imgUrl.isNotEmpty && imgUrl.startsWith("static")) {
                        imgUrl = "${AppConfig.apiUrl}/$imgUrl";
                      } else if (imgUrl.isEmpty) {
                        imgUrl = "https://via.placeholder.com/150";
                      }

                      return Card(
                        margin: const EdgeInsets.only(bottom: 15),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        child: Padding(
                          padding: const EdgeInsets.all(12.0),
                          child: Row(
                            children: [
                              // Hình ảnh
                              ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: Image.network(imgUrl, width: 80, height: 80, fit: BoxFit.cover, errorBuilder: (ctx, err, stack) => Container(width: 80, height: 80, color: Colors.grey[300], child: const Icon(Icons.image_not_supported))),
                              ),
                              const SizedBox(width: 15),
                              
                              // Thông tin
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                    const SizedBox(height: 4),
                                    Text(desc, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                    const SizedBox(height: 8),
                                    Text("${price.toStringAsFixed(0)}đ", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.orange, fontSize: 15)),
                                  ],
                                ),
                              ),
                              
                              // Nút Hành động
                              Column(
                                children: [
                                  IconButton(icon: const Icon(Icons.edit, color: Colors.blue), onPressed: () => _startEdit(p)),
                                  IconButton(icon: const Icon(Icons.delete, color: Colors.red), onPressed: () => _deleteProduct(p['id'].toString())),
                                ],
                              )
                            ],
                          ),
                        ),
                      );
                    },
                  ),
              ],
            ),
          ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withOpacity(0.3))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 10),
          Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
          Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        ],
      ),
    );
  }
}