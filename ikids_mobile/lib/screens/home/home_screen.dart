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

  String _cleanHtmlToPlainText(String htmlString) {
    String parsed = htmlString.replaceAll(RegExp(r'<br\s*/?>', caseSensitive: false), '\n');
    parsed = parsed.replaceAll(RegExp(r'</p>', caseSensitive: false), '\n\n');
    parsed = parsed.replaceAll(RegExp(r'<[^>]*>'), ''); // Xóa sạch các tag còn lại
    return parsed.trim();
  }

  String _getValidImageUrl(dynamic imgPath) {
    String path = imgPath?.toString() ?? "";
    
    final fallbackUrl = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png";

    if (path.trim().isEmpty || path.contains("anh_laptop.jpg")) {
      return fallbackUrl;
    }
    
    if (path.startsWith("http")) {
      return path;
    }
    
    final baseUrl = AppConfig.apiUrl.endsWith('/') ? AppConfig.apiUrl.substring(0, AppConfig.apiUrl.length - 1) : AppConfig.apiUrl;
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    
    final finalUrl = "$baseUrl/$cleanPath";
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
                            "https://images.unsplash.com/photo-1546410531-dd4cb6ca7404?q=80&w=1200&auto=format&fit=crop", 
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
                      padding: const EdgeInsets.only(left: 16, right: 16, top: 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildSectionHeader(labels["lbl_about"]!),
                          _buildAboutCard(),
                          const SizedBox(height: 35),
                          _buildSectionHeader(labels["lbl_news"]!),
                        ],
                      ),
                    ),
                  ),

                  // Khối Tin Tức (Lướt Ngang)
                  SliverToBoxAdapter(
                    child: _buildHorizontalNewsFeed(labels),
                  ),

                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        children: [
                          const SizedBox(height: 10),
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

  Widget _buildAboutCard() {
    String aboutTitle = _getLocalized(_aboutData['title'], "iKids Education");
    String rawContent = _getLocalized(_aboutData['content'], "");
    String cleanContent = _cleanHtmlToPlainText(rawContent);

    List<dynamic> images = _aboutData['images'] ?? [];
    String imgUrl = _getValidImageUrl(images.isNotEmpty ? images[0] : null);
    
    String layout = _aboutData['layout'] ?? "left";

    Widget textContent = Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(aboutTitle, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87)),
          const SizedBox(height: 10),
          Text(cleanContent.isEmpty ? "..." : cleanContent, style: const TextStyle(fontSize: 14, color: Colors.black87, height: 1.5)),
        ],
      ),
    );

    Widget imageContent = ClipRRect(
      borderRadius: layout == "full" 
        ? const BorderRadius.vertical(top: Radius.circular(15)) 
        : (layout == "left" ? const BorderRadius.horizontal(left: Radius.circular(15)) : const BorderRadius.horizontal(right: Radius.circular(15))),
      child: Image.network(
        imgUrl, 
        height: layout == "full" ? 200 : 150, 
        width: layout == "full" ? double.infinity : 130, 
        fit: BoxFit.cover, 
        errorBuilder: (_, __, ___) => Container(
          color: Colors.grey[300], 
          width: 130, 
          height: 150, 
          child: const Icon(Icons.business),
        ),
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
              : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [imageContent, textContent]), 
    );
  }

  Widget _buildHorizontalNewsFeed(Map<String, String> labels) {
    if (_posts.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Text(
            labels["msg_empty_news"]!,
            style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic),
          ),
        ),
      );
    }

    return SizedBox(
      height: 300, 
      child: ListView.builder(
        scrollDirection: Axis.horizontal, 
        physics: const BouncingScrollPhysics(), 
        padding: const EdgeInsets.symmetric(horizontal: 16.0),
        itemCount: _posts.length,
        itemBuilder: (context, index) {
          final p = _posts[index];
          String pTitle = _getLocalized(p['title'], "No Title");
          String rawContent = _getLocalized(p['content'], "");
          String cleanContent = _cleanHtmlToPlainText(rawContent); 
          
          String pImg = _getValidImageUrl(p['image_url']);

          return GestureDetector(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => NewsDetailScreen(
                    postData: p,
                    imageUrl: pImg,
                    lang: _lang,
                  ),
                ),
              );
            },
            child: Container(
              width: 250,
              margin: const EdgeInsets.only(right: 16, bottom: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(15),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 10, offset: const Offset(0, 4))
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
                    child: Image.network(
                      pImg, 
                      height: 140, 
                      width: double.infinity, 
                      fit: BoxFit.cover, 
                      errorBuilder: (_, __, ___) => Container(
                        height: 140, width: double.infinity, color: Colors.grey[200], child: const Icon(Icons.image, color: Colors.grey)
                      )
                    ),
                  ),
                  
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(pTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, height: 1.3), maxLines: 2, overflow: TextOverflow.ellipsis),
                          const SizedBox(height: 6),
                          Text(cleanContent, style: const TextStyle(color: Colors.black54, fontSize: 13, height: 1.3), maxLines: 2, overflow: TextOverflow.ellipsis),
                          const Spacer(), 
                          
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.access_time_filled, size: 13, color: Colors.blueGrey),
                                  const SizedBox(width: 4),
                                  Text("${p['date'] ?? ''}", style: const TextStyle(fontSize: 11, color: Colors.blueGrey, fontWeight: FontWeight.bold)),
                                ],
                              ),
                              Text(
                                _lang == "vi" ? "Đọc chi tiết ➔" : "Read more ➔",
                                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.indigo.shade700),
                              )
                            ],
                          ),
                        ],
                      ),
                    ),
                  )
                ],
              ),
            ),
          );
        },
      ),
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

// =======================================================================
//  MÀN HÌNH CHI TIẾT TIN TỨC
// =======================================================================
class NewsDetailScreen extends StatelessWidget {
  final dynamic postData;
  final String imageUrl;
  final String lang;

  const NewsDetailScreen({
    super.key,
    required this.postData,
    required this.imageUrl,
    required this.lang,
  });

  String _cleanHtmlToPlainText(String htmlString) {
    String parsed = htmlString.replaceAll(RegExp(r'<br\s*/?>', caseSensitive: false), '\n');
    parsed = parsed.replaceAll(RegExp(r'</p>', caseSensitive: false), '\n\n');
    parsed = parsed.replaceAll(RegExp(r'<[^>]*>'), '');
    return parsed.trim();
  }

  @override
  Widget build(BuildContext context) {
    String pTitle = postData['title'] is Map ? (postData['title'][lang] ?? postData['title']['vi'] ?? "") : postData['title'].toString();
    String rawContent = postData['content'] is Map ? (postData['content'][lang] ?? postData['content']['vi'] ?? "") : postData['content'].toString();
    
    String cleanContent = _cleanHtmlToPlainText(rawContent);
    String dateStr = postData['date'] ?? '';

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text(lang == "vi" ? "Chi tiết tin tức" : "News Details", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: Colors.indigo.shade900,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Image.network(
              imageUrl,
              width: double.infinity,
              height: 250,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Container(
                height: 250, width: double.infinity, color: Colors.grey[200], 
                child: const Icon(Icons.image, size: 50, color: Colors.grey)
              ),
            ),
            
            Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    pTitle,
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.indigo.shade900, height: 1.3),
                  ),
                  const SizedBox(height: 12),
                  
                  Row(
                    children: [
                      const Icon(Icons.calendar_month_rounded, size: 16, color: Colors.blueGrey),
                      const SizedBox(width: 6),
                      Text(
                        dateStr,
                        style: const TextStyle(fontSize: 13, color: Colors.blueGrey, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 20),
                    child: Divider(thickness: 1, color: Colors.black12),
                  ),
                  
                  Text(
                    cleanContent,
                    style: const TextStyle(fontSize: 16, height: 1.7, color: Colors.black87),
                  ),
                  
                  const SizedBox(height: 50), 
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}