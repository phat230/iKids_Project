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

  Map<String, dynamic> _studentProfile = {
    "name": "Đang tải...",
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
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _allQuizzes = [];
      _selectedQuiz = null;
      _userAnswers.clear();
    });

try {
      String? userInfo = await _storage.read(key: 'user_info'); 
      if (userInfo == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text("Lỗi: Không tìm thấy thông tin tài khoản! Vui lòng đăng nhập lại.", style: TextStyle(color: Colors.white)),
            backgroundColor: Colors.red,
          ));
          setState(() => _isLoading = false);
        }
        return; 
      }
      final Map<String, dynamic> decodedUser = jsonDecode(userInfo);
      
      // ================= ĐÃ SỬA CHỖ NÀY =================
      // Ép Mobile ưu tiên dùng ID hệ thống, ngăn chặn 100% việc trùng lặp dữ liệu do trùng tên/trống email
      String anchorKey = decodedUser["id"]?.toString() ?? decodedUser["_id"]?.toString() ?? decodedUser["email"]?.toString() ?? decodedUser["username"]?.toString() ?? decodedUser["name"]?.toString() ?? "Student";
      String displayName = decodedUser["full_name"]?.toString() ?? decodedUser["name"]?.toString() ?? "Học sinh";
      // ===================================================

      String encodedKey = Uri.encodeComponent(anchorKey);

      final profRes = await http.get(Uri.parse('${AppConfig.apiUrl}$_apiPrefix/student/$encodedKey/profile')).timeout(const Duration(seconds: 15));
      
      Map<String, dynamic> profileData = {
        "name": displayName,
        "email_key": anchorKey, 
        "exp": 0,
        "completed_tasks": []
      };

      if (profRes.statusCode == 200) {
        profileData = jsonDecode(utf8.decode(profRes.bodyBytes));
        profileData["email_key"] = anchorKey; 
        profileData["name"] = displayName;
      }

      final quizRes = await http.get(Uri.parse('${AppConfig.apiUrl}$_apiPrefix/quizzes')).timeout(const Duration(seconds: 15));

      List<dynamic> parsedQuizzes = [];
      if (quizRes.statusCode == 200) {
        parsedQuizzes = jsonDecode(utf8.decode(quizRes.bodyBytes));
        for (int i = 0; i < parsedQuizzes.length; i++) {
          parsedQuizzes[i]['id'] ??= "quiz_backup_id_$i";
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi Server: Không tìm thấy bài tập (${quizRes.statusCode})")));
        }
      }

      if (mounted) {
        setState(() {
          _studentProfile = profileData;
          _allQuizzes = parsedQuizzes;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("Lỗi kết nối mạng: Vui lòng kiểm tra lại IP hoặc Backend", style: const TextStyle(color: Colors.white)),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 4),
        ));
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _submitQuiz(List<dynamic> questions, String quizId) async {
    if (_userAnswers.length < questions.length) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!["err_unanswered"]!), backgroundColor: Colors.red));
      return;
    }

    int correctCount = 0;
    for (int i = 0; i < questions.length; i++) {
      if (_userAnswers[i] == questions[i]['correct_answer']) correctCount++;
    }

    int totalQuestions = questions.length;
    double score = totalQuestions > 0 ? ((correctCount / totalQuestions) * 10).toDouble() : 0.0;
    int earnedExp = 50 + (correctCount * 10);

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator(color: Colors.orange)),
    );

    try {
      String anchorKey = _studentProfile["email_key"] ?? "Student";
      String encodedKey = Uri.encodeComponent(anchorKey);
      
      Map<String, dynamic> submitPayload = {
        "quiz_id": quizId,
        "exp_earned": earnedExp,
        "score": score 
      };

      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}$_apiPrefix/student/$encodedKey/submit-quiz'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(submitPayload),
      ).timeout(const Duration(seconds: 15));

      if (mounted) Navigator.pop(context);

      if (response.statusCode == 200 || response.statusCode == 201) {
        await _fetchQuizData(); 
        setState(() {
          _selectedQuiz = null; 
          _userAnswers.clear(); 
        });

        if (mounted) {
          showDialog(
            context: context,
            barrierDismissible: false,
            builder: (_) => AlertDialog(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              title: const Column(
                children: [
                  Icon(Icons.stars_rounded, color: Colors.orange, size: 50),
                  SizedBox(height: 10),
                  Text("Hoàn Thành Xuất Sắc!", textAlign: TextAlign.center),
                ],
              ),
              content: Text(
                "Bạn trả lời đúng $correctCount/$totalQuestions câu.\nĐiểm số: ${score.toStringAsFixed(1)}/10\n\nPhần thưởng: 🚀 +$earnedExp EXP!",
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16),
              ),
              actions: [
                Center(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                    onPressed: () => Navigator.pop(context), 
                    child: const Text("Đóng")
                  ),
                )
              ],
            )
          );
        }
      } else {
        if (mounted) {
          showDialog(
            context: context,
            builder: (_) => AlertDialog(
              title: const Text("⚠️ Không Thể Nhận Điểm"),
              content: const Text("Bạn đã hoàn thành bài tập này rồi! Dữ liệu sẽ được cập nhật lại ngay."), 
              actions: [
                TextButton(onPressed: () { 
                  Navigator.pop(context);
                  setState(() => _selectedQuiz = null);
                  _fetchQuizData(); 
                }, child: const Text("Tải lại danh sách"))
              ],
            )
          );
        }
      }
    } catch (e) {
      if (mounted) Navigator.pop(context); 
      if (mounted) {
         showDialog(
            context: context,
            builder: (_) => AlertDialog(
              title: const Text("⚠️ Lỗi Ứng Dụng/Mạng"),
              content: const Text("Mất kết nối tới hệ thống, vui lòng thử lại."), 
              actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text("Đóng"))],
            )
          );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(_labels[_lang]!["title"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.orange,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: "Làm mới dữ liệu",
            onPressed: () => _fetchQuizData(),
          ),
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : _selectedQuiz == null 
              ? _buildQuizList() 
              : _buildDoingQuizRoom(),
    );
  }

  Widget _buildQuizList() {
    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          color: Colors.orange[50],
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(_labels[_lang]!["subtitle"]!, style: TextStyle(color: Colors.orange[900], fontSize: 13)),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20), border: Border.all(color: Colors.orange)),
                child: Text(
                  "🏅 ${_labels[_lang]!['lbl_total_exp']} ${_studentProfile['exp'] ?? 0} EXP", 
                  style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.orange),
                ),
              )
            ],
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _fetchQuizData,
            color: Colors.orange,
            child: _allQuizzes.isEmpty
                ? ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      const SizedBox(height: 150),
                      Center(child: Text(_labels[_lang]!["info_empty_quizzes"]!)),
                    ],
                  )
                : ListView.builder(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(12),
                    itemCount: _allQuizzes.length,
                    itemBuilder: (context, index) {
                      final q = _allQuizzes[index];
                      String quizId = q['id']; 
                      
                      List<dynamic> completedTasks = _studentProfile['completed_tasks'] ?? [];
                      bool isCompleted = completedTasks.contains(quizId);
                      int qCount = (q['questions'] as List?)?.length ?? 0;

                      return Card(
                        elevation: 2,
                        margin: const EdgeInsets.only(bottom: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        child: Padding(
                          padding: const EdgeInsets.all(12.0),
                          child: Row(
                            children: [
                              Container(
                                width: 60, height: 60,
                                decoration: BoxDecoration(color: Colors.orange[100], borderRadius: BorderRadius.circular(10)),
                                child: const Icon(Icons.quiz_rounded, color: Colors.orange, size: 35),
                              ),
                              const SizedBox(width: 15),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(q['title'] ?? "Bài tập", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                    const SizedBox(height: 5),
                                    Text("${_labels[_lang]!['lbl_questions_count']} $qCount | ${_labels[_lang]!['lbl_reward']} +50 EXP", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                  ],
                                ),
                              ),
                              ElevatedButton(
                                onPressed: isCompleted ? null : () {
                                  setState(() {
                                    _selectedQuiz = q;
                                    _userAnswers.clear(); 
                                  });
                                },
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: isCompleted ? Colors.grey : Colors.orange,
                                  foregroundColor: Colors.white,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))
                                ),
                                child: Text(isCompleted ? _labels[_lang]!["btn_completed"]! : _labels[_lang]!["btn_start"]!, style: const TextStyle(fontSize: 12)),
                              )
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
        )
      ],
    );
  }

  Widget _buildDoingQuizRoom() {
    String quizId = _selectedQuiz!['id']; 
    List<dynamic> questions = _selectedQuiz!['questions'] ?? [];

    return Column(
      children: [
        Container(
          color: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 10),
          child: Row(
            children: [
              IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => setState(() => _selectedQuiz = null)),
              Expanded(
                child: Text("${_labels[_lang]!['lbl_quiz_title']} ${_selectedQuiz!['title']}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              )
            ],
          ),
        ),
        Container(
          width: double.infinity,
          color: Colors.blue[50],
          padding: const EdgeInsets.all(12),
          child: Text(_labels[_lang]!["info_quiz_hint"]!, style: TextStyle(color: Colors.blue[800], fontSize: 12, fontStyle: FontStyle.italic)),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(15),
            itemCount: questions.length,
            itemBuilder: (context, qIndex) {
              final questionItem = questions[qIndex];
              List<dynamic> options = questionItem['options'] ?? [];

              return Card(
                elevation: 1,
                margin: const EdgeInsets.only(bottom: 20),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                child: Padding(
                  padding: const EdgeInsets.all(15.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "${_labels[_lang]!['lbl_question_prefix']} ${qIndex + 1}: ${questionItem['question']}",
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                      ),
                      const SizedBox(height: 15),
                      ...options.map((opt) {
                        return RadioListTile<String>(
                          title: Text(opt.toString(), style: const TextStyle(fontSize: 14)),
                          value: opt.toString(),
                          groupValue: _userAnswers[qIndex],
                          activeColor: Colors.orange,
                          contentPadding: EdgeInsets.zero,
                          onChanged: (value) {
                            setState(() {
                              _userAnswers[qIndex] = value!;
                            });
                          },
                        );
                      }).toList(),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(15),
          decoration: const BoxDecoration(
            color: Colors.white,
            boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, -2))]
          ),
          child: ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 15),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))
            ),
            onPressed: () => _submitQuiz(questions, quizId),
            child: Text(_labels[_lang]!["btn_submit_quiz"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ),
        )
      ],
    );
  }
}