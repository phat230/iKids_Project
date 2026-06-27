import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

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

  Map<String, dynamic>? _editingProduct;

  final _nameController = TextEditingController();
  final _descController = TextEditingController();
  final _priceController = TextEditingController();
  final _searchController = TextEditingController();

  XFile? _pickedImage;

  final Map<String, Map<String, String>> _locales = {
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
      "input_image": "Hình ảnh sản phẩm",
      "btn_pick_image": "Chọn ảnh từ thiết bị",
      "btn_save": "Lưu cập nhật",
      "btn_add": "Đăng sản phẩm",
      "btn_cancel": "Hủy",
      "msg_success": "Thao tác thành công!",
      "msg_err_empty": "⚠️ Thiếu thông tin bắt buộc hoặc giá không hợp lệ!",
      "msg_err_upload": "Upload ảnh thất bại!",
      "msg_err_server": "Lỗi Server xử lý dữ liệu!",
      "sub_catalog": "📦 Danh mục hàng hóa",
      "search_placeholder": "Tìm kiếm sản phẩm...",
      "no_products": "Chưa có sản phẩm nào trong kho.",
      "btn_edit": "Sửa",
      "btn_del": "Xóa",
      "img_keep_hint": "Không chọn ảnh mới thì hệ thống giữ ảnh cũ.",
      "current_image": "Ảnh hiện tại",
      "new_image": "Ảnh mới đã chọn",
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
      "input_image": "Product Image",
      "btn_pick_image": "Pick Image from Device",
      "btn_save": "Save Changes",
      "btn_add": "Publish Product",
      "btn_cancel": "Cancel",
      "msg_success": "Operation successful!",
      "msg_err_empty": "⚠️ Required fields cannot be empty!",
      "msg_err_upload": "Image upload failed!",
      "msg_err_server": "Server error processing data!",
      "sub_catalog": "📦 Inventory Catalog",
      "search_placeholder": "Search rewards...",
      "no_products": "The store database is currently empty.",
      "btn_edit": "Edit",
      "btn_del": "Delete",
      "img_keep_hint": "Leave empty to keep the current image.",
      "current_image": "Current image",
      "new_image": "New selected image",
    }
  };

  @override
  void initState() {
    super.initState();
    _initData();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descController.dispose();
    _priceController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _initData() async {
    if (!mounted) return;

    setState(() => _isLoading = true);

    try {
      final savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) {
        _lang = savedLang;
      }

      _token = await _storage.read(key: 'jwt_token') ?? "";

      await _fetchProducts();
    } catch (e) {
      debugPrint("Lỗi init dữ liệu kho hàng: $e");
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _fetchProducts() async {
    try {
      final res = await http.get(
        Uri.parse('${AppConfig.apiTv3}/products'),
        headers: {
          "Content-Type": "application/json",
          if (_token.isNotEmpty) "Authorization": "Bearer $_token",
        },
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));

        if (!mounted) return;

        setState(() {
          _products = data is List ? data : [];
          _filteredProducts = List.from(_products);
        });
      } else {
        debugPrint("Lỗi lấy sản phẩm: ${res.statusCode} - ${res.body}");
      }
    } catch (e) {
      debugPrint("Lỗi Fetch Products: $e");
    }
  }

  String _getLocalized(dynamic data) {
    if (data == null) return "";

    if (data is Map) {
      return data[_lang]?.toString() ?? data['vi']?.toString() ?? "";
    }

    return data.toString();
  }

  String _getProductId(Map<String, dynamic> product) {
    return (product['id'] ?? product['_id'] ?? "").toString();
  }

  double _getPrice(dynamic value) {
    if (value == null) return 0;

    if (value is int) return value.toDouble();
    if (value is double) return value;

    return double.tryParse(value.toString()) ?? 0;
  }

  String _normalizeImageUrl(dynamic imageUrl) {
    final fallbackUrl =
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png";

    if (imageUrl == null) return fallbackUrl;

    String url = imageUrl.toString().trim();

    if (url.isEmpty || url.toLowerCase().contains("placeholder")) {
      return fallbackUrl;
    }

    if (url.startsWith("http://") || url.startsWith("https://")) {
      return url;
    }

    if (url.startsWith("/")) {
      url = url.substring(1);
    }

    return "${AppConfig.baseUrl}/$url";
  }

  void _filterProducts(String query) {
    setState(() {
      if (query.trim().isEmpty) {
        _filteredProducts = List.from(_products);
      } else {
        _filteredProducts = _products.where((p) {
          final name = _getLocalized(p['name']).toLowerCase();
          return name.contains(query.toLowerCase());
        }).toList();
      }
    });
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();

    final image = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );

    if (image != null) {
      setState(() {
        _pickedImage = image;
      });
    }
  }

  Future<Map<String, String>> _uploadImageToBackend(XFile imageFile) async {
    final uri = Uri.parse('${AppConfig.apiTv3}/upload_image');

    final request = http.MultipartRequest('POST', uri);

    if (_token.isNotEmpty) {
      request.headers['Authorization'] = "Bearer $_token";
    }

    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        imageFile.path,
      ),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));

      return {
        "image_url": data["image_url"]?.toString() ?? "",
        "image_public_id":
            (data["image_public_id"] ?? data["public_id"] ?? "").toString(),
      };
    }

    throw Exception("Upload image failed: ${response.statusCode} - ${response.body}");
  }

  void _startEdit(Map<String, dynamic> product) {
    setState(() {
      _editingProduct = product;
      _nameController.text = _getLocalized(product['name']);
      _descController.text = _getLocalized(product['description']);
      _priceController.text = _getPrice(product['price']).toStringAsFixed(0);
      _pickedImage = null;
    });
  }

  void _cancelEdit() {
    setState(() {
      _editingProduct = null;
      _nameController.clear();
      _descController.clear();
      _priceController.clear();
      _pickedImage = null;
    });
  }

  Future<void> _submitForm() async {
    final labels = _locales[_lang]!;

    final name = _nameController.text.trim();
    final desc = _descController.text.trim();
    final price = double.tryParse(_priceController.text.trim()) ?? 0;

    if (name.isEmpty || price <= 0) {
      _showSnack(labels["msg_err_empty"]!, Colors.red);
      return;
    }

    setState(() => _isLoading = true);

    try {
      String imageUrl = "";
      String imagePublicId = "";

      if (_editingProduct != null) {
        imageUrl = _editingProduct!['image_url']?.toString() ?? "";
        imagePublicId =
            (_editingProduct!['image_public_id'] ?? _editingProduct!['public_id'] ?? "")
                .toString();
      }

      if (_pickedImage != null) {
        final uploadResult = await _uploadImageToBackend(_pickedImage!);

        imageUrl = uploadResult["image_url"] ?? "";
        imagePublicId = uploadResult["image_public_id"] ?? "";

        if (imageUrl.isEmpty) {
          throw Exception(labels["msg_err_upload"]);
        }
      }

      final payload = {
        "name": name,
        "description": desc,
        "price": price,
        "image_url": imageUrl,
        "image_public_id": imagePublicId,
        "updated_at": DateTime.now().toIso8601String(),
      };

      late http.Response res;

      if (_editingProduct != null) {
        final productId = _getProductId(_editingProduct!);

        res = await http.put(
          Uri.parse('${AppConfig.apiTv3}/products/$productId'),
          headers: {
            "Content-Type": "application/json",
            if (_token.isNotEmpty) "Authorization": "Bearer $_token",
          },
          body: jsonEncode(payload),
        );
      } else {
        payload["created_at"] = DateTime.now().toIso8601String();

        res = await http.post(
          Uri.parse('${AppConfig.apiTv3}/products'),
          headers: {
            "Content-Type": "application/json",
            if (_token.isNotEmpty) "Authorization": "Bearer $_token",
          },
          body: jsonEncode(payload),
        );
      }

      if (res.statusCode == 200 || res.statusCode == 201) {
        _showSnack(labels["msg_success"]!, Colors.green);
        _cancelEdit();
        await _fetchProducts();
      } else {
        String msg = labels["msg_err_server"]!;

        try {
          final err = jsonDecode(utf8.decode(res.bodyBytes));
          msg = err["detail"]?.toString() ?? msg;
        } catch (_) {}

        _showSnack(msg, Colors.red);
      }
    } catch (e) {
      debugPrint("Lỗi Submit Product: $e");
      _showSnack(e.toString().replaceFirst("Exception: ", ""), Colors.red);
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _deleteProduct(String id) async {
    final labels = _locales[_lang]!;

    setState(() => _isLoading = true);

    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiTv3}/products/$id'),
        headers: {
          "Content-Type": "application/json",
          if (_token.isNotEmpty) "Authorization": "Bearer $_token",
        },
      );

      if (res.statusCode == 200) {
        _showSnack(labels["msg_success"]!, Colors.green);
        await _fetchProducts();
      } else {
        _showSnack(labels["msg_err_server"]!, Colors.red);
      }
    } catch (e) {
      debugPrint("Lỗi xóa sản phẩm: $e");
      _showSnack("Lỗi: $e", Colors.red);
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
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

    final totalProducts = _products.length;

    double maxPrice = 0;
    if (_products.isNotEmpty) {
      for (final p in _products) {
        final price = _getPrice(p['price']);
        if (price > maxPrice) {
          maxPrice = price;
        }
      }
    }

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
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        actions: [
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
              child: CircularProgressIndicator(color: Colors.teal),
            )
          : RefreshIndicator(
              onRefresh: _fetchProducts,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      labels["caption"]!,
                      style: const TextStyle(color: Colors.black54),
                    ),
                    const SizedBox(height: 16),

                    Row(
                      children: [
                        Expanded(
                          child: _buildStatCard(
                            title: labels["stat_total"]!,
                            value: totalProducts.toString(),
                            icon: Icons.inventory_2,
                            color: Colors.teal,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildStatCard(
                            title: labels["stat_max_price"]!,
                            value: "${maxPrice.toStringAsFixed(0)}đ",
                            icon: Icons.attach_money,
                            color: Colors.orange,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    _buildProductForm(labels),

                    const SizedBox(height: 24),

                    Text(
                      labels["sub_catalog"]!,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
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
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    if (_filteredProducts.isEmpty)
                      Center(
                        child: Padding(
                          padding: const EdgeInsets.all(30),
                          child: Text(labels["no_products"]!),
                        ),
                      )
                    else
                      ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _filteredProducts.length,
                        itemBuilder: (context, index) {
                          final product =
                              Map<String, dynamic>.from(_filteredProducts[index]);

                          return _buildProductItem(product, labels);
                        },
                      ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildStatCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 12,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: color.withOpacity(0.12),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 19,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Colors.black54,
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildProductForm(Map<String, String> labels) {
    final isEditing = _editingProduct != null;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 12,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            isEditing
                ? labels["form_edit_title"]!
                : labels["form_add_title"]!,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 17,
            ),
          ),

          const SizedBox(height: 16),

          TextField(
            controller: _nameController,
            decoration: InputDecoration(
              labelText: labels["input_name"],
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),

          const SizedBox(height: 12),

          TextField(
            controller: _descController,
            maxLines: 3,
            decoration: InputDecoration(
              labelText: labels["input_desc"],
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),

          const SizedBox(height: 12),

          TextField(
            controller: _priceController,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: labels["input_price"],
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),

          const SizedBox(height: 14),

          Text(
            labels["input_image"]!,
            style: const TextStyle(
              fontWeight: FontWeight.w600,
            ),
          ),

          const SizedBox(height: 8),

          _buildImagePreview(labels),

          const SizedBox(height: 10),

          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: _pickImage,
              icon: const Icon(Icons.photo_library),
              label: Text(labels["btn_pick_image"]!),
            ),
          ),

          if (isEditing && _pickedImage == null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                labels["img_keep_hint"]!,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.black54,
                ),
              ),
            ),

          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _submitForm,
                  icon: Icon(isEditing ? Icons.save : Icons.add),
                  label: Text(
                    isEditing ? labels["btn_save"]! : labels["btn_add"]!,
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.teal,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              if (isEditing)
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _cancelEdit,
                    icon: const Icon(Icons.close),
                    label: Text(labels["btn_cancel"]!),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildImagePreview(Map<String, String> labels) {
    if (_pickedImage != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            labels["new_image"]!,
            style: const TextStyle(fontSize: 12, color: Colors.black54),
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.file(
              File(_pickedImage!.path),
              width: double.infinity,
              height: 160,
              fit: BoxFit.cover,
            ),
          ),
        ],
      );
    }

    if (_editingProduct != null) {
      final oldImage = _normalizeImageUrl(_editingProduct!['image_url']);

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            labels["current_image"]!,
            style: const TextStyle(fontSize: 12, color: Colors.black54),
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.network(
              oldImage,
              width: double.infinity,
              height: 160,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) {
                return Container(
                  height: 160,
                  color: Colors.grey[200],
                  child: const Center(
                    child: Icon(Icons.image_not_supported, size: 40),
                  ),
                );
              },
            ),
          ),
        ],
      );
    }

    return Container(
      width: double.infinity,
      height: 120,
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.black12),
      ),
      child: const Center(
        child: Icon(Icons.add_photo_alternate, size: 42, color: Colors.grey),
      ),
    );
  }

  Widget _buildProductItem(
    Map<String, dynamic> product,
    Map<String, String> labels,
  ) {
    final productId = _getProductId(product);
    final name = _getLocalized(product['name']);
    final desc = _getLocalized(product['description']);
    final price = _getPrice(product['price']);
    final imageUrl = _normalizeImageUrl(product['image_url']);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
      ),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
                imageUrl,
                width: 88,
                height: 88,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) {
                  return Container(
                    width: 88,
                    height: 88,
                    color: Colors.grey[200],
                    child: const Icon(
                      Icons.inventory_2,
                      color: Colors.grey,
                    ),
                  );
                },
              ),
            ),

            const SizedBox(width: 12),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name.isEmpty ? "Sản phẩm" : name,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    desc,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.black54,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    "${price.toStringAsFixed(0)}đ",
                    style: const TextStyle(
                      color: Colors.orange,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),

            Column(
              children: [
                IconButton(
                  tooltip: labels["btn_edit"],
                  onPressed: () => _startEdit(product),
                  icon: const Icon(Icons.edit, color: Colors.blue),
                ),
                IconButton(
                  tooltip: labels["btn_del"],
                  onPressed: () => _deleteProduct(productId),
                  icon: const Icon(Icons.delete, color: Colors.red),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }
}