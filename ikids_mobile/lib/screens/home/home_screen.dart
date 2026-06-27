import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

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
      "hero_title": "iKids Education Portal",
      "hero_subtitle": "Hệ thống học tập thông minh dành cho trung tâm, giáo viên, phụ huynh và học sinh.",
      "btn_login": "Đăng Nhập",
      "lbl_about": "Về Chúng Tôi",
      "lbl_news": "Tin Tức & Sự Kiện",
      "lbl_contact": "Thông Tin Liên Hệ",
      "lbl_address": "Địa chỉ:",
      "lbl_email": "Email:",
      "lbl_hotline": "Hotline:",
      "msg_empty_about": "Nội dung giới thiệu đang được cập nhật.",
      "msg_empty_news": "Hiện chưa có tin tức nào được xuất bản.",
      "msg_empty_contact": "Thông tin liên hệ đang được cập nhật.",
      "err_conn": "Lỗi kết nối máy chủ!",
      "unassigned": "Chưa cập nhật",
      "read_more": "Đọc chi tiết ➔",
      "detail_title": "Chi tiết tin tức",
      "feature_class": "Quản lý lớp học",
      "feature_parent": "Kết nối phụ huynh",
      "feature_ai": "Học tập thông minh",
    },
    "en": {
      "title": "iKids Edu",
      "hero_title": "iKids Education Portal",
      "hero_subtitle": "A smart learning platform for centers, teachers, parents, and students.",
      "btn_login": "Sign In",
      "lbl_about": "About Us",
      "lbl_news": "News & Events",
      "lbl_contact": "Contact Info",
      "lbl_address": "Address:",
      "lbl_email": "Email:",
      "lbl_hotline": "Hotline:",
      "msg_empty_about": "About content is being updated.",
      "msg_empty_news": "No news or events published yet.",
      "msg_empty_contact": "Contact information is being updated.",
      "err_conn": "Server connection error!",
      "unassigned": "Updating",
      "read_more": "Read more ➔",
      "detail_title": "News Details",
      "feature_class": "Class Management",
      "feature_parent": "Parent Connection",
      "feature_ai": "Smart Learning",
    }
  };

  String get _apiTv3 => AppConfig.apiTv3;

  @override
  void initState() {
    super.initState();
    _fetchCmsData();
  }

  Future<void> _fetchCmsData() async {
    if (!mounted) return;

    setState(() => _isLoading = true);

    try {
      final savedLang = await _storage.read(key: 'app_lang');

      if (savedLang != null && mounted) {
        setState(() => _lang = savedLang);
      }

      final responses = await Future.wait([
        http.get(Uri.parse('$_apiTv3/about')).timeout(const Duration(seconds: 15)),
        http.get(Uri.parse('$_apiTv3/contact')).timeout(const Duration(seconds: 15)),
        http.get(Uri.parse('$_apiTv3/posts')).timeout(const Duration(seconds: 15)),
      ]);

      final about = _decodeMap(responses[0]);
      final contact = _decodeMap(responses[1]);
      final rawPosts = _decodeList(responses[2]);

      final publishedPosts = rawPosts.where((p) {
        if (p is! Map) return false;
        return (p['status'] ?? 'published').toString() == 'published';
      }).toList();

      if (!mounted) return;

      setState(() {
        _aboutData = about;
        _contactData = contact;
        _posts = publishedPosts;
        _isLoading = false;
      });
    } catch (e) {
      debugPrint("Home CMS error: $e");

      if (!mounted) return;

      setState(() => _isLoading = false);
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

  Future<void> _toggleLanguage() async {
    final newLang = _lang == "vi" ? "en" : "vi";

    setState(() => _lang = newLang);

    await _storage.write(key: 'app_lang', value: newLang);

    await _fetchCmsData();
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Colors.indigo),
            )
          : RefreshIndicator(
              onRefresh: _fetchCmsData,
              color: Colors.indigo,
              child: CustomScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  _buildAppBar(labels),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildFeatureRow(labels),
                          const SizedBox(height: 24),
                          _buildSectionHeader(labels["lbl_about"]!),
                          _buildAboutCard(labels),
                          const SizedBox(height: 28),
                          _buildSectionHeader(labels["lbl_news"]!),
                        ],
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: _buildHorizontalNewsFeed(labels),
                  ),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
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

  Widget _buildAppBar(Map<String, String> labels) {
    return SliverAppBar(
      expandedHeight: 250,
      floating: false,
      pinned: true,
      backgroundColor: Colors.indigo.shade900,
      actions: [
        TextButton(
          onPressed: _toggleLanguage,
          child: Text(
            _lang.toUpperCase(),
            style: const TextStyle(
              color: Colors.cyanAccent,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(right: 12, top: 10, bottom: 10),
          child: ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.cyanAccent,
              foregroundColor: Colors.indigo.shade900,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            onPressed: () => Navigator.pushNamed(context, '/login'),
            child: Text(
              labels["btn_login"]!,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
          ),
        )
      ],
      flexibleSpace: FlexibleSpaceBar(
        title: Text(
          labels["title"]!,
          style: const TextStyle(
            fontWeight: FontWeight.w900,
            color: Colors.white,
            shadows: [
              Shadow(color: Colors.black45, blurRadius: 10),
            ],
          ),
        ),
        background: Stack(
          fit: StackFit.expand,
          children: [
            Image.network(
              "https://images.unsplash.com/photo-1546410531-dd4cb6ca7404?q=80&w=1200&auto=format&fit=crop",
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Container(
                color: Colors.indigo.shade800,
              ),
            ),
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    Colors.indigo.shade900.withOpacity(0.95),
                  ],
                ),
              ),
            ),
            Positioned(
              left: 18,
              right: 18,
              bottom: 62,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    labels["hero_title"]!,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 26,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    labels["hero_subtitle"]!,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureRow(Map<String, String> labels) {
    return Row(
      children: [
        Expanded(
          child: _featureCard(
            icon: Icons.class_,
            title: labels["feature_class"]!,
            color: Colors.indigo,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _featureCard(
            icon: Icons.family_restroom,
            title: labels["feature_parent"]!,
            color: Colors.teal,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _featureCard(
            icon: Icons.smart_toy,
            title: labels["feature_ai"]!,
            color: Colors.deepOrange,
          ),
        ),
      ],
    );
  }

  Widget _featureCard({
    required IconData icon,
    required String title,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.15)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color),
          const SizedBox(height: 8),
          Text(
            title,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          )
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
          color: Colors.indigo,
        ),
      ),
    );
  }

  Widget _buildAboutCard(Map<String, String> labels) {
    final aboutTitle = _getLocalized(_aboutData['title'], "iKids Education");
    final rawContent = _getLocalized(_aboutData['content'], "");
    final cleanContent = _cleanHtmlToPlainText(rawContent);

    final images = _aboutData['images'];
    String imgUrl = "";

    if (images is List && images.isNotEmpty) {
      imgUrl = _getValidImageUrl(images.first);
    }

    final layout = (_aboutData['layout'] ?? "left").toString();

    final textContent = Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            aboutTitle,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            cleanContent.isEmpty ? labels["msg_empty_about"]! : cleanContent,
            style: const TextStyle(
              fontSize: 14,
              color: Colors.black87,
              height: 1.5,
            ),
          ),
        ],
      ),
    );

    final imageContent = ClipRRect(
      borderRadius: layout == "full"
          ? const BorderRadius.vertical(top: Radius.circular(15))
          : layout == "left"
              ? const BorderRadius.horizontal(left: Radius.circular(15))
              : const BorderRadius.horizontal(right: Radius.circular(15)),
      child: Image.network(
        imgUrl.isEmpty ? _getValidImageUrl(null) : imgUrl,
        height: layout == "full" ? 200 : 150,
        width: layout == "full" ? double.infinity : 130,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => Container(
          color: Colors.grey[300],
          width: layout == "full" ? double.infinity : 130,
          height: layout == "full" ? 200 : 150,
          child: const Icon(Icons.business),
        ),
      ),
    );

    return Card(
      elevation: 3,
      shadowColor: Colors.black26,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
      ),
      child: layout == "left"
          ? Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                imageContent,
                Expanded(child: textContent),
              ],
            )
          : layout == "right"
              ? Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: textContent),
                    imageContent,
                  ],
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    imageContent,
                    textContent,
                  ],
                ),
    );
  }

  Widget _buildHorizontalNewsFeed(Map<String, String> labels) {
    if (_posts.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            labels["msg_empty_news"]!,
            style: const TextStyle(
              color: Colors.grey,
              fontStyle: FontStyle.italic,
            ),
          ),
        ),
      );
    }

    return SizedBox(
      height: 310,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: _posts.length,
        itemBuilder: (context, index) {
          final p = _posts[index];

          final pTitle = _getLocalized(p['title'], "No Title");
          final rawContent = _getLocalized(p['content'], "");
          final cleanContent = _cleanHtmlToPlainText(rawContent);
          final pImg = _getValidImageUrl(p['image_url']);

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
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  )
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(15),
                    ),
                    child: Image.network(
                      pImg,
                      height: 145,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        height: 145,
                        width: double.infinity,
                        color: Colors.grey[200],
                        child: const Icon(
                          Icons.image,
                          color: Colors.grey,
                        ),
                      ),
                    ),
                  ),
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            pTitle,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                              height: 1.3,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 6),
                          Text(
                            cleanContent,
                            style: const TextStyle(
                              color: Colors.black54,
                              fontSize: 13,
                              height: 1.3,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const Spacer(),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  const Icon(
                                    Icons.access_time_filled,
                                    size: 13,
                                    color: Colors.blueGrey,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    "${p['date'] ?? ''}",
                                    style: const TextStyle(
                                      fontSize: 11,
                                      color: Colors.blueGrey,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                              Text(
                                labels["read_more"]!,
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.indigo.shade700,
                                ),
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
    final addrDisplay = _getLocalized(
      _contactData['address'],
      labels["unassigned"]!,
    );

    final phone = (_contactData['phone'] ?? labels["unassigned"]!).toString();
    final email = (_contactData['email'] ?? labels["unassigned"]!).toString();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.indigo.shade900,
            Colors.blue.shade900,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 10,
            offset: Offset(0, 5),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            labels["lbl_contact"]!,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
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
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: RichText(
        text: TextSpan(
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 13,
            height: 1.5,
          ),
          children: [
            TextSpan(
              text: "$title ",
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.cyanAccent,
              ),
            ),
            TextSpan(text: value),
          ],
        ),
      ),
    );
  }
}


// =======================================================================
// MÀN HÌNH CHI TIẾT TIN TỨC
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

  String _getLocalized(dynamic field, String defaultVal) {
    if (field == null) return defaultVal;

    if (field is Map) {
      return (field[lang] ?? field['vi'] ?? field['en'] ?? defaultVal).toString();
    }

    return field.toString();
  }

  @override
  Widget build(BuildContext context) {
    final pTitle = _getLocalized(postData['title'], "");
    final rawContent = _getLocalized(postData['content'], "");
    final cleanContent = _cleanHtmlToPlainText(rawContent);
    final dateStr = (postData['date'] ?? '').toString();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text(
          lang == "vi" ? "Chi tiết tin tức" : "News Details",
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
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
                height: 250,
                width: double.infinity,
                color: Colors.grey[200],
                child: const Icon(
                  Icons.image,
                  size: 50,
                  color: Colors.grey,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    pTitle,
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Colors.indigo.shade900,
                      height: 1.3,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(
                        Icons.calendar_month_rounded,
                        size: 16,
                        color: Colors.blueGrey,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        dateStr,
                        style: const TextStyle(
                          fontSize: 13,
                          color: Colors.blueGrey,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 20),
                    child: Divider(
                      thickness: 1,
                      color: Colors.black12,
                    ),
                  ),
                  Text(
                    cleanContent,
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.7,
                      color: Colors.black87,
                    ),
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