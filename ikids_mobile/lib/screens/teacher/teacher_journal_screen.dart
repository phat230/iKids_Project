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
  String _lang = "vi";

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Nhật Ký & Điểm Danh",
      "sec_1": "1. Lựa chọn ca dạy",
      "hint_sched": "Chọn ca dạy...",
      "sec_2": "2. Điểm danh lớp học",
      "msg_demo": "Lớp học này chưa có học sinh thật. Hệ thống kích hoạt dữ liệu mẫu.",
      "col_id": "Mã HS",
      "col_name": "Tên Học Sinh",
      "col_present": "Có mặt",
      "col_absent": "Vắng",
      "col_late": "Đi trễ",
      "col_note": "Nhận Xét (Tùy chọn)",
      "sec_3": "3. Nhật ký giảng dạy",
      "lbl_topic": "Chủ đề giảng dạy (*)",
      "err_empty": "Không được bỏ trống",
      "lbl_video": "Video Bài Tập Đã Dùng",
      "msg_no_video": "Chưa có video nào trong kho học liệu",
      "lbl_quiz": "Giao Bài Tập Về Nhà",
      "msg_no_quiz": "Chưa có bộ đề nào trong kho",
      "lbl_content": "Chi Tiết Nội Dung Giảng Dạy (*)",
      "btn_submit": "LƯU & GỬI BÁO CÁO",
      "msg_success": "Lưu nhật ký và báo cáo thành công!",
      "msg_fail": "Lỗi hệ thống",
      "msg_err_conn": "Mất kết nối máy chủ."
    },
    "en": {
      "title": "Journal & Attendance",
      "sec_1": "1. Select Teaching Session",
      "hint_sched": "Select session...",
      "sec_2": "2. Class Attendance",
      "msg_demo": "No real students in this class. Demo data activated.",
      "col_id": "Student ID",
      "col_name": "Student Name",
      "col_present": "Present",
      "col_absent": "Absent",
      "col_late": "Late",
      "col_note": "Remarks (Optional)",
      "sec_3": "3. Teaching Journal",
      "lbl_topic": "Teaching Topic (*)",
      "err_empty": "Cannot be empty",
      "lbl_video": "Used Video Resources",
      "msg_no_video": "No videos in the repository",
      "lbl_quiz": "Assign Homework (Quiz)",
      "msg_no_quiz": "No quizzes in the repository",
      "lbl_content": "Teaching Content Details (*)",
      "btn_submit": "SAVE & SUBMIT REPORT",
      "msg_success": "Journal and report saved successfully!",
      "msg_fail": "System error",
      "msg_err_conn": "Server connection lost."
    }
  };

  @override
  void initState() {
    super.initState();
    _initialLoad();
  }

  Future<void> _initialLoad() async {
    String? savedLang = await _storage.read(key: 'app_lang');
    if (savedLang != null) setState(() => _lang = savedLang);

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
      
      final schedRes = await http.get(Uri.parse('${AppConfig.apiTv1}/schedule/list'), headers: {"Authorization": "Bearer $token"});
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
      debugPrint("Lỗi kết nối: $e");
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
          _attendanceStates[sid] = "present";
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
    final labels = _locales[_lang]!;
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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_success"]!), backgroundColor: Colors.green));
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("${labels["msg_fail"]!}: ${res.body}"), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_err_conn"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;
    final dayNames = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
    String currentWeekday = dayNames[_selectedDate.weekday % 7];
    
    List<dynamic> filteredScheds = _availableSchedules.where((s) {
      List<dynamic> dOW = s["days_of_week"] ?? [];
      return dOW.contains(currentWeekday);
    }).toList();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold)), backgroundColor: Colors.blueGrey, foregroundColor: Colors.white),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.blueGrey))
          : Form(
              key: _formKey,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(labels["sec_1"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
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
                            hint: Text(labels["hint_sched"]!),
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
                      Text(labels["sec_2"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                      
                      if (_students.isNotEmpty && _students.first["Mã HS"].toString().contains("DEMO"))
                        Container(
                          margin: const EdgeInsets.symmetric(vertical: 10),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
                          child: Row(
                            children: [
                              const Icon(Icons.info, color: Colors.blue),
                              const SizedBox(width: 10),
                              Expanded(child: Text(labels["msg_demo"]!, style: TextStyle(color: Colors.blue.shade800))),
                            ],
                          ),
                        ),

                      const SizedBox(height: 10),
                      Container(
                        decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(8)),
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: DataTable(
                            headingRowColor: MaterialStateProperty.all(Colors.blueGrey.shade50),
                            columnSpacing: 25,
                            columns: [
                              DataColumn(label: Text(labels["col_id"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text(labels["col_name"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text(labels["col_present"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text(labels["col_absent"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text(labels["col_late"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text(labels["col_note"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                            ],
                            rows: _students.map((st) {
                              String sid = (st["Mã HS"] ?? st["id"]).toString();
                              return DataRow(
                                cells: [
                                  DataCell(Text(sid)),
                                  DataCell(Text(st["Tên Học Sinh"] ?? st["name"] ?? "")),
                                  DataCell(Checkbox(
                                    activeColor: Colors.green,
                                    value: _attendanceStates[sid] == "present",
                                    onChanged: (val) => setState(() => _attendanceStates[sid] = "present"),
                                  )),
                                  DataCell(Checkbox(
                                    activeColor: Colors.red,
                                    value: _attendanceStates[sid] == "absent",
                                    onChanged: (val) => setState(() => _attendanceStates[sid] = "absent"),
                                  )),
                                  DataCell(Checkbox(
                                    activeColor: Colors.orange,
                                    value: _attendanceStates[sid] == "late",
                                    onChanged: (val) => setState(() => _attendanceStates[sid] = "late"),
                                  )),
                                  DataCell(
                                    SizedBox(
                                      width: 200,
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
                      Text(labels["sec_3"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                      const SizedBox(height: 15),
                      TextFormField(
                        controller: _topicController,
                        decoration: InputDecoration(labelText: labels["lbl_topic"], border: const OutlineInputBorder()),
                        validator: (v) => v!.trim().isEmpty ? labels["err_empty"] : null,
                      ),
                      
                      const SizedBox(height: 15),
                      ExpansionTile(
                        title: Text(labels["lbl_video"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
                        collapsedShape: RoundedRectangleBorder(side: BorderSide(color: Colors.grey.shade400), borderRadius: BorderRadius.circular(5)),
                        shape: RoundedRectangleBorder(side: const BorderSide(color: Colors.blueGrey), borderRadius: BorderRadius.circular(5)),
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(8.0),
                            child: _allVideos.isEmpty 
                              ? Text(labels["msg_no_video"]!)
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
                      ExpansionTile(
                        title: Text(labels["lbl_quiz"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
                        collapsedShape: RoundedRectangleBorder(side: BorderSide(color: Colors.grey.shade400), borderRadius: BorderRadius.circular(5)),
                        shape: RoundedRectangleBorder(side: const BorderSide(color: Colors.blueGrey), borderRadius: BorderRadius.circular(5)),
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(8.0),
                            child: _allQuizzes.isEmpty 
                              ? Text(labels["msg_no_quiz"]!)
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
                        decoration: InputDecoration(labelText: labels["lbl_content"], border: const OutlineInputBorder(), alignLabelWithHint: true),
                        validator: (v) => v!.trim().isEmpty ? labels["err_empty"] : null,
                      ),
                      
                      const SizedBox(height: 25),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.send),
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.blueGrey, foregroundColor: Colors.white, minimumSize: const Size(double.infinity, 55)),
                        onPressed: _submitJournal,
                        label: Text(labels["btn_submit"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      )
                    ]
                  ],
                ),
              ),
            ),
    );
  }
}