import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart';
import '../../core/config.dart';

class OperatorScheduleScreen extends StatefulWidget {
  const OperatorScheduleScreen({super.key});

  @override
  State<OperatorScheduleScreen> createState() => _OperatorScheduleScreenState();
}

class _OperatorScheduleScreenState extends State<OperatorScheduleScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";
  String _token = "";
  String _userId = "";

  List<dynamic> _teachers = [];
  List<dynamic> _classes = [];
  List<dynamic> _schedules = [];

  // Form Controllers
  final _subjectCtrl = TextEditingController();
  final _roomCtrl = TextEditingController(text: "Online");
  String? _selectedClassId;
  String? _selectedTeacherId;
  DateTime _startDate = DateTime.now();
  DateTime _endDate = DateTime.now().add(const Duration(days: 90));
  String _startTime = "18:00";
  String _endTime = "19:30";
  bool _isPublic = true;
  List<String> _selectedDays = [];

  final List<String> _daysVi = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];
  final List<String> _daysEn = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  // Tạo danh sách khung giờ từ 07:00 đến 21:30
  final List<String> _timeSlots = List.generate(29, (index) {
    int hour = 7 + (index ~/ 2);
    int minute = (index % 2) * 30;
    return "${hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')}";
  });

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Xếp Lịch Học",
      "tab_create": "Tạo Lịch Mới",
      "tab_list": "Danh Sách Lịch",
      "lbl_class": "Chọn lớp học (*)",
      "lbl_teacher": "Giáo viên giảng dạy (*)",
      "lbl_subject": "Môn học (*)",
      "lbl_room": "Phòng học / Hình thức",
      "lbl_start_date": "Ngày bắt đầu",
      "lbl_end_date": "Ngày kết thúc",
      "lbl_start_time": "Giờ bắt đầu",
      "lbl_end_time": "Giờ kết thúc",
      "lbl_days": "Thứ trong tuần (*)",
      "lbl_public": "Công khai đăng ký",
      "btn_create": "TẠO LỊCH HỌC",
      "success_created": "Đã tạo lịch học thành công!",
      "err_validation": "Vui lòng điền đủ thông tin bắt buộc!",
      "notif_title": "Thay đổi lịch học",
      "msg_reschedule": "Thông báo: Lớp {} đổi lịch sang các ngày {} lúc {}. Phòng: {}.",
    },
    "en": {
      "title": "Class Scheduler",
      "tab_create": "New Schedule",
      "tab_list": "Current Timetables",
      "lbl_class": "Select Class (*)",
      "lbl_teacher": "Assigned Lecturer (*)",
      "lbl_subject": "Subject (*)",
      "lbl_room": "Classroom / Venue",
      "lbl_start_date": "Start Date",
      "lbl_end_date": "End Date",
      "lbl_start_time": "Start Time",
      "lbl_end_time": "End Time",
      "lbl_days": "Weekly Days (*)",
      "lbl_public": "Public Enrollment",
      "btn_create": "GENERATE TIMETABLE",
      "success_created": "Timetable scheduled successfully!",
      "err_validation": "Please fill in all required fields!",
      "notif_title": "Schedule Update",
      "msg_reschedule": "Notice: Class {} rescheduled to {} at {}. Room: {}.",
    }
  };

  @override
  void initState() {
    super.initState();
    _initData();
  }

  Future<void> _initData() async {
    setState(() => _isLoading = true);
    try {
      _token = await _storage.read(key: 'jwt_token') ?? "";
      _userId = await _storage.read(key: 'user_id') ?? "";
      
      await Future.wait([_fetchTeachers(), _fetchClasses(), _fetchSchedules()]);
    } catch (e) {
      debugPrint("Lỗi Init: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _fetchTeachers() async {
    final res = await http.get(Uri.parse('${AppConfig.apiUrl}/api/auth/users'), headers: {"Authorization": "Bearer $_token"});
    if (res.statusCode == 200) {
      final List<dynamic> data = jsonDecode(utf8.decode(res.bodyBytes));
      _teachers = data.where((u) => u['role'].toString().contains('teacher')).toList();
    }
  }

  Future<void> _fetchClasses() async {
    final res = await http.get(Uri.parse('${AppConfig.apiUrl}/classes'));
    if (res.statusCode == 200) _classes = jsonDecode(utf8.decode(res.bodyBytes));
  }

  Future<void> _fetchSchedules() async {
    final res = await http.get(Uri.parse('${AppConfig.apiUrl}/schedule/list'), headers: {"Authorization": "Bearer $_token"});
    if (res.statusCode == 200) _schedules = jsonDecode(utf8.decode(res.bodyBytes));
  }

  // Gửi thông báo tự động cho Phụ huynh & Học sinh
  Future<void> _dispatchNotifications(String classId, String className, String content) async {
    try {
      final res = await http.get(Uri.parse('${AppConfig.apiUrl}/classes/$classId/students/details'), headers: {"Authorization": "Bearer $_token"});
      if (res.statusCode == 200) {
        final List<dynamic> students = jsonDecode(utf8.decode(res.bodyBytes));
        for (var s in students) {
          final payload = {
            "sender_id": _userId,
            "sender_role": "operator",
            "sender_name": "Bộ phận Vận hành",
            "receiver_id": s['Mã HS'],
            "receiver_role": "student",
            "type": "schedule",
            "title": _labels[_lang]!['notif_title'],
            "content": content
          };
          await http.post(Uri.parse('${AppConfig.apiUrl}/api/notifications/send'), headers: {"Content-Type": "application/json"}, body: jsonEncode(payload));
          
          payload["receiver_role"] = "parent";
          payload["receiver_id"] = "all"; // Backend sẽ tự phân giải sang phụ huynh của học sinh này
          await http.post(Uri.parse('${AppConfig.apiUrl}/api/notifications/send'), headers: {"Content-Type": "application/json"}, body: jsonEncode(payload));
        }
      }
    } catch (e) { debugPrint("Lỗi gửi tin: $e"); }
  }

  Future<void> _submitCreate() async {
    if (_selectedClassId == null || _selectedTeacherId == null || _subjectCtrl.text.isEmpty || _selectedDays.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['err_validation']!), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isLoading = true);
    final cls = _classes.firstWhere((c) => c['id'] == _selectedClassId);
    final teacher = _teachers.firstWhere((t) => t['id'] == _selectedTeacherId);

    final payload = {
      "class_id": _selectedClassId,
      "class_name": cls['class_name'],
      "subject": _subjectCtrl.text.trim(),
      "is_public": _isPublic,
      "teacher_id": cls['teacher_id'],
      "teacher_name": cls['teacher_name'],
      "teaching_teacher_id": _selectedTeacherId,
      "teaching_teacher_name": teacher['full_name'] ?? teacher['name'],
      "study_date": "${DateFormat('dd/MM/yyyy').format(_startDate)} đến ${DateFormat('dd/MM/yyyy').format(_endDate)}",
      "days_of_week": _selectedDays,
      "start_time": _startTime,
      "end_time": _endTime,
      "room": _roomCtrl.text.trim(),
      "status": "active"
    };

    final res = await http.post(Uri.parse('${AppConfig.apiUrl}/schedule/create'), headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"}, body: jsonEncode(payload));

    if (res.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['success_created']!), backgroundColor: Colors.green));
      _initData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          backgroundColor: Colors.indigo,
          foregroundColor: Colors.white,
          bottom: TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white60,
            indicatorColor: Colors.amber,
            tabs: [
              Tab(icon: const Icon(Icons.edit_calendar), text: labels["tab_create"]),
              Tab(icon: const Icon(Icons.list_alt), text: labels["tab_list"]),
            ],
          ),
        ),
        body: _isLoading 
          ? const Center(child: CircularProgressIndicator(color: Colors.indigo))
          : TabBarView(
              children: [
                _buildCreateForm(labels),
                _buildScheduleList(labels),
              ],
            ),
      ),
    );
  }

  Widget _buildCreateForm(Map<String, String> labels) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<String>(
                decoration: InputDecoration(labelText: labels["lbl_class"]),
                items: _classes.map((c) => DropdownMenuItem(value: c['id'].toString(), child: Text(c['class_name']))).toList(),
                onChanged: (val) => setState(() => _selectedClassId = val),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                decoration: InputDecoration(labelText: labels["lbl_teacher"]),
                items: _teachers.map((t) => DropdownMenuItem(value: t['id'].toString(), child: Text(t['full_name'] ?? t['name']))).toList(),
                onChanged: (val) => setState(() => _selectedTeacherId = val),
              ),
              const SizedBox(height: 10),
              TextField(controller: _subjectCtrl, decoration: InputDecoration(labelText: labels["lbl_subject"])),
              const SizedBox(height: 10),
              TextField(controller: _roomCtrl, decoration: InputDecoration(labelText: labels["lbl_room"])),
              const SizedBox(height: 15),
              const Text("Lịch học trong tuần:", style: TextStyle(fontWeight: FontWeight.bold)),
              Wrap(
                spacing: 8,
                children: _daysVi.map((day) {
                  bool isSelected = _selectedDays.contains(day);
                  return FilterChip(
                    label: Text(day, style: TextStyle(fontSize: 12, color: isSelected ? Colors.white : Colors.black)),
                    selected: isSelected,
                    selectedColor: Colors.indigo,
                    onSelected: (bool selected) {
                      setState(() {
                        if (selected) _selectedDays.add(day);
                        else _selectedDays.remove(day);
                      });
                    },
                  );
                }).toList(),
              ),
              const SizedBox(height: 15),
              Row(
                children: [
                  Expanded(child: DropdownButtonFormField<String>(value: _startTime, items: _timeSlots.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(), onChanged: (v) => setState(() => _startTime = v!), decoration: InputDecoration(labelText: labels["lbl_start_time"]))),
                  const SizedBox(width: 10),
                  Expanded(child: DropdownButtonFormField<String>(value: _endTime, items: _timeSlots.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(), onChanged: (v) => setState(() => _endTime = v!), decoration: InputDecoration(labelText: labels["lbl_end_time"]))),
                ],
              ),
              const SizedBox(height: 15),
              CheckboxListTile(title: Text(labels["lbl_public"]!), value: _isPublic, onChanged: (v) => setState(() => _isPublic = v!), activeColor: Colors.indigo),
              const SizedBox(height: 20),
              SizedBox(width: double.infinity, height: 45, child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white), onPressed: _submitCreate, child: Text(labels["btn_create"]!))),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildScheduleList(Map<String, String> labels) {
    if (_schedules.isEmpty) return const Center(child: Text("Chưa có lịch học nào."));
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _schedules.length,
      itemBuilder: (context, index) {
        final item = _schedules[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ExpansionTile(
            leading: const Icon(Icons.calendar_today, color: Colors.indigo),
            title: Text(item['class_name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text("${item['subject']} | ${item['start_time']} - ${item['end_time']}"),
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("Phòng: ${item['room']}"),
                    Text("Ngày: ${item['study_date']}"),
                    Text("Thứ: ${item['days_of_week'].join(', ')}"),
                    Text("GV: ${item['teaching_teacher_name']}"),
                    const Divider(),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton.icon(icon: const Icon(Icons.delete, color: Colors.red), label: const Text("Xóa", style: TextStyle(color: Colors.red)), onPressed: () async {
                          final res = await http.delete(Uri.parse('${AppConfig.apiUrl}/schedule/${item['id']}'), headers: {"Authorization": "Bearer $_token"});
                          if (res.statusCode == 200) _initData();
                        }),
                      ],
                    )
                  ],
                ),
              )
            ],
          ),
        );
      },
    );
  }
}