import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key});

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  final _storage = const FlutterSecureStorage();

  bool _isLoading = true;
  String _lang = "vi"; 
  String _selectedDay = "Thứ 2"; 

  List<dynamic> _mySchedules = [];

  final List<Map<String, String>> _daysOfWeek = [
    {"vi": "Thứ 2", "en": "Mon"},
    {"vi": "Thứ 3", "en": "Tue"},
    {"vi": "Thứ 4", "en": "Wed"},
    {"vi": "Thứ 5", "en": "Thu"},
    {"vi": "Thứ 6", "en": "Fri"},
    {"vi": "Thứ 7", "en": "Sat"},
    {"vi": "Chủ Nhật", "en": "Sun"},
  ];

  final List<Map<String, String>> _timeSlots = [
    {"slot": "Ca 1", "time": "07:30 - 09:00"},
    {"slot": "Ca 2", "time": "09:00 - 10:30"},
    {"slot": "Ca 3", "time": "10:30 - 12:00"},
    {"slot": "Ca 4", "time": "13:00 - 14:30"},
    {"slot": "Ca 5", "time": "14:30 - 16:00"},
    {"slot": "Ca 6", "time": "16:00 - 17:30"},
    {"slot": "Ca 7", "time": "17:30 - 19:00"},
  ];

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "📅 Thời Khóa Biểu Của Tôi",
      "subtitle": "Theo dõi lịch học để không bỏ lỡ buổi học nào nhé!",
      "lbl_teacher": "Giáo viên:",
      "lbl_room": "Phòng:",
      "free_slot": "Ca học trống",
      "sec_timeline": "🕒 Khung Giờ Học Hôm Nay",
      "sec_table": "📊 Bảng Chi Tiết Thời Khóa Biểu (Bản Web)",
      "caption_footer": "💡 Lịch học sẽ tự động cập nhật nếu có thay đổi.",
      "col_subject": "Môn học",
      "col_class": "Tên lớp",
      "col_teacher_head": "Giáo viên",
      "col_days": "Thứ",
      "col_slot": "Ca học",
      "col_duration_head": "Khóa học",
      "col_room_head": "Phòng học",
      "col_status": "Trạng thái",
      "status_ongoing": "🟢 Đang diễn ra",
      "status_completed": "🔴 Đã kết thúc",
      "empty_schedule": "Chưa có lịch học nào.",
    },
    "en": {
      "title": "📅 My Class Schedule",
      "subtitle": "Keep track of your classes and never miss a lesson!",
      "lbl_teacher": "Teacher:",
      "lbl_room": "Room:",
      "free_slot": "Free Slot",
      "sec_timeline": "🕒 Today's Time Slots",
      "sec_table": "📊 Detailed Schedule Table",
      "caption_footer": "💡 Your schedule updates automatically.",
      "col_subject": "Subject",
      "col_class": "Class",
      "col_teacher_head": "Teacher",
      "col_days": "Days",
      "col_slot": "Time Slot",
      "col_duration_head": "Duration",
      "col_room_head": "Room",
      "col_status": "Status",
      "status_ongoing": "🟢 Ongoing",
      "status_completed": "🔴 Completed",
      "empty_schedule": "No schedule available.",
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchMyScheduleData();
  }

  Future<void> _fetchMyScheduleData() async {
    try {
      // ĐỒNG BỘ NGÔN NGỮ TỪ BỘ NHỚ
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      String? token = await _storage.read(key: 'jwt_token');
      String? studentId = await _storage.read(key: 'user_id');

      if (studentId == null) return;

      final classResponse = await http.get(Uri.parse('${AppConfig.apiTv1}/classes')).timeout(const Duration(seconds: 10));
      if (classResponse.statusCode != 200) return;
      List<dynamic> allClasses = jsonDecode(utf8.decode(classResponse.bodyBytes));

      List<String> myClassIds = [];
      for (var c in allClasses) {
        List<dynamic> studentsInClass = c['student_ids'] ?? [];
        if (studentsInClass.contains(studentId)) {
          myClassIds.add((c['id'] ?? c['_id']).toString());
        }
      }

      if (myClassIds.isEmpty) {
        setState(() => _isLoading = false);
        return;
      }

      final scheduleResponse = await http.get(
        Uri.parse('${AppConfig.apiTv1}/schedule/list'),
        headers: {"Authorization": "Bearer $token"},
      ).timeout(const Duration(seconds: 10));

      if (scheduleResponse.statusCode == 200) {
        List<dynamic> allSchedules = jsonDecode(utf8.decode(scheduleResponse.bodyBytes));
        setState(() {
          _mySchedules = allSchedules.where((s) => myClassIds.contains(s['class_id']) && s['status'] == 'active').toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint("Lỗi tải lịch học: $e");
      setState(() => _isLoading = false);
    }
  }

  String _calculateStatus(Map<String, dynamic> s) {
    try {
      final now = DateTime.now();
      final endTimeStr = s['end_time'] ?? '23:59';
      String studyDateStr = s['study_date'] ?? '';
      
      String endDateStr = '';
      if (studyDateStr.contains('đến')) {
        endDateStr = studyDateStr.split('đến')[1].trim();
      } else if (studyDateStr.contains('to')) {
        endDateStr = studyDateStr.split('to')[1].trim();
      } else {
        endDateStr = studyDateStr.trim();
      }

      List<String> dateParts;
      if (endDateStr.contains('/')) {
        dateParts = endDateStr.split('/');
        final endDateTime = DateTime(int.parse(dateParts[2]), int.parse(dateParts[1]), int.parse(dateParts[0]), int.parse(endTimeStr.split(':')[0]), int.parse(endTimeStr.split(':')[1]));
        return now.isAfter(endDateTime) ? _labels[_lang]!["status_completed"]! : _labels[_lang]!["status_ongoing"]!;
      }
      return _labels[_lang]!["status_ongoing"]!;
    } catch (e) {
      return _labels[_lang]!["status_ongoing"]!;
    }
  }

  Map<String, dynamic>? _getClassForSlot(String day, String timeRange) {
    String startStr = timeRange.split(" - ")[0].trim();
    for (var s in _mySchedules) {
      List<dynamic> daysInWeek = s['days_of_week'] ?? [];
      String scheduleStartTime = s['start_time'] ?? "";
      if (daysInWeek.contains(day) && scheduleStartTime.startsWith(startStr.substring(0, 5))) {
        return s;
      }
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(labels["title"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          TextButton(
            onPressed: () async {
              setState(() => _lang = _lang == "vi" ? "en" : "vi");
              await _storage.write(key: 'app_lang', value: _lang); // LƯU NGÔN NGỮ KHI ĐỔI
            },
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.blue))
          : SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: double.infinity,
                    color: Colors.blue,
                    padding: const EdgeInsets.only(left: 16, right: 16, bottom: 16),
                    child: Text(labels["subtitle"]!, style: const TextStyle(color: Colors.white70, fontSize: 13)),
                  ),

                  // 1. THANH CHỌN THỨ NGANG
                  Container(
                    height: 65,
                    color: Colors.white,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      itemCount: _daysOfWeek.length,
                      itemBuilder: (context, index) {
                        String dayVi = _daysOfWeek[index]["vi"]!;
                        String dayDisplay = _lang == "vi" ? dayVi : _daysOfWeek[index]["en"]!;
                        bool isSelected = _selectedDay == dayVi;

                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 5),
                          child: InkWell(
                            onTap: () => setState(() => _selectedDay = dayVi),
                            borderRadius: BorderRadius.circular(12),
                            child: Container(
                              width: 65,
                              decoration: BoxDecoration(
                                color: isSelected ? Colors.blue : Colors.blue.withOpacity(0.05),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: isSelected ? Colors.blue : Colors.blue.withOpacity(0.15)),
                              ),
                              child: Center(
                                child: Text(
                                  dayDisplay,
                                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: isSelected ? Colors.white : Colors.blue[800]),
                                ),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),

                  Padding(
                    padding: const EdgeInsets.only(left: 16, top: 15, bottom: 5),
                    child: Text(labels["sec_timeline"]!, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                  ),

                  // 2. TIMELINE CÁC CA HỌC THEO NGÀY ĐÃ CHỌN
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    itemCount: _timeSlots.length,
                    itemBuilder: (context, index) {
                      final slotInfo = _timeSlots[index];
                      final matchClass = _getClassForSlot(_selectedDay, slotInfo["time"]!);

                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4.0),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 90,
                              padding: const EdgeInsets.symmetric(vertical: 10),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(slotInfo["slot"]!.replaceFirst("Ca", _lang == "en" ? "Slot" : "Ca"), style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey, fontSize: 13)),
                                  Text(slotInfo["time"]!, style: TextStyle(color: Colors.grey[600], fontSize: 11)),
                                ],
                              ),
                            ),
                            Expanded(
                              child: matchClass != null
                                  ? Card(
                                      elevation: 2,
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10), side: const BorderSide(color: Colors.blueAccent, width: 1)),
                                      child: Padding(
                                        padding: const EdgeInsets.all(10.0),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Expanded(child: Text(matchClass['subject'] ?? "", maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.blueAccent))),
                                                Text(matchClass['class_name'] ?? "", style: TextStyle(fontSize: 11, color: Colors.green[800], fontWeight: FontWeight.bold)),
                                              ],
                                            ),
                                            const SizedBox(height: 4),
                                            Text("👤 ${labels['lbl_teacher']} ${matchClass['teacher_name'] ?? 'Đang xếp'}", style: const TextStyle(fontSize: 12)),
                                            Text("🏫 ${labels['lbl_room']} ${matchClass['room'] ?? 'Online'}", style: const TextStyle(fontSize: 12)),
                                          ],
                                        ),
                                      ),
                                    )
                                  : Card(
                                      elevation: 0,
                                      color: Colors.grey[100],
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10), side: BorderSide(color: Colors.grey.withOpacity(0.2))),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 12),
                                        child: Text(labels["free_slot"]!, style: TextStyle(color: Colors.grey[400], fontStyle: FontStyle.italic, fontSize: 12)),
                                      ),
                                    ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),

                  const Divider(height: 35, thickness: 1),

                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(labels["sec_table"]!, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.indigo)),
                  ),
                  const SizedBox(height: 10),

                  // 3. BẢNG CHI TIẾT
                  _mySchedules.isEmpty
                      ? Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Text(labels["empty_schedule"]!, style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic)),
                        )
                      : Container(
                          margin: const EdgeInsets.symmetric(horizontal: 14),
                          decoration: BoxDecoration(color: Colors.white, border: Border.all(color: Colors.grey.withOpacity(0.3)), borderRadius: BorderRadius.circular(8)),
                          child: SingleChildScrollView(
                            scrollDirection: Axis.horizontal, 
                            child: DataTable(
                              headingRowColor: MaterialStateProperty.all(Colors.blue.withOpacity(0.1)),
                              columnSpacing: 20,
                              horizontalMargin: 12,
                              columns: [
                                DataColumn(label: Text(labels["col_subject"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(labels["col_class"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(labels["col_teacher_head"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(labels["col_days"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(labels["col_slot"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(labels["col_duration_head"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(labels["col_room_head"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(labels["col_status"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                              ],
                              rows: _mySchedules.map((s) {
                                List<dynamic> daysList = s['days_of_week'] ?? [];
                                
                                // Dịch ngôn ngữ các "Thứ" trong tuần cho Data Table
                                String daysStr = daysList.map((d) {
                                  if (_lang == "en") {
                                    final match = _daysOfWeek.firstWhere((element) => element["vi"] == d, orElse: () => {"en": d.toString()});
                                    return match["en"];
                                  }
                                  return d.toString();
                                }).join(", ");

                                String timeStr = "${s['start_time'] ?? '--:--'} - ${s['end_time'] ?? '--:--'}";
                                String status = _calculateStatus(s);

                                return DataRow(cells: [
                                  DataCell(Text(s['subject'] ?? "N/A")),
                                  DataCell(Text(s['class_name'] ?? "N/A")),
                                  DataCell(Text(s['teacher_name'] ?? "N/A")),
                                  DataCell(Text(daysStr)),
                                  DataCell(Text(timeStr)),
                                  DataCell(Text(s['study_date'] ?? "N/A")),
                                  DataCell(Text(s['room'] ?? "Online")),
                                  DataCell(
                                    Text(
                                      status,
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        color: status.contains("🟢") ? Colors.green : Colors.red,
                                      ),
                                    ),
                                  ),
                                ]);
                              }).toList(),
                            ),
                          ),
                        ),
                  
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(labels["caption_footer"]!, style: TextStyle(fontSize: 11, color: Colors.grey[500], fontStyle: FontStyle.italic)),
                  ),
                ],
              ),
            ),
    );
  }
}