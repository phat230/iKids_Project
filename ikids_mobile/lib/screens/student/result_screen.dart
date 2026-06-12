import 'package:flutter/material.dart';

class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  String _lang = "vi";

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "📊 Bảng Điểm Cá Nhân",
      "subtitle": "Theo dõi sự tiến bộ của bạn qua từng bài kiểm tra và các kỳ thi nhé!",
      "sub_ai": "🤖 Phân Tích Từ Hệ Thống AI",
      "ai_comment": "💡 AI Nhận xét: Bạn đang làm rất tốt môn Kỹ Năng Sống và Anh Văn! Tuy nhiên, điểm môn Khoa Học đang hơi thấp. Hãy vào mục Bài Tập AI để ôn luyện thêm phần này, vừa cải thiện điểm số vừa nhận thêm thật nhiều iKids Xu nhé!",
      "col_subject": "Môn học",
      "col_midterm": "Giữa Kỳ",
      "col_final": "Cuối Kỳ",
      "col_grade": "Đánh giá",
      "sub_math": "Toán Tư Duy",
      "sub_english": "Anh Văn",
      "sub_science": "Khoa Học",
      "sub_skills": "Kỹ Năng Sống",
      "not_available": "Chưa có",
      "grade_good": "Khá",
      "grade_excellent": "Tốt",
      "grade_needs_improvement": "Cần cố gắng",
      "grade_outstanding": "Xuất sắc"
    },
    "en": {
      "title": "📊 My Report Card",
      "subtitle": "Track your academic growth and exam grades throughout the semester!",
      "sub_ai": "🤖 AI Insights & Recommendations",
      "ai_comment": "💡 AI Feedback: You are performing excellently in Life Skills and English! However, your Science score has room for improvement. Head over to the AI Quizzes section to practice more, level up your scores, and earn lots of iKids Coins! 🪙",
      "col_subject": "Course Subject",
      "col_midterm": "Midterm",
      "col_final": "Final",
      "col_grade": "Evaluation",
      "sub_math": "Critical Math",
      "sub_english": "English",
      "sub_science": "Science",
      "sub_skills": "Life Skills",
      "not_available": "N/A",
      "grade_good": "Good",
      "grade_excellent": "Very Good",
      "grade_needs_improvement": "Needs Improvement",
      "grade_outstanding": "Outstanding"
    }
  };

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    // Cấu trúc dữ liệu tĩnh giống hệt bên Web
    final List<Map<String, dynamic>> tableData = [
      {
        "subject": labels["sub_math"],
        "midterm": "8.5",
        "final": labels["not_available"],
        "grade": labels["grade_good"],
        "color": Colors.blue
      },
      {
        "subject": labels["sub_english"],
        "midterm": "9.0",
        "final": labels["not_available"],
        "grade": labels["grade_excellent"],
        "color": Colors.green
      },
      {
        "subject": labels["sub_science"],
        "midterm": "7.5",
        "final": labels["not_available"],
        "grade": labels["grade_needs_improvement"],
        "color": Colors.orange
      },
      {
        "subject": labels["sub_skills"],
        "midterm": "10.0",
        "final": labels["not_available"],
        "grade": labels["grade_outstanding"],
        "color": Colors.purple
      },
    ];

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold)), 
        backgroundColor: Colors.amber, 
        foregroundColor: Colors.black,
        actions: [
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Subtitle
            Text(
              labels["subtitle"]!,
              style: TextStyle(fontSize: 14, color: Colors.grey[800], fontStyle: FontStyle.italic),
            ),
            const SizedBox(height: 20),

            // Bảng điểm (DataTable) bọc trong thanh cuộn ngang để chống vỡ giao diện trên điện thoại nhỏ
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: DataTable(
                  headingRowColor: MaterialStateProperty.all(Colors.amber[100]),
                  columns: [
                    DataColumn(label: Text(labels["col_subject"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                    DataColumn(label: Text(labels["col_midterm"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                    DataColumn(label: Text(labels["col_final"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                    DataColumn(label: Text(labels["col_grade"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                  ],
                  rows: tableData.map((data) {
                    return DataRow(cells: [
                      DataCell(
                        Row(
                          children: [
                            Icon(Icons.book, size: 16, color: data["color"]),
                            const SizedBox(width: 8),
                            Text(data["subject"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                      DataCell(Text(data["midterm"]!)),
                      DataCell(Text(data["final"]!, style: const TextStyle(color: Colors.grey))),
                      DataCell(
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: (data["color"] as Color).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: data["color"])
                          ),
                          child: Text(data["grade"]!, style: TextStyle(color: data["color"], fontSize: 12, fontWeight: FontWeight.bold)),
                        )
                      ),
                    ]);
                  }).toList(),
                ),
              ),
            ),

            const SizedBox(height: 30),

            // Góc phân tích AI
            Text(
              labels["sub_ai"]!,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87),
            ),
            const SizedBox(height: 10),
            Container(
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
                      labels["ai_comment"]!,
                      style: TextStyle(color: Colors.blue[900], fontSize: 14, height: 1.5),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}