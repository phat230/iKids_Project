import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class OperatorClassScreen extends StatefulWidget {
  const OperatorClassScreen({super.key});

  @override
  State<OperatorClassScreen> createState() => _OperatorClassScreenState();
}

class _OperatorClassScreenState extends State<OperatorClassScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";
  String _token = "";

  List<dynamic> _teachers = [];
  List<dynamic> _classes = [];
  List<dynamic> _studentsInClass = [];

  // Form Tạo lớp
  final _createNameCtrl = TextEditingController();
  final _createDescCtrl = TextEditingController();
  String? _createTeacherId;

  // Form Quản lý & Sửa lớp
  String? _selectedClassId;
  int _subTabIndex = 0; // 0: Học sinh, 1: Sửa lớp, 2: Xóa lớp
  final _editNameCtrl = TextEditingController();
  final _editDescCtrl = TextEditingController();
  String? _editTeacherId;

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Quản Lý Lớp Học & Học Viên",
      "subtitle": "Tạo lớp học mới, xếp học viên, xem danh sách và chỉnh sửa/xóa lớp.",
      "tab_create": "Tạo Lớp Học",
      "tab_manage": "Quản Lý Lớp",
      "form_create_header": "Nhập thông tin lớp học",
      "input_name": "Tên lớp học (*)",
      "input_desc": "Ghi chú nội bộ",
      "input_teacher": "Giáo viên phụ trách (*)",
      "warn_no_teacher": "Chưa có giáo viên hợp lệ.",
      "btn_create": "Tạo Lớp Mới",
      "err_fields": "Vui lòng điền đủ (*)",
      "success_created": "Tạo lớp thành công!",
      "select_class": "Chọn lớp để quản lý:",
      "sub_students": "Danh Sách Học Viên",
      "sub_edit": "Sửa Thông Tin",
      "sub_delete": "Xóa Lớp",
      "lbl_teacher": "Giáo viên:",
      "no_students": "Lớp này chưa có học sinh.",
      "btn_remove": "Xóa",
      "success_removed": "Đã xóa học sinh khỏi lớp!",
      "btn_save": "Lưu Thay Đổi",
      "success_updated": "Cập nhật lớp thành công!",
      "warn_delete": "Hành động này là vĩnh viễn!",
      "btn_delete": "Xác nhận Xóa lớp",
      "success_deleted": "Đã xóa lớp thành công!",
      "msg_error": "Có lỗi xảy ra, vui lòng thử lại.",
    },
    "en": {
      "title": "Class & Student Management",
      "subtitle": "Provision classes, enroll students, and modify registries.",
      "tab_create": "Create Class",
      "tab_manage": "Manage Classes",
      "form_create_header": "Enter Class Specifications",
      "input_name": "Class Name (*)",
      "input_desc": "Internal Notes",
      "input_teacher": "Assigned Teacher (*)",
      "warn_no_teacher": "No valid teachers found.",
      "btn_create": "Create New Class",
      "err_fields": "Fill in required fields (*)",
      "success_created": "Class created successfully!",
      "select_class": "Select class:",
      "sub_students": "Student List",
      "sub_edit": "Edit Profile",
      "sub_delete": "Delete Class",
      "lbl_teacher": "Instructor:",
      "no_students": "No students enrolled yet.",
      "btn_remove": "Remove",
      "success_removed": "Student removed from class!",
      "btn_save": "Save Changes",
      "success_updated": "Class updated successfully!",
      "warn_delete": "This action is permanent!",
      "btn_delete": "Confirm Deletion",
      "success_deleted": "Class deleted successfully!",
      "msg_error": "An error occurred.",
    }
  };

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
      if (_token.isEmpty) return;

      await Future.wait([_fetchTeachers(), _fetchClasses()]);
    } catch (e) {
      debugPrint("Lỗi Init Data: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _fetchTeachers() async {
    final headers = {"Authorization": "Bearer $_token"};
    try {
      // 1. Thử API Teachers chuẩn
      var res = await http.get(Uri.parse('${AppConfig.apiUrl}/teachers'), headers: headers).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        var data = jsonDecode(utf8.decode(res.bodyBytes));
        if (data is List && data.isNotEmpty) {
          _teachers = data;
          return;
        }
      }
      
      // 2. Fallback quét Auth Users
      res = await http.get(Uri.parse('${AppConfig.apiUrl}/api/auth/users'), headers: headers).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        var rawData = jsonDecode(utf8.decode(res.bodyBytes));
        _teachers = rawData.where((u) {
          String role = (u['role'] ?? u['quyen'] ?? '').toString().toLowerCase();
          String status = (u['status'] ?? u['trang_thai'] ?? '').toString();
          bool isActive = u['is_active'] ?? true;
          return (role.contains("teacher") || role.contains("giáo viên")) && 
                 status != "Nghỉ việc" && status != "Vô hiệu hóa" && isActive;
        }).toList();
      }
    } catch (e) {
      debugPrint("Lỗi Fetch Teachers: $e");
    }
  }

  Future<void> _fetchClasses() async {
    try {
      final res = await http.get(Uri.parse('${AppConfig.apiUrl}/classes')).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        _classes = jsonDecode(utf8.decode(res.bodyBytes));
      }
    } catch (e) {
      debugPrint("Lỗi Fetch Classes: $e");
    }
  }

  Future<void> _fetchClassStudents(String classId) async {
    setState(() => _isLoading = true);
    try {
      final res = await http.get(Uri.parse('${AppConfig.apiUrl}/classes/$classId/students/details'));
      if (res.statusCode == 200) {
        _studentsInClass = jsonDecode(utf8.decode(res.bodyBytes));
      } else {
        _studentsInClass = [];
      }
    } catch (e) {
      _studentsInClass = [];
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // --- ACTIONS ---
  Future<void> _createClass() async {
    final labels = _labels[_lang]!;
    if (_createNameCtrl.text.isEmpty || _createTeacherId == null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["err_fields"]!), backgroundColor: Colors.orange));
      return;
    }

    setState(() => _isLoading = true);
    try {
      final teacher = _teachers.firstWhere((t) => (t['id'] ?? t['_id']).toString() == _createTeacherId);
      final payload = {
        "class_name": _createNameCtrl.text.trim(),
        "subject": _lang == "vi" ? "Chưa xác định" : "Unassigned",
        "teacher_id": _createTeacherId,
        "teacher_name": teacher['name'] ?? teacher['full_name'],
        "student_ids": [],
        "is_public": false,
        "description": _createDescCtrl.text.trim(),
        "status": "active"
      };

      final res = await http.post(
        Uri.parse('${AppConfig.apiUrl}/classes/create'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload)
      );

      if (res.statusCode == 200 || res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["success_created"]!), backgroundColor: Colors.green));
        _createNameCtrl.clear();
        _createDescCtrl.clear();
        _createTeacherId = null;
        await _fetchClasses();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_error"]!), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_error"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _updateClass() async {
    final labels = _labels[_lang]!;
    if (_editNameCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["err_fields"]!), backgroundColor: Colors.orange));
      return;
    }

    setState(() => _isLoading = true);
    try {
      final payload = {
        "class_name": _editNameCtrl.text.trim(),
        "description": _editDescCtrl.text.trim(),
      };
      
      if (_editTeacherId != null) {
        final teacher = _teachers.firstWhere((t) => (t['id'] ?? t['_id']).toString() == _editTeacherId, orElse: () => null);
        if (teacher != null) {
          payload["teacher_id"] = _editTeacherId!;
          payload["teacher_name"] = teacher['name'] ?? teacher['full_name'];
        }
      }

      final res = await http.put(
        Uri.parse('${AppConfig.apiUrl}/classes/$_selectedClassId'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload)
      );

      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["success_updated"]!), backgroundColor: Colors.green));
        await _fetchClasses();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_error"]!), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_error"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteClass() async {
    final labels = _labels[_lang]!;
    setState(() => _isLoading = true);
    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiUrl}/classes/$_selectedClassId'),
        headers: {"Authorization": "Bearer $_token"}
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["success_deleted"]!), backgroundColor: Colors.green));
        _selectedClassId = null;
        await _fetchClasses();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_error"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _removeStudent(String studentId) async {
    final labels = _labels[_lang]!;
    setState(() => _isLoading = true);
    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiUrl}/classes/$_selectedClassId/students/$studentId'),
        headers: {"Authorization": "Bearer $_token"}
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["success_removed"]!), backgroundColor: Colors.green));
        await _fetchClassStudents(_selectedClassId!);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_error"]!), backgroundColor: Colors.red));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // --- UI RENDER ---
  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          backgroundColor: Colors.indigo,
          foregroundColor: Colors.white,
          actions: [
            TextButton(
              onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"),
              child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            )
          ],
          bottom: TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white60,
            indicatorColor: Colors.amber,
            indicatorWeight: 3,
            tabs: [
              Tab(icon: const Icon(Icons.add_circle), text: labels["tab_create"]),
              Tab(icon: const Icon(Icons.manage_accounts), text: labels["tab_manage"]),
            ],
          ),
        ),
        body: _isLoading 
          ? const Center(child: CircularProgressIndicator(color: Colors.indigo))
          : TabBarView(
              children: [
                _buildCreateTab(labels),
                _buildManageTab(labels),
              ],
            ),
      ),
    );
  }

  Widget _buildCreateTab(Map<String, String> labels) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(labels["subtitle"]!, style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic)),
          const SizedBox(height: 20),
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            elevation: 3,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(labels["form_create_header"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.indigo)),
                  const Divider(),
                  TextField(controller: _createNameCtrl, decoration: InputDecoration(labelText: labels["input_name"])),
                  const SizedBox(height: 10),
                  TextField(controller: _createDescCtrl, decoration: InputDecoration(labelText: labels["input_desc"])),
                  const SizedBox(height: 15),
                  
                  if (_teachers.isEmpty)
                    Text(labels["warn_no_teacher"]!, style: const TextStyle(color: Colors.red))
                  else
                    DropdownButtonFormField<String>(
                      decoration: InputDecoration(labelText: labels["input_teacher"]),
                      value: _createTeacherId,
                      items: _teachers.map((t) {
                        String tId = (t['id'] ?? t['_id']).toString();
                        String tName = t['name'] ?? t['full_name'] ?? 'Unknown';
                        return DropdownMenuItem(value: tId, child: Text(tName));
                      }).toList(),
                      onChanged: (val) => setState(() => _createTeacherId = val),
                    ),
                  
                  const SizedBox(height: 25),
                  SizedBox(
                    width: double.infinity,
                    height: 45,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                      onPressed: _createClass,
                      child: Text(labels["btn_create"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    ),
                  )
                ],
              ),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildManageTab(Map<String, String> labels) {
    if (_classes.isEmpty) {
      return Center(child: Text("Hệ thống chưa có lớp học nào.", style: TextStyle(color: Colors.grey[600])));
    }

    return Column(
      children: [
        // Dropdown Chọn lớp
        Container(
          color: Colors.white,
          padding: const EdgeInsets.all(15),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(labels["select_class"]!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  isExpanded: true,
                  value: _selectedClassId,
                  style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo, fontSize: 16),
                  items: _classes.map((c) {
                    String cId = (c['id'] ?? c['_id']).toString();
                    return DropdownMenuItem(value: cId, child: Text(c['class_name'] ?? ''));
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() {
                        _selectedClassId = val;
                        final selClass = _classes.firstWhere((c) => (c['id'] ?? c['_id']).toString() == val);
                        _editNameCtrl.text = selClass['class_name'] ?? '';
                        _editDescCtrl.text = selClass['description'] ?? '';
                        _editTeacherId = selClass['teacher_id']?.toString();
                        // Tránh lỗi nếu Teacher ID không nằm trong danh sách giáo viên hiện tại
                        if (!_teachers.any((t) => (t['id'] ?? t['_id']).toString() == _editTeacherId)) {
                          _editTeacherId = null; 
                        }
                      });
                      _fetchClassStudents(val);
                    }
                  },
                ),
              )
            ],
          ),
        ),

        if (_selectedClassId != null) ...[
          // Thanh Sub-tabs điều hướng giả lập
          Padding(
            padding: const EdgeInsets.all(12),
            child: Container(
              decoration: BoxDecoration(color: Colors.indigo[50], borderRadius: BorderRadius.circular(10)),
              child: Row(
                children: [
                  _buildSubTabBtn(0, Icons.people, labels["sub_students"]!),
                  _buildSubTabBtn(1, Icons.edit, labels["sub_edit"]!),
                  _buildSubTabBtn(2, Icons.delete, labels["sub_delete"]!),
                ],
              ),
            ),
          ),

          // Nội dung Sub-tab
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(15),
              child: _buildSubTabContent(labels),
            ),
          )
        ]
      ],
    );
  }

  Widget _buildSubTabBtn(int index, IconData icon, String title) {
    bool isSelected = _subTabIndex == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _subTabIndex = index),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected ? Colors.indigo : Colors.transparent,
            borderRadius: BorderRadius.circular(10)
          ),
          child: Column(
            children: [
              Icon(icon, size: 20, color: isSelected ? Colors.white : Colors.indigo[300]),
              const SizedBox(height: 2),
              Text(title, textAlign: TextAlign.center, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: isSelected ? Colors.white : Colors.indigo[300])),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSubTabContent(Map<String, String> labels) {
    if (_subTabIndex == 0) {
      // DANH SÁCH HỌC SINH
      if (_studentsInClass.isEmpty) return Center(child: Padding(padding: const EdgeInsets.all(20), child: Text(labels["no_students"]!)));
      
      return ListView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: _studentsInClass.length,
        itemBuilder: (context, index) {
          final student = _studentsInClass[index];
          String sId = student['id'] ?? student['_id'] ?? student['Mã HS'] ?? '';
          String sName = student['name'] ?? student['Tên Học Sinh'] ?? 'Unknown';
          
          return Card(
            margin: const EdgeInsets.only(bottom: 10),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            child: ListTile(
              leading: const CircleAvatar(backgroundColor: Colors.indigo, child: Icon(Icons.person, color: Colors.white)),
              title: Text(sName, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text("ID: $sId"),
              trailing: IconButton(
                icon: const Icon(Icons.remove_circle, color: Colors.red),
                onPressed: () => _removeStudent(sId),
              ),
            ),
          );
        },
      );

    } else if (_subTabIndex == 1) {
      // CHỈNH SỬA THÔNG TIN
      return Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              TextField(controller: _editNameCtrl, decoration: InputDecoration(labelText: labels["input_name"])),
              const SizedBox(height: 10),
              TextField(controller: _editDescCtrl, decoration: InputDecoration(labelText: labels["input_desc"])),
              const SizedBox(height: 15),
              DropdownButtonFormField<String>(
                decoration: InputDecoration(labelText: labels["lbl_teacher"]),
                value: _editTeacherId,
                items: _teachers.map((t) {
                  String tId = (t['id'] ?? t['_id']).toString();
                  String tName = t['name'] ?? t['full_name'] ?? 'Unknown';
                  return DropdownMenuItem(value: tId, child: Text(tName));
                }).toList(),
                onChanged: (val) => setState(() => _editTeacherId = val),
              ),
              const SizedBox(height: 25),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white),
                  onPressed: _updateClass,
                  child: Text(labels["btn_save"]!),
                ),
              )
            ],
          ),
        ),
      );

    } else {
      // XÓA LỚP
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: Colors.red[50], borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.red[200]!)),
        child: Column(
          children: [
            const Icon(Icons.warning_amber_rounded, color: Colors.red, size: 50),
            const SizedBox(height: 15),
            Text(labels["warn_delete"]!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
                onPressed: _deleteClass,
                child: Text(labels["btn_delete"]!),
              ),
            )
          ],
        ),
      );
    }
  }
}