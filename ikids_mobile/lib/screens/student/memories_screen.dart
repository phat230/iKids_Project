import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/config.dart';

class MemoriesScreen extends StatefulWidget {
  const MemoriesScreen({super.key});

  @override
  State<MemoriesScreen> createState() => _MemoriesScreenState();
}

class _MemoriesScreenState extends State<MemoriesScreen> {
  final _storage = const FlutterSecureStorage();
  List<dynamic> _memories = [];
  bool _isLoading = true;
  String _lang = "vi";

  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "📸 Góc Kỷ Niệm",
      "tooltip_refresh": "Làm mới",
      "empty_memories": "✨ Hiện chưa có khoảnh khắc kỷ niệm nào.",
      "shared_moment": "đã chia sẻ một khoảnh khắc",
      "no_desc": "Không có mô tả.",
      "likes": "lượt thích",
      "err_fetch": "Lỗi tải dữ liệu",
      "err_conn": "Lỗi kết nối mạng!",
      "err_like": "Lỗi kết nối khi thả tim!",
      "err_img": "Không thể tải ảnh",
    },
    "en": {
      "title": "📸 Class Memories",
      "tooltip_refresh": "Refresh",
      "empty_memories": "✨ No memories available yet.",
      "shared_moment": "shared a moment",
      "no_desc": "No description.",
      "likes": "likes",
      "err_fetch": "Error loading data",
      "err_conn": "Network connection error!",
      "err_like": "Error while liking!",
      "err_img": "Cannot load image",
    }
  };

  @override
  void initState() {
    super.initState();
    _initData();
  }

  Future<void> _initData() async {
    String? savedLang = await _storage.read(key: 'app_lang');
    if (savedLang != null) setState(() => _lang = savedLang);
    _fetchMemories();
  }

  Future<void> _fetchMemories() async {
    if (!mounted) return;
    setState(() => _isLoading = true);
    
    try {
      final response = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/memories')).timeout(const Duration(seconds: 15));
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(response.bodyBytes));
        if (mounted) setState(() => _memories = data);
      } else {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("${_locales[_lang]!['err_fetch']}: ${response.statusCode}")));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(_locales[_lang]!['err_conn']!, style: const TextStyle(color: Colors.white)),
          backgroundColor: Colors.red,
        ));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _likeMemory(String id, int index) async {
    try {
      final response = await http.post(Uri.parse('${AppConfig.apiUrl}/api/tv3/memories/$id/like')).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        setState(() {
          _memories[index]['likes'] = (_memories[index]['likes'] ?? 0) + 1;
        });
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_locales[_lang]!['err_like']!)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[200],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold)), 
        backgroundColor: Colors.purple, 
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: labels["tooltip_refresh"],
            onPressed: _fetchMemories,
          )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.purple))
        : _memories.isEmpty
            ? Center(child: Text(labels["empty_memories"]!, style: const TextStyle(fontSize: 16)))
            : RefreshIndicator(
                color: Colors.purple,
                onRefresh: _fetchMemories,
                child: ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _memories.length,
                  itemBuilder: (context, index) {
                    final memory = _memories[index];
                    
                    String memId = memory['_id'] ?? memory['id'] ?? '';
                    String teacherName = memory['teacher_name'] ?? 'Teacher';
                    String mediaUrl = memory['media_url'] ?? 'https://via.placeholder.com/800x500';
                    int likes = memory['likes'] ?? 0;
                    
                    String rawDate = memory['created_at'] ?? '';
                    String timeStr = rawDate.length >= 16 ? rawDate.substring(0, 16).replaceAll('T', ' ') : "---";

                    // Trích xuất đa ngôn ngữ an toàn
                    String description = labels["no_desc"]!;
                    if (memory['description'] is Map) {
                      description = memory['description'][_lang] ?? memory['description']['vi'] ?? labels["no_desc"]!;
                    } else if (memory['description'] is String) {
                      description = memory['description'];
                    }

                    return Card(
                      margin: const EdgeInsets.only(bottom: 20),
                      elevation: 3,
                      clipBehavior: Clip.antiAlias,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ListTile(
                            leading: const CircleAvatar(
                              backgroundColor: Colors.purple, 
                              child: Icon(Icons.school, color: Colors.white)
                            ),
                            title: Text(teacherName, style: const TextStyle(fontWeight: FontWeight.bold)),
                            subtitle: Text("${labels['shared_moment']} • $timeStr", style: const TextStyle(fontSize: 12)),
                          ),
                          
                          Image.network(
                            mediaUrl, 
                            width: double.infinity, 
                            height: 250, 
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) => Container(
                              height: 200,
                              color: Colors.grey[300],
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  const Icon(Icons.broken_image, size: 50, color: Colors.grey),
                                  Text(labels["err_img"]!, style: const TextStyle(color: Colors.grey))
                                ],
                              ),
                            ),
                          ),
                          
                          Padding(
                            padding: const EdgeInsets.all(15.0),
                            child: Text(description, style: const TextStyle(fontSize: 15, height: 1.4)),
                          ),
                          
                          const Divider(height: 1),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            child: Row(
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.favorite, color: Colors.red, size: 28),
                                  onPressed: () => _likeMemory(memId, index),
                                ),
                                Text("$likes ${labels['likes']}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                              ],
                            ),
                          )
                        ],
                      ),
                    );
                  },
                ),
              ),
    );
  }
}