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
  String _lang = "vi";

  DateTime _currentWeekDate = DateTime.now();

  final List<String> _dayNames = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];
  final List<String> _sessions = ["SÁNG", "CHIỀU", "TỐI"];

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Lịch Dạy Của Tôi",
      "btn_today": "Hôm nay",
      "lbl_month": "Tháng",
      "msg_empty": "Chưa có lịch dạy.",
      "lbl_room": "Phòng:"
    },
    "en": {
      "title": "My Teaching Schedule",
      "btn_today": "Today",
      "lbl_month": "Month",
      "msg_empty": "No schedule available.",
      "lbl_room": "Room:"
    }
  };

  String _translateDay(String viDay) {
    if (_lang == "vi") return viDay;
    switch (viDay) {
      case "Thứ 2": return "Mon";
      case "Thứ 3": return "Tue";
      case "Thứ 4": return "Wed";
      case "Thứ 5": return "Thu";
      case "Thứ 6": return "Fri";
      case "Thứ 7": return "Sat";
      case "Chủ nhật": return "Sun";
      default: return viDay;
    }
  }

  String _translateSession(String viSession) {
    if (_lang == "vi") return viSession;
    switch (viSession) {
      case "SÁNG": return "MORNING";
      case "CHIỀU": return "AFTERNOON";
      case "TỐI": return "EVENING";
      default: return viSession;
    }
  }

  @override
  void initState() {
    super.initState();
    _loadSchedules();
  }

  Future<void> _loadSchedules() async {
    setState(() => _isLoading = true);
    try {
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

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

    for (var session in _sessions) {
      for (var day in _dayNames) {
        matrix[session]![day]!.sort((a, b) => (a["start_time"] ?? "").compareTo(b["start_time"] ?? ""));
      }
    }

    return matrix;
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;
    int currentWeekday = _currentWeekDate.weekday; 
    DateTime startOfWeek = _currentWeekDate.subtract(Duration(days: currentWeekday - 1));
    List<DateTime> weekDates = List.generate(7, (index) => startOfWeek.add(Duration(days: index)));

    final matrix = _buildScheduleMatrix();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
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
                        child: Text(labels["btn_today"]!, style: const TextStyle(color: Colors.indigo)),
                      ),
                      Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.chevron_left, color: Colors.indigo),
                            onPressed: () => _changeWeek(-7),
                          ),
                          Text(
                            "${labels['lbl_month']} ${DateFormat('M - yyyy').format(_currentWeekDate)}",
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
                
                // --- BẢNG LỊCH HỌC ---
                Expanded(
                  child: InteractiveViewer(
                    constrained: false, 
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
                            0: FixedColumnWidth(50), 
                            1: FixedColumnWidth(140), 2: FixedColumnWidth(140),
                            3: FixedColumnWidth(140), 4: FixedColumnWidth(140),
                            5: FixedColumnWidth(140), 6: FixedColumnWidth(140),
                            7: FixedColumnWidth(140),
                          },
                          children: [
                            // 1. DÒNG HEADER
                            TableRow(
                              decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: const BorderRadius.vertical(top: Radius.circular(12))),
                              children: [
                                _buildHeaderCell(""),
                                for (int i = 0; i < 7; i++)
                                  _buildHeaderCell("${_translateDay(_dayNames[i])}\n(${DateFormat('dd/MM').format(weekDates[i])})"),
                              ],
                            ),
                            
                            // 2. CÁC DÒNG CA DẠY
                            for (var session in _sessions)
                              TableRow(
                                children: [
                                  TableCell(
                                    verticalAlignment: TableCellVerticalAlignment.fill,
                                    child: Container(
                                      color: Colors.grey.shade50,
                                      child: Center(
                                        child: RotatedBox(
                                          quarterTurns: 3,
                                          child: Text(
                                            _translateSession(session),
                                            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey, letterSpacing: 2),
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                  
                                  for (var day in _dayNames)
                                    TableCell(
                                      child: Container(
                                        constraints: const BoxConstraints(minHeight: 120),
                                        padding: const EdgeInsets.all(8),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: matrix[session]![day]!.map((item) => _buildClassCard(item, labels)).toList(),
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

  Widget _buildClassCard(Map<String, dynamic> item, Map<String, String> labels) {
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
          Text(item['subject'] ?? "Subject", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue, fontSize: 13)),
          const SizedBox(height: 4),
          Text(item['class_name'] ?? "Class Name", style: const TextStyle(fontSize: 12, color: Colors.black87, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text("${item['start_time']} - ${item['end_time']}", style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
          Text("${labels['lbl_room']} ${item['room']}", style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
        ],
      ),
    );
  }
}