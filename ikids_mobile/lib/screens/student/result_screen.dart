import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  final _storage = const FlutterSecureStorage();
  String _lang = "vi";
  bool _isLoading = true;
  String _studentId = "";
  
  List<dynamic> _realGrades = [];

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "📊 Bảng Điểm Cá Nhân",
      "subtitle": "Theo dõi sự tiến bộ của bạn qua từng bài kiểm tra và các kỳ thi nhé!",
      "sub_ai": "🤖 Phân Tích Từ Hệ Thống AI",
      "no_grades": "Hiện tại bạn chưa có điểm tổng kết nào được ghi nhận. Hãy cố gắng học tập nhé!",
      "col_subject": "Môn học",
      "col_attend": "CC",
      "col_test": "Kiểm Tra",
      "col_midterm": "Giữa Kỳ",
      "col_final": "Cuối Kỳ",
      "col_total": "Tổng",
      "col_grade": "Đánh giá",
      "ai_excellent": "💡 AI Nhận xét: Xin chúc mừng, bạn đang học rất xuất sắc môn ",
      "ai_excellent_score": " với số điểm tổng kết là ",
      "ai_weak": "Tuy nhiên, môn ",
      "ai_weak_score": " của bạn đang cần chú ý hơn một chút. Hãy vào mục Bài Tập AI để ôn luyện thêm phần này nhé!",
    },
    "en": {
      "title": "📊 My Report Card",
      "subtitle": "Track your academic growth and exam grades throughout the semester!",
      "sub_ai": "🤖 AI Insights & Recommendations",
      "no_grades": "No grades have been recorded for you yet. Keep up the good work!",
      "col_subject": "Course",
      "col_attend": "Att",
      "col_test": "Test",
      "col_midterm": "Mid",
      "col_final": "Final",
      "col_total": "Total",
      "col_grade": "Eval",
      "ai_excellent": "💡 AI Feedback: Congratulations, you are performing excellently in ",
      "ai_excellent_score": " with a final grade of ",
      "ai_weak": "However, your ",
      "ai_weak_score": " score requires a bit more attention. Head over to the AI Quizzes section to practice more!",
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchGrades();
  }

  Future<void> _fetchGrades() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    try {
      String? token = await _storage.read(key: 'jwt_token');
      _studentId = await _storage.read(key: 'user_id') ?? "";

      if (token != null && _studentId.isNotEmpty) {
        final res = await http.get(
          Uri.parse('${AppConfig.apiUrl}/api/tv2/grades/$_studentId'),
          headers: {"Authorization": "Bearer $token"},
        ).timeout(const Duration(seconds: 10));

        if (res.statusCode == 200) {
          if (mounted) {
            setState(() {
              _realGrades = jsonDecode(utf8.decode(res.bodyBytes));
            });
          }
        }
      }
    } catch (e) {
      debugPrint("Lỗi tải điểm: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String _translateRank(String rankVi) {
    if (_lang == "vi") return rankVi;
    switch (rankVi) {
      case "Giỏi": return "Excellent";
      case "Khá": return "Good";
      case "TB": return "Average";
      case "Yếu": return "Poor";
      default: return rankVi;
    }
  }

  Color _getRankColor(String rankVi) {
    if (rankVi == "Giỏi" || rankVi == "Excellent") return Colors.green;
    if (rankVi == "Khá" || rankVi == "Good") return Colors.blue;
    if (rankVi == "TB" || rankVi == "Average") return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)), 
        backgroundColor: Colors.amber, 
        foregroundColor: Colors.black,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchGrades),
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.amber))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    labels["subtitle"]!,
                    style: TextStyle(fontSize: 14, color: Colors.grey[800], fontStyle: FontStyle.italic),
                  ),
                  const SizedBox(height: 20),

                  if (_realGrades.isEmpty)
                    Center(child: Padding(padding: const EdgeInsets.all(20.0), child: Text(labels["no_grades"]!)))
                  else
                    // Bảng điểm động (DataTable)
                    Card(
                      elevation: 2,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: DataTable(
                          columnSpacing: 15,
                          headingRowColor: MaterialStateProperty.all(Colors.amber[100]),
                          columns: [
                            DataColumn(label: Text(labels["col_subject"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                            DataColumn(label: Text(labels["col_attend"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                            DataColumn(label: Text(labels["col_test"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                            DataColumn(label: Text(labels["col_midterm"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                            DataColumn(label: Text(labels["col_final"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                            DataColumn(label: Text(labels["col_total"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                            DataColumn(label: Text(labels["col_grade"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                          ],
                          rows: _realGrades.map((data) {
                            String rankDisplay = _translateRank(data["xep_loai"] ?? "");
                            Color rankColor = _getRankColor(data["xep_loai"] ?? "");

                            return DataRow(cells: [
                              DataCell(Text(data["subject"]?.toString() ?? "N/A", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo))),
                              DataCell(Text(data["chuyen_can"]?.toString() ?? "0")),
                              DataCell(Text(data["tb_kiem_tra"]?.toString() ?? "0")),
                              DataCell(Text(data["giua_ky"]?.toString() ?? "0")),
                              DataCell(Text(data["cuoi_ky"]?.toString() ?? "0")),
                              DataCell(Text(data["tong_ket"]?.toString() ?? "0", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red))),
                              DataCell(
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: rankColor.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: rankColor)
                                  ),
                                  child: Text(rankDisplay, style: TextStyle(color: rankColor, fontSize: 12, fontWeight: FontWeight.bold)),
                                )
                              ),
                            ]);
                          }).toList(),
                        ),
                      ),
                    ),

                  const SizedBox(height: 30),

                  // Góc phân tích AI Động
                  Text(
                    labels["sub_ai"]!,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87),
                  ),
                  const SizedBox(height: 10),
                  
                  if (_realGrades.isNotEmpty)
                    Builder(
                      builder: (context) {
                        // Tính toán môn cao nhất và thấp nhất
                        var bestSub = _realGrades.reduce((a, b) => (a["tong_ket"] ?? 0) > (b["tong_ket"] ?? 0) ? a : b);
                        var weakSub = _realGrades.reduce((a, b) => (a["tong_ket"] ?? 0) < (b["tong_ket"] ?? 0) ? a : b);
                        
                        String aiComment = labels["ai_excellent"]! + "**${bestSub['subject']}**" + labels["ai_excellent_score"]! + "**${bestSub['tong_ket']}/10**! 🎉\n\n";
                        
                        if (bestSub['subject'] != weakSub['subject']) {
                          aiComment += labels["ai_weak"]! + "**${weakSub['subject']}**" + labels["ai_weak_score"]!;
                        }

                        return Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.blue[50],
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.blue[200]!),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.psychology, color: Colors.blue, size: 30),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  aiComment,
                                  style: TextStyle(color: Colors.blue[900], fontSize: 14, height: 1.5),
                                ),
                              ),
                            ],
                          ),
                        );
                      }
                    )
                  else
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.blue[200]!)),
                      child: Text("AI đang chờ bạn làm bài kiểm tra để có thể phân tích nhé!", style: TextStyle(color: Colors.blue[900])),
                    )
                ],
              ),
            ),
    );
  }
}