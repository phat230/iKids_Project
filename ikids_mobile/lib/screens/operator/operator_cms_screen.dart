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

  final _aboutTitleCtrl = TextEditingController();
  final _aboutContentCtrl = TextEditingController();
  String _aboutLayout = "left";
  XFile? _pickedAboutImage; 

  final _phoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _addressCtrl = TextEditingController();

  final _postTitleCtrl = TextEditingController();
  final _postContentCtrl = TextEditingController();
  String _postLayout = "left";
  XFile? _pickedPostImage; 

  @override
  void initState() {
    super.initState();
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
          _aboutContentCtrl.text = _aboutData['content']?['vi'] ?? _aboutData['content']?.toString() ?? "";
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

  // ✅ HÀM UPLOAD ẢNH CHUYÊN SÂU: Bắt lỗi triệt để
  Future<String?> _uploadImageToServer(XFile imageFile) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse('${AppConfig.apiUrl}/api/tv3/upload_image'));
      request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
      
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['image_url']; 
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi Server khi tải ảnh lên (Mã: ${response.statusCode})"), backgroundColor: Colors.red));
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi mạng khi tải ảnh: $e"), backgroundColor: Colors.red));
      }
    }
    return null; // Trả về null nếu thất bại
  }

  Future<void> _updateAbout() async {
    setState(() => _isLoading = true);
    try {
      List<String> finalImages = [];
      
      // ✅ NẾU CÓ CHỌN ẢNH MỚI -> BẮT BUỘC PHẢI UPLOAD THÀNH CÔNG MỚI ĐI TIẾP
      if (_pickedAboutImage != null) {
        String? newImgPath = await _uploadImageToServer(_pickedAboutImage!);
        if (newImgPath != null) {
          finalImages.add(newImgPath);
        } else {
          // Upload ảnh xịt -> Dừng lại luôn
          setState(() => _isLoading = false);
          return;
        }
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
      
      final res = await http.put(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/about'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload)
      );

      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Cập nhật Giới thiệu thành công!"), backgroundColor: Colors.green));
        _fetchCmsData();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi hệ thống!"), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _addPost() async {
    if (_postTitleCtrl.text.isEmpty || _postContentCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng nhập đủ Tiêu đề và Nội dung"), backgroundColor: Colors.red));
      return;
    }
    setState(() => _isLoading = true);

    try {
      String imagePath = "";
      
      // ✅ NẾU CÓ ẢNH -> UPLOAD TRƯỚC. LỖI THÌ DỪNG LẠI.
      if (_pickedPostImage != null) {
        String? uploadedPath = await _uploadImageToServer(_pickedPostImage!);
        if (uploadedPath != null) {
          imagePath = uploadedPath;
        } else {
          setState(() => _isLoading = false);
          return; // Dừng lại, không đăng bài ảo
        }
      }

      final payload = {
        "title": _postTitleCtrl.text.trim(),
        "content": _postContentCtrl.text.trim(),
        "layout": _postLayout,
        "image_url": imagePath,
        "status": "published",
        "date": "${DateTime.now().day}/${DateTime.now().month}/${DateTime.now().year}",
        "img_width": 500
      };

      final res = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/posts'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload)
      );

      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Đăng tin tức thành công!"), backgroundColor: Colors.green));
        _postTitleCtrl.clear();
        _postContentCtrl.clear();
        _pickedPostImage = null;
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
      final res = await http.put(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/contact'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload)
      );
      if (res.statusCode == 200) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Cập nhật Liên hệ thành công!"), backgroundColor: Colors.green));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Widget _buildImagePickerBox({required XFile? pickedFile, required String? currentImgUrl, required VoidCallback onTap}) {
    String validUrl = "";
    if (currentImgUrl != null && currentImgUrl.isNotEmpty) {
      validUrl = currentImgUrl.startsWith("http") ? currentImgUrl : "${AppConfig.apiUrl}/$currentImgUrl";
      validUrl += "?v=${DateTime.now().millisecondsSinceEpoch}";
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 180,
        width: double.infinity,
        decoration: BoxDecoration(color: Colors.teal.shade50, borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.teal.shade300, width: 2)),
        child: pickedFile != null 
          ? ClipRRect(borderRadius: BorderRadius.circular(13), child: Image.file(File(pickedFile.path), fit: BoxFit.cover))
          : (validUrl.isNotEmpty 
              ? ClipRRect(borderRadius: BorderRadius.circular(13), child: Image.network(validUrl, fit: BoxFit.cover))
              : Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.add_photo_alternate_rounded, size: 50, color: Colors.teal.shade400),
                    const SizedBox(height: 10),
                    const Text("Chạm để chọn ảnh từ điện thoại", style: TextStyle(color: Colors.teal, fontWeight: FontWeight.bold))
                  ],
                )
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
          backgroundColor: Colors.teal,
          foregroundColor: Colors.white,
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white60,
            indicatorColor: Colors.amber,
            tabs: [
              Tab(icon: Icon(Icons.business), text: "Giới thiệu"),
              Tab(icon: Icon(Icons.article), text: "Tin tức"),
              Tab(icon: Icon(Icons.contact_phone), text: "Liên hệ"),
            ],
          ),
        ),
        body: _isLoading 
          ? const Center(child: CircularProgressIndicator(color: Colors.teal))
          : TabBarView(
              children: [_buildAboutTab(), _buildNewsTab(), _buildContactTab()],
            ),
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
              _buildImagePickerBox(
                pickedFile: _pickedAboutImage, 
                currentImgUrl: (_aboutData['images'] != null && _aboutData['images'].isNotEmpty) ? _aboutData['images'][0] : "", 
                onTap: () => _pickImage(isAbout: true)
              ),
              const SizedBox(height: 20),
              TextField(controller: _aboutTitleCtrl, decoration: const InputDecoration(labelText: "Tiêu đề bài viết", border: OutlineInputBorder())),
              const SizedBox(height: 15),
              DropdownButtonFormField<String>(
                value: _aboutLayout,
                decoration: const InputDecoration(labelText: "Bố cục hiển thị", border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: "left", child: Text("Ảnh Trái - Chữ Phải")),
                  DropdownMenuItem(value: "right", child: Text("Ảnh Phải - Chữ Trái")),
                  DropdownMenuItem(value: "full", child: Text("Banner (Ảnh Trên)")),
                ],
                onChanged: (v) => setState(() => _aboutLayout = v!),
              ),
              const SizedBox(height: 15),
              TextField(controller: _aboutContentCtrl, maxLines: 6, decoration: const InputDecoration(labelText: "Nội dung bài viết", border: OutlineInputBorder())),
              const SizedBox(height: 25),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                  onPressed: _updateAbout,
                  icon: const Icon(Icons.save),
                  label: const Text("LƯU THAY ĐỔI GIỚI THIỆU", style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              )
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
          Card(
            color: Colors.teal.shade50,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15), side: BorderSide(color: Colors.teal.shade200)),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("➕ Soạn bài mới", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.teal)),
                  const SizedBox(height: 15),
                  const Text("Ảnh đại diện bài viết", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                  const SizedBox(height: 8),
                  _buildImagePickerBox(pickedFile: _pickedPostImage, currentImgUrl: "", onTap: () => _pickImage(isAbout: false)),
                  const SizedBox(height: 15),
                  TextField(controller: _postTitleCtrl, decoration: const InputDecoration(labelText: "Tiêu đề tin tức", filled: true, fillColor: Colors.white, border: OutlineInputBorder())),
                  const SizedBox(height: 15),
                  DropdownButtonFormField<String>(
                    value: _postLayout,
                    decoration: const InputDecoration(labelText: "Bố cục", filled: true, fillColor: Colors.white, border: OutlineInputBorder()),
                    items: const [
                      DropdownMenuItem(value: "left", child: Text("Ảnh Trái")),
                      DropdownMenuItem(value: "right", child: Text("Ảnh Phải")),
                      DropdownMenuItem(value: "full", child: Text("Banner")),
                    ],
                    onChanged: (v) => setState(() => _postLayout = v!),
                  ),
                  const SizedBox(height: 15),
                  TextField(controller: _postContentCtrl, maxLines: 5, decoration: const InputDecoration(labelText: "Nội dung chi tiết", filled: true, fillColor: Colors.white, border: OutlineInputBorder())),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                      onPressed: _addPost,
                      icon: const Icon(Icons.send),
                      label: const Text("ĐĂNG BÀI VIẾT", style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  )
                ],
              ),
            ),
          ),
          const SizedBox(height: 30),
          const Text("📰 Quản lý bài viết đã đăng", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 10),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _posts.length,
            itemBuilder: (context, index) {
              final p = _posts[index];
              String imgUrl = p['image_url'] ?? "";
              
              // Cập nhật lại đường dẫn để hiển thị ảnh mặc định nếu trống
              if (imgUrl.isEmpty) {
                imgUrl = "https://images.unsplash.com/photo-1546410531-dd4cb6ca7404?q=80&w=800&auto=format&fit=crop";
              } else if (!imgUrl.startsWith("http")) {
                imgUrl = "${AppConfig.apiUrl}/$imgUrl?v=${DateTime.now().millisecondsSinceEpoch}";
              }

              return Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(10),
                  leading: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.network(imgUrl, width: 60, height: 60, fit: BoxFit.cover, errorBuilder: (_,__,___) => Container(width: 60, height: 60, color: Colors.grey[300], child: const Icon(Icons.image))),
                  ),
                  title: Text(p['title'] is Map ? p['title']['vi'] : p['title'].toString(), maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text("Ngày đăng: ${p['date'] ?? ''}"),
                  trailing: IconButton(icon: const Icon(Icons.delete, color: Colors.red), onPressed: () => _deletePost(p['id'] ?? p['_id'])),
                ),
              );
            },
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
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                  onPressed: _updateContact,
                  icon: const Icon(Icons.save),
                  label: const Text("LƯU THÔNG TIN LIÊN HỆ", style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }
}