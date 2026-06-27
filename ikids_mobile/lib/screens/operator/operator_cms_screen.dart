import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
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
  final _contactDescCtrl = TextEditingController();

  final _postTitleCtrl = TextEditingController();
  final _postContentCtrl = TextEditingController();
  XFile? _pickedPostImage;
  String? _editingPostId;
  String _oldPostImageUrl = "";
  String _oldPostImagePublicId = "";
  String _postStatus = "published";

  String get _apiTv3 => AppConfig.apiTv3;

  @override
  void initState() {
    super.initState();
    _postTitleCtrl.addListener(_safeSetState);
    _postContentCtrl.addListener(_safeSetState);
    _fetchCmsData();
  }

  @override
  void dispose() {
    _aboutTitleCtrl.dispose();
    _aboutContentCtrl.dispose();
    _phoneCtrl.dispose();
    _emailCtrl.dispose();
    _addressCtrl.dispose();
    _contactDescCtrl.dispose();
    _postTitleCtrl.dispose();
    _postContentCtrl.dispose();
    super.dispose();
  }

  void _safeSetState() {
    if (mounted) setState(() {});
  }

  Map<String, String> get _headers {
    return {
      "Content-Type": "application/json",
      if (_token.isNotEmpty) "Authorization": "Bearer $_token",
    };
  }

  Future<void> _fetchCmsData() async {
    if (!mounted) return;

    setState(() => _isLoading = true);

    try {
      final savedLang = await _storage.read(key: 'app_lang');
      final savedToken = await _storage.read(key: 'jwt_token');

      _lang = savedLang ?? "vi";
      _token = savedToken ?? "";

      final responses = await Future.wait([
        http.get(Uri.parse('$_apiTv3/about')),
        http.get(Uri.parse('$_apiTv3/contact')),
        http.get(Uri.parse('$_apiTv3/posts')),
      ]);

      final about = _decodeMap(responses[0]);
      final contact = _decodeMap(responses[1]);
      final posts = _decodeList(responses[2]);

      if (!mounted) return;

      setState(() {
        _aboutData = about;
        _contactData = contact;
        _posts = posts;

        _aboutTitleCtrl.text = _getLocalized(_aboutData['title'], "");
        _aboutContentCtrl.text = _cleanHtmlToPlainText(_getLocalized(_aboutData['content'], ""));
        _aboutLayout = (_aboutData['layout'] ?? "left").toString();

        _phoneCtrl.text = (_contactData['phone'] ?? "").toString();
        _emailCtrl.text = (_contactData['email'] ?? "").toString();
        _addressCtrl.text = _getLocalized(_contactData['address'], "");
        _contactDescCtrl.text = _cleanHtmlToPlainText(_getLocalized(_contactData['description'], ""));

        _pickedAboutImage = null;
        _isLoading = false;
      });
    } catch (e) {
      debugPrint("CMS fetch error: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Map<String, dynamic> _decodeMap(http.Response response) {
    try {
      if (response.statusCode != 200) return {};
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      if (data is Map<String, dynamic>) return data;
      return {};
    } catch (_) {
      return {};
    }
  }

  List<dynamic> _decodeList(http.Response response) {
    try {
      if (response.statusCode != 200) return [];
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      if (data is List) return data;
      return [];
    } catch (_) {
      return [];
    }
  }

  String _getLocalized(dynamic field, String defaultVal) {
    if (field == null) return defaultVal;

    if (field is Map) {
      return (field[_lang] ?? field['vi'] ?? field['en'] ?? defaultVal).toString();
    }

    return field.toString();
  }

  String _cleanHtmlToPlainText(String htmlString) {
    String parsed = htmlString.replaceAll(
      RegExp(r'<br\s*/?>', caseSensitive: false),
      '\n',
    );

    parsed = parsed.replaceAll(
      RegExp(r'</p>', caseSensitive: false),
      '\n\n',
    );

    parsed = parsed.replaceAll(RegExp(r'<[^>]*>'), '');

    return parsed.trim();
  }

  String _textToHtml(String text) {
    return text.trim().replaceAll('\n', '<br>');
  }

  String _getValidImageUrl(dynamic imgPath) {
    const fallbackUrl =
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png";

    String path = imgPath?.toString().trim() ?? "";

    if (path.isEmpty ||
        path.toLowerCase().contains("placeholder") ||
        path.toLowerCase().contains("via.placeholder") ||
        path.toLowerCase().contains("anh_laptop.jpg")) {
      return fallbackUrl;
    }

    if (path.startsWith("http://") || path.startsWith("https://")) {
      return path;
    }

    final baseUrl = AppConfig.baseUrl.endsWith("/")
        ? AppConfig.baseUrl.substring(0, AppConfig.baseUrl.length - 1)
        : AppConfig.baseUrl;

    final cleanPath = path.startsWith("/") ? path.substring(1) : path;

    return "$baseUrl/$cleanPath";
  }

  Future<void> _pickImage({required bool isAbout}) async {
    final picker = ImagePicker();

    final image = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 82,
    );

    if (image == null) return;

    setState(() {
      if (isAbout) {
        _pickedAboutImage = image;
      } else {
        _pickedPostImage = image;
      }
    });
  }

  Future<Map<String, String>?> _uploadImageToServer(XFile imageFile) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_apiTv3/upload_image'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));

        return {
          "image_url": (data["image_url"] ?? "").toString(),
          "image_public_id": (data["image_public_id"] ?? data["public_id"] ?? "").toString(),
        };
      }

      _showSnack("Upload ảnh thất bại: ${response.body}", Colors.red);
    } catch (e) {
      _showSnack("Lỗi tải ảnh: $e", Colors.red);
    }

    return null;
  }

  Future<void> _updateAbout() async {
    setState(() => _isLoading = true);

    try {
      final oldImages = _aboutData['images'] is List ? List<dynamic>.from(_aboutData['images']) : [];
      final oldPublicIds = _aboutData['image_public_ids'] is List ? List<dynamic>.from(_aboutData['image_public_ids']) : [];

      final finalImages = <String>[];
      final finalPublicIds = <String>[];

      if (_pickedAboutImage != null) {
        final uploaded = await _uploadImageToServer(_pickedAboutImage!);

        if (uploaded != null && uploaded["image_url"]!.isNotEmpty) {
          finalImages.add(uploaded["image_url"]!);
          finalPublicIds.add(uploaded["image_public_id"] ?? "");
        }
      } else if (oldImages.isNotEmpty) {
        finalImages.add(oldImages.first.toString());

        if (oldPublicIds.isNotEmpty) {
          finalPublicIds.add(oldPublicIds.first.toString());
        }
      }

      final payload = {
        "title": _aboutTitleCtrl.text.trim(),
        "content": _textToHtml(_aboutContentCtrl.text),
        "layout": _aboutLayout,
        "img_width": 500,
        "images": finalImages,
        "image_public_ids": finalPublicIds,
      };

      final res = await http.put(
        Uri.parse('$_apiTv3/about'),
        headers: _headers,
        body: jsonEncode(payload),
      );

      if (res.statusCode == 200) {
        _showSnack("✅ Cập nhật Giới thiệu thành công!", Colors.green);
        await _fetchCmsData();
      } else {
        _showSnack("Lỗi lưu Giới thiệu: ${res.body}", Colors.red);
      }
    } catch (e) {
      _showSnack("Lỗi lưu Giới thiệu: $e", Colors.red);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _submitPost() async {
    if (_postTitleCtrl.text.trim().isEmpty || _postContentCtrl.text.trim().isEmpty) {
      _showSnack("Vui lòng nhập đủ Tiêu đề và Nội dung", Colors.red);
      return;
    }

    setState(() => _isLoading = true);

    try {
      String imageUrl = _oldPostImageUrl;
      String imagePublicId = _oldPostImagePublicId;

      if (_pickedPostImage != null) {
        final uploaded = await _uploadImageToServer(_pickedPostImage!);

        if (uploaded != null && uploaded["image_url"]!.isNotEmpty) {
          imageUrl = uploaded["image_url"]!;
          imagePublicId = uploaded["image_public_id"] ?? "";
        }
      }

      final now = DateTime.now();

      final payload = {
        "title": _postTitleCtrl.text.trim(),
        "content": _textToHtml(_postContentCtrl.text),
        "layout": "full",
        "image_url": imageUrl,
        "image_public_id": imagePublicId,
        "status": _postStatus,
        "date": "${now.day.toString().padLeft(2, '0')}/${now.month.toString().padLeft(2, '0')}/${now.year}",
        "img_width": 500,
      };

      http.Response res;

      if (_editingPostId != null) {
        res = await http.put(
          Uri.parse('$_apiTv3/posts/$_editingPostId'),
          headers: _headers,
          body: jsonEncode(payload),
        );
      } else {
        res = await http.post(
          Uri.parse('$_apiTv3/posts'),
          headers: _headers,
          body: jsonEncode(payload),
        );
      }

      if (res.statusCode == 200 || res.statusCode == 201) {
        _showSnack(
          _editingPostId != null ? "✅ Sửa bài thành công!" : "✅ Đăng bài thành công!",
          Colors.green,
        );

        _cancelEditing();
        await _fetchCmsData();
      } else {
        _showSnack("Lỗi lưu bài viết: ${res.body}", Colors.red);
      }
    } catch (e) {
      _showSnack("Lỗi lưu bài viết: $e", Colors.red);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _deletePost(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Xóa bài viết"),
          content: const Text("Bạn có chắc muốn xóa bài viết này không?"),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text("Hủy"),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              child: const Text("Xóa"),
            ),
          ],
        );
      },
    );

    if (confirm != true) return;

    setState(() => _isLoading = true);

    try {
      final res = await http.delete(
        Uri.parse('$_apiTv3/posts/$id'),
        headers: _headers,
      );

      if (res.statusCode == 200) {
        _showSnack("✅ Đã xóa bài viết!", Colors.green);
        await _fetchCmsData();
      } else {
        _showSnack("Xóa thất bại: ${res.body}", Colors.red);
      }
    } catch (e) {
      _showSnack("Lỗi xóa bài viết: $e", Colors.red);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _updateContact() async {
    setState(() => _isLoading = true);

    try {
      final payload = {
        "phone": _phoneCtrl.text.trim(),
        "email": _emailCtrl.text.trim(),
        "address": _addressCtrl.text.trim(),
        "description": _textToHtml(_contactDescCtrl.text),
      };

      final res = await http.put(
        Uri.parse('$_apiTv3/contact'),
        headers: _headers,
        body: jsonEncode(payload),
      );

      if (res.statusCode == 200) {
        _showSnack("✅ Cập nhật Liên hệ thành công!", Colors.green);
        await _fetchCmsData();
      } else {
        _showSnack("Lỗi lưu Liên hệ: ${res.body}", Colors.red);
      }
    } catch (e) {
      _showSnack("Lỗi lưu Liên hệ: $e", Colors.red);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _startEditingPost(dynamic p) {
    setState(() {
      _editingPostId = (p['id'] ?? p['_id'] ?? "").toString();
      _postTitleCtrl.text = _getLocalized(p['title'], "");
      _postContentCtrl.text = _cleanHtmlToPlainText(_getLocalized(p['content'], ""));
      _oldPostImageUrl = (p['image_url'] ?? "").toString();
      _oldPostImagePublicId = (p['image_public_id'] ?? p['public_id'] ?? "").toString();
      _postStatus = (p['status'] ?? "published").toString();
      _pickedPostImage = null;
    });
  }

  void _cancelEditing() {
    setState(() {
      _editingPostId = null;
      _postTitleCtrl.clear();
      _postContentCtrl.clear();
      _oldPostImageUrl = "";
      _oldPostImagePublicId = "";
      _postStatus = "published";
      _pickedPostImage = null;
    });
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

  Widget _buildImagePickerBox({
    required XFile? pickedFile,
    required String? currentImgUrl,
    required VoidCallback onTap,
  }) {
    String validUrl = "";

    if (currentImgUrl != null && currentImgUrl.isNotEmpty) {
      validUrl = _getValidImageUrl(currentImgUrl);
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 180,
        width: double.infinity,
        decoration: BoxDecoration(
          color: Colors.teal.shade50,
          borderRadius: BorderRadius.circular(15),
          border: Border.all(color: Colors.teal.shade300, width: 2),
        ),
        child: pickedFile != null
            ? ClipRRect(
                borderRadius: BorderRadius.circular(13),
                child: Image.file(
                  File(pickedFile.path),
                  fit: BoxFit.cover,
                ),
              )
            : validUrl.isNotEmpty
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(13),
                    child: Image.network(
                      validUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => _emptyImagePicker(),
                    ),
                  )
                : _emptyImagePicker(),
      ),
    );
  }

  Widget _emptyImagePicker() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.add_photo_alternate_rounded,
          size: 50,
          color: Colors.teal.shade400,
        ),
        const SizedBox(height: 10),
        const Text(
          "Chạm để chọn ảnh",
          style: TextStyle(
            color: Colors.teal,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(
            _lang == "vi" ? "Quản lý Trang chủ CMS" : "Homepage CMS",
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          backgroundColor: Colors.teal,
          foregroundColor: Colors.white,
          actions: [
            IconButton(
              onPressed: _fetchCmsData,
              icon: const Icon(Icons.refresh),
            ),
          ],
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
                children: [
                  _buildAboutTab(),
                  _buildNewsTab(),
                  _buildContactTab(),
                ],
              ),
      ),
    );
  }

  Widget _buildAboutTab() {
    final currentImage = _aboutData['images'] is List && (_aboutData['images'] as List).isNotEmpty
        ? (_aboutData['images'] as List).first.toString()
        : "";

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
                currentImgUrl: currentImage,
                onTap: () => _pickImage(isAbout: true),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _aboutTitleCtrl,
                decoration: const InputDecoration(
                  labelText: "Tiêu đề giới thiệu",
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 15),
              DropdownButtonFormField<String>(
                value: _aboutLayout,
                decoration: const InputDecoration(
                  labelText: "Bố cục hiển thị",
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: "left", child: Text("Ảnh Trái - Chữ Phải")),
                  DropdownMenuItem(value: "right", child: Text("Ảnh Phải - Chữ Trái")),
                  DropdownMenuItem(value: "full", child: Text("Banner - Ảnh Trên")),
                ],
                onChanged: (v) => setState(() => _aboutLayout = v ?? "left"),
              ),
              const SizedBox(height: 15),
              TextField(
                controller: _aboutContentCtrl,
                maxLines: 7,
                decoration: const InputDecoration(
                  labelText: "Nội dung giới thiệu",
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 25),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.teal,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _updateAbout,
                  icon: const Icon(Icons.save),
                  label: const Text(
                    "LƯU THAY ĐỔI GIỚI THIỆU",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
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
            color: _editingPostId != null ? Colors.amber.shade50 : Colors.teal.shade50,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15),
              side: BorderSide(
                color: _editingPostId != null ? Colors.amber : Colors.teal.shade200,
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          _editingPostId != null ? "✏️ Sửa bài viết" : "➕ Soạn bài mới",
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                            color: _editingPostId != null ? Colors.amber.shade900 : Colors.teal,
                          ),
                        ),
                      ),
                      if (_editingPostId != null)
                        TextButton(
                          onPressed: _cancelEditing,
                          child: const Text("Hủy", style: TextStyle(color: Colors.red)),
                        )
                    ],
                  ),
                  const SizedBox(height: 15),
                  const Text(
                    "Ảnh đại diện bài viết",
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey),
                  ),
                  const SizedBox(height: 8),
                  _buildImagePickerBox(
                    pickedFile: _pickedPostImage,
                    currentImgUrl: _oldPostImageUrl,
                    onTap: () => _pickImage(isAbout: false),
                  ),
                  const SizedBox(height: 15),
                  TextField(
                    controller: _postTitleCtrl,
                    decoration: const InputDecoration(
                      labelText: "Tiêu đề tin tức",
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 15),
                  TextField(
                    controller: _postContentCtrl,
                    maxLines: 6,
                    decoration: const InputDecoration(
                      labelText: "Nội dung chi tiết",
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 15),
                  DropdownButtonFormField<String>(
                    value: _postStatus,
                    decoration: const InputDecoration(
                      labelText: "Trạng thái",
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(value: "published", child: Text("published")),
                      DropdownMenuItem(value: "draft", child: Text("draft")),
                    ],
                    onChanged: (v) => setState(() => _postStatus = v ?? "published"),
                  ),
                  const SizedBox(height: 25),
                  const Text(
                    "👀 XEM TRƯỚC HIỂN THỊ:",
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey),
                  ),
                  const SizedBox(height: 8),
                  _buildLivePreviewCard(),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _editingPostId != null ? Colors.amber.shade700 : Colors.teal,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: _submitPost,
                      icon: const Icon(Icons.send),
                      label: Text(
                        _editingPostId != null ? "CẬP NHẬT BÀI VIẾT" : "ĐĂNG BÀI VIẾT",
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                  )
                ],
              ),
            ),
          ),
          const SizedBox(height: 30),
          const Text(
            "📰 Quản lý bài viết đã đăng",
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 10),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _posts.length,
            itemBuilder: (context, index) {
              final p = _posts[index];
              final id = (p['id'] ?? p['_id'] ?? "").toString();
              final imgUrl = _getValidImageUrl(p['image_url']);
              final title = _getLocalized(p['title'], "");

              return Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(10),
                  leading: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.network(
                      imgUrl,
                      width: 60,
                      height: 60,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        width: 60,
                        height: 60,
                        color: Colors.grey[300],
                        child: const Icon(Icons.image),
                      ),
                    ),
                  ),
                  title: Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text("Ngày đăng: ${p['date'] ?? ''} | ${p['status'] ?? 'published'}"),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit, color: Colors.blue),
                        onPressed: () => _startEditingPost(p),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        onPressed: () => _deletePost(id),
                      ),
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

  Widget _buildLivePreviewCard() {
    final pTitle = _postTitleCtrl.text.isEmpty ? "Tiêu đề bài báo..." : _postTitleCtrl.text;
    final pContent = _postContentCtrl.text.isEmpty ? "Nội dung bài báo..." : _postContentCtrl.text;

    Widget imageWidget;

    if (_pickedPostImage != null) {
      imageWidget = Image.file(File(_pickedPostImage!.path), fit: BoxFit.cover);
    } else if (_oldPostImageUrl.isNotEmpty) {
      imageWidget = Image.network(_getValidImageUrl(_oldPostImageUrl), fit: BoxFit.cover);
    } else {
      imageWidget = Image.network(_getValidImageUrl(""), fit: BoxFit.cover);
    }

    return Container(
      width: 250,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 3),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
            child: SizedBox(
              height: 140,
              width: double.infinity,
              child: imageWidget,
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  pTitle,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, height: 1.3),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),
                Text(
                  pContent,
                  style: const TextStyle(color: Colors.black54, fontSize: 13, height: 1.3),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
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
              const Text(
                "Thông tin liên hệ chân trang",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.teal),
              ),
              const Divider(height: 30),
              TextField(
                controller: _phoneCtrl,
                decoration: const InputDecoration(
                  labelText: "Hotline",
                  prefixIcon: Icon(Icons.phone),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 15),
              TextField(
                controller: _emailCtrl,
                decoration: const InputDecoration(
                  labelText: "Email hỗ trợ",
                  prefixIcon: Icon(Icons.email),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 15),
              TextField(
                controller: _addressCtrl,
                decoration: const InputDecoration(
                  labelText: "Địa chỉ trụ sở",
                  prefixIcon: Icon(Icons.location_on),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 15),
              TextField(
                controller: _contactDescCtrl,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: "Mô tả liên hệ",
                  prefixIcon: Icon(Icons.description),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 25),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.teal,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _updateContact,
                  icon: const Icon(Icons.save),
                  label: const Text(
                    "LƯU THÔNG TIN LIÊN HỆ",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }
}