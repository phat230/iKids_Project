import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:intl/intl.dart';
import '../../core/config.dart';
import '../../core/network.dart';

class TeacherAssignmentScreen extends StatefulWidget {
  const TeacherAssignmentScreen({super.key});

  @override
  State<TeacherAssignmentScreen> createState() => _TeacherAssignmentScreenState();
}

class _TeacherAssignmentScreenState extends State<TeacherAssignmentScreen> {
  final _storage = const FlutterSecureStorage();
  
  List<dynamic> _quizzes = [];
  List<dynamic> _videos = [];
  List<dynamic> _myClasses = [];
  
  bool _isLoading = true;
  String _teacherEmail = "";
  String _teacherId = "";

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      String? token = await _storage.read(key: 'jwt_token');
      String? userInfoStr = await _storage.read(key: 'user_info');
      
      if (userInfoStr != null) {
        final userInfo = jsonDecode(userInfoStr);
        _teacherEmail = userInfo["email"] ?? "";
        _teacherId = userInfo["id"]?.toString() ?? userInfo["_id"]?.toString() ?? "";
      }

      // 1. Tải danh sách Lớp học (TV1) để đổ vào Form Giao bài
      final classRes = await http.get(Uri.parse('${AppConfig.apiTv1}/classes'), headers: {"Authorization": "Bearer $token"});
      if (classRes.statusCode == 200) {
        List<dynamic> allClasses = jsonDecode(utf8.decode(classRes.bodyBytes));
        _myClasses = allClasses.where((c) => (c["teacher_id"] ?? "").toString() == _teacherId).toList();
      }

      // 2. Tải Kho Bài tập (TV2)
      final quizRes = await http.get(Uri.parse('${AppConfig.apiTv2}/quizzes'));
      if (quizRes.statusCode == 200) {
        List<dynamic> allQuizzes = jsonDecode(utf8.decode(quizRes.bodyBytes));
        _quizzes = allQuizzes.where((q) => q["author_email"] == _teacherEmail || q["author"] == _teacherEmail).toList();
      }

      // 3. Tải Kho Video (TV2)
      final vidRes = await http.get(Uri.parse('${AppConfig.apiTv2}/videos'));
      if (vidRes.statusCode == 200) {
        _videos = jsonDecode(utf8.decode(vidRes.bodyBytes));
      }

    } catch (e) {
      debugPrint("Lỗi tải kho học liệu: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // Bảng Modal Giao Bài Tập hiển thị trượt từ dưới lên
  void _showAssignModal(Map<String, dynamic> quiz) {
    List<String> selectedClasses = [];
    DateTime deadlineDate = DateTime.now().add(const Duration(days: 3));
    TimeOfDay deadlineTime = const TimeOfDay(hour: 23, minute: 59);
    final noteCtrl = TextEditingController();
    bool isSubmitting = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (BuildContext context, StateSetter setModalState) {
            return Padding(
              padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 20, right: 20, top: 20),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text("Giao bài: ${quiz['title']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.orange)),
                    const Divider(),
                    
                    // Chọn lớp học (Multi-select)
                    const Text("Chọn lớp nhận bài (*)", style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    _myClasses.isEmpty
                        ? const Text("Bạn chưa được phân công lớp nào.", style: TextStyle(color: Colors.red))
                        : Wrap(
                            spacing: 8,
                            children: _myClasses.map((c) {
                              String cName = c["class_name"] ?? "Lớp";
                              bool isSel = selectedClasses.contains(cName);
                              return FilterChip(
                                label: Text(cName),
                                selected: isSel,
                                selectedColor: Colors.orange.shade200,
                                onSelected: (val) {
                                  setModalState(() {
                                    if (val) selectedClasses.add(cName);
                                    else selectedClasses.remove(cName);
                                  });
                                },
                              );
                            }).toList(),
                          ),
                    const SizedBox(height: 15),

                    // Chọn Hạn chót
                    const Text("Hạn chót nộp bài (*)", style: TextStyle(fontWeight: FontWeight.bold)),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.calendar_month, size: 18),
                            label: Text(DateFormat('dd/MM/yyyy').format(deadlineDate)),
                            onPressed: () async {
                              DateTime? pickedDate = await showDatePicker(
                                context: context, initialDate: deadlineDate, firstDate: DateTime.now(), lastDate: DateTime(2030)
                              );
                              if (pickedDate != null) setModalState(() => deadlineDate = pickedDate);
                            },
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.access_time, size: 18),
                            label: Text(deadlineTime.format(context)),
                            onPressed: () async {
                              TimeOfDay? pickedTime = await showTimePicker(context: context, initialTime: deadlineTime);
                              if (pickedTime != null) setModalState(() => deadlineTime = pickedTime);
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 15),

                    // Lời nhắn
                    TextField(
                      controller: noteCtrl,
                      maxLines: 2,
                      decoration: const InputDecoration(labelText: "Lời nhắn cho học sinh", border: OutlineInputBorder(), hintText: "Ví dụ: Các con nhớ xem bài kỹ nhé!"),
                    ),
                    const SizedBox(height: 20),

                    // Nút xác nhận
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                        onPressed: isSubmitting
                            ? null
                            : () async {
                                if (selectedClasses.isEmpty) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vui lòng chọn ít nhất 1 lớp!"), backgroundColor: Colors.red));
                                  return;
                                }

                                setModalState(() => isSubmitting = true);
                                
                                // Format deadline chuẩn cho Backend: YYYY-MM-DD HH:mm
                                String formattedDate = DateFormat('yyyy-MM-dd').format(deadlineDate);
                                String formattedTime = "${deadlineTime.hour.toString().padLeft(2, '0')}:${deadlineTime.minute.toString().padLeft(2, '0')}";
                                
                                Map<String, dynamic> payload = {
                                  "quiz_id": quiz["id"].toString(),
                                  "quiz_title": quiz["title"],
                                  "teacher_id": _teacherEmail,
                                  "class_id": selectedClasses.join(", "),
                                  "deadline": "$formattedDate $formattedTime",
                                  "note": noteCtrl.text.trim()
                                };

                                try {
                                  final res = await NetworkHelper.safeRequest(
                                    http.post(
                                      Uri.parse('${AppConfig.apiTv2}/assign-quiz'),
                                      headers: {"Content-Type": "application/json"},
                                      body: jsonEncode(payload),
                                    )
                                  );

                                  if (res.statusCode == 200 || res.statusCode == 201) {
                                    Navigator.pop(context); // Đóng Modal
                                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đã giao bài tập thành công!"), backgroundColor: Colors.green));
                                  } else {
                                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi hệ thống: ${res.body}"), backgroundColor: Colors.red));
                                  }
                                } catch (e) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi kết nối mạng."), backgroundColor: Colors.red));
                                } finally {
                                  setModalState(() => isSubmitting = false);
                                }
                              },
                        child: isSubmitting ? const CircularProgressIndicator(color: Colors.white) : const Text("XÁC NHẬN GIAO BÀI", style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.grey.shade100,
        appBar: AppBar(
          title: const Text("Kho Học Liệu & Giao Bài", style: TextStyle(fontWeight: FontWeight.bold)),
          backgroundColor: Colors.orange,
          foregroundColor: Colors.white,
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: [
              Tab(icon: Icon(Icons.quiz), text: "Bộ Đề (Quiz)"),
              Tab(icon: Icon(Icons.video_library), text: "Video Học Tập"),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Colors.orange))
            : TabBarView(
                children: [
                  _buildQuizTab(),
                  _buildVideoTab(),
                ],
              ),
      ),
    );
  }

  Widget _buildQuizTab() {
    if (_quizzes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 60, color: Colors.grey.shade400),
            const SizedBox(height: 10),
            const Text("Kho bài tập trống.\nHãy dùng trang Web để AI sinh bộ đề!", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _quizzes.length,
      itemBuilder: (context, index) {
        final item = _quizzes[index];
        return Card(
          elevation: 2,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(color: Colors.orange.shade50, borderRadius: BorderRadius.circular(10)),
                      child: const Icon(Icons.quiz, color: Colors.orange, size: 30),
                    ),
                    const SizedBox(width: 15),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item['title'] ?? 'Bài tập', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          const SizedBox(height: 4),
                          Text("Số câu hỏi: ${item['questions']?.length ?? 0}", style: TextStyle(color: Colors.grey.shade600)),
                          Text("Ngày tạo: ${(item['created_at'] ?? '').toString().split('T')[0]}", style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
                        ],
                      ),
                    ),
                  ],
                ),
                const Divider(),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.orange), foregroundColor: Colors.orange),
                    icon: const Icon(Icons.send),
                    label: const Text("Giao Bài Cho Lớp", style: TextStyle(fontWeight: FontWeight.bold)),
                    onPressed: () => _showAssignModal(item),
                  ),
                )
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildVideoTab() {
    if (_videos.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.video_file, size: 60, color: Colors.grey.shade400),
            const SizedBox(height: 10),
            const Text("Chưa có video nào trong hệ thống.", style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _videos.length,
      itemBuilder: (context, index) {
        final v = _videos[index];
        return Card(
          elevation: 2,
          margin: const EdgeInsets.only(bottom: 15),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            contentPadding: const EdgeInsets.all(12),
            leading: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.network(
                "https://img.youtube.com/vi/${_extractYoutubeId(v['url'] ?? '')}/0.jpg",
                width: 80, height: 60, fit: BoxFit.cover,
                errorBuilder: (c, e, s) => Container(width: 80, height: 60, color: Colors.grey.shade300, child: const Icon(Icons.video_library)),
              ),
            ),
            title: Text(v['title'] ?? 'Video bài giảng', style: const TextStyle(fontWeight: FontWeight.bold), maxLines: 2, overflow: TextOverflow.ellipsis),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text("Chủ đề: ${v['topic'] ?? 'Khác'} | Lớp: ${v['level'] ?? 'Chung'}", style: const TextStyle(fontSize: 12)),
              ],
            ),
            trailing: const Icon(Icons.play_circle_fill, color: Colors.red, size: 35),
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Link Video: ${v['url']}")));
            },
          ),
        );
      },
    );
  }

  String _extractYoutubeId(String url) {
    try {
      if (url.contains("v=")) return url.split("v=")[1].substring(0, 11);
      if (url.contains("youtu.be/")) return url.split("youtu.be/")[1].substring(0, 11);
    } catch (e) {
      return "";
    }
    return "";
  }
}