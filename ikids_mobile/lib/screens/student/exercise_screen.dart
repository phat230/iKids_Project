import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class ExerciseScreen extends StatefulWidget {
  const ExerciseScreen({super.key});

  @override
  State<ExerciseScreen> createState() => _ExerciseScreenState();
}

class _ExerciseScreenState extends State<ExerciseScreen> {
  final _storage = const FlutterSecureStorage();
  final String _apiPrefix = '/api/tv2'; 

  bool _isLoading = true;
  String _lang = "vi"; 

  List<dynamic> _allQuizzes = [];
  Map<String, dynamic>? _selectedQuiz;
  Map<int, String> _userAnswers = {};

  // Profile này sẽ được Server cập nhật
  Map<String, dynamic> _studentProfile = {
    "name": "Học sinh",
    "email_key": "", 
    "exp": 0,
    "completed_tasks": []
  };

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "📝 Trạm Quiz AI",
      "subtitle": "Hoàn thành các bài tập dưới đây để tích lũy EXP thăng hạng nhé!",
      "lbl_total_exp": "Tổng EXP của bạn:",
      "info_empty_quizzes": "✨ Hiện tại giáo viên chưa có bài tập nào.",
      "lbl_questions_count": "Số câu:",
      "lbl_reward": "Phần thưởng:",
      "btn_completed": "✅ Đã hoàn thành",
      "btn_start": "▶ Bắt đầu làm",
      "lbl_quiz_title": "Đề Bài:",
      "info_quiz_hint": "💡 Hãy đọc kỹ câu hỏi và chọn đáp án chính xác nhất.",
      "lbl_question_prefix": "Câu",
      "btn_submit_quiz": "🏆 Nộp Bài & Nhận Thưởng",
      "err_unanswered": "⚠️ Bạn chưa chọn đáp án cho tất cả các câu!",
    },
    "en": {
      "title": "📝 AI Quiz Station",
      "subtitle": "Complete quizzes to earn EXP!",
      "lbl_total_exp": "Total EXP:",
      "info_empty_quizzes": "✨ No active quizzes.",
      "lbl_questions_count": "Questions:",
      "lbl_reward": "Reward:",
      "btn_completed": "✅ Completed",
      "btn_start": "▶ Start Quiz",
      "lbl_quiz_title": "Quiz Title:",
      "info_quiz_hint": "💡 Read carefully and select the best answer.",
      "lbl_question_prefix": "Question",
      "btn_submit_quiz": "🏆 Submit",
      "err_unanswered": "⚠️ Please answer all questions!",
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchQuizData();
  }

  Future<void> _fetchQuizData() async {
    setState(() => _isLoading = true);
    try {
      // 1. Lấy thông tin user từ storage
      String? userInfo = await _storage.read(key: 'user_info'); 
      if (userInfo == null) return;
      
      final Map<String, dynamic> decodedUser = jsonDecode(userInfo);
      
      // ĐỒNG BỘ: Sử dụng Email làm khóa định danh (Giống hệt logic của Web)
      String anchorKey = decodedUser["email"] ?? decodedUser["username"] ?? decodedUser["name"] ?? "Student";
      String displayName = decodedUser["full_name"] ?? decodedUser["name"] ?? "Học sinh";
      
      String encodedKey = Uri.encodeComponent(anchorKey);

      // 2. Gọi API Profile
      final profRes = await http.get(Uri.parse('${AppConfig.apiUrl}$_apiPrefix/student/$encodedKey/profile')).timeout(const Duration(seconds: 5));
      
      // 3. Gọi API Quiz
      final quizRes = await http.get(Uri.parse('${AppConfig.apiUrl}$_apiPrefix/quizzes')).timeout(const Duration(seconds: 5));

      if (profRes.statusCode == 200 && quizRes.statusCode == 200) {
        var profileData = jsonDecode(utf8.decode(profRes.bodyBytes));
        profileData["email_key"] = anchorKey; // Lưu khóa đồng bộ
        profileData["name"] = displayName;
        
        List<dynamic> parsedQuizzes = jsonDecode(utf8.decode(quizRes.bodyBytes));
        for (int i = 0; i < parsedQuizzes.length; i++) {
          parsedQuizzes[i]['id'] ??= "quiz_backup_id_$i";
        }

        setState(() {
          _studentProfile = profileData;
          _allQuizzes = parsedQuizzes;
          _isLoading = false;
        });
      }
    } catch (e) {
      if(mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _submitQuiz(List<dynamic> questions, String quizId) async {
    // ... (Giữ nguyên logic nộp bài như trước)
    // Sau khi nộp thành công, gọi await _fetchQuizData(); để làm mới màn hình ngay
    await _fetchQuizData();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_labels[_lang]!["title"]!),
        actions: [
          IconButton(icon: const Icon(Icons.sync), onPressed: _fetchQuizData),
        ],
      ),
      body: _isLoading ? const Center(child: CircularProgressIndicator()) 
            : (_selectedQuiz == null ? _buildQuizList() : _buildDoingQuizRoom()),
    );
  }

  Widget _buildQuizList() {
    return RefreshIndicator(
      onRefresh: _fetchQuizData, // Kéo xuống để reload đồng bộ
      child: ListView.builder(
        itemCount: _allQuizzes.length,
        itemBuilder: (context, i) {
          final q = _allQuizzes[i];
          // Kiểm tra bài đã làm trong completed_tasks (Đã đồng bộ)
          bool isCompleted = (_studentProfile['completed_tasks'] as List? ?? []).contains(q['id']);
          return Card(
            child: ListTile(
              title: Text(q['title'] ?? "Quiz"),
              trailing: ElevatedButton(
                onPressed: isCompleted ? null : () => setState(() => _selectedQuiz = q),
                child: Text(isCompleted ? "✅" : "▶"),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildDoingQuizRoom() { /* (Giữ nguyên) */ return Container(); }
}