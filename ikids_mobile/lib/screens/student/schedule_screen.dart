import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';
import '../../services/api_service.dart';

class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key});

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  final ApiService _apiService = ApiService();
  final _storage = const FlutterSecureStorage();

  bool _isLoading = true;
  String _lang = "vi"; // Hỗ trợ song ngữ chuẩn kiến trúc giống Web
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

  // Bổ sung các tiêu đề cột bảng dữ liệu tương thích hoàn toàn bản Web Python
  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "📅 Thời Khóa Biểu Của Tôi",
      "subtitle": "Theo dõi lịch học để không bỏ lỡ buổi học nào nhé!",
      "lbl_teacher": "Giáo viên:",
      "lbl_room": "Phòng:",
      "lbl_duration": "Khóa học:",
      "free_slot": "Ca học trống",
      "sec_timeline": "🕒 Khung Giờ Học Hôm Nay",
      "sec_table": "📊 Bảng Chi Tiết Thời Khóa Biểu (Bản Web)",
      "caption_footer": "💡 Lịch học sẽ tự động cập nhật nếu Nhân viên vận hành thay đổi thời gian hoặc phòng học.",
      "col_subject": "Môn học",
      "col_class": "Tên lớp",
      "col_teacher_head": "Giáo viên",
      "col_days": "Thứ",
      "col_slot": "Ca học",
      "col_duration_head": "Khóa học",
      "col_room_head": "Phòng học",
      "col_status": "Trạng thái"
    },
    "en": {
      "title": "📅 My Class Schedule",
      "subtitle": "Keep track of your classes and never miss a single lesson!",
      "lbl_teacher": "Teacher:",
      "lbl_room": "Room:",
      "lbl_duration": "Duration:",
      "free_slot": "Free Slot",
      "sec_timeline": "🕒 Today's Time Slots",
      "sec_table": "📊 Detailed Schedule Table (Web Version)",
      "caption_footer": "💡 Your schedule updates automatically whenever operators change time slots.",
      "col_subject": "Subject",
      "col_class": "Class",
      "col_teacher_head": "Teacher",
      "col_days": "Days",
      "col_slot": "Time Slot",
      "col_duration_head": "Duration",
      "col_room_head": "Room",
      "col_status": "Status"
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchMyScheduleData();
  }

  Future<void> _fetchMyScheduleData() async {
    try {
      String? token = await _storage.read(key: 'jwt_token');
      String? studentId = await _storage.read(key: 'user_id');

      if (studentId == null) throw Exception("Không tìm thấy thông tin học sinh");

      final classResponse = await http.get(Uri.parse('${AppConfig.apiUrl}/classes')).timeout(const Duration(seconds: 10));
      if (classResponse.statusCode != 200) return;
      List<dynamic> allClasses = jsonDecode(utf8.decode(classResponse.bodyBytes));

      List<String> myClassIds = [];
      for (var c in allClasses) {
        List<dynamic> studentsInClass = c['student_ids'] ?? [];
        if (studentsInClass.contains(studentId)) {
          myClassIds.add(c['id'] ?? c['_id']);
        }
      }

      if (myClassIds.isEmpty) {
        setState(() => _isLoading = false);
        return;
      }

      final scheduleResponse = await http.get(
        Uri.parse('${AppConfig.apiUrl}/schedule/list'),
        headers: {"Authorization": "Bearer $token"},
      ).timeout(const Duration(seconds: 10));

      if (scheduleResponse.statusCode == 200) {
        List<dynamic> allSchedules = jsonDecode(utf8.decode(scheduleResponse.bodyBytes));
        
        setState(() {
          _mySchedules = allSchedules.where((s) => 
            myClassIds.contains(s['class_id']) && s['status'] == 'active'
          ).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      print("Lỗi tải lịch học: $e");
      setState(() => _isLoading = false);
    }
  }

  // Hàm tính toán logic Trạng thái lớp học (Đang học / Đã hoàn thành) đồng bộ chính xác với file Python
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
      int day, month, year;
      if (endDateStr.contains('/')) {
        dateParts = endDateStr.split('/');
        day = int.parse(dateParts[0]);
        month = int.parse(dateParts[1]);
        year = int.parse(dateParts[2]);
      } else {
        dateParts = endDateStr.split('-');
        year = int.parse(dateParts[0]);
        month = int.parse(dateParts[1]);
        day = int.parse(dateParts[2]);
      }

      List<String> timeParts = endTimeStr.split(':');
      int hour = int.parse(timeParts[0]);
      int minute = int.parse(timeParts[1]);

      final endDateTime = DateTime(year, month, day, hour, minute);
      
      if (now.isAfter(endDateTime)) {
        return _lang == "vi" ? "🔴 Đã kết thúc" : "🔴 Completed";
      } else {
        return _lang == "vi" ? "🟢 Đang diễn ra" : "🟢 Ongoing";
      }
    } catch (e) {
      return _lang == "vi" ? "🟢 Đang diễn ra" : "🟢 Ongoing";
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
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(_labels[_lang]!["title"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
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
                    child: Text(_labels[_lang]!["subtitle"]!, style: const TextStyle(color: Colors.white70, fontSize: 13)),
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

                  // Tiêu đề phân đoạn 1
                  Padding(
                    padding: const EdgeInsets.only(left: 16, top: 15, bottom: 5),
                    child: Text(_labels[_lang]!["sec_timeline"]!, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
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
                                  Text(slotInfo["slot"]!, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey, fontSize: 13)),
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
                                                Text(matchClass['subject'] ?? "", style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.blueAccent)),
                                                Text(matchClass['class_name'] ?? "", style: TextStyle(fontSize: 11, color: Colors.green[800], fontWeight: FontWeight.bold)),
                                              ],
                                            ),
                                            const SizedBox(height: 4),
                                            Text("👤 ${_labels[_lang]!['lbl_teacher']} ${matchClass['teacher_name'] ?? 'Đang xếp'}", style: const TextStyle(fontSize: 12)),
                                            Text("🏫 ${_labels[_lang]!['lbl_room']} ${matchClass['room'] ?? 'Online'}", style: const TextStyle(fontSize: 12)),
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
                                        child: Text(_labels[_lang]!["free_slot"]!, style: TextStyle(color: Colors.grey[400], fontStyle: FontStyle.italic, fontSize: 12)),
                                      ),
                                    ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),

                  const Divider(height: 35, thickness: 1),

                  // Tiêu đề phân đoạn 2 (Bảng chi tiết giống trên Web)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(_labels[_lang]!["sec_table"]!, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.indigo)),
                  ),
                  const SizedBox(height: 10),

                  // 3. CẤU TRÚC BẢNG DATATABLE SONG HÀNH CUỘN NGANG (GIỐNG PANDAS DATAFRAME)
                  _mySchedules.isEmpty
                      ? Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Text(_labels[_lang]!["info_empty"]!, style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic)),
                        )
                      : Container(
                          margin: const EdgeInsets.symmetric(horizontal: 14),
                          decoration: BoxDecoration(color: Colors.white, border: Border.all(color: Colors.grey.withOpacity(0.3)), borderRadius: BorderRadius.circular(8)),
                          child: SingleChildScrollView(
                            scrollDirection: Axis.horizontal, // Bật chế độ cuộn ngang cho bảng dữ liệu nhiều cột
                            child: DataTable(
                              headingRowColor: MaterialStateProperty.all(Colors.blue.withOpacity(0.1)),
                              columnSpacing: 20,
                              horizontalMargin: 12,
                              columns: [
                                DataColumn(label: Text(_labels[_lang]!["col_subject"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(_labels[_lang]!["col_class"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(_labels[_lang]!["col_teacher_head"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(_labels[_lang]!["col_days"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(_labels[_lang]!["col_slot"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(_labels[_lang]!["col_duration_head"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(_labels[_lang]!["col_room_head"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataColumn(label: Text(_labels[_lang]!["col_status"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
                              ],
                              rows: _mySchedules.map((s) {
                                List<dynamic> daysList = s['days_of_week'] ?? [];
                                String daysStr = daysList.join(", ");
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
                  
                  // Ghi chú chân trang của bảng
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(_labels[_lang]!["caption_footer"]!, style: TextStyle(fontSize: 11, color: Colors.grey[500], fontStyle: FontStyle.italic)),
                  ),
                ],
              ),
            ),
    );
  }
}