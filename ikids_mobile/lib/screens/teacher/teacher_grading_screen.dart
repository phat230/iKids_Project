import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/config.dart';

class TeacherGradingScreen extends StatefulWidget {
  const TeacherGradingScreen({super.key});

  @override
  State<TeacherGradingScreen> createState() => _TeacherGradingScreenState();
}

class _TeacherGradingScreenState extends State<TeacherGradingScreen> {
  final _storage = const FlutterSecureStorage();
  List<dynamic> _myClasses = [];
  List<dynamic> _students = [];
  String? _selectedClassId;
  String _teacherId = "";
  String _teacherName = "";
  bool _isLoading = true;

  bool _isApproved = false;
  bool _isPending = false;

  final Map<String, Map<String, TextEditingController>> _gradeControllers = {};

  @override
  void initState() {
    super.initState();
    _loadTeacherAndClasses();
  }

  Future<void> _loadTeacherAndClasses() async {
    try {
      String? token = await _storage.read(key: 'jwt_token');
      String? userInfoStr = await _storage.read(key: 'user_info');
      if (userInfoStr != null) {
        final decoded = jsonDecode(userInfoStr);
        _teacherId = decoded["id"]?.toString() ?? decoded["_id"]?.toString() ?? "";
        _teacherName = decoded["full_name"] ?? decoded["name"] ?? "Teacher";
      }

      final res = await http.get(
        Uri.parse('${AppConfig.apiTv1}/classes'), 
        headers: {"Authorization": "Bearer $token"}
      );
      
      if (res.statusCode == 200) {
        List<dynamic> allClasses = jsonDecode(utf8.decode(res.bodyBytes));
        setState(() {
          _myClasses = allClasses.where((c) => (c["teacher_id"] ?? "").toString() == _teacherId).toList();
        });
      }
    } catch (e) {
      debugPrint("Lỗi tải lớp: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _checkPermissionAndLoadStudents(String classId) async {
    setState(() => _isLoading = true);
    _gradeControllers.clear();
    _students.clear();
    try {
      String? token = await _storage.read(key: 'jwt_token');
      final headers = {"Authorization": "Bearer $token"}; // ĐÃ SỬA: Khai báo header chuẩn
      
      // 1. Kiểm tra quyền nhập điểm
      final pendingRes = await http.get(Uri.parse('${AppConfig.apiTv1}/pending-requests'), headers: headers);
      final historyRes = await http.get(Uri.parse('${AppConfig.apiTv1}/request-history'), headers: headers);
      
      List<dynamic> allReqs = [];
      if (pendingRes.statusCode == 200) allReqs.addAll(jsonDecode(utf8.decode(pendingRes.bodyBytes)));
      if (historyRes.statusCode == 200) allReqs.addAll(jsonDecode(utf8.decode(historyRes.bodyBytes)));

      final currentClass = _myClasses.firstWhere((c) => (c["id"] ?? c["_id"]).toString() == classId);
      String classFullName = currentClass["class_name"] ?? "";

      var myGradeReqs = allReqs.where((r) =>
          r["teacher_id"] == _teacherId &&
          r["type"] == "Xin cấp quyền nhập điểm" &&
          r["details"].toString().contains(classFullName)).toList();

      if (myGradeReqs.isNotEmpty) {
        myGradeReqs.sort((a, b) => (b["created_at"] ?? "").compareTo(a["created_at"] ?? ""));
        String status = myGradeReqs.first["status"] ?? "pending";
        _isPending = (status == "pending" || status == "Chờ duyệt");
        _isApproved = (status == "approved" || status == "Đã duyệt");
      } else {
        _isPending = false;
        _isApproved = false;
      }

      // 2. Tải danh sách học sinh THẬT từ lớp
      final studentRes = await http.get(Uri.parse('${AppConfig.apiTv1}/classes/$classId/students/details'), headers: headers);
      if (studentRes.statusCode == 200) {
        _students = jsonDecode(utf8.decode(studentRes.bodyBytes));
      }
        
      // 3. Khởi tạo Controllers và nạp điểm từ Backend
      for (var st in _students) {
        String sid = (st["Mã HS"] ?? st["id"]).toString();
        _initControllersForStudent(sid);
        
        final gradeRes = await http.get(Uri.parse('${AppConfig.apiTv2}/grades/$sid'), headers: headers);
        if (gradeRes.statusCode == 200) {
          List<dynamic> studentGrades = jsonDecode(utf8.decode(gradeRes.bodyBytes));
          var currentClassGrade = studentGrades.where((g) => (g["class_id"] ?? "").toString() == classId);
          if (currentClassGrade.isNotEmpty) {
            var g = currentClassGrade.first;
            _gradeControllers[sid]!["chuyen_can"]!.text = (g["chuyen_can"] ?? "10.0").toString();
            _gradeControllers[sid]!["kt_1"]!.text = (g["kt_1"] ?? "0").toString();
            _gradeControllers[sid]!["kt_2"]!.text = (g["kt_2"] ?? "0").toString();
            _gradeControllers[sid]!["kt_3"]!.text = (g["kt_3"] ?? "0").toString();
            _gradeControllers[sid]!["kt_4"]!.text = (g["kt_4"] ?? "0").toString();
            _gradeControllers[sid]!["kt_5"]!.text = (g["kt_5"] ?? "0").toString();
            _gradeControllers[sid]!["giua_ky"]!.text = (g["giua_ky"] ?? "0").toString();
            _gradeControllers[sid]!["cuoi_ky"]!.text = (g["cuoi_ky"] ?? "0").toString();
          }
        }
      }
    } catch (e) {
      debugPrint("Lỗi phân luồng chấm điểm: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _initControllersForStudent(String sid) {
    _gradeControllers[sid] = {
      "chuyen_can": TextEditingController(text: "10"),
      "kt_1": TextEditingController(text: "0"),
      "kt_2": TextEditingController(text: "0"),
      "kt_3": TextEditingController(text: "0"),
      "kt_4": TextEditingController(text: "0"),
      "kt_5": TextEditingController(text: "0"),
      "giua_ky": TextEditingController(text: "0"),
      "cuoi_ky": TextEditingController(text: "0"),
    };
  }

  Future<void> _requestPermission() async {
    final currentClass = _myClasses.firstWhere((c) => (c["id"] ?? c["_id"]).toString() == _selectedClassId);
    Map<String, dynamic> newReq = {
      "teacher_id": _teacherId,
      "teacher_name": _teacherName,
      "type": "Xin cấp quyền nhập điểm",
      "details": "Lớp: ${currentClass['class_name']}",
      "reason": "Yêu cầu mở khóa bảng điểm để cập nhật điểm số cho học viên.",
      "status": "pending",
      "created_at": DateTime.now().toIso8601String()
    };

    try {
      String? token = await _storage.read(key: 'jwt_token');
      final res = await http.post(
        Uri.parse('${AppConfig.apiTv1}/requests/create'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $token"},
        body: jsonEncode(newReq),
      );
      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đã gửi yêu cầu cấp quyền nhập điểm!"), backgroundColor: Colors.green));
        _checkPermissionAndLoadStudents(_selectedClassId!);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi kết nối."), backgroundColor: Colors.red));
    }
  }

  Future<void> _submitGrades() async {
    setState(() => _isLoading = true);
    List<Map<String, dynamic>> gradesPayload = [];

    for (var st in _students) {
      String sid = (st["Mã HS"] ?? st["id"]).toString();
      var ctrl = _gradeControllers[sid]!;

      double cc = double.tryParse(ctrl["chuyen_can"]!.text) ?? 0;
      double k1 = double.tryParse(ctrl["kt_1"]!.text) ?? 0;
      double k2 = double.tryParse(ctrl["kt_2"]!.text) ?? 0;
      double k3 = double.tryParse(ctrl["kt_3"]!.text) ?? 0;
      double k4 = double.tryParse(ctrl["kt_4"]!.text) ?? 0;
      double k5 = double.tryParse(ctrl["kt_5"]!.text) ?? 0;
      double gk = double.tryParse(ctrl["giua_ky"]!.text) ?? 0;
      double ck = double.tryParse(ctrl["cuoi_ky"]!.text) ?? 0;

      double tbKt = (k1 + k2 + k3 + k4 + k5) / 5;
      double tongKet = (cc * 0.1) + (tbKt * 0.2) + (gk * 0.7 * 0.3) + (ck * 0.7 * 0.7);

      String xl = "Yếu";
      if (tongKet >= 8.5) xl = "Giỏi";
      else if (tongKet >= 6.5) xl = "Khá";
      else if (tongKet >= 5.0) xl = "TB";

      gradesPayload.add({
        "student_id": sid,
        "student_name": st["Tên Học Sinh"] ?? st["name"],
        "chuyen_can": cc,
        "kt_1": k1, "kt_2": k2, "kt_3": k3, "kt_4": k4, "kt_5": k5,
        "giua_ky": gk,
        "cuoi_ky": ck,
        "tb_kiem_tra": double.parse(tbKt.toStringAsFixed(2)),
        "tong_ket": double.parse(tongKet.toStringAsFixed(2)),
        "xep_loai": xl
      });
    }

    Map<String, dynamic> payload = {
      "class_id": _selectedClassId,
      "teacher_id": _teacherId,
      "grades": gradesPayload
    };

    try {
      String? token = await _storage.read(key: 'jwt_token');
      final res = await http.post(
        Uri.parse('${AppConfig.apiTv2}/grades'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $token"}, // ĐÃ SỬA: Thêm Token vào POST
        body: jsonEncode(payload),
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đã đồng bộ điểm số lên hệ thống trung tâm!"), backgroundColor: Colors.green));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi lưu điểm."), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _onGradeChanged() {
    setState(() {}); 
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(title: const Text("Quản Lý Điểm Học Tập"), backgroundColor: Colors.blueGrey, foregroundColor: Colors.white),
      body: _isLoading && _myClasses.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: DropdownButtonFormField<String>(
                    value: _selectedClassId,
                    hint: const Text("Chọn lớp học ghi điểm"),
                    decoration: const InputDecoration(border: OutlineInputBorder(), filled: true, fillColor: Colors.white),
                    items: _myClasses.map((c) {
                      return DropdownMenuItem<String>(value: (c["id"] ?? c["_id"]).toString(), child: Text(c["class_name"] ?? ""));
                    }).toList(),
                    onChanged: (val) {
                      setState(() => _selectedClassId = val);
                      if (val != null) _checkPermissionAndLoadStudents(val);
                    },
                  ),
                ),
                
                if (_selectedClassId != null) ...[
                  if (!_isApproved)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: _isPending ? Colors.orange.shade50 : Colors.red.shade50,
                        border: Border.all(color: _isPending ? Colors.orange : Colors.red),
                        borderRadius: BorderRadius.circular(8)
                      ),
                      child: Column(
                        children: [
                          Text(
                            _isPending ? "Đơn xin mở khóa đang chờ phê duyệt..." : "Bảng điểm hiện đang bị khóa.", 
                            style: TextStyle(color: _isPending ? Colors.orange.shade900 : Colors.red, fontWeight: FontWeight.bold)
                          ),
                          if (!_isPending) ...[
                            const SizedBox(height: 10),
                            ElevatedButton.icon(
                              icon: const Icon(Icons.lock_open, size: 18),
                              onPressed: _requestPermission, 
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white), 
                              label: const Text("Yêu cầu cấp quyền nhập điểm")
                            )
                          ]
                        ],
                      ),
                    ),

                  if (_students.isEmpty && !_isLoading)
                    Expanded(
                      child: Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.people_alt_outlined, size: 60, color: Colors.grey.shade400),
                            const SizedBox(height: 10),
                            const Text("Lớp học này hiện tại chưa có học sinh nào.", style: TextStyle(color: Colors.grey, fontSize: 16)),
                          ],
                        ),
                      ),
                    )
                  else
                    Expanded(
                      child: SingleChildScrollView(
                        scrollDirection: Axis.vertical,
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: DataTable(
                            headingRowColor: MaterialStateProperty.all(Colors.blueGrey.shade50),
                            columnSpacing: 20,
                            dataRowMaxHeight: 60,
                            columns: const [
                              DataColumn(label: Text("Tên Học Sinh", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Chuyên Cần", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("KT 1", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("KT 2", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("KT 3", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("KT 4", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("KT 5", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Giữa Kỳ", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("Cuối Kỳ", style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text("TB KT", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo))),
                              DataColumn(label: Text("TỔNG KẾT", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red))),
                              DataColumn(label: Text("Xếp Loại", style: TextStyle(fontWeight: FontWeight.bold))),
                            ],
                            rows: _students.where((st) => _gradeControllers.containsKey((st["Mã HS"] ?? st["id"]).toString())).map((st) {
                              String sid = (st["Mã HS"] ?? st["id"]).toString();
                              var ctrl = _gradeControllers[sid]!;

                              double cc = double.tryParse(ctrl["chuyen_can"]!.text) ?? 0;
                              double k1 = double.tryParse(ctrl["kt_1"]!.text) ?? 0;
                              double k2 = double.tryParse(ctrl["kt_2"]!.text) ?? 0;
                              double k3 = double.tryParse(ctrl["kt_3"]!.text) ?? 0;
                              double k4 = double.tryParse(ctrl["kt_4"]!.text) ?? 0;
                              double k5 = double.tryParse(ctrl["kt_5"]!.text) ?? 0;
                              double gk = double.tryParse(ctrl["giua_ky"]!.text) ?? 0;
                              double ck = double.tryParse(ctrl["cuoi_ky"]!.text) ?? 0;

                              double tbKt = (k1 + k2 + k3 + k4 + k5) / 5;
                              double tongKet = (cc * 0.1) + (tbKt * 0.2) + (gk * 0.7 * 0.3) + (ck * 0.7 * 0.7);

                              String xl = "Yếu";
                              if (tongKet >= 8.5) xl = "Giỏi";
                              else if (tongKet >= 6.5) xl = "Khá";
                              else if (tongKet >= 5.0) xl = "TB";

                              return DataRow(
                                cells: [
                                  DataCell(Text(st["Tên Học Sinh"] ?? st["name"] ?? "", style: const TextStyle(fontWeight: FontWeight.w600))),
                                  DataCell(_buildGradeField(ctrl["chuyen_can"]!)),
                                  DataCell(_buildGradeField(ctrl["kt_1"]!)),
                                  DataCell(_buildGradeField(ctrl["kt_2"]!)),
                                  DataCell(_buildGradeField(ctrl["kt_3"]!)),
                                  DataCell(_buildGradeField(ctrl["kt_4"]!)),
                                  DataCell(_buildGradeField(ctrl["kt_5"]!)),
                                  DataCell(_buildGradeField(ctrl["giua_ky"]!)),
                                  DataCell(_buildGradeField(ctrl["cuoi_ky"]!)),
                                  DataCell(Text(tbKt.toStringAsFixed(1), style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo))),
                                  DataCell(Text(tongKet.toStringAsFixed(1), style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red, fontSize: 16))),
                                  DataCell(Text(xl, style: TextStyle(fontWeight: FontWeight.bold, color: xl == "Giỏi" ? Colors.green : (xl == "Khá" ? Colors.blue : Colors.orange)))),
                                ],
                              );
                            }).toList(),
                          ),
                        ),
                      ),
                    ),

                  if (_isApproved && _students.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.all(16),
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.cloud_upload),
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.blueGrey, foregroundColor: Colors.white, minimumSize: const Size(double.infinity, 50)),
                        onPressed: _submitGrades,
                        label: const Text("GHI NHẬN LÊN HỆ THỐNG", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                      ),
                    )
                ]
              ],
            ),
    );
  }

  Widget _buildGradeField(TextEditingController controller) {
    return SizedBox(
      width: 55,
      child: TextField(
        controller: controller,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        enabled: _isApproved,
        textAlign: TextAlign.center,
        onChanged: (val) => _onGradeChanged(),
        decoration: InputDecoration(
          isDense: true, 
          contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 5),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(5)),
          filled: !_isApproved,
          fillColor: Colors.grey.shade100
        ),
      ),
    );
  }
}