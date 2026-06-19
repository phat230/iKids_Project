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
  String _lang = "vi";

  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Kho Học Liệu & Giao Bài",
      "tab_quiz": "Bộ Đề (Quiz)",
      "tab_video": "Video Học Tập",
      "empty_quiz": "Kho bài tập trống.\nHãy dùng trang Web hoặc Soạn Đề AI để sinh bộ đề!",
      "empty_video": "Chưa có video nào trong hệ thống.",
      "lbl_questions": "Số câu hỏi:",
      "lbl_date": "Ngày tạo:",
      "btn_assign": "Giao Bài Cho Lớp",
      "lbl_topic": "Chủ đề:",
      "lbl_level": "Lớp:",
      "assign_title": "Giao bài:",
      "assign_class": "Chọn lớp nhận bài (*)",
      "assign_no_class": "Bạn chưa được phân công lớp nào.",
      "assign_deadline": "Hạn chót nộp bài (*)",
      "assign_note": "Lời nhắn cho học sinh",
      "assign_note_hint": "Ví dụ: Các con nhớ xem bài kỹ nhé!",
      "btn_confirm": "XÁC NHẬN GIAO BÀI",
      "msg_select_class": "Vui lòng chọn ít nhất 1 lớp!",
      "msg_success": "Đã giao bài tập thành công!",
      "msg_fail": "Lỗi hệ thống",
    },
    "en": {
      "title": "Learning Resources & Assignments",
      "tab_quiz": "Quizzes",
      "tab_video": "Learning Videos",
      "empty_quiz": "No quizzes available.\nUse the AI Quiz Maker to generate some!",
      "empty_video": "No learning videos in the system.",
      "lbl_questions": "Questions:",
      "lbl_date": "Created Date:",
      "btn_assign": "Assign to Class",
      "lbl_topic": "Topic:",
      "lbl_level": "Grade:",
      "assign_title": "Assigning:",
      "assign_class": "Select target class (*)",
      "assign_no_class": "You are not assigned to any classes yet.",
      "assign_deadline": "Submission Deadline (*)",
      "assign_note": "Message for students",
      "assign_note_hint": "Example: Please review the materials carefully!",
      "btn_confirm": "CONFIRM ASSIGNMENT",
      "msg_select_class": "Please select at least 1 class!",
      "msg_success": "Assignment sent successfully!",
      "msg_fail": "System error",
    }
  };

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      String? token = await _storage.read(key: 'jwt_token');
      String? userInfoStr = await _storage.read(key: 'user_info');
      
      if (userInfoStr != null) {
        final userInfo = jsonDecode(userInfoStr);
        _teacherEmail = userInfo["email"] ?? "";
        _teacherId = userInfo["id"]?.toString() ?? userInfo["_id"]?.toString() ?? "";
      }

      final classRes = await http.get(Uri.parse('${AppConfig.apiTv1}/classes'), headers: {"Authorization": "Bearer $token"});
      if (classRes.statusCode == 200) {
        List<dynamic> allClasses = jsonDecode(utf8.decode(classRes.bodyBytes));
        _myClasses = allClasses.where((c) => (c["teacher_id"] ?? "").toString() == _teacherId).toList();
      }

      final quizRes = await http.get(Uri.parse('${AppConfig.apiTv2}/quizzes'));
      if (quizRes.statusCode == 200) {
        List<dynamic> allQuizzes = jsonDecode(utf8.decode(quizRes.bodyBytes));
        _quizzes = allQuizzes.where((q) => q["author_email"] == _teacherEmail || q["author"] == _teacherEmail).toList();
      }

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

  void _showAssignModal(Map<String, dynamic> quiz) {
    final labels = _locales[_lang]!;
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
                    Text("${labels['assign_title']} ${quiz['title']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.orange)),
                    const Divider(),
                    
                    Text(labels["assign_class"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    _myClasses.isEmpty
                        ? Text(labels["assign_no_class"]!, style: const TextStyle(color: Colors.red))
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

                    Text(labels["assign_deadline"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
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

                    TextField(
                      controller: noteCtrl,
                      maxLines: 2,
                      decoration: InputDecoration(labelText: labels["assign_note"], border: const OutlineInputBorder(), hintText: labels["assign_note_hint"]),
                    ),
                    const SizedBox(height: 20),

                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                        onPressed: isSubmitting
                            ? null
                            : () async {
                                if (selectedClasses.isEmpty) {
                                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_select_class"]!), backgroundColor: Colors.red));
                                  return;
                                }

                                setModalState(() => isSubmitting = true);
                                
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
                                    Navigator.pop(context);
                                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_success"]!), backgroundColor: Colors.green));
                                  } else {
                                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("${labels["msg_fail"]!}: ${res.body}"), backgroundColor: Colors.red));
                                  }
                                } catch (e) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Error."), backgroundColor: Colors.red));
                                } finally {
                                  setModalState(() => isSubmitting = false);
                                }
                              },
                        child: isSubmitting ? const CircularProgressIndicator(color: Colors.white) : Text(labels["btn_confirm"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
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
    final labels = _locales[_lang]!;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.grey.shade100,
        appBar: AppBar(
          title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
          backgroundColor: Colors.orange,
          foregroundColor: Colors.white,
          bottom: TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: [
              Tab(icon: const Icon(Icons.quiz), text: labels["tab_quiz"]),
              Tab(icon: const Icon(Icons.video_library), text: labels["tab_video"]),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Colors.orange))
            : TabBarView(
                children: [
                  _buildQuizTab(labels),
                  _buildVideoTab(labels),
                ],
              ),
      ),
    );
  }

  Widget _buildQuizTab(Map<String, String> labels) {
    if (_quizzes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 60, color: Colors.grey.shade400),
            const SizedBox(height: 10),
            Text(labels["empty_quiz"]!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
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
                          Text(item['title'] ?? 'Quiz', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          const SizedBox(height: 4),
                          Text("${labels['lbl_questions']} ${item['questions']?.length ?? 0}", style: TextStyle(color: Colors.grey.shade600)),
                          Text("${labels['lbl_date']} ${(item['created_at'] ?? '').toString().split('T')[0]}", style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
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
                    label: Text(labels["btn_assign"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
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

  Widget _buildVideoTab(Map<String, String> labels) {
    if (_videos.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.video_file, size: 60, color: Colors.grey.shade400),
            const SizedBox(height: 10),
            Text(labels["empty_video"]!, style: const TextStyle(color: Colors.grey)),
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
            title: Text(v['title'] ?? 'Video', style: const TextStyle(fontWeight: FontWeight.bold), maxLines: 2, overflow: TextOverflow.ellipsis),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text("${labels['lbl_topic']} ${v['topic'] ?? 'N/A'} | ${labels['lbl_level']} ${v['level'] ?? 'N/A'}", style: const TextStyle(fontSize: 12)),
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