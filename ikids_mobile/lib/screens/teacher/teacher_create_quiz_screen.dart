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
  String _lang = "vi";

  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Tạo Bài Tập AI",
      "tab_create": "Soạn Đề",
      "tab_preview": "Xem Trước",
      "sub_ai": "Soạn đề thông minh bằng AI",
      "hint_topic": "Nhập chủ đề cần sinh bài tập",
      "lbl_topic_ex": "Ví dụ: Các loại quả bằng tiếng Anh",
      "lbl_count": "Số câu:",
      "btn_ai": "Xác nhận sinh đề bằng AI",
      "sub_manual": "Nhập câu hỏi thủ công",
      "hint_q": "Nội dung câu hỏi",
      "hint_opt": "Đáp án",
      "hint_correct": "Đáp án chính xác",
      "btn_add": "Thêm vào danh sách câu hỏi",
      "lbl_title": "Đặt tên cho bộ bài tập này (*)",
      "msg_empty": "Danh sách câu hỏi đang trống. Hãy thiết kế bài tập ở Tab soạn đề.",
      "btn_save": "XÁC NHẬN LƯU VÀO KHO HỌC LIỆU",
      "msg_ai_success": "AI đã soạn xong bộ đề! Hãy sang tab xem trước.",
      "msg_manual_success": "Đã thêm 1 câu hỏi thủ công!",
      "msg_save_success": "Lưu bộ đề vào kho bài tập thành công!",
      "msg_err": "Lỗi xử lý.",
    },
    "en": {
      "title": "AI Quiz Maker",
      "tab_create": "Compose",
      "tab_preview": "Preview",
      "sub_ai": "Smart AI Quiz Generation",
      "hint_topic": "Enter the topic for the quiz",
      "lbl_topic_ex": "Example: Fruits in English",
      "lbl_count": "Questions:",
      "btn_ai": "Generate Quiz with AI",
      "sub_manual": "Add Question Manually",
      "hint_q": "Question Content",
      "hint_opt": "Option",
      "hint_correct": "Correct Answer",
      "btn_add": "Add to question list",
      "lbl_title": "Enter a title for this quiz (*)",
      "msg_empty": "Question list is empty. Design your quiz in the Compose tab.",
      "btn_save": "SAVE TO LEARNING LIBRARY",
      "msg_ai_success": "AI has generated the quiz! Go to Preview tab.",
      "msg_manual_success": "Manual question added!",
      "msg_save_success": "Quiz saved to library successfully!",
      "msg_err": "Processing error.",
    }
  };

  @override
  void initState() {
    super.initState();
    _loadTeacherMetaData();
  }

  Future<void> _loadTeacherMetaData() async {
    String? savedLang = await _storage.read(key: 'app_lang');
    if (savedLang != null) setState(() => _lang = savedLang);

    String? userInfoStr = await _storage.read(key: 'user_info');
    if (userInfoStr != null) {
      final decoded = jsonDecode(userInfoStr);
      _teacherEmail = decoded["email"] ?? "";
      _teacherName = decoded["full_name"] ?? decoded["name"] ?? "Teacher";
    }
  }

  Future<void> _generateAiQuiz() async {
    final labels = _locales[_lang]!;
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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_ai_success"]!), backgroundColor: Colors.green));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_err"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  void _addManualQuestion() {
    final labels = _locales[_lang]!;
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
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_manual_success"]!), backgroundColor: Colors.green));
  }

  Future<void> _saveQuizToLibrary() async {
    final labels = _locales[_lang]!;
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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_save_success"]!), backgroundColor: Colors.green));
        Navigator.pop(context);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_err"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(labels["title"]!),
          backgroundColor: Colors.orange,
          foregroundColor: Colors.white,
          bottom: TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: [Tab(icon: const Icon(Icons.psychology), text: labels["tab_create"]), Tab(icon: const Icon(Icons.preview), text: labels["tab_preview"])],
          ),
        ),
        body: _isProcessing
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _buildCreateTab(labels),
                  _buildPreviewTab(labels),
                ],
              ),
      ),
    );
  }

  Widget _buildCreateTab(Map<String, String> labels) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(labels["sub_ai"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange)),
          const SizedBox(height: 10),
          TextFormField(
            controller: _aiTopicController,
            decoration: InputDecoration(labelText: labels["hint_topic"], border: const OutlineInputBorder(), hintText: labels["lbl_topic_ex"]),
          ),
          Row(
            children: [
              Text(labels["lbl_count"]!),
              Expanded(
                child: Slider(
                  value: _aiQuestionCount,
                  min: 1, max: 20, divisions: 19,
                  label: _aiQuestionCount.toInt().toString(),
                  onChanged: (val) => setState(() => _aiQuestionCount = val),
                ),
              ),
              Text("${_aiQuestionCount.toInt()}")
            ],
          ),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white, minimumSize: const Size(double.infinity, 45)),
            onPressed: _generateAiQuiz,
            icon: const Icon(Icons.bolt),
            label: Text(labels["btn_ai"]!),
          ),
          const Padding(padding: EdgeInsets.symmetric(vertical: 15), child: Divider()),
          Text(labels["sub_manual"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange)),
          const SizedBox(height: 10),
          TextFormField(controller: _manualQController, decoration: InputDecoration(labelText: labels["hint_q"], border: const OutlineInputBorder())),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: TextFormField(controller: _optAController, decoration: InputDecoration(labelText: "${labels['hint_opt']} A"))),
              const SizedBox(width: 8),
              Expanded(child: TextFormField(controller: _optBController, decoration: InputDecoration(labelText: "${labels['hint_opt']} B"))),
            ],
          ),
          Row(
            children: [
              Expanded(child: TextFormField(controller: _optCController, decoration: InputDecoration(labelText: "${labels['hint_opt']} C"))),
              const SizedBox(width: 8),
              Expanded(child: TextFormField(controller: _optDController, decoration: InputDecoration(labelText: "${labels['hint_opt']} D"))),
            ],
          ),
          DropdownButtonFormField<String>(
            value: _correctManualOpt,
            decoration: InputDecoration(labelText: labels["hint_correct"]),
            items: ["A", "B", "C", "D"].map((o) => DropdownMenuItem(value: o, child: Text("${labels['hint_opt']} $o"))).toList(),
            onChanged: (val) => setState(() => _correctManualOpt = val!),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.orange), minimumSize: const Size(double.infinity, 45)),
            onPressed: _addManualQuestion,
            icon: const Icon(Icons.add, color: Colors.orange),
            label: Text(labels["btn_add"]!, style: const TextStyle(color: Colors.orange)),
          ),
        ],
      ),
    );
  }

  Widget _buildPreviewTab(Map<String, String> labels) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16.0),
          key: const ValueKey("HeaderPreview"),
          child: TextFormField(
            controller: _quizTitleController,
            decoration: InputDecoration(labelText: labels["lbl_title"], border: const OutlineInputBorder()),
          ),
        ),
        Expanded(
          child: _questionsList.isEmpty
              ? Center(child: Text(labels["msg_empty"]!, textAlign: TextAlign.center))
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
                                Expanded(child: Text("${_lang == 'vi' ? 'Câu' : 'Q'} ${index + 1}: ${q['question']}", style: const TextStyle(fontWeight: FontWeight.bold))),
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
              child: Text(labels["btn_save"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
          )
      ],
    );
  }
}