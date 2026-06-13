import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class EnrollClassScreen extends StatefulWidget {
  const EnrollClassScreen({super.key});

  @override
  State<EnrollClassScreen> createState() => _EnrollClassScreenState();
}

class _EnrollClassScreenState extends State<EnrollClassScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";
  String _parentId = "";
  String _token = "";

  List<dynamic> _children = [];
  List<dynamic> _publicClasses = [];
  List<dynamic> _allClasses = [];
  List<dynamic> _schedules = [];
  
  String? _selectedChildIdForEnroll;
  Map<String, String> _scheduleSubjectMap = {};

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Đăng Ký Lớp Học Cho Con",
      "subtitle": "Dưới đây là danh sách các lớp học đang mở. Phụ huynh có thể chọn lớp phù hợp cho con em mình.",
      "err_login": "Vui lòng đăng nhập với tài khoản Phụ huynh để đăng ký lớp học.",
      "warn_no_child": "Bạn chưa có hồ sơ học sinh nào. Vui lòng tạo tài khoản cho bé trước khi đăng ký lớp!",
      "expander_schedule": "Thời Khóa Biểu Hiện Tại Của Bé",
      "expander_desc": "⚠️ Kiểm tra lịch hiện tại để tránh trùng thời gian học.",
      "info_no_schedule": "Bé hiện chưa có lịch học nào.",
      "session_morning": "SÁNG",
      "session_afternoon": "CHIỀU",
      "session_evening": "TỐI",
      "session_label": "Buổi",
      "sub_enroll_section": "Danh Sách Lớp Học Đang Mở",
      "select_child_global": "Chọn học sinh để xem môn học mới:",
      "lbl_registering_for": "Đăng ký cho bé:",
      "info_all_enrolled": "Học sinh này đã tham gia tất cả các lớp đang mở.",
      "info_empty_classes": "Hiện tại chưa có lớp học nào mở đăng ký công khai.",
      "lbl_class_unknown": "Tên lớp chưa rõ",
      "lbl_subject": "Môn học:",
      "lbl_sub_unassigned": "Chưa cập nhật",
      "lbl_teacher": "Giáo viên phụ trách:",
      "btn_enroll": "Xác Nhận Đăng Ký Lớp",
      "success_enrolled": "Đã đăng ký thành công cho bé!",
      "err_failed_enroll": "Đăng ký thất bại. Lớp học có thể đã đầy.",
    },
    "en": {
      "title": "Course Enrollment for Children",
      "subtitle": "Below is the list of active open classes. Parents can review and select the most suitable option.",
      "err_login": "Authentication required. Please log in with a Parent account.",
      "warn_no_child": "No student profiles found. Please create a profile for your child first!",
      "expander_schedule": "Children's Current Timetable",
      "expander_desc": "⚠️ Please check current schedules to avoid conflicting time slots.",
      "info_no_schedule": "This child currently has no scheduled classes.",
      "session_morning": "MORNING",
      "session_afternoon": "AFTERNOON",
      "session_evening": "EVENING",
      "session_label": "Session",
      "sub_enroll_section": "Open Classes for Registration",
      "select_child_global": "Select a child to view available courses:",
      "lbl_registering_for": "Enrolling:",
      "info_all_enrolled": "This student is already enrolled in all available classes.",
      "info_empty_classes": "There are currently no open classes available for registration.",
      "lbl_class_unknown": "Unknown Class Title",
      "lbl_subject": "Subject:",
      "lbl_sub_unassigned": "Unassigned",
      "lbl_teacher": "Instructor:",
      "btn_enroll": "Confirm Enrollment",
      "success_enrolled": "Registration successful for your child!",
      "err_failed_enroll": "Enrollment failed. Class might be fully occupied.",
    }
  };

  final List<String> _daysOfWeekVi = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];
  final List<String> _daysOfWeekEn = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

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

      if (_token.isEmpty || _parentId.isEmpty) {
        setState(() => _isLoading = false);
        return;
      }

      final headers = {
        "Authorization": "Bearer $_token",
        "parent-id": _parentId,
        "Content-Type": "application/json"
      };

      final childrenRes = await http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/parent/my-children'), headers: headers);
      if (childrenRes.statusCode == 200) {
        _children = jsonDecode(utf8.decode(childrenRes.bodyBytes));
        if (_children.isNotEmpty) {
          _selectedChildIdForEnroll = _children[0]['id'];
        }
      }

      final publicRes = await http.get(Uri.parse('${AppConfig.apiUrl}/classes/public'));
      if (publicRes.statusCode == 200) {
        _publicClasses = jsonDecode(utf8.decode(publicRes.bodyBytes));
      }

      final allRes = await http.get(Uri.parse('${AppConfig.apiUrl}/classes'), headers: headers);
      if (allRes.statusCode == 200) {
        _allClasses = jsonDecode(utf8.decode(allRes.bodyBytes));
      } else {
        _allClasses = _publicClasses;
      }

      final schedRes = await http.get(Uri.parse('${AppConfig.apiUrl}/schedule/list'), headers: headers);
      if (schedRes.statusCode == 200) {
        _schedules = jsonDecode(utf8.decode(schedRes.bodyBytes));
        _scheduleSubjectMap.clear();
        for (var s in _schedules) {
          String cId = s["class_id"]?.toString() ?? "";
          String subj = s["subject"]?.toString() ?? "";
          if (cId.isNotEmpty && subj.isNotEmpty) {
            _scheduleSubjectMap[cId] = subj;
          }
        }
      }

    } catch (e) {
      debugPrint("Lỗi kết nối Backend: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _enrollClass(String classId) async {
    if (_selectedChildIdForEnroll == null) return;
    
    showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator()));

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}/classes/register'),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $_token"
        },
        body: jsonEncode({
          "class_id": classId,
          "student_id": _selectedChildIdForEnroll
        }),
      ).timeout(const Duration(seconds: 10));

      if (mounted) Navigator.pop(context);

      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("${_labels[_lang]!['success_enrolled']}"),
          backgroundColor: Colors.green,
        ));
        _initData();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("${_labels[_lang]!['err_failed_enroll']}"),
          backgroundColor: Colors.red,
        ));
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi mạng, vui lòng thử lại.")));
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
        title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _initData),
          TextButton(
            onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
            child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.green))
          : _children.isEmpty
              ? Padding(padding: const EdgeInsets.all(20), child: Center(child: Text(labels["warn_no_child"]!, textAlign: TextAlign.center)))
              : DefaultTabController(
                  length: _children.length,
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(labels["subtitle"]!, style: TextStyle(color: Colors.grey[700], fontSize: 13, fontStyle: FontStyle.italic)),
                        const SizedBox(height: 15),
                        
                        Text(labels["expander_schedule"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.green)),
                        Text(labels["expander_desc"]!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        const SizedBox(height: 10),

                        if (_children.length > 1)
                          TabBar(
                            isScrollable: true,
                            labelColor: Colors.green,
                            unselectedLabelColor: Colors.grey,
                            indicatorColor: Colors.green,
                            tabs: _children.map((c) => Tab(text: c['name']?.toString())).toList(),
                          ),
                        
                        SizedBox(
                          height: 320,
                          child: TabBarView(
                            physics: const NeverScrollableScrollPhysics(),
                            children: _children.map((c) => _buildTimetableGrid(c['id'])).toList(),
                          ),
                        ),

                        const Divider(height: 30),
                        
                        Text(labels["sub_enroll_section"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.indigo)),
                        const SizedBox(height: 10),
                        Text(labels["select_child_global"]!, style: const TextStyle(fontSize: 13)),
                        const SizedBox(height: 5),
                        
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          decoration: BoxDecoration(color: Colors.white, border: Border.all(color: Colors.grey[400]!), borderRadius: BorderRadius.circular(8)),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              isExpanded: true,
                              value: _selectedChildIdForEnroll,
                              items: _children.map((c) => DropdownMenuItem<String>(value: c['id']?.toString(), child: Text(c['name'] ?? ''))).toList(),
                              onChanged: (val) => setState(() => _selectedChildIdForEnroll = val),
                            ),
                          ),
                        ),
                        const SizedBox(height: 15),

                        _buildAvailableClassesList(),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildTimetableGrid(String childId) {
    final labels = _labels[_lang]!;
    final displayDays = _lang == "vi" ? _daysOfWeekVi : _daysOfWeekEn;
    final sessions = [labels["session_morning"]!, labels["session_afternoon"]!, labels["session_evening"]!];

    Map<String, Map<String, List<Map<String, dynamic>>>> matrix = {
      for (var s in ["SÁNG", "CHIỀU", "TỐI"]) s: {for (var d in _daysOfWeekVi) d: []}
    };

    bool childHasClasses = false;

    for (var cls in _allClasses) {
      List studentsInClass = (cls["student_ids"] as List<dynamic>?) ?? [];
      if (studentsInClass.contains(childId)) {
        
        // ĐÃ KHẮC PHỤC LỖI .get() CUỐI CÙNG TẠI ĐÂY
        String cId = cls["id"]?.toString() ?? cls["_id"]?.toString() ?? "";
        
        var sched = _schedules.firstWhere((s) => s["class_id"]?.toString() == cId, orElse: () => null);
        
        if (sched != null) {
          childHasClasses = true;
          String startTime = sched["start_time"] ?? "08:00";
          int hour = int.tryParse(startTime.split(":")[0]) ?? 8;
          
          String sessionKey = "SÁNG";
          if (hour >= 12 && hour < 17) {
            sessionKey = "CHIỀU";
          } else if (hour >= 17) {
            sessionKey = "TỐI";
          }

          List days = sched["days_of_week"] ?? [];
          for (var d in days) {
            if (matrix[sessionKey]!.containsKey(d)) {
              matrix[sessionKey]![d]!.add({
                "class_name": cls["class_name"] ?? labels["lbl_class_unknown"],
                "subject": sched["subject"] ?? cls["subject"] ?? labels["lbl_sub_unassigned"],
                "time": "$startTime - ${sched['end_time'] ?? ''}"
              });
            }
          }
        }
      }
    }

    if (!childHasClasses) {
      return Center(child: Text(labels["info_no_schedule"]!, style: const TextStyle(fontStyle: FontStyle.italic, color: Colors.grey)));
    }

    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(top: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: SingleChildScrollView(
          child: DataTable(
            columnSpacing: 12,
            headingRowColor: MaterialStateProperty.all(Colors.green[50]),
            border: TableBorder.all(color: Colors.grey[300]!, width: 1, borderRadius: BorderRadius.circular(5)),
            columns: [
              DataColumn(label: Text(labels["session_label"]!, style: const TextStyle(fontWeight: FontWeight.bold))),
              ...displayDays.map((d) => DataColumn(label: Text(d, style: const TextStyle(fontWeight: FontWeight.bold)))),
            ],
            rows: ["SÁNG", "CHIỀU", "TỐI"].asMap().entries.map((entry) {
              String rawSession = entry.value;
              String displaySession = sessions[entry.key];

              return DataRow(cells: [
                DataCell(Container(
                  alignment: Alignment.center,
                  child: Text(displaySession, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueGrey, fontSize: 11)),
                )),
                ..._daysOfWeekVi.map((dayVi) {
                  ListCellCardData? slotClasses = matrix[rawSession]![dayVi];
                  if (slotClasses == null || slotClasses.isEmpty) return const DataCell(Text(""));
                  
                  // ĐÃ KHẮC PHỤC LỖI OVERFLOW TRÀN VIỀN TẠI ĐÂY BẰNG CÁCH BỌC SCROLL VÀ GIỚI HẠN DÒNG
                  return DataCell(
                    Container(
                      alignment: Alignment.centerLeft,
                      child: SingleChildScrollView(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.start,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: slotClasses.map<Widget>((c) => Container(
                            width: 100, 
                            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                            margin: const EdgeInsets.only(bottom: 4),
                            decoration: BoxDecoration(
                              color: Colors.blue[50], 
                              border: const Border(left: BorderSide(color: Colors.blue, width: 3)), 
                              borderRadius: BorderRadius.circular(2)
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(c["class_name"], maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.blue)),
                                Text(c["subject"], maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 9, color: Colors.black87)),
                                Text(c["time"], maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 8, color: Colors.grey)),
                              ],
                            ),
                          )).toList(),
                        ),
                      ),
                    ),
                  );
                }).toList()
              ]);
            }).toList(),
          ),
        ),
      ),
    );
  }

  Widget _buildAvailableClassesList() {
    final labels = _labels[_lang]!;
    if (_publicClasses.isEmpty) {
      return Center(child: Text(labels["info_empty_classes"]!));
    }

    final availableClasses = _publicClasses.where((cls) {
      List studentIds = cls["student_ids"] ?? [];
      return !studentIds.contains(_selectedChildIdForEnroll);
    }).toList();

    if (availableClasses.isEmpty) {
      return Card(
        color: Colors.orange[50],
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(children: [const Icon(Icons.info, color: Colors.orange), const SizedBox(width: 10), Expanded(child: Text(labels["info_all_enrolled"]!))]),
        ),
      );
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: availableClasses.length,
      itemBuilder: (context, index) {
        final cls = availableClasses[index];
        String classId = cls['id'] ?? cls['_id'] ?? '';
        String className = cls['class_name'] ?? labels["lbl_class_unknown"];
        
        String subjectRaw = _scheduleSubjectMap[classId] ?? cls['subject'] ?? labels["lbl_sub_unassigned"];
        String teacherName = cls['teacher_name'] ?? labels["lbl_teacher_arranging"];

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(14.0),
            child: Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(className, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.indigo)),
                      const SizedBox(height: 6),
                      Text("${labels["lbl_subject"]} $subjectRaw", style: const TextStyle(fontSize: 13)),
                      Text("${labels["lbl_teacher"]} $teacherName", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                    ],
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.indigo,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.symmetric(vertical: 10)
                    ),
                    onPressed: () => _enrollClass(classId),
                    child: Text(labels["btn_enroll"]!, textAlign: TextAlign.center, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                  ),
                )
              ],
            ),
          ),
        );
      },
    );
  }
}

typedef ListCellCardData = List<Map<String, dynamic>>;