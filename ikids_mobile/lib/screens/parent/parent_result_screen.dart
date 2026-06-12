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
  
  // Dữ liệu cho View 1 (Progress)
  List<dynamic> _attendanceHistory = [];
  
  // Dữ liệu cho View 2 (Exam)
  List<dynamic> _realGrades = [];

  // Trạng thái View: 0 = Tiến độ (Progress), 1 = Bảng điểm (Exam)
  int _currentViewIndex = 0;

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Báo Cáo Học Tập",
      "err_login": "Vui lòng đăng nhập để xem báo cáo.",
      "select_child": "Đang hiển thị dữ liệu của bé:",
      "warn_no_child": "Bạn chưa có hồ sơ học sinh nào.",
      "view_progress": "Tiến độ học tập",
      "view_exam": "Điểm tổng kết",
      "stat_attendance": "Tỷ lệ chuyên cần",
      "stat_quiz": "TB điểm Quiz",
      "stat_videos": "Video đã học",
      "stat_rank": "Hạng hiện tại",
      "chart_title": "Biểu đồ điểm Quiz gần đây",
      "journal_title": "Lịch Sử Điểm Danh & Nhận Xét",
      "no_journal": "Chưa có lịch sử điểm danh.",
      "exam_title": "Bảng Điểm Tổng Kết Môn Học",
      "exam_desc": "Kết quả học tập dựa trên điểm chuyên cần, kiểm tra, giữa kỳ và cuối kỳ.",
      "no_grades": "Bé chưa có điểm tổng kết nào được ghi nhận.",
    },
    "en": {
      "title": "Learning Analytics",
      "err_login": "Authentication required.",
      "select_child": "Displaying data for:",
      "warn_no_child": "No student profiles found.",
      "view_progress": "Learning Progress",
      "view_exam": "Final Grades",
      "stat_attendance": "Attendance Rate",
      "stat_quiz": "Avg Quiz Score",
      "stat_videos": "Videos Completed",
      "stat_rank": "Current Rank",
      "chart_title": "Recent Quiz Score Trend",
      "journal_title": "Attendance & Remarks History",
      "no_journal": "No attendance history available.",
      "exam_title": "Final Grade Report",
      "exam_desc": "Academic results based on attendance, tests, midterm, and final exams.",
      "no_grades": "No grades recorded for this student yet.",
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

  Future<void> _fetchChildData(String childId) async {
    final headers = {"Authorization": "Bearer $_token", "parent-id": _parentId};
    try {
      // Gọi API Điểm danh
      final attRes = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv2/attendance/$childId'), headers: headers);
      if (attRes.statusCode == 200) _attendanceHistory = jsonDecode(utf8.decode(attRes.bodyBytes));
      else _attendanceHistory = [];

      // Gọi API Bảng điểm
      final gradeRes = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv2/grades/$childId'), headers: headers);
      if (gradeRes.statusCode == 200) _realGrades = jsonDecode(utf8.decode(gradeRes.bodyBytes));
      else _realGrades = [];

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
                // 1. HEADER CHỌN HỌC SINH
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
                
                // 2. THANH CHUYỂN ĐỔI VIEW (TOGGLE BUTTONS)
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

                // 3. NỘI DUNG VIEW
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

  // ================= VIEW 1: TIẾN ĐỘ HỌC TẬP =================
  Widget _buildProgressView(Map<String, String> labels) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 4 Thẻ chỉ số tổng quan (Grid)
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 2,
          children: [
            _buildStatCard(labels["stat_attendance"]!, "92%", Icons.event_available, Colors.green),
            _buildStatCard(labels["stat_quiz"]!, "7.5/10", Icons.quiz, Colors.orange),
            _buildStatCard(labels["stat_videos"]!, "8", Icons.play_circle, Colors.red),
            _buildStatCard(labels["stat_rank"]!, "Beginner", Icons.military_tech, Colors.purple),
          ],
        ),
        
        const SizedBox(height: 25),
        Text(labels["chart_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 15),
        
        // Biểu đồ Điểm số
        Container(
          height: 200,
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 5)]),
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: false),
              titlesData: const FlTitlesData(rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)), topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false))),
              borderData: FlBorderData(show: false),
              minX: 0, maxX: 4, minY: 0, maxY: 10,
              lineBarsData: [
                LineChartBarData(
                  spots: const [FlSpot(0, 6), FlSpot(1, 9), FlSpot(2, 8), FlSpot(3, 7), FlSpot(4, 9)],
                  isCurved: true,
                  color: Colors.amber[700],
                  barWidth: 4,
                  isStrokeCapRound: true,
                  dotData: const FlDotData(show: true),
                  belowBarData: BarAreaData(show: true, color: Colors.amber.withOpacity(0.2)),
                ),
              ],
            ),
          ),
        ),
        
        const SizedBox(height: 25),
        Text(labels["journal_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),

        // Lịch sử điểm danh (Timeline/List)
        _attendanceHistory.isEmpty 
          ? Center(child: Padding(padding: const EdgeInsets.all(20), child: Text(labels["no_journal"]!)))
          : ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _attendanceHistory.length,
              itemBuilder: (context, index) {
                final att = _attendanceHistory[index];
                
                String statusVi = att['Trạng Thái'] ?? 'Có mặt';
                String statusEn = statusVi == "Có mặt" ? "Present" : (statusVi == "Vắng mặt" ? "Absent" : "Late");
                String displayStatus = _lang == "en" ? statusEn : statusVi;

                Color statusColor = displayStatus.contains("Có") || displayStatus.contains("Present") 
                  ? Colors.green 
                  : (displayStatus.contains("Vắng") || displayStatus.contains("Absent") ? Colors.red : Colors.orange);

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

                Color rankColor = displayRank.contains("Giỏi") || displayRank.contains("Excellent") 
                  ? Colors.green 
                  : (displayRank.contains("Khá") || displayRank.contains("Good") ? Colors.blue : Colors.orange);

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