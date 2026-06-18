import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/config.dart';

class TeacherCreateQuizScreen extends StatefulWidget {
  const TeacherCreateQuizScreen({super.key});

  @override
  State<TeacherCreateQuizScreen> createState() => _TeacherCreateQuizScreenState();
}

class _TeacherCreateQuizScreenState extends State<TeacherCreateQuizScreen> {
  final _storage = const FlutterSecureStorage();
  
  List<Map<String, dynamic>> _questionsList = [];
  final _quizTitleController = TextEditingController();
  
  // AI Form Controls
  final _aiTopicController = TextEditingController();
  double _aiQuestionCount = 5;

  // Manual Form Controls
  final _manualQController = TextEditingController();
  final _optAController = TextEditingController();
  final _optBController = TextEditingController();
  final _optCController = TextEditingController();
  final _optDController = TextEditingController();
  String _correctManualOpt = "A";

  bool _isProcessing = false;
  String _teacherEmail = "";
  String _teacherName = "";

  @override
  void initState() {
    super.initState();
    _loadTeacherMetaData();
  }

  Future<void> _loadTeacherMetaData() async {
    String? userInfoStr = await _storage.read(key: 'user_info');
    if (userInfoStr != null) {
      final decoded = jsonDecode(userInfoStr);
      _teacherEmail = decoded["email"] ?? "";
      _teacherName = decoded["full_name"] ?? decoded["name"] ?? "Teacher";
    }
  }

  Future<void> _generateAiQuiz() async {
    if (_aiTopicController.text.trim().isEmpty) return;
    setState(() => _isProcessing = true);
    
    try {
      final res = await http.post(
        Uri.parse('${AppConfig.apiTv2}/generate-quiz'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"topic": _aiTopicController.text.trim(), "num_questions": _aiQuestionCount.toInt()}),
      );

      if (res.statusCode == 200) {
        List<dynamic> rawQs = jsonDecode(utf8.decode(res.bodyBytes))["questions"] ?? [];
        setState(() {
          for (var q in rawQs) {
            _questionsList.add({
              "question": q["question"],
              "options": List<String>.from(q["options"]),
              "correct_answer": q["correct_answer"]
            });
          }
        });
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("AI đã soạn xong bộ đề! Hãy sang tab xem trước."), backgroundColor: Colors.green));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi sinh đề AI."), backgroundColor: Colors.red));
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  void _addManualQuestion() {
    if (_manualQController.text.trim().isEmpty) return;
    List<String> opts = [
      "A. ${_optAController.text.trim()}",
      "B. ${_optBController.text.trim()}",
      "C. ${_optCController.text.trim()}",
      "D. ${_optDController.text.trim()}"
    ];
    String correctAns = opts[["A", "B", "C", "D"].indexOf(_correctManualOpt)];

    setState(() {
      _questionsList.add({
        "question": _manualQController.text.trim(),
        "options": opts,
        "correct_answer": correctAns
      });
      _manualQController.clear();
      _optAController.clear(); _optBController.clear();
      _optCController.clear(); _optDController.clear();
    });
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đã thêm 1 câu hỏi thủ công!"), backgroundColor: Colors.green));
  }

  Future<void> _saveQuizToLibrary() async {
    if (_quizTitleController.text.trim().isEmpty || _questionsList.isEmpty) return;
    setState(() => _isProcessing = true);

    Map<String, dynamic> payload = {
      "title": _quizTitleController.text.trim(),
      "questions": _questionsList,
      "author_email": _teacherEmail,
      "author": _teacherName
    };

    try {
      final res = await http.post(
        Uri.parse('${AppConfig.apiTv2}/quizzes'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload),
      );
      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lưu bộ đề vào kho bài tập thành công!"), backgroundColor: Colors.green));
        Navigator.pop(context);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi lưu trữ kho học liệu."), backgroundColor: Colors.red));
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text("Tạo Bài Tập AI"),
          backgroundColor: Colors.orange,
          foregroundColor: Colors.white,
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: [Tab(icon: Icon(Icons.psychology), text: "Soạn Đề"), Tab(icon: Icon(Icons.preview), text: "Xem Trước")],
          ),
        ),
        body: _isProcessing
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _buildCreateTab(),
                  _buildPreviewTab(),
                ],
              ),
      ),
    );
  }

  Widget _buildCreateTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("Soạn đề thông minh bằng AI", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange)),
          const SizedBox(height: 10),
          TextFormField(
            controller: _aiTopicController,
            decoration: const InputDecoration(labelText: "Nhập chủ đề cần sinh bài tập", border: OutlineInputBorder(), hintText: "Ví dụ: Các loại quả bằng tiếng Anh"),
          ),
          Row(
            children: [
              const Text("Số câu:"),
              Expanded(
                child: Slider(
                  value: _aiQuestionCount,
                  min: 1, max: 20, divisions: 19,
                  label: _aiQuestionCount.toInt().toString(),
                  onChanged: (val) => setState(() => _aiQuestionCount = val),
                ),
              ),
              Text("${_aiQuestionCount.toInt()} câu")
            ],
          ),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white, minimumSize: const Size(double.infinity, 45)),
            onPressed: _generateAiQuiz,
            icon: const Icon(Icons.bolt),
            label: const Text("Xác nhận sinh đề bằng AI"),
          ),
          const Padding(padding: EdgeInsets.symmetric(vertical: 15), child: Divider()),
          const Text("Nhập câu hỏi thủ công", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange)),
          const SizedBox(height: 10),
          TextFormField(controller: _manualQController, decoration: const InputDecoration(labelText: "Nội dung câu hỏi", border: OutlineInputBorder())),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: TextFormField(controller: _optAController, decoration: const InputDecoration(labelText: "Đáp án A"))),
              const SizedBox(width: 8),
              Expanded(child: TextFormField(controller: _optBController, decoration: const InputDecoration(labelText: "Đáp án B"))),
            ],
          ),
          Row(
            children: [
              Expanded(child: TextFormField(controller: _optCController, decoration: const InputDecoration(labelText: "Đáp án C"))),
              const SizedBox(width: 8),
              Expanded(child: TextFormField(controller: _optDController, decoration: const InputDecoration(labelText: "Đáp án D"))),
            ],
          ),
          DropdownButtonFormField<String>(
            value: _correctManualOpt,
            decoration: const InputDecoration(labelText: "Đáp án chính xác"),
            items: ["A", "B", "C", "D"].map((o) => DropdownMenuItem(value: o, child: Text("Đáp án $o"))).toList(),
            onChanged: (val) => setState(() => _correctManualOpt = val!),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.orange), minimumSize: const Size(double.infinity, 45)),
            onPressed: _addManualQuestion,
            icon: const Icon(Icons.add, color: Colors.orange),
            label: const Text("Thêm vào danh sách câu hỏi", style: TextStyle(color: Colors.orange)),
          ),
        ],
      ),
    );
  }

  Widget _buildPreviewTab() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16.0),
          key: const ValueKey("HeaderPreview"),
          child: TextFormField(
            controller: _quizTitleController,
            decoration: const InputDecoration(labelText: "Đặt tên cho bộ bài tập này (*)", border: OutlineInputBorder()),
          ),
        ),
        Expanded(
          child: _questionsList.isEmpty
              ? const Center(child: Text("Danh sách câu hỏi đang trống. Hãy thiết kế bài tập ở Tab soạn đề."))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _questionsList.length,
                  itemBuilder: (context, index) {
                    final q = _questionsList[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(child: Text("Câu ${index + 1}: ${q['question']}", style: const TextStyle(fontWeight: FontWeight.bold))),
                                IconButton(icon: const Icon(Icons.delete, color: Colors.red), onPressed: () => setState(() => _questionsList.removeAt(index)))
                              ],
                            ),
                            ...(q['options'] as List<String>).map((opt) {
                              bool isCorrect = opt == q['correct_answer'];
                              return Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(6),
                                margin: const EdgeInsets.only(top: 4),
                                color: isCorrect ? Colors.green.withOpacity(0.1) : Colors.transparent,
                                child: Text(opt, style: TextStyle(color: isCorrect ? Colors.green.shade800 : Colors.black87, fontWeight: isCorrect ? FontWeight.bold : FontWeight.normal)),
                              );
                            }),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
        if (_questionsList.isNotEmpty)
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white, minimumSize: const Size(double.infinity, 50)),
              onPressed: _saveQuizToLibrary,
              child: const Text("XÁC NHẬN LƯU VÀO KHO HỌC LIỆU", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          )
      ],
    );
  }
}