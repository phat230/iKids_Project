import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class ParentMemoriesScreen extends StatefulWidget {
  const ParentMemoriesScreen({super.key});

  @override
  State<ParentMemoriesScreen> createState() => _ParentMemoriesScreenState();
}

class _ParentMemoriesScreenState extends State<ParentMemoriesScreen> {
  List<dynamic> _memories = [];
  bool _isLoading = true;
  String _lang = "vi";

  // Bộ từ điển song ngữ đồng bộ với Web
  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "📸 Góc Kỷ Niệm",
      "subtitle": "Nơi lưu giữ những khoảnh khắc học tập và vui chơi tuyệt vời của các bé!",
      "info_empty": "✨ Hiện chưa có kỷ niệm nào được chia sẻ. Những khoảnh khắc đáng yêu sẽ xuất hiện tại đây!",
      "default_teacher": "Giáo viên iKids",
      "hint_like": "Hãy nhấn tim để ủng hộ khoảnh khắc này của bé!",
      "no_description": "Không có mô tả bài viết."
    },
    "en": {
      "title": "📸 Class Memories Corner",
      "subtitle": "Preserving the wonderful learning and playing moments of our children!",
      "info_empty": "✨ There are currently no memories shared yet. Adorable moments will appear here soon!",
      "default_teacher": "iKids Teacher",
      "hint_like": "Click the heart button to show love for this moment!",
      "no_description": "No description provided."
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchMemories();
  }

  // 1. Gọi API lấy danh sách kỷ niệm từ TV3
  Future<void> _fetchMemories() async {
    if (!mounted) return;
    setState(() => _isLoading = true);
    
    try {
      final response = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/memories')).timeout(const Duration(seconds: 15));
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(response.bodyBytes));
        if (mounted) {
          setState(() {
            _memories = data;
          });
        }
      } else {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi tải dữ liệu: ${response.statusCode}")));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text("Lỗi kết nối mạng!", style: TextStyle(color: Colors.white)),
          backgroundColor: Colors.red,
        ));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // 2. Gọi API Thả tim
  Future<void> _likeMemory(String id, int index) async {
    try {
      final response = await http.post(Uri.parse('${AppConfig.apiUrl}/api/tv3/memories/$id/like')).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        // Tăng số tim trên giao diện ngay lập tức
        setState(() {
          _memories[index]['likes'] = (_memories[index]['likes'] ?? 0) + 1;
        });
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi kết nối khi thả tim!")));
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[200],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)), 
        backgroundColor: Colors.purple, 
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: "Làm mới",
            onPressed: _fetchMemories,
          ),
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.purple))
        : _memories.isEmpty
            ? Center(
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Text(labels["info_empty"]!, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16)),
                )
              )
            // HIỂN THỊ DẠNG DANH SÁCH CUỘN (Tương tự Feed Facebook)
            : RefreshIndicator(
                color: Colors.purple,
                onRefresh: _fetchMemories,
                child: Column(
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      color: Colors.purple[50],
                      child: Text(labels["subtitle"]!, style: TextStyle(color: Colors.purple[900], fontStyle: FontStyle.italic, fontSize: 13)),
                    ),
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _memories.length,
                        itemBuilder: (context, index) {
                          final memory = _memories[index];
                          
                          // Bóc tách dữ liệu
                          String memId = memory['_id'] ?? memory['id'] ?? '';
                          String teacherName = memory['teacher_name'] ?? labels["default_teacher"]!;
                          if (teacherName == "Giáo viên iKids" && _lang == "en") teacherName = "iKids Teacher";

                          String mediaUrl = memory['media_url'] ?? 'https://via.placeholder.com/800x500';
                          int likes = memory['likes'] ?? 0;
                          
                          String rawDate = memory['created_at'] ?? '';
                          String timeStr = rawDate.length >= 16 ? rawDate.substring(0, 16).replaceAll('T', ' ') : "---";

                          // Xử lý mô tả đa ngôn ngữ thông minh
                          String description = labels["no_description"]!;
                          if (memory['description'] is Map) {
                            description = memory['description'][_lang] ?? memory['description']['vi'] ?? labels["no_description"]!;
                          } else if (memory['description'] is String && memory['description'].toString().isNotEmpty) {
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
                                // 1. Tiêu đề
                                ListTile(
                                  leading: const CircleAvatar(
                                    backgroundColor: Colors.purple, 
                                    child: Icon(Icons.school, color: Colors.white)
                                  ),
                                  title: Text(teacherName, style: const TextStyle(fontWeight: FontWeight.bold)),
                                  subtitle: Text("🕒 $timeStr", style: const TextStyle(fontSize: 12)),
                                ),
                                
                                // 2. Hình ảnh kỷ niệm
                                Image.network(
                                  mediaUrl, 
                                  width: double.infinity, 
                                  height: 250, 
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) => Container(
                                    height: 200,
                                    color: Colors.grey[300],
                                    child: const Column(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Icon(Icons.broken_image, size: 50, color: Colors.grey),
                                        Text("Không thể tải ảnh", style: TextStyle(color: Colors.grey))
                                      ],
                                    ),
                                  ),
                                ),
                                
                                // 3. Nội dung mô tả
                                Padding(
                                  padding: const EdgeInsets.all(15.0),
                                  child: Text(description, style: const TextStyle(fontSize: 15, height: 1.4)),
                                ),
                                
                                // 4. Thanh tương tác (Thả tim)
                                const Divider(height: 1),
                                Padding(
                                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 5),
                                  child: Row(
                                    children: [
                                      IconButton(
                                        icon: const Icon(Icons.favorite, color: Colors.red, size: 28),
                                        onPressed: () => _likeMemory(memId, index),
                                      ),
                                      Text("$likes", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                      const SizedBox(width: 15),
                                      Expanded(child: Text(labels["hint_like"]!, style: const TextStyle(fontSize: 11, color: Colors.grey, fontStyle: FontStyle.italic))),
                                    ],
                                  ),
                                )
                              ],
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
    );
  }
}