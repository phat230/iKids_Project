import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";

  Map<String, dynamic> _aboutData = {};
  Map<String, dynamic> _contactData = {};
  List<dynamic> _posts = [];

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "iKids Edu",
      "btn_login": "Đăng Nhập",
      "lbl_about": "Về Chúng Tôi",
      "lbl_news": "Tin Tức & Sự Kiện",
      "lbl_contact": "Thông Tin Liên Hệ",
      "lbl_address": "Địa chỉ:",
      "lbl_email": "Email:",
      "lbl_hotline": "Hotline:",
      "msg_empty_news": "Hiện chưa có tin tức nào được xuất bản.",
      "err_conn": "Lỗi kết nối máy chủ!",
      "unassigned": "Chưa cập nhật"
    },
    "en": {
      "title": "iKids Edu",
      "btn_login": "Sign In",
      "lbl_about": "About Us",
      "lbl_news": "News & Events",
      "lbl_contact": "Contact Info",
      "lbl_address": "Address:",
      "lbl_email": "Email:",
      "lbl_hotline": "Hotline:",
      "msg_empty_news": "No news or events published yet.",
      "err_conn": "Server connection error!",
      "unassigned": "Updating"
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchCmsData();
  }

  Future<void> _fetchCmsData() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    try {
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

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
          
          List<dynamic> rawPosts = responses[2].statusCode == 200 ? jsonDecode(utf8.decode(responses[2].bodyBytes)) : [];
          _posts = rawPosts.where((p) => p['status'] == 'published').toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  String _getLocalized(dynamic field, String defaultVal) {
    if (field == null) return defaultVal;
    if (field is Map) return field[_lang] ?? field['vi'] ?? defaultVal;
    return field.toString();
  }

  // ✅ ĐÃ SỬA: Đưa ảnh mặc định về đúng "static/anh_laptop.jpg" giống bên Web
String _getValidImageUrl(dynamic imgPath) {
    String path = imgPath?.toString() ?? "";
    
    // 1. Nếu bài viết không có ảnh, hoặc đang dùng cái tên "anh_laptop.jpg" bị thiếu trên server
    // -> Trả về thẳng một bức ảnh lớp học mặc định từ internet cho an toàn & đẹp.
    if (path.isEmpty || path.contains("anh_laptop.jpg")) {
      return "https://images.unsplash.com/photo-1546410531-dd4cb6ca7404?q=80&w=800&auto=format&fit=crop";
    }
    
    // 2. Nếu là ảnh do Admin/Operator vừa tải lên từ điện thoại
    String finalUrl = path;
    if (!path.startsWith("http")) {
      String cleanPath = path.startsWith("/") ? path.substring(1) : path;
      finalUrl = "${AppConfig.apiUrl}/$cleanPath";
    }
    
    // Gắn thêm thời gian để ép Flutter tải lại ảnh mới (chống Cache)
    return "$finalUrl?v=${DateTime.now().millisecondsSinceEpoch}";
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.indigo))
          : RefreshIndicator(
              onRefresh: _fetchCmsData,
              color: Colors.indigo,
              child: CustomScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  SliverAppBar(
                    expandedHeight: 220.0,
                    floating: false,
                    pinned: true,
                    backgroundColor: Colors.indigo.shade900,
                    actions: [
                      TextButton(
                        onPressed: () async {
                          setState(() => _lang = _lang == "vi" ? "en" : "vi");
                          await _storage.write(key: 'app_lang', value: _lang);
                          _fetchCmsData(); 
                        },
                        child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold)),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(right: 12, top: 10, bottom: 10),
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.cyanAccent, foregroundColor: Colors.indigo.shade900, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                          onPressed: () => Navigator.pushNamed(context, '/login'),
                          child: Text(labels["btn_login"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        ),
                      )
                    ],
                    flexibleSpace: FlexibleSpaceBar(
                      title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, shadows: [Shadow(color: Colors.black45, blurRadius: 10)])),
                      background: Stack(
                        fit: StackFit.expand,
                        children: [
                          Image.network(
                            _getValidImageUrl("static/anh_laptop.jpg"), // Dùng ảnh mặc định cho Banner to
                            fit: BoxFit.cover,
                            errorBuilder: (_,__,___) => Container(color: Colors.indigo.shade800),
                          ),
                          Container(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topCenter, end: Alignment.bottomCenter,
                                colors: [Colors.transparent, Colors.indigo.shade900.withOpacity(0.9)],
                              )
                            ),
                          )
                        ],
                      ),
                    ),
                  ),

                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // --- 1. KHỐI GIỚI THIỆU ---
                          _buildSectionHeader(labels["lbl_about"]!),
                          _buildAboutCard(),
                          const SizedBox(height: 35),

                          // --- 2. KHỐI TIN TỨC & SỰ KIỆN ---
                          _buildSectionHeader(labels["lbl_news"]!),
                          const SizedBox(height: 10),
                          _buildNewsFeed(labels),
                          const SizedBox(height: 35),

                          // --- 3. FOOTER THÔNG TIN LIÊN HỆ ---
                          _buildContactFooter(labels),
                          const SizedBox(height: 30),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.indigo)),
    );
  }

  // ✅ ĐÃ SỬA: Card Giới thiệu nay đã đọc biến "layout" (left, right, full)
  Widget _buildAboutCard() {
    String aboutTitle = _getLocalized(_aboutData['title'], "iKids Education");
    String aboutContent = _getLocalized(_aboutData['content'], "");
    aboutContent = aboutContent.replaceAll(RegExp(r'<[^>]*>'), '');

    List<dynamic> images = _aboutData['images'] ?? [];
    String imgUrl = _getValidImageUrl(images.isNotEmpty ? images[0] : null);
    
    String layout = _aboutData['layout'] ?? "left";

    // Khối chữ
    Widget textContent = Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(aboutTitle, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87)),
          const SizedBox(height: 10),
          Text(aboutContent.isEmpty ? "..." : aboutContent, style: const TextStyle(fontSize: 14, color: Colors.black87, height: 1.5)),
        ],
      ),
    );

    // Khối ảnh (tự chỉnh kích thước dựa trên layout)
    Widget imageContent = ClipRRect(
      borderRadius: layout == "full" 
        ? const BorderRadius.vertical(top: Radius.circular(15)) 
        : (layout == "left" ? const BorderRadius.horizontal(left: Radius.circular(15)) : const BorderRadius.horizontal(right: Radius.circular(15))),
      child: Image.network(
        imgUrl, 
        height: layout == "full" ? 200 : 150, 
        width: layout == "full" ? double.infinity : 130, 
        fit: BoxFit.cover, 
        errorBuilder: (_, __, ___) => Container(color: Colors.grey[300], width: 130, height: 150, child: const Icon(Icons.business))
      ),
    );

    return Card(
      elevation: 3,
      shadowColor: Colors.black26,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: layout == "left"
          ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [imageContent, Expanded(child: textContent)])
          : layout == "right"
              ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: textContent), imageContent])
              : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [imageContent, textContent]), // Banner Full
    );
  }

  // ✅ ĐÃ SỬA: Card Tin tức nay đã đọc biến "layout" (left, right, full)
  Widget _buildNewsFeed(Map<String, String> labels) {
    if (_posts.isEmpty) {
      return Center(child: Padding(padding: const EdgeInsets.all(20.0), child: Text(labels["msg_empty_news"]!, style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic))));
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _posts.length,
      itemBuilder: (context, index) {
        final p = _posts[index];
        String pTitle = _getLocalized(p['title'], "No Title");
        String pContent = _getLocalized(p['content'], "");
        pContent = pContent.replaceAll(RegExp(r'<[^>]*>'), ''); 
        
        String pImg = _getValidImageUrl(p['image_url']);
        String layout = p['layout'] ?? "left";

        // Khối chữ cho bài viết
        Widget textContent = Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(pTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15), maxLines: 2, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 6),
              Text(pContent, style: const TextStyle(color: Colors.black54, fontSize: 13, height: 1.3), maxLines: layout == "full" ? 3 : 2, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 8),
              Text("🕒 ${p['date'] ?? ''}", style: const TextStyle(fontSize: 11, color: Colors.blueGrey, fontWeight: FontWeight.w600)),
            ],
          ),
        );

        // Khối ảnh cho bài viết
        Widget imageContent = ClipRRect(
          borderRadius: layout == "full" 
            ? const BorderRadius.vertical(top: Radius.circular(12)) 
            : BorderRadius.circular(8),
          child: Image.network(
            pImg, 
            width: layout == "full" ? double.infinity : 100, 
            height: layout == "full" ? 160 : 100, 
            fit: BoxFit.cover, 
            errorBuilder: (_, __, ___) => Container(width: 100, height: 100, color: Colors.grey[200], child: const Icon(Icons.image))
          ),
        );

        return Card(
          margin: const EdgeInsets.only(bottom: 16),
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: layout == "full"
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [imageContent, textContent],
              )
            : Padding(
                padding: const EdgeInsets.all(8.0),
                child: layout == "left"
                  ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [imageContent, const SizedBox(width: 10), Expanded(child: textContent)])
                  : Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: textContent), const SizedBox(width: 10), imageContent]),
              )
        );
      },
    );
  }

  Widget _buildContactFooter(Map<String, String> labels) {
    String addrDisplay = _getLocalized(_contactData['address'], labels["unassigned"]!);
    String phone = _contactData['phone'] ?? labels["unassigned"]!;
    String email = _contactData['email'] ?? labels["unassigned"]!;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [Colors.indigo.shade900, Colors.blue.shade900], begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 10, offset: Offset(0, 5))]
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(labels["lbl_contact"]!, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 15),
          _buildContactRow(labels["lbl_address"]!, addrDisplay),
          _buildContactRow(labels["lbl_email"]!, email),
          _buildContactRow(labels["lbl_hotline"]!, phone),
        ],
      ),
    );
  }

  Widget _buildContactRow(String title, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: RichText(
        text: TextSpan(
          style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.5),
          children: [
            TextSpan(text: "$title ", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.cyanAccent)),
            TextSpan(text: value),
          ],
        ),
      ),
    );
  }
}