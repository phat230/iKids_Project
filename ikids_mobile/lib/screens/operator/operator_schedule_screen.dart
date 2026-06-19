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
  
  // Tạo danh sách khung giờ từ 07:00 đến 21:30
  final List<String> _timeSlots = List.generate(29, (index) {
    int hour = 7 + (index ~/ 2);
    int minute = (index % 2) * 30;
    return "${hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')}";
  });

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Xếp Lịch Học",
      "tab_create": "Tạo Lịch Học Mới",
      "tab_list": "Danh Sách Lịch",
      "lbl_class": "Chọn lớp học (*)",
      "lbl_teacher": "Giáo viên giảng dạy (*)",
      "lbl_subject": "Môn học (*)",
      "lbl_room": "Phòng học / Hình thức",
      "lbl_start_date": "Ngày bắt đầu",
      "lbl_end_date": "Ngày kết thúc",
      "lbl_start_time": "Giờ bắt đầu",
      "lbl_end_time": "Giờ kết thúc",
      "lbl_days": "Lịch học trong tuần (*)",
      "lbl_public": "Mở lớp (Công khai cho phụ huynh đăng ký)",
      "btn_create": "TẠO LỊCH HỌC",
      "success_created": "Đã tạo lịch học thành công!",
      "err_validation": "Vui lòng điền đủ thông tin bắt buộc!",
      "notif_title": "Thay đổi lịch học",
      "msg_reschedule": "Thông báo: Lớp {} đổi lịch sang các ngày {} lúc {}. Phòng: {}.",
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
    final res = await http.get(Uri.parse('${AppConfig.apiTv1}/teachers'), headers: {"Authorization": "Bearer $_token"});
    if (res.statusCode == 200) {
      final List<dynamic> data = jsonDecode(utf8.decode(res.bodyBytes));
      _teachers = data;
    } else {
      final authRes = await http.get(Uri.parse('${AppConfig.apiAuth}/users'), headers: {"Authorization": "Bearer $_token"});
      if (authRes.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(authRes.bodyBytes));
        _teachers = data.where((u) => u['role'].toString().contains('teacher')).toList();
      }
    }
  }

  Future<void> _fetchClasses() async {
    final res = await http.get(Uri.parse('${AppConfig.apiTv1}/classes'));
    if (res.statusCode == 200) _classes = jsonDecode(utf8.decode(res.bodyBytes));
  }

  Future<void> _fetchSchedules() async {
    final res = await http.get(Uri.parse('${AppConfig.apiTv1}/schedule/list'), headers: {"Authorization": "Bearer $_token"});
    if (res.statusCode == 200) _schedules = jsonDecode(utf8.decode(res.bodyBytes));
  }

  Future<void> _submitCreate() async {
    if (_selectedClassId == null || _selectedTeacherId == null || _subjectCtrl.text.isEmpty || _selectedDays.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['err_validation']!), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isLoading = true);
    final cls = _classes.firstWhere((c) => (c['id'] ?? c['_id']).toString() == _selectedClassId);
    final teacher = _teachers.firstWhere((t) => (t['id'] ?? t['_id']).toString() == _selectedTeacherId);

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

    final res = await http.post(
      Uri.parse('${AppConfig.apiTv1}/schedule/create'), 
      headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"}, 
      body: jsonEncode(payload)
    );

    if (res.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!['success_created']!), backgroundColor: Colors.green));
      _initData(); 
    } else {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi hệ thống khi tạo lịch"), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.grey.shade100,
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

  // ✅ ĐÃ SỬA: Đập đi xây lại toàn bộ UI form tạo lịch y hệt bản Web
  Widget _buildCreateForm(Map<String, String> labels) {
    
    // Tìm tên Giáo viên phụ trách từ danh sách lớp
    String assignedTeacher = "Chưa phân công";
    if (_selectedClassId != null) {
      final cls = _classes.firstWhere((c) => (c['id'] ?? c['_id']).toString() == _selectedClassId, orElse: () => {});
      assignedTeacher = cls['teacher_name'] ?? "Chưa phân công";
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        elevation: 3,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. CHỌN LỚP HỌC
              Text(labels["lbl_class"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
              const SizedBox(height: 5),
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
                items: _classes.map((c) => DropdownMenuItem(value: (c['id'] ?? c['_id']).toString(), child: Text(c['class_name']))).toList(),
                onChanged: (val) => setState(() => _selectedClassId = val),
              ),
              const SizedBox(height: 15),

              // 2. GIÁO VIÊN PHỤ TRÁCH (Khung xanh giống Web)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.shade100)
                ),
                child: Text(
                  "Giáo viên phụ trách: $assignedTeacher",
                  style: TextStyle(color: Colors.blue.shade800, fontWeight: FontWeight.w600, fontSize: 15),
                ),
              ),
              const SizedBox(height: 20),

              // 3. ROW: GIÁO VIÊN GIẢNG DẠY & MÔN HỌC
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_teacher"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        DropdownButtonFormField<String>(
                          isExpanded: true, // Chống vỡ layout tên dài
                          decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
                          items: _teachers.map((t) => DropdownMenuItem(value: (t['id'] ?? t['_id']).toString(), child: Text(t['full_name'] ?? t['name'], overflow: TextOverflow.ellipsis))).toList(),
                          onChanged: (val) => setState(() => _selectedTeacherId = val),
                        ),
                      ]
                    )
                  ),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_subject"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        TextField(
                          controller: _subjectCtrl, 
                          decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(vertical: 13, horizontal: 10))
                        ),
                      ]
                    )
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 4. ROW: NGÀY BẮT ĐẦU & NGÀY KẾT THÚC (MỚI THÊM)
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_start_date"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
                            alignment: Alignment.centerLeft,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(5))
                          ),
                          onPressed: () async {
                            DateTime? picked = await showDatePicker(context: context, initialDate: _startDate, firstDate: DateTime(2020), lastDate: DateTime(2030));
                            if (picked != null) setState(() => _startDate = picked);
                          },
                          child: Text(DateFormat('yyyy/MM/dd').format(_startDate), style: const TextStyle(color: Colors.black87)),
                        ),
                      ],
                    )
                  ),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_end_date"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
                            alignment: Alignment.centerLeft,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(5))
                          ),
                          onPressed: () async {
                            DateTime? picked = await showDatePicker(context: context, initialDate: _endDate, firstDate: DateTime(2020), lastDate: DateTime(2030));
                            if (picked != null) setState(() => _endDate = picked);
                          },
                          child: Text(DateFormat('yyyy/MM/dd').format(_endDate), style: const TextStyle(color: Colors.black87)),
                        ),
                      ],
                    )
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 5. ROW: GIỜ BẮT ĐẦU & GIỜ KẾT THÚC
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_start_time"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        DropdownButtonFormField<String>(
                          value: _startTime, 
                          items: _timeSlots.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(), 
                          onChanged: (v) => setState(() => _startTime = v!), 
                          decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true)
                        )
                      ]
                    )
                  ),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_end_time"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        DropdownButtonFormField<String>(
                          value: _endTime, 
                          items: _timeSlots.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(), 
                          onChanged: (v) => setState(() => _endTime = v!), 
                          decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true)
                        )
                      ]
                    )
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 6. ROW: LỊCH HỌC TRONG TUẦN & PHÒNG HỌC
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_days"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(color: Colors.grey.shade50, border: Border.all(color: Colors.grey.shade400), borderRadius: BorderRadius.circular(5)),
                          child: Wrap(
                            spacing: 6, runSpacing: -6,
                            children: _daysVi.map((day) {
                              bool isSelected = _selectedDays.contains(day);
                              return FilterChip(
                                label: Text(day, style: TextStyle(fontSize: 12, color: isSelected ? Colors.white : Colors.black87)),
                                selected: isSelected,
                                selectedColor: Colors.blueAccent,
                                showCheckmark: false,
                                onSelected: (bool selected) {
                                  setState(() {
                                    if (selected) _selectedDays.add(day);
                                    else _selectedDays.remove(day);
                                  });
                                },
                              );
                            }).toList(),
                          ),
                        ),
                      ],
                    )
                  ),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["lbl_room"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                        const SizedBox(height: 5),
                        TextField(
                          controller: _roomCtrl, 
                          decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(vertical: 13, horizontal: 10))
                        ),
                      ],
                    ),
                  )
                ],
              ),
              
              const SizedBox(height: 15),
              // 7. CHECKBOX MỞ LỚP
              CheckboxListTile(
                title: Text(labels["lbl_public"]!, style: const TextStyle(fontSize: 14)), 
                value: _isPublic, 
                onChanged: (v) => setState(() => _isPublic = v!), 
                activeColor: Colors.blueAccent,
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
              ),
              
              const SizedBox(height: 20),
              // 8. BUTTON TẠO LỊCH
              SizedBox(
                width: double.infinity, 
                height: 50, 
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), 
                  onPressed: _submitCreate, 
                  child: Text(labels["btn_create"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16))
                )
              ),
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
                        TextButton.icon(
                          icon: const Icon(Icons.delete, color: Colors.red), 
                          label: const Text("Xóa", style: TextStyle(color: Colors.red)), 
                          onPressed: () async {
                            final res = await http.delete(Uri.parse('${AppConfig.apiTv1}/schedule/${item['id']}'), headers: {"Authorization": "Bearer $_token"});
                            if (res.statusCode == 200) _initData();
                          }
                        ),
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