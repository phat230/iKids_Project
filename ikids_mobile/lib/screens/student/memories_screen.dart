import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class MemoriesScreen extends StatefulWidget {
  const MemoriesScreen({super.key});

  @override
  State<MemoriesScreen> createState() => _MemoriesScreenState();
}

class _MemoriesScreenState extends State<MemoriesScreen> {
  List<dynamic> _memories = [];
  bool _isLoading = true;

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
        // Tăng số tim trên giao diện ngay lập tức mà không cần load lại API
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
    return Scaffold(
      backgroundColor: Colors.grey[200],
      appBar: AppBar(
        title: const Text("📸 Góc Kỷ Niệm", style: TextStyle(fontWeight: FontWeight.bold)), 
        backgroundColor: Colors.purple, 
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: "Làm mới",
            onPressed: _fetchMemories,
          )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.purple))
        : _memories.isEmpty
            ? const Center(child: Text("✨ Hiện chưa có khoảnh khắc kỷ niệm nào.", style: TextStyle(fontSize: 16)))
            // HIỂN THỊ DẠNG DANH SÁCH CUỘN (Tương tự Feed Facebook)
            : RefreshIndicator(
                color: Colors.purple,
                onRefresh: _fetchMemories,
                child: ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _memories.length,
                  itemBuilder: (context, index) {
                    final memory = _memories[index];
                    
                    // Bóc tách dữ liệu an toàn
                    String memId = memory['_id'] ?? memory['id'] ?? '';
                    String teacherName = memory['teacher_name'] ?? 'Giáo viên';
                    String mediaUrl = memory['media_url'] ?? 'https://via.placeholder.com/800x500';
                    int likes = memory['likes'] ?? 0;
                    
                    // Xử lý chuỗi ngày tháng
                    String rawDate = memory['created_at'] ?? '';
                    String timeStr = rawDate.length >= 16 ? rawDate.substring(0, 16).replaceAll('T', ' ') : "---";

                    // Xử lý ngôn ngữ: Nếu description là dạng từ điển đa ngôn ngữ
                    String description = "Không có mô tả.";
                    if (memory['description'] is Map) {
                      description = memory['description']['vi'] ?? "Không có mô tả.";
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
                          // 1. Dòng tiêu đề (Avatar + Tên giáo viên + Thời gian)
                          ListTile(
                            leading: const CircleAvatar(
                              backgroundColor: Colors.purple, 
                              child: Icon(Icons.school, color: Colors.white)
                            ),
                            title: Text(teacherName, style: const TextStyle(fontWeight: FontWeight.bold)),
                            subtitle: Text("đã chia sẻ một khoảnh khắc • $timeStr", style: const TextStyle(fontSize: 12)),
                          ),
                          
                          // 2. Hình ảnh kỷ niệm
                          Image.network(
                            mediaUrl, 
                            width: double.infinity, 
                            height: 250, 
                            fit: BoxFit.cover,
                            // Bọc thép lỗi đường dẫn ảnh hỏng
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
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            child: Row(
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.favorite, color: Colors.red, size: 28),
                                  onPressed: () => _likeMemory(memId, index),
                                ),
                                Text("$likes lượt thích", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
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