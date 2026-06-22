import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import '../../core/config.dart';

class OperatorCmsScreen extends StatefulWidget {
  const OperatorCmsScreen({super.key});

  @override
  State<OperatorCmsScreen> createState() => _OperatorCmsScreenState();
}

class _OperatorCmsScreenState extends State<OperatorCmsScreen> {
  final _storage = const FlutterSecureStorage();
  bool _isLoading = true;
  String _lang = "vi";
  String _token = "";

  Map<String, dynamic> _aboutData = {};
  Map<String, dynamic> _contactData = {};
  List<dynamic> _posts = [];

  // Controllers Giới thiệu
  final _aboutTitleCtrl = TextEditingController();
  final _aboutContentCtrl = TextEditingController();
  String _aboutLayout = "left";
  XFile? _pickedAboutImage; 

  // Controllers Liên hệ
  final _phoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _addressCtrl = TextEditingController();

  // Controllers Tin tức
  final _postTitleCtrl = TextEditingController();
  final _postContentCtrl = TextEditingController();
  XFile? _pickedPostImage; 
  String? _editingPostId; // ID bài viết đang sửa (Nếu null là Đăng mới)
  String _oldPostImageUrl = ""; // Lưu link ảnh cũ khi sửa bài

  @override
  void initState() {
    super.initState();
    // Lắng nghe thay đổi để cập nhật giao diện XEM TRƯỚC theo thời gian thực
    _postTitleCtrl.addListener(() => setState(() {}));
    _postContentCtrl.addListener(() => setState(() {}));
    _fetchCmsData();
  }

  Future<void> _fetchCmsData() async {
    setState(() => _isLoading = true);
    try {
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;
      _token = await _storage.read(key: 'jwt_token') ?? "";

      final basePrefix = '${AppConfig.apiUrl}/api/tv3';
      final responses = await Future.wait([
        http.get(Uri.parse('$basePrefix/about')),
        http.get(Uri.parse('$basePrefix/contact')),
        http.get(Uri.parse('$basePrefix/posts'))
      ]);

      if (mounted) {
        setState(() {
          _aboutData = responses[0].statusCode == 200 ? jsonDecode(utf8.decode(responses[0].bodyBytes)) : {};
          _contactData = responses[1].statusCode == 200 ? jsonDecode(utf8.decode(responses[1].bodyBytes)) : {};
          _posts = responses[2].statusCode == 200 ? jsonDecode(utf8.decode(responses[2].bodyBytes)) : [];

          _aboutTitleCtrl.text = _aboutData['title']?['vi'] ?? _aboutData['title']?.toString() ?? "";
          _aboutContentCtrl.text = _cleanHtmlToPlainText(_aboutData['content']?['vi'] ?? _aboutData['content']?.toString() ?? "");
          _aboutLayout = _aboutData['layout'] ?? "left";

          _phoneCtrl.text = _contactData['phone'] ?? "";
          _emailCtrl.text = _contactData['email'] ?? "";
          _addressCtrl.text = _contactData['address']?['vi'] ?? _contactData['address']?.toString() ?? "";
          
          _pickedAboutImage = null;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // ✅ HÀM LÀM SẠCH HTML TỪ WEB THÀNH XUỐNG DÒNG CỦA APP
  String _cleanHtmlToPlainText(String htmlString) {
    String parsed = htmlString.replaceAll(RegExp(r'<br\s*/?>', caseSensitive: false), '\n');
    parsed = parsed.replaceAll(RegExp(r'</p>', caseSensitive: false), '\n\n');
    parsed = parsed.replaceAll(RegExp(r'<[^>]*>'), '');
    return parsed.trim();
  }

  // Lấy link ảnh chuẩn
  String _getValidImageUrl(String? imgPath) {
    String path = imgPath ?? "";
    if (path.trim().isEmpty || path.contains("anh_laptop.jpg")) {
      return "https://images.unsplash.com/photo-1546410531-dd4cb6ca7404?q=80&w=800&auto=format&fit=crop";
    }
    if (path.startsWith("http")) return path;
    final baseUrl = AppConfig.apiUrl.endsWith('/') ? AppConfig.apiUrl.substring(0, AppConfig.apiUrl.length - 1) : AppConfig.apiUrl;
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    return "$baseUrl/$cleanPath?v=${DateTime.now().millisecondsSinceEpoch}";
  }

  Future<void> _pickImage({required bool isAbout}) async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (image != null) {
      setState(() {
        if (isAbout) _pickedAboutImage = image;
        else _pickedPostImage = image;
      });
    }
  }

  Future<String?> _uploadImageToServer(XFile imageFile) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/upload_image'));
      request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return jsonDecode(response.body)['image_url']; 
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi tải ảnh: $e"), backgroundColor: Colors.red));
    }
    return null; 
  }

  Future<void> _updateAbout() async {
    setState(() => _isLoading = true);
    try {
      List<String> finalImages = [];
      if (_pickedAboutImage != null) {
        String? newImgPath = await _uploadImageToServer(_pickedAboutImage!);
        if (newImgPath != null) finalImages.add(newImgPath);
      } else if (_aboutData['images'] != null && (_aboutData['images'] as List).isNotEmpty) {
        finalImages.add(_aboutData['images'][0]);
      }

      final payload = {
        "title": _aboutTitleCtrl.text.trim(),
        "content": _aboutContentCtrl.text.trim(),
        "layout": _aboutLayout,
        "img_width": 500,
        "images": finalImages
      };
      
      final res = await http.put(Uri.parse('${AppConfig.apiUrl}/api/tv3/about'), headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"}, body: jsonEncode(payload));
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Cập nhật Giới thiệu thành công!"), backgroundColor: Colors.green));
        _fetchCmsData();
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // ✅ HÀM GỘP CHUNG: VỪA ĐĂNG MỚI VỪA SỬA BÀI VIẾT
  Future<void> _submitPost() async {
    if (_postTitleCtrl.text.isEmpty || _postContentCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng nhập đủ Tiêu đề và Nội dung"), backgroundColor: Colors.red));
      return;
    }
    setState(() => _isLoading = true);

    try {
      String imagePath = _oldPostImageUrl; 
      
      if (_pickedPostImage != null) {
        String? uploadedPath = await _uploadImageToServer(_pickedPostImage!);
        if (uploadedPath != null) imagePath = uploadedPath;
      }

      final payload = {
        "title": _postTitleCtrl.text.trim(),
        "content": _postContentCtrl.text.trim(), // App sẽ lưu dạng text thường (có \n)
        "layout": "full",
        "image_url": imagePath,
        "status": "published",
        "date": "${DateTime.now().day}/${DateTime.now().month}/${DateTime.now().year}",
        "img_width": 500
      };

      http.Response res;
      if (_editingPostId != null) {
        // SỬA BÀI VIẾT CŨ
        res = await http.put(Uri.parse('${AppConfig.apiUrl}/api/tv3/posts/$_editingPostId'), headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"}, body: jsonEncode(payload));
      } else {
        // TẠO BÀI VIẾT MỚI
        res = await http.post(Uri.parse('${AppConfig.apiUrl}/api/tv3/posts'), headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"}, body: jsonEncode(payload));
      }

      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_editingPostId != null ? "✅ Sửa bài thành công!" : "✅ Đăng bài thành công!"), backgroundColor: Colors.green));
        _cancelEditing(); // Reset Form
        _fetchCmsData();
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _deletePost(String id) async {
    try {
      final res = await http.delete(Uri.parse('${AppConfig.apiUrl}/api/tv3/posts/$id'), headers: {"Authorization": "Bearer $_token"});
      if (res.statusCode == 200) _fetchCmsData();
    } catch (e) {}
  }

  Future<void> _updateContact() async {
    setState(() => _isLoading = true);
    try {
      final payload = {"phone": _phoneCtrl.text.trim(), "email": _emailCtrl.text.trim(), "address": _addressCtrl.text.trim()};
      final res = await http.put(Uri.parse('${AppConfig.apiUrl}/api/tv3/contact'), headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"}, body: jsonEncode(payload));
      if (res.statusCode == 200) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Cập nhật Liên hệ thành công!"), backgroundColor: Colors.green));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // Gọi hàm này khi bấm "Sửa" một bài trong danh sách
  void _startEditingPost(dynamic p) {
    setState(() {
      _editingPostId = p['id'] ?? p['_id'];
      _postTitleCtrl.text = p['title'] is Map ? (p['title']['vi'] ?? "") : p['title'].toString();
      _postContentCtrl.text = _cleanHtmlToPlainText(p['content'] is Map ? (p['content']['vi'] ?? "") : p['content'].toString());
      _oldPostImageUrl = p['image_url'] ?? "";
      _pickedPostImage = null;
    });
  }

  void _cancelEditing() {
    setState(() {
      _editingPostId = null;
      _postTitleCtrl.clear();
      _postContentCtrl.clear();
      _oldPostImageUrl = "";
      _pickedPostImage = null;
    });
  }

  Widget _buildImagePickerBox({required XFile? pickedFile, required String? currentImgUrl, required VoidCallback onTap}) {
    String validUrl = "";
    if (currentImgUrl != null && currentImgUrl.isNotEmpty) {
      validUrl = _getValidImageUrl(currentImgUrl);
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 180, width: double.infinity,
        decoration: BoxDecoration(color: Colors.teal.shade50, borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.teal.shade300, width: 2)),
        child: pickedFile != null 
          ? ClipRRect(borderRadius: BorderRadius.circular(13), child: Image.file(File(pickedFile.path), fit: BoxFit.cover))
          : (validUrl.isNotEmpty 
              ? ClipRRect(borderRadius: BorderRadius.circular(13), child: Image.network(validUrl, fit: BoxFit.cover))
              : Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.add_photo_alternate_rounded, size: 50, color: Colors.teal.shade400), const SizedBox(height: 10), const Text("Chạm để chọn ảnh", style: TextStyle(color: Colors.teal, fontWeight: FontWeight.bold))])
            ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(_lang == "vi" ? "Quản lý Trang chủ (CMS)" : "Homepage CMS", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          backgroundColor: Colors.teal, foregroundColor: Colors.white,
          bottom: const TabBar(labelColor: Colors.white, unselectedLabelColor: Colors.white60, indicatorColor: Colors.amber, tabs: [Tab(icon: Icon(Icons.business), text: "Giới thiệu"), Tab(icon: Icon(Icons.article), text: "Tin tức"), Tab(icon: Icon(Icons.contact_phone), text: "Liên hệ")]),
        ),
        body: _isLoading 
          ? const Center(child: CircularProgressIndicator(color: Colors.teal))
          : TabBarView(children: [_buildAboutTab(), _buildNewsTab(), _buildContactTab()]),
      ),
    );
  }

  Widget _buildAboutTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("Ảnh bìa trung tâm", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
              const SizedBox(height: 8),
              _buildImagePickerBox(pickedFile: _pickedAboutImage, currentImgUrl: (_aboutData['images'] != null && _aboutData['images'].isNotEmpty) ? _aboutData['images'][0] : "", onTap: () => _pickImage(isAbout: true)),
              const SizedBox(height: 20),
              TextField(controller: _aboutTitleCtrl, decoration: const InputDecoration(labelText: "Tiêu đề bài viết", border: OutlineInputBorder())),
              const SizedBox(height: 15),
              DropdownButtonFormField<String>(
                value: _aboutLayout,
                decoration: const InputDecoration(labelText: "Bố cục hiển thị", border: OutlineInputBorder()),
                items: const [DropdownMenuItem(value: "left", child: Text("Ảnh Trái - Chữ Phải")), DropdownMenuItem(value: "right", child: Text("Ảnh Phải - Chữ Trái")), DropdownMenuItem(value: "full", child: Text("Banner (Ảnh Trên)"))],
                onChanged: (v) => setState(() => _aboutLayout = v!),
              ),
              const SizedBox(height: 15),
              TextField(controller: _aboutContentCtrl, maxLines: 6, decoration: const InputDecoration(labelText: "Nội dung bài viết", border: OutlineInputBorder())),
              const SizedBox(height: 25),
              SizedBox(width: double.infinity, height: 50, child: ElevatedButton.icon(style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))), onPressed: _updateAbout, icon: const Icon(Icons.save), label: const Text("LƯU THAY ĐỔI GIỚI THIỆU", style: TextStyle(fontWeight: FontWeight.bold))))
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNewsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // KHU VỰC FORM (THÊM / SỬA) VÀ XEM TRƯỚC
          Card(
            color: _editingPostId != null ? Colors.amber.shade50 : Colors.teal.shade50,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15), side: BorderSide(color: _editingPostId != null ? Colors.amber : Colors.teal.shade200)),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(_editingPostId != null ? "✏️ Sửa bài viết" : "➕ Soạn bài mới", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: _editingPostId != null ? Colors.amber.shade900 : Colors.teal)),
                      if (_editingPostId != null)
                        TextButton(onPressed: _cancelEditing, child: const Text("Hủy", style: TextStyle(color: Colors.red)))
                    ],
                  ),
                  const SizedBox(height: 15),
                  const Text("Ảnh đại diện bài viết", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                  const SizedBox(height: 8),
                  _buildImagePickerBox(pickedFile: _pickedPostImage, currentImgUrl: _oldPostImageUrl, onTap: () => _pickImage(isAbout: false)),
                  const SizedBox(height: 15),
                  TextField(controller: _postTitleCtrl, decoration: const InputDecoration(labelText: "Tiêu đề tin tức", filled: true, fillColor: Colors.white, border: OutlineInputBorder())),
                  const SizedBox(height: 15),
                  TextField(controller: _postContentCtrl, maxLines: 5, decoration: const InputDecoration(labelText: "Nội dung chi tiết", filled: true, fillColor: Colors.white, border: OutlineInputBorder())),
                  
                  // ✅ TÍNH NĂNG XEM TRƯỚC BÀI VIẾT (LIVE PREVIEW)
                  const SizedBox(height: 25),
                  const Text("👀 XEM TRƯỚC HIỂN THỊ:", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                  const SizedBox(height: 8),
                  _buildLivePreviewCard(),
                  const SizedBox(height: 20),

                  SizedBox(
                    width: double.infinity, height: 50,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(backgroundColor: _editingPostId != null ? Colors.amber.shade700 : Colors.teal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                      onPressed: _submitPost,
                      icon: const Icon(Icons.send),
                      label: Text(_editingPostId != null ? "CẬP NHẬT BÀI VIẾT" : "ĐĂNG BÀI VIẾT", style: const TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  )
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 30),
          const Text("📰 Quản lý bài viết đã đăng", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 10),
          
          // DANH SÁCH BÀI VIẾT
          ListView.builder(
            shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
            itemCount: _posts.length,
            itemBuilder: (context, index) {
              final p = _posts[index];
              String imgUrl = _getValidImageUrl(p['image_url']);
              return Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(10),
                  leading: ClipRRect(borderRadius: BorderRadius.circular(8), child: Image.network(imgUrl, width: 60, height: 60, fit: BoxFit.cover, errorBuilder: (_,__,___) => Container(width: 60, height: 60, color: Colors.grey[300], child: const Icon(Icons.image)))),
                  title: Text(p['title'] is Map ? (p['title']['vi'] ?? "") : p['title'].toString(), maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text("Ngày đăng: ${p['date'] ?? ''}"),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(icon: const Icon(Icons.edit, color: Colors.blue), onPressed: () => _startEditingPost(p)),
                      IconButton(icon: const Icon(Icons.delete, color: Colors.red), onPressed: () => _deletePost(p['id'] ?? p['_id'])),
                    ],
                  ),
                ),
              );
            },
          )
        ],
      ),
    );
  }

  // KHUNG XEM TRƯỚC GIỐNG HỆT APP KHÁCH
  Widget _buildLivePreviewCard() {
    String pTitle = _postTitleCtrl.text.isEmpty ? "Tiêu đề bài báo..." : _postTitleCtrl.text;
    String pContent = _postContentCtrl.text.isEmpty ? "Nội dung bài báo..." : _postContentCtrl.text;
    
    Widget imageWidget;
    if (_pickedPostImage != null) {
      imageWidget = Image.file(File(_pickedPostImage!.path), fit: BoxFit.cover);
    } else if (_oldPostImageUrl.isNotEmpty) {
      imageWidget = Image.network(_getValidImageUrl(_oldPostImageUrl), fit: BoxFit.cover);
    } else {
      imageWidget = Image.network(_getValidImageUrl(""), fit: BoxFit.cover); // Fallback
    }

    return Container(
      width: 250,
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 8, offset: const Offset(0, 3))]),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(borderRadius: const BorderRadius.vertical(top: Radius.circular(15)), child: SizedBox(height: 140, width: double.infinity, child: imageWidget)),
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(pTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, height: 1.3), maxLines: 2, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 6),
                Text(pContent, style: const TextStyle(color: Colors.black54, fontSize: 13, height: 1.3), maxLines: 2, overflow: TextOverflow.ellipsis),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildContactTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("Thông tin liên hệ chân trang", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.teal)),
              const Divider(height: 30),
              TextField(controller: _phoneCtrl, decoration: const InputDecoration(labelText: "Hotline", prefixIcon: Icon(Icons.phone), border: OutlineInputBorder())),
              const SizedBox(height: 15),
              TextField(controller: _emailCtrl, decoration: const InputDecoration(labelText: "Email hỗ trợ", prefixIcon: Icon(Icons.email), border: OutlineInputBorder())),
              const SizedBox(height: 15),
              TextField(controller: _addressCtrl, decoration: const InputDecoration(labelText: "Địa chỉ trụ sở", prefixIcon: Icon(Icons.location_on), border: OutlineInputBorder())),
              const SizedBox(height: 25),
              SizedBox(width: double.infinity, height: 50, child: ElevatedButton.icon(style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))), onPressed: _updateContact, icon: const Icon(Icons.save), label: const Text("LƯU THÔNG TIN LIÊN HỆ", style: TextStyle(fontWeight: FontWeight.bold))))
            ],
          ),
        ),
      ),
    );
  }
}