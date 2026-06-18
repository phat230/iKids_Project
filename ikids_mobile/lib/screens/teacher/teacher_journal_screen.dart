import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:intl/intl.dart';
import '../../core/config.dart';
import '../../core/network.dart';

class TeacherJournalScreen extends StatefulWidget {
  const TeacherJournalScreen({super.key});

  @override
  State<TeacherJournalScreen> createState() => _TeacherJournalScreenState();
}

class _TeacherJournalScreenState extends State<TeacherJournalScreen> {
  final _storage = const FlutterSecureStorage();
  final _formKey = GlobalKey<FormState>();
  
  DateTime _selectedDate = DateTime.now();
  String? _selectedSchedId;
  List<dynamic> _availableSchedules = [];
  List<dynamic> _students = [];
  
  // Trạng thái điểm danh: { studentId: "present" | "absent" | "late" }
  Map<String, String> _attendanceStates = {};
  Map<String, TextEditingController> _noteControllers = {};

  final _topicController = TextEditingController();
  final _notesController = TextEditingController();

  List<dynamic> _allVideos = [];
  List<dynamic> _allQuizzes = [];
  List<String> _selectedVideos = [];
  List<String> _selectedQuizzes = [];

  bool _isLoading = true;
  String _teacherId = "";

  @override
  void initState() {
    super.initState();
    _initialLoad();
  }

  Future<void> _initialLoad() async {
    await _loadTeacherInfo();
    await _loadSchedulesAndContent();
  }

  Future<void> _loadTeacherInfo() async {
    String? userInfoStr = await _storage.read(key: 'user_info');
    if (userInfoStr != null) {
      final decoded = jsonDecode(userInfoStr);
      _teacherId = decoded["id"]?.toString() ?? decoded["_id"]?.toString() ?? "";
    }
  }

  Future<void> _loadSchedulesAndContent() async {
    setState(() => _isLoading = true);
    try {
      String? token = await _storage.read(key: 'jwt_token');
      
      // 1. Tải lịch dạy (TV1)
      final schedRes = await http.get(
        Uri.parse('${AppConfig.apiTv1}/schedule/list'),
        headers: {"Authorization": "Bearer $token"},
      );
      
      // 2. Tải video và học liệu quiz (TV2)
      final vidRes = await http.get(Uri.parse('${AppConfig.apiTv2}/videos'));
      final quizRes = await http.get(Uri.parse('${AppConfig.apiTv2}/quizzes'));

      if (schedRes.statusCode == 200) {
        List<dynamic> allScheds = jsonDecode(utf8.decode(schedRes.bodyBytes));
        _availableSchedules = allScheds.where((s) => (s["teaching_teacher_id"] ?? "").toString() == _teacherId || (s["teacher_id"] ?? "").toString() == _teacherId).toList();
      }
      if (vidRes.statusCode == 200) _allVideos = jsonDecode(utf8.decode(vidRes.bodyBytes));
      if (quizRes.statusCode == 200) _allQuizzes = jsonDecode(utf8.decode(quizRes.bodyBytes));

      _filterSchedulesByDate();
    } catch (e) {
      debugPrint("Lỗi kết nối học liệu: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _filterSchedulesByDate() {
    final dayNames = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
    String weekdayName = dayNames[_selectedDate.weekday % 7];

    setState(() {
      _selectedSchedId = null;
      _students.clear();
      _attendanceStates.clear();
      _noteControllers.clear();
      _selectedVideos.clear();
      _selectedQuizzes.clear();
      _topicController.clear();
      _notesController.clear();
    });
  }

  Future<void> _loadStudents(String classId) async {
    setState(() => _isLoading = true);
    try {
      String? token = await _storage.read(key: 'jwt_token');
      final res = await http.get(
        Uri.parse('${AppConfig.apiTv1}/classes/$classId/students/details'),
        headers: {"Authorization": "Bearer $token"},
      );
      
      if (res.statusCode == 200) {
        _students = jsonDecode(utf8.decode(res.bodyBytes));
      }

      // ✅ ĐÃ SỬA: Thêm Fallback Data y hệt như Web nếu lớp chưa có học sinh
      if (_students.isEmpty) {
        final sc = _availableSchedules.firstWhere((s) => (s["id"] ?? s["_id"]).toString() == _selectedSchedId);
        String cName = sc["class_name"] ?? "Lớp";
        _students = [
          {"Mã HS": "HS001_DEMO", "Tên Học Sinh": "Nguyễn Văn A ($cName Demo)"},
          {"Mã HS": "HS002_DEMO", "Tên Học Sinh": "Trần Thị B ($cName Demo)"},
          {"Mã HS": "HS003_DEMO", "Tên Học Sinh": "Lê Hoàng C ($cName Demo)"},
          {"Mã HS": "HS004_DEMO", "Tên Học Sinh": "Phạm Mai D ($cName Demo)"},
        ];
      }

      setState(() {
        for (var st in _students) {
          String sid = (st["Mã HS"] ?? st["id"]).toString();
          _attendanceStates[sid] = "present"; // Mặc định là Có mặt
          _noteControllers[sid] = TextEditingController();
        }
      });
      
    } catch (e) {
      debugPrint("Lỗi tải danh sách lớp: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _submitJournal() async {
    if (!_formKey.currentState!.validate() || _selectedSchedId == null) return;

    setState(() => _isLoading = true);
    final currentSched = _availableSchedules.firstWhere((s) => (s["id"] ?? s["_id"]).toString() == _selectedSchedId);

    List<Map<String, dynamic>> attendanceData = _students.map((st) {
      String sid = (st["Mã HS"] ?? st["id"]).toString();
      return {
        "Mã HS": sid,
        "Tên Học Sinh": st["Tên Học Sinh"] ?? st["name"],
        "Có mặt": _attendanceStates[sid] == "present",
        "Vắng": _attendanceStates[sid] == "absent",
        "Đi trễ": _attendanceStates[sid] == "late",
        "Nhận Xét (Tùy chọn)": _noteControllers[sid]?.text.trim() ?? ""
      };
    }).toList();

    Map<String, dynamic> payload = {
      "class_id": currentSched["class_id"].toString(),
      "class_name": currentSched["class_name"],
      "teacher_id": _teacherId,
      "date": DateFormat('dd/MM/yyyy').format(_selectedDate),
      "topic": _topicController.text.trim(),
      "videos_used": _selectedVideos,
      "quizzes_assigned": _selectedQuizzes,
      "notes": _notesController.text.trim(),
      "attendance": attendanceData
    };

    try {
      String? token = await _storage.read(key: 'jwt_token');
      final res = await NetworkHelper.safeRequest(
        http.post(
          Uri.parse('${AppConfig.apiTv2}/journal'),
          headers: {"Content-Type": "application/json", "Authorization": "Bearer $token"},
          body: jsonEncode(payload),
        ),
      );

      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lưu nhật ký và báo cáo thành công!"), backgroundColor: Colors.green));
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Lỗi hệ thống: ${res.body}"), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Mất kết nối máy chủ."), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final dayNames = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
    String currentWeekday = dayNames[_selectedDate.weekday % 7];
    
    List<dynamic> filteredScheds = _availableSchedules.where((s) {
      List<dynamic> dOW = s["days_of_week"] ?? [];
      return dOW.contains(currentWeekday);
    }).toList();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(title: const Text("Nhật Ký & Điểm Danh", style: TextStyle(fontWeight: FontWeight.bold)), backgroundColor: Colors.blueGrey, foregroundColor: Colors.white),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.blueGrey))
          : Form(
              key: _formKey,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // --- 1. LỰA CHỌN CA DẠY ---
                    const Text("1. Lựa chọn ca dạy", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.date_range),
                            label: Text(DateFormat('dd/MM/yyyy').format(_selectedDate)),
                            style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 15)),
                            onPressed: () async {
                              DateTime? picked = await showDatePicker(
                                context: context,
                                initialDate: _selectedDate,
                                firstDate: DateTime(2025),
                                lastDate: DateTime(2030),
                              );
                              if (picked != null) {
                                setState(() => _selectedDate = picked);
                                _filterSchedulesByDate();
                              }
                            },
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 3,
                          child: DropdownButtonFormField<String>(
                            value: _selectedSchedId,
                            hint: const Text("Chọn ca dạy..."),
                            isExpanded: true,
                            decoration: const InputDecoration(border: OutlineInputBorder(), contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 13)),
                            items: filteredScheds.map((s) {
                              return DropdownMenuItem<String>(
                                value: (s["id"] ?? s["_id"]).toString(),
                                child: Text("${s['class_name']} (${s['start_time']})", overflow: TextOverflow.ellipsis),
                              );
                            }).toList(),
                            onChanged: (val) {
                              setState(() => _selectedSchedId = val);
                              if (val != null) {
                                final sc = _availableSchedules.firstWhere((s) => (s["id"] ?? s["_id"]).toString() == val);
                                _topicController.text = sc["subject"] ?? "";
                                _loadStudents(sc["class_id"].toString());
                              }
                            },
                          ),
                        )
                      ],
                    ),
                    const SizedBox(height: 25),
                    
                    if (_selectedSchedId != null) ...[
                      // --- 2. ĐIỂM DANH (GIAO DIỆN BẢNG Y HỆT WEB) ---
                      const Text("2. Điểm danh lớp học", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                      
                      // Thông báo nếu dùng dữ liệu Demo
                      if (_students.isNotEmpty && _students.first["Mã HS"].toString().contains("DEMO"))
                        Container(
                          margin: const EdgeInsets.symmetric(vertical: 10),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
                          child: Row(
                            children: [
                              const Icon(Icons.info, color: Colors.blue),
                              const SizedBox(width: 10),
                              Expanded(child: Text("Lớp học này chưa có học sinh thật. Hệ thống kích hoạt dữ liệu mẫu.", style: TextStyle(color: Colors.blue.shade800))),
                            ],
                          ),
                        ),

                      const SizedBox(height: 10),
                      // Bọc Data Table trong SingleChildScrollView để vuốt ngang
                      Container(
                        decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(8)),
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: DataTable(
                            headingRowColor: MaterialStateProperty.all(Colors.blueGrey.shade50),
                            columnSpacing: 25,
                            columns: const [
                              DataColumn(label: Text("Mã HS", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Tên Học Sinh", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Có mặt", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Vắng", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Đi trễ", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Nhận Xét (Tùy chọn)", style: TextStyle(fontWeight: FontWeight.bold))),
                            ],
                            rows: _students.map((st) {
                              String sid = (st["Mã HS"] ?? st["id"]).toString();
                              return DataRow(
                                cells: [
                                  DataCell(Text(sid)),
                                  DataCell(Text(st["Tên Học Sinh"] ?? st["name"] ?? "")),
                                  // Checkbox Có mặt
                                  DataCell(Checkbox(
                                    activeColor: Colors.green,
                                    value: _attendanceStates[sid] == "present",
                                    onChanged: (val) => setState(() => _attendanceStates[sid] = "present"),
                                  )),
                                  // Checkbox Vắng
                                  DataCell(Checkbox(
                                    activeColor: Colors.red,
                                    value: _attendanceStates[sid] == "absent",
                                    onChanged: (val) => setState(() => _attendanceStates[sid] = "absent"),
                                  )),
                                  // Checkbox Đi trễ
                                  DataCell(Checkbox(
                                    activeColor: Colors.orange,
                                    value: _attendanceStates[sid] == "late",
                                    onChanged: (val) => setState(() => _attendanceStates[sid] = "late"),
                                  )),
                                  // Nhập nhận xét
                                  DataCell(
                                    SizedBox(
                                      width: 200, // Chiều rộng cố định cho ô Textfield trong bảng
                                      child: TextFormField(
                                        controller: _noteControllers[sid],
                                        decoration: const InputDecoration(isDense: true, border: OutlineInputBorder()),
                                      ),
                                    )
                                  )
                                ]
                              );
                            }).toList(),
                          ),
                        ),
                      ),
                      
                      const SizedBox(height: 30),
                      // --- 3. NHẬT KÝ BÀI GIẢNG ---
                      const Text("3. Nhật ký giảng dạy", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                      const SizedBox(height: 15),
                      TextFormField(
                        controller: _topicController,
                        decoration: const InputDecoration(labelText: "Chủ đề giảng dạy (*)", border: OutlineInputBorder()),
                        validator: (v) => v!.trim().isEmpty ? "Không được bỏ trống" : null,
                      ),
                      
                      const SizedBox(height: 15),
                      // Chọn Video
                      ExpansionTile(
                        title: const Text("Video Bài Tập Đã Dùng", style: TextStyle(fontWeight: FontWeight.bold)),
                        collapsedShape: RoundedRectangleBorder(side: BorderSide(color: Colors.grey.shade400), borderRadius: BorderRadius.circular(5)),
                        shape: RoundedRectangleBorder(side: BorderSide(color: Colors.blueGrey), borderRadius: BorderRadius.circular(5)),
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(8.0),
                            child: _allVideos.isEmpty 
                              ? const Text("Chưa có video nào trong kho học liệu")
                              : Wrap(
                                  spacing: 8,
                                  children: _allVideos.map((v) {
                                    String vId = v["id"].toString();
                                    return FilterChip(
                                      label: Text(v["title"] ?? "Video"),
                                      selected: _selectedVideos.contains(vId),
                                      selectedColor: Colors.blue.shade100,
                                      onSelected: (bool selected) {
                                        setState(() {
                                          if (selected) _selectedVideos.add(vId);
                                          else _selectedVideos.remove(vId);
                                        });
                                      }
                                    );
                                  }).toList()
                                ),
                          )
                        ],
                      ),
                      
                      const SizedBox(height: 15),
                      // Chọn Quiz / Bài tập
                      ExpansionTile(
                        title: const Text("Giao Bài Tập Về Nhà", style: TextStyle(fontWeight: FontWeight.bold)),
                        collapsedShape: RoundedRectangleBorder(side: BorderSide(color: Colors.grey.shade400), borderRadius: BorderRadius.circular(5)),
                        shape: RoundedRectangleBorder(side: BorderSide(color: Colors.blueGrey), borderRadius: BorderRadius.circular(5)),
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(8.0),
                            child: _allQuizzes.isEmpty 
                              ? const Text("Chưa có bộ đề nào trong kho")
                              : Wrap(
                                  spacing: 8,
                                  children: _allQuizzes.map((q) {
                                    String qId = q["id"].toString();
                                    return FilterChip(
                                      label: Text(q["title"] ?? "Quiz"),
                                      selected: _selectedQuizzes.contains(qId),
                                      selectedColor: Colors.orange.shade100,
                                      onSelected: (bool selected) {
                                        setState(() {
                                          if (selected) _selectedQuizzes.add(qId);
                                          else _selectedQuizzes.remove(qId);
                                        });
                                      }
                                    );
                                  }).toList()
                                ),
                          )
                        ],
                      ),

                      const SizedBox(height: 15),
                      TextFormField(
                        controller: _notesController,
                        maxLines: 4,
                        decoration: const InputDecoration(labelText: "Chi Tiết Nội Dung Giảng Dạy (*)", border: OutlineInputBorder(), alignLabelWithHint: true),
                        validator: (v) => v!.trim().isEmpty ? "Không được bỏ trống" : null,
                      ),
                      
                      const SizedBox(height: 25),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.send),
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.blueGrey, foregroundColor: Colors.white, minimumSize: const Size(double.infinity, 55)),
                        onPressed: _submitJournal,
                        label: const Text("LƯU & GỬI BÁO CÁO", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      )
                    ]
                  ],
                ),
              ),
            ),
    );
  }
}