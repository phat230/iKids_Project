import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
import '../../core/config.dart';

class ParentResultScreen extends StatefulWidget {
  const ParentResultScreen({super.key});

  @override
  State<ParentResultScreen> createState() => _ParentResultScreenState();
}

class _ParentResultScreenState extends State<ParentResultScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";
  String _parentId = "";
  String _token = "";

  List<dynamic> _children = [];
  String? _selectedChildId;
  
  List<dynamic> _attendanceHistory = [];
  Map<String, dynamic> _gameProfile = {};
  List<dynamic> _totalQuizzes = [];
  
  List<dynamic> _realGrades = [];
  String? _selectedSubjectChart;

  int _currentViewIndex = 0;

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Báo Cáo Học Tập",
      "err_login": "Vui lòng đăng nhập để xem báo cáo.",
      "select_child": "Đang hiển thị dữ liệu của bé:",
      "warn_no_child": "Bạn chưa có hồ sơ học sinh nào.",
      "view_progress": "Phân tích Tiến độ",
      "view_exam": "Bảng điểm",
      "stat_attendance": "Tỷ lệ chuyên cần",
      "stat_quiz": "TB Kiểm Tra",
      "stat_quiz_progress": "Tiến độ bài tập",
      "stat_rank": "Hạng hiện tại",
      "chart_title_1": "Điểm Tổng Kết Các Môn",
      "chart_title_2": "Tỷ Lệ Làm Bài Tập",
      "line_chart_title": "Sơ Đồ Tiến Trình Môn:",
      "journal_title": "Lịch Sử Điểm Danh",
      "no_journal": "Chưa có lịch sử điểm danh.",
      "exam_title": "Bảng Điểm Tổng Kết",
      "exam_desc": "Kết quả đánh giá dựa trên điểm thành phần, giữa kỳ và cuối kỳ.",
      "no_grades": "Bé chưa có điểm tổng kết nào được ghi nhận.",
      "ai_title": "🤖 AI Phân Tích & Tư Vấn",
      "lbl_done": "Đã làm",
      "lbl_missing": "Chưa làm",
    },
    "en": {
      "title": "Learning Analytics",
      "err_login": "Authentication required.",
      "select_child": "Displaying data for:",
      "warn_no_child": "No student profiles found.",
      "view_progress": "Progress Analytics",
      "view_exam": "Final Grades",
      "stat_attendance": "Attendance Rate",
      "stat_quiz": "Avg Test Score",
      "stat_quiz_progress": "Quizzes Done",
      "stat_rank": "Current Rank",
      "chart_title_1": "Final Grades Overview",
      "chart_title_2": "Homework Completion",
      "line_chart_title": "Score Progression for:",
      "journal_title": "Attendance History",
      "no_journal": "No attendance history available.",
      "exam_title": "Final Grade Report",
      "exam_desc": "Evaluations based on component, midterm, and final scores.",
      "no_grades": "No grades recorded for this student yet.",
      "ai_title": "🤖 AI Insights",
      "lbl_done": "Completed",
      "lbl_missing": "Pending",
    }
  };

  @override
  void initState() {
    super.initState();
    _initData();
  }

  Future<void> _initData() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    try {
      _token = await _storage.read(key: 'jwt_token') ?? "";
      _parentId = await _storage.read(key: 'user_id') ?? "";

      if (_token.isEmpty || _parentId.isEmpty) return;

      final headers = {"Authorization": "Bearer $_token", "parent-id": _parentId};
      final childrenRes = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/parent/my-children'), headers: headers);
      
      if (childrenRes.statusCode == 200) {
        _children = jsonDecode(utf8.decode(childrenRes.bodyBytes));
        if (_children.isNotEmpty) {
          _selectedChildId = _children[0]['id'];
          await _fetchChildData(_selectedChildId!);
        }
      }
    } catch (e) {
      debugPrint("Lỗi Init Data: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // ĐÃ SỬA CHỮA HOÀN TOÀN: Logic quét đa tầng (ID và Email) y hệt như Web
  Future<void> _fetchChildData(String childId) async {
    final headers = {"Authorization": "Bearer $_token", "parent-id": _parentId};
    try {
      final childData = _children.firstWhere((c) => c['id'].toString() == childId, orElse: () => {});
      final childEmail = childData['email'] ?? '';

      // 1. Fetch nhanh các dữ liệu nền
      final resAtt = http.get(Uri.parse('${AppConfig.apiUrl}/api/tv2/attendance/$childId'), headers: headers);
      final resGrades = http.get(Uri.parse('${AppConfig.apiUrl}/api/tv2/grades/$childId'), headers: headers);
      final resProfileTV3 = http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/gamification/profile/$childId'), headers: headers);
      final resQuizzes = http.get(Uri.parse('${AppConfig.apiUrl}/api/tv2/quizzes'), headers: headers);
      
      final responses = await Future.wait([resAtt, resGrades, resProfileTV3, resQuizzes]);

      if (responses[0].statusCode == 200) _attendanceHistory = jsonDecode(utf8.decode(responses[0].bodyBytes));
      else _attendanceHistory = [];

      if (responses[1].statusCode == 200) {
        _realGrades = jsonDecode(utf8.decode(responses[1].bodyBytes));
        if (_realGrades.isNotEmpty) _selectedSubjectChart = _realGrades[0]['subject'];
      } else {
        _realGrades = [];
        _selectedSubjectChart = null;
      }

      if (responses[3].statusCode == 200) _totalQuizzes = jsonDecode(utf8.decode(responses[3].bodyBytes));
      else _totalQuizzes = [];

      Map<String, dynamic> tv3Prof = {};
      if (responses[2].statusCode == 200) tv3Prof = jsonDecode(utf8.decode(responses[2].bodyBytes));

      // 2. KHẮC PHỤC LỖI TẠI ĐÂY: Quét chéo tìm "completed_tasks" qua ID trước, nếu không có mới qua Email
      List<dynamic> compTasks = [];
      List<String> keysToTest = [childId]; 
      if (childEmail.isNotEmpty) keysToTest.add(childEmail);

      for (String key in keysToTest) {
        final encodedKey = Uri.encodeComponent(key);
        try {
          final resProfTV2 = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv2/student/$encodedKey/profile'), headers: headers);
          if (resProfTV2.statusCode == 200) {
            final tv2Prof = jsonDecode(utf8.decode(resProfTV2.bodyBytes));
            if (tv2Prof.containsKey('completed_tasks') && (tv2Prof['completed_tasks'] as List).isNotEmpty) {
              compTasks = tv2Prof['completed_tasks'];
              break; // Dừng quét khi đã tìm thấy dữ liệu đúng
            }
          }
        } catch(e) {
          debugPrint("Bỏ qua quét: $key");
        }
      }
      
      // Nếu TV2 có dữ liệu thì ghi đè vào, không thì giữ nguyên của TV3 (phòng hờ)
      tv3Prof['completed_tasks'] = compTasks.isNotEmpty ? compTasks : (tv3Prof['completed_tasks'] ?? []);
      _gameProfile = tv3Prof;

    } catch (e) {
      debugPrint("Lỗi Fetch Child Data: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;
    if (_token.isEmpty || _parentId.isEmpty) {
      return Scaffold(body: Center(child: Text(labels["err_login"]!, style: const TextStyle(color: Colors.red))));
    }

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        backgroundColor: Colors.amber[700],
        foregroundColor: Colors.white,
        actions: [
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading 
        ? Center(child: CircularProgressIndicator(color: Colors.amber[700]))
        : _children.isEmpty 
          ? Center(child: Text(labels["warn_no_child"]!))
          : Column(
              children: [
                Container(
                  color: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                  child: Row(
                    children: [
                      const CircleAvatar(backgroundColor: Colors.amber, child: Icon(Icons.face, color: Colors.white)),
                      const SizedBox(width: 15),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(labels["select_child"]!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                            DropdownButtonHideUnderline(
                              child: DropdownButton<String>(
                                isDense: true,
                                value: _selectedChildId,
                                style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.black87, fontSize: 16),
                                items: _children.map((c) => DropdownMenuItem<String>(value: c['id'].toString(), child: Text(c['name'] ?? ''))).toList(),
                                onChanged: (val) async {
                                  if (val != null) {
                                    setState(() { _selectedChildId = val; _isLoading = true; });
                                    await _fetchChildData(val);
                                    setState(() => _isLoading = false);
                                  }
                                },
                              ),
                            )
                          ],
                        ),
                      )
                    ],
                  ),
                ),
                
                Padding(
                  padding: const EdgeInsets.all(15.0),
                  child: Container(
                    decoration: BoxDecoration(color: Colors.amber[100], borderRadius: BorderRadius.circular(10)),
                    child: Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _currentViewIndex = 0),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              decoration: BoxDecoration(
                                color: _currentViewIndex == 0 ? Colors.amber[700] : Colors.transparent,
                                borderRadius: BorderRadius.circular(10)
                              ),
                              child: Text(labels["view_progress"]!, textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.bold, color: _currentViewIndex == 0 ? Colors.white : Colors.black54)),
                            ),
                          ),
                        ),
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _currentViewIndex = 1),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              decoration: BoxDecoration(
                                color: _currentViewIndex == 1 ? Colors.amber[700] : Colors.transparent,
                                borderRadius: BorderRadius.circular(10)
                              ),
                              child: Text(labels["view_exam"]!, textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.bold, color: _currentViewIndex == 1 ? Colors.white : Colors.black54)),
                            ),
                          ),
                        )
                      ],
                    ),
                  ),
                ),

                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(horizontal: 15),
                    child: _currentViewIndex == 0 ? _buildProgressView(labels) : _buildExamView(labels),
                  ),
                )
              ],
            ),
    );
  }

  Widget _buildProgressView(Map<String, String> labels) {
    String attRate = "N/A";
    if (_attendanceHistory.isNotEmpty) {
      int present = _attendanceHistory.where((att) => att['Trạng Thái'] == 'Có mặt').length;
      attRate = "${((present / _attendanceHistory.length) * 100).toStringAsFixed(0)}%";
    }

    String avgScore = "N/A";
    if (_realGrades.isNotEmpty) {
      double total = _realGrades.fold(0, (sum, item) => sum + (item['tb_kiem_tra'] ?? 0).toDouble());
      avgScore = "${(total / _realGrades.length).toStringAsFixed(1)}/10";
    }

    // ĐÃ KHẮC PHỤC LOGIC ĐẾM: Xử lý fallback ID bài tập
    List<dynamic> compTasks = _gameProfile['completed_tasks'] ?? [];
    int totalQuizCount = _totalQuizzes.length;
    int doneQuizCount = _totalQuizzes.where((q) {
      String qId = q['id']?.toString() ?? q['_id']?.toString() ?? '';
      if (qId.isEmpty) {
        int idx = _totalQuizzes.indexOf(q);
        qId = "quiz_backup_id_$idx"; // Khớp y hệt fallback của Streamlit Web
      }
      return compTasks.contains(qId);
    }).length;
    String quizStr = "$doneQuizCount/$totalQuizCount";

    String rank = _gameProfile['rank'] ?? "Beginner";

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 2,
          children: [
            _buildStatCard(labels["stat_attendance"]!, attRate, Icons.event_available, Colors.green),
            _buildStatCard(labels["stat_quiz"]!, avgScore, Icons.score, Colors.blue),
            _buildStatCard(labels["stat_quiz_progress"]!, quizStr, Icons.quiz, Colors.orange),
            _buildStatCard(labels["stat_rank"]!, rank, Icons.military_tech, Colors.purple),
          ],
        ),
        
        const SizedBox(height: 25),
        
        // --- SƠ ĐỒ CỘT: ĐIỂM TỔNG KẾT ---
        Text(labels["chart_title_1"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 15),
        _realGrades.isEmpty 
          ? Center(child: Text(labels["no_grades"]!))
          : Container(
              height: 250,
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 5)]),
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: 10,
                  barTouchData: BarTouchData(enabled: true),
                  titlesData: FlTitlesData(
                    show: true,
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (double value, TitleMeta meta) {
                          int idx = value.toInt();
                          if (idx >= 0 && idx < _realGrades.length) {
                            String sub = _realGrades[idx]['subject'] ?? '';
                            return Padding(
                              padding: const EdgeInsets.only(top: 8.0),
                              child: Text(sub, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                            );
                          }
                          return const Text('');
                        },
                      ),
                    ),
                    leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 28)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: _realGrades.asMap().entries.map((e) {
                    return BarChartGroupData(
                      x: e.key,
                      barRods: [
                        BarChartRodData(
                          toY: (e.value['tong_ket'] ?? 0).toDouble(),
                          color: Colors.blue,
                          width: 20,
                          borderRadius: BorderRadius.circular(4),
                        )
                      ],
                    );
                  }).toList(),
                ),
              ),
            ),
        
        const SizedBox(height: 25),

        // --- SƠ ĐỒ VÒNG: TỶ LỆ LÀM BÀI TẬP ---
        Text(labels["chart_title_2"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 15),
        Container(
          height: 200,
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 5)]),
          child: totalQuizCount == 0
            ? const Center(child: Text("Hệ thống chưa có bộ đề Quiz nào."))
            : Row(
                children: [
                  Expanded(
                    child: PieChart(
                      PieChartData(
                        sectionsSpace: 2,
                        centerSpaceRadius: 40,
                        sections: [
                          PieChartSectionData(
                            color: Colors.green,
                            value: doneQuizCount.toDouble(),
                            title: "$doneQuizCount",
                            radius: 30,
                            titleStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                          PieChartSectionData(
                            color: Colors.redAccent,
                            value: (totalQuizCount - doneQuizCount).toDouble(),
                            title: "${totalQuizCount - doneQuizCount}",
                            radius: 30,
                            titleStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                        ],
                      ),
                    ),
                  ),
                  Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [const Icon(Icons.circle, color: Colors.green, size: 14), const SizedBox(width: 5), Text(labels["lbl_done"]!)]),
                      const SizedBox(height: 10),
                      Row(children: [const Icon(Icons.circle, color: Colors.redAccent, size: 14), const SizedBox(width: 5), Text(labels["lbl_missing"]!)]),
                    ],
                  )
                ],
              ),
        ),

        const SizedBox(height: 25),

        // --- SƠ ĐỒ ĐƯỜNG: TIẾN TRÌNH ---
        if (_realGrades.isNotEmpty) ...[
          Row(
            children: [
              Expanded(child: Text(labels["line_chart_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold))),
              Container(
                height: 35,
                padding: const EdgeInsets.symmetric(horizontal: 8),
                decoration: BoxDecoration(color: Colors.amber[50], borderRadius: BorderRadius.circular(8)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedSubjectChart,
                    style: const TextStyle(color: Colors.amber, fontWeight: FontWeight.bold),
                    items: _realGrades.map((g) => DropdownMenuItem<String>(value: g['subject']?.toString(), child: Text(g['subject'] ?? ''))).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _selectedSubjectChart = val);
                    },
                  ),
                ),
              )
            ],
          ),
          const SizedBox(height: 15),
          Container(
            height: 220,
            padding: const EdgeInsets.only(right: 20, left: 10, top: 20, bottom: 10),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 5)]),
            child: _buildLineChartData(),
          ),
          const SizedBox(height: 25),
        ],

        // --- NHẬN XÉT AI ---
        Text(labels["ai_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        _buildAICommentSection(labels),
        
        const SizedBox(height: 25),

        // --- LỊCH SỬ ĐIỂM DANH ---
        Text(labels["journal_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        _attendanceHistory.isEmpty 
          ? Center(child: Padding(padding: const EdgeInsets.all(20), child: Text(labels["no_journal"]!)))
          : ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _attendanceHistory.length,
              itemBuilder: (context, index) {
                final att = _attendanceHistory[index];
                String statusVi = att['Trạng Thái'] ?? 'Có mặt';
                String displayStatus = _lang == "en" ? (statusVi == "Có mặt" ? "Present" : (statusVi == "Vắng mặt" ? "Absent" : "Late")) : statusVi;
                Color statusColor = displayStatus.contains("Có") || displayStatus.contains("Present") ? Colors.green : (displayStatus.contains("Vắng") || displayStatus.contains("Absent") ? Colors.red : Colors.orange);

                return Card(
                  elevation: 1,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  child: ListTile(
                    leading: Icon(Icons.circle, color: statusColor, size: 16),
                    title: Text(att['Môn Học'] ?? 'Môn học', style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text(att['Nhận Xét'] ?? '', style: const TextStyle(fontStyle: FontStyle.italic)),
                        const SizedBox(height: 4),
                        Text(att['Ngày'] ?? '', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                    trailing: Text(displayStatus, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold)),
                  ),
                );
              },
            ),
        const SizedBox(height: 20),
      ],
    );
  }

  Widget _buildLineChartData() {
    final subData = _realGrades.firstWhere((g) => g['subject'] == _selectedSubjectChart, orElse: () => {});
    if (subData.isEmpty) return const Center(child: Text("Không có dữ liệu"));

    List<FlSpot> spots = [
      FlSpot(0, (subData['kt_1'] ?? 0).toDouble()),
      FlSpot(1, (subData['kt_2'] ?? 0).toDouble()),
      FlSpot(2, (subData['kt_3'] ?? 0).toDouble()),
      FlSpot(3, (subData['kt_4'] ?? 0).toDouble()),
      FlSpot(4, (subData['kt_5'] ?? 0).toDouble()),
      FlSpot(5, (subData['giua_ky'] ?? 0).toDouble()),
      FlSpot(6, (subData['cuoi_ky'] ?? 0).toDouble()),
    ];

    List<String> xLabels = ["KT1", "KT2", "KT3", "KT4", "KT5", "GK", "CK"];

    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        titlesData: FlTitlesData(
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 22,
              getTitlesWidget: (value, meta) {
                int idx = value.toInt();
                if (idx >= 0 && idx < xLabels.length) {
                  return Padding(padding: const EdgeInsets.only(top: 5), child: Text(xLabels[idx], style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)));
                }
                return const Text('');
              }
            )
          ),
        ),
        borderData: FlBorderData(show: false),
        minX: 0, maxX: 6, minY: 0, maxY: 10,
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Colors.orange,
            barWidth: 4,
            isStrokeCapRound: true,
            dotData: const FlDotData(show: true),
            belowBarData: BarAreaData(show: true, color: Colors.orange.withOpacity(0.1)),
          ),
        ],
      ),
    );
  }

  Widget _buildAICommentSection(Map<String, String> labels) {
    if (_realGrades.isEmpty) {
      return Container(padding: const EdgeInsets.all(15), decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(10)), child: const Text("Chưa có đủ dữ liệu để AI phân tích."));
    }

    var bestSub = _realGrades.reduce((a, b) => (a["tong_ket"] ?? 0) > (b["tong_ket"] ?? 0) ? a : b);
    var weakSub = _realGrades.reduce((a, b) => (a["tong_ket"] ?? 0) < (b["tong_ket"] ?? 0) ? a : b);

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: Colors.green[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.green[200]!)),
          child: Row(
            children: [
              const Icon(Icons.thumb_up, color: Colors.green),
              const SizedBox(width: 10),
              Expanded(child: Text(_lang == "vi" ? "🎯 Ưu điểm: Bé học tốt nhất môn ${bestSub['subject']} (${bestSub['tong_ket']}/10)." : "🎯 Strength: Excelling in ${bestSub['subject']} (${bestSub['tong_ket']}/10).")),
            ],
          )
        ),
        if (bestSub['subject'] != weakSub['subject']) ...[
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.orange[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.orange[200]!)),
            child: Row(
              children: [
                const Icon(Icons.warning_amber_rounded, color: Colors.orange),
                const SizedBox(width: 10),
                Expanded(child: Text(_lang == "vi" ? "⚠️ Cần chú ý: Môn ${weakSub['subject']} đang thấp nhất (${weakSub['tong_ket']}/10). Phụ huynh đôn đốc bé làm bài tập trên Trạm Quiz AI nhé!" : "⚠️ Area for Growth: ${weakSub['subject']} is currently ${weakSub['tong_ket']}/10. Encourage practicing quizzes!")),
              ],
            )
          )
        ]
      ],
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withOpacity(0.3))),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 5),
          Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
          Text(title, style: const TextStyle(fontSize: 11, color: Colors.grey), textAlign: TextAlign.center),
        ],
      ),
    );
  }

  // ================= VIEW 2: BẢNG ĐIỂM TỔNG KẾT =================
  Widget _buildExamView(Map<String, String> labels) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(labels["exam_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 5),
        Text(labels["exam_desc"]!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 20),

        _realGrades.isEmpty
          ? Center(child: Padding(padding: const EdgeInsets.all(20), child: Text(labels["no_grades"]!)))
          : ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _realGrades.length,
              itemBuilder: (context, index) {
                final grade = _realGrades[index];
                
                String rankVi = grade['xep_loai'] ?? '';
                String rankEn = {"Giỏi": "Excellent", "Khá": "Good", "TB": "Average", "Yếu": "Poor"}[rankVi] ?? rankVi;
                String displayRank = _lang == "en" ? rankEn : rankVi;

                Color rankColor = displayRank.contains("Giỏi") || displayRank.contains("Excellent") ? Colors.green : (displayRank.contains("Khá") || displayRank.contains("Good") ? Colors.blue : Colors.orange);

                return Card(
                  margin: const EdgeInsets.only(bottom: 15),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(15.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(child: Text(grade['subject'] ?? 'Môn học', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16))),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(color: rankColor.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                              child: Text(displayRank, style: TextStyle(color: rankColor, fontWeight: FontWeight.bold)),
                            )
                          ],
                        ),
                        const Divider(height: 20),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            _buildScoreCol(_lang == "vi" ? "Chuyên cần" : "Attend", grade['chuyen_can']),
                            _buildScoreCol(_lang == "vi" ? "Kiểm tra" : "Test", grade['tb_kiem_tra']),
                            _buildScoreCol(_lang == "vi" ? "Giữa kỳ" : "Midterm", grade['giua_ky']),
                            _buildScoreCol(_lang == "vi" ? "Cuối kỳ" : "Final", grade['cuoi_ky']),
                          ],
                        ),
                        const SizedBox(height: 15),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(color: Colors.amber[50], borderRadius: BorderRadius.circular(8)),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(_lang == "vi" ? "Tổng Kết Điểm: " : "Final Grade: ", style: const TextStyle(fontWeight: FontWeight.bold)),
                              Text("${grade['tong_ket'] ?? '0.0'}", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.amber[900])),
                            ],
                          ),
                        )
                      ],
                    ),
                  ),
                );
              },
            ),
      ],
    );
  }

  Widget _buildScoreCol(String title, dynamic score) {
    return Column(
      children: [
        Text(title, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        const SizedBox(height: 4),
        Text("${score ?? '-'}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
      ],
    );
  }
}