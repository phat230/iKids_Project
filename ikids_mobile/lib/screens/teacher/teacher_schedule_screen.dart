import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:intl/intl.dart';
import '../../core/config.dart';

class TeacherScheduleScreen extends StatefulWidget {
  const TeacherScheduleScreen({super.key});

  @override
  State<TeacherScheduleScreen> createState() => _TeacherScheduleScreenState();
}

class _TeacherScheduleScreenState extends State<TeacherScheduleScreen> {
  final _storage = const FlutterSecureStorage();
  List<dynamic> _schedules = [];
  bool _isLoading = true;
  String _teacherId = "";

  DateTime _currentWeekDate = DateTime.now();

  final List<String> _dayNames = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];
  final List<String> _sessions = ["SÁNG", "CHIỀU", "TỐI"];

  @override
  void initState() {
    super.initState();
    _loadSchedules();
  }

  Future<void> _loadSchedules() async {
    setState(() => _isLoading = true);
    try {
      String? token = await _storage.read(key: 'jwt_token');
      String? userInfoStr = await _storage.read(key: 'user_info');
      if (userInfoStr != null) {
        final userInfo = jsonDecode(userInfoStr);
        _teacherId = userInfo["id"]?.toString() ?? userInfo["_id"]?.toString() ?? "";
      }

      final res = await http.get(
        Uri.parse('${AppConfig.apiTv1}/schedule/list'),
        headers: {"Authorization": "Bearer $token"},
      );

      if (res.statusCode == 200) {
        List<dynamic> allSchedules = jsonDecode(utf8.decode(res.bodyBytes));
        setState(() {
          _schedules = allSchedules.where((s) => s["teaching_teacher_id"] == _teacherId || s["teacher_id"] == _teacherId).toList();
        });
      }
    } catch (e) {
      debugPrint("Lỗi tải lịch dạy: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _changeWeek(int days) {
    setState(() {
      _currentWeekDate = _currentWeekDate.add(Duration(days: days));
    });
  }

  void _goToToday() {
    setState(() {
      _currentWeekDate = DateTime.now();
    });
  }

  // Thuật toán chia lịch vào ma trận
  Map<String, Map<String, List<dynamic>>> _buildScheduleMatrix() {
    Map<String, Map<String, List<dynamic>>> matrix = {};
    for (var session in _sessions) {
      matrix[session] = {};
      for (var day in _dayNames) {
        matrix[session]![day] = [];
      }
    }

    for (var s in _schedules) {
      String startTime = s["start_time"] ?? "08:00";
      int hour = int.tryParse(startTime.split(":")[0]) ?? 8;
      
      String session = _sessions[0]; // SÁNG
      if (hour >= 12 && hour < 17) {
        session = _sessions[1]; // CHIỀU
      } else if (hour >= 17) {
        session = _sessions[2]; // TỐI
      }

      List<dynamic> rawDays = s["days_of_week"] ?? [];
      for (String d in rawDays) {
        if (matrix[session]!.containsKey(d)) {
          matrix[session]![d]!.add(s);
        }
      }
    }

    // Sắp xếp các lớp trong cùng 1 ô theo giờ học
    for (var session in _sessions) {
      for (var day in _dayNames) {
        matrix[session]![day]!.sort((a, b) => (a["start_time"] ?? "").compareTo(b["start_time"] ?? ""));
      }
    }

    return matrix;
  }

  @override
  Widget build(BuildContext context) {
    // Tính toán các ngày trong tuần hiện tại
    int currentWeekday = _currentWeekDate.weekday; // 1 = Thứ 2, 7 = CN
    DateTime startOfWeek = _currentWeekDate.subtract(Duration(days: currentWeekday - 1));
    List<DateTime> weekDates = List.generate(7, (index) => startOfWeek.add(Duration(days: index)));

    final matrix = _buildScheduleMatrix();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("Lịch Dạy Của Tôi", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.indigo))
          : Column(
              children: [
                // --- THANH ĐIỀU HƯỚNG TUẦN ---
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 15),
                  color: Colors.indigo.withOpacity(0.05),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      OutlinedButton(
                        style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.indigo)),
                        onPressed: _goToToday,
                        child: const Text("Hôm nay", style: TextStyle(color: Colors.indigo)),
                      ),
                      Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.chevron_left, color: Colors.indigo),
                            onPressed: () => _changeWeek(-7),
                          ),
                          Text(
                            "Tháng ${DateFormat('M - yyyy').format(_currentWeekDate)}",
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.indigo),
                          ),
                          IconButton(
                            icon: const Icon(Icons.chevron_right, color: Colors.indigo),
                            onPressed: () => _changeWeek(7),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                
                // --- BẢNG LỊCH HỌC (SCROLL NGANG + DỌC) ---
                Expanded(
                  child: InteractiveViewer(
                    constrained: false, // Cho phép vuốt ngang vuốt dọc như xem bản đồ
                    minScale: 0.5,
                    maxScale: 2.0,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Container(
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey.shade300),
                          borderRadius: BorderRadius.circular(12),
                          color: Colors.white,
                        ),
                        child: Table(
                          border: TableBorder.symmetric(
                            inside: BorderSide(color: Colors.grey.shade200),
                          ),
                          columnWidths: const {
                            0: FixedColumnWidth(50), // Cột Buổi (Sáng/Chiều/Tối)
                            1: FixedColumnWidth(140), // Các cột Thứ
                            2: FixedColumnWidth(140),
                            3: FixedColumnWidth(140),
                            4: FixedColumnWidth(140),
                            5: FixedColumnWidth(140),
                            6: FixedColumnWidth(140),
                            7: FixedColumnWidth(140),
                          },
                          children: [
                            // 1. DÒNG HEADER (Thứ + Ngày)
                            TableRow(
                              decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: const BorderRadius.vertical(top: Radius.circular(12))),
                              children: [
                                _buildHeaderCell("Buổi"),
                                for (int i = 0; i < 7; i++)
                                  _buildHeaderCell("${_dayNames[i]}\n(${DateFormat('dd/MM').format(weekDates[i])})"),
                              ],
                            ),
                            
                            // 2. CÁC DÒNG CA DẠY
                            for (var session in _sessions)
                              TableRow(
                                children: [
                                  // Cột ghi chú SÁNG/CHIỀU/TỐI (Chữ xoay dọc)
                                  TableCell(
                                    verticalAlignment: TableCellVerticalAlignment.fill,
                                    child: Container(
                                      color: Colors.grey.shade50,
                                      child: Center(
                                        child: RotatedBox(
                                          quarterTurns: 3,
                                          child: Text(
                                            session,
                                            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey, letterSpacing: 2),
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                  
                                  // Các cột lịch học
                                  for (var day in _dayNames)
                                    TableCell(
                                      child: Container(
                                        constraints: const BoxConstraints(minHeight: 120),
                                        padding: const EdgeInsets.all(8),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: matrix[session]![day]!.map((item) => _buildClassCard(item)).toList(),
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  // Widget vẽ ô tiêu đề (Header)
  Widget _buildHeaderCell(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey.shade800, fontSize: 13),
      ),
    );
  }

  // Widget vẽ Card thông tin môn học y như bản Web
  Widget _buildClassCard(Map<String, dynamic> item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        border: const Border(left: BorderSide(color: Colors.blue, width: 4)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(item['subject'] ?? "Môn học", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue, fontSize: 13)),
          const SizedBox(height: 4),
          Text(item['class_name'] ?? "Tên lớp", style: const TextStyle(fontSize: 12, color: Colors.black87, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text("${item['start_time']} - ${item['end_time']}", style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
          Text("Phòng: ${item['room']}", style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
        ],
      ),
    );
  }
}