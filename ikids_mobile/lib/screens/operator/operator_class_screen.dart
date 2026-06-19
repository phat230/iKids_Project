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

  // ================= BỘ TỪ ĐIỂN SONG NGỮ ĐẦY ĐỦ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Quản Lý Lớp Học",
      "subtitle": "Khởi tạo, sắp xếp giáo viên và quản lý danh sách học viên.",
      "tab_create": "Tạo Lớp Mới",
      "tab_manage": "Quản Lý Lớp",
      "form_create_header": "Thông Tin Lớp Học Mới",
      "input_name": "Tên lớp học (*)",
      "input_desc": "Ghi chú nội bộ",
      "input_teacher": "Giáo viên phụ trách (*)",
      "warn_no_teacher": "Không tìm thấy giáo viên hợp lệ.",
      "btn_create": "TẠO LỚP HỌC",
      "err_fields": "⚠️ Vui lòng điền đủ thông tin có dấu (*)",
      "success_created": "✅ Tạo lớp thành công!",
      "select_class": "Chọn lớp học cần quản lý:",
      "sub_students": "Danh Sách Học Viên",
      "sub_edit": "Cập Nhật Thông Tin",
      "sub_delete": "Xóa Lớp Học",
      "lbl_teacher": "Đổi giáo viên phụ trách:",
      "no_classes": "Hệ thống chưa có lớp học nào.",
      "no_students": "Lớp học này hiện chưa có học sinh nào.",
      "btn_remove": "Xóa khỏi lớp",
      "success_removed": "Đã xóa học sinh khỏi lớp!",
      "btn_save": "LƯU THAY ĐỔI",
      "success_updated": "Cập nhật thông tin lớp thành công!",
      "warn_delete": "CẢNH BÁO: Hành động này là vĩnh viễn và không thể khôi phục. Toàn bộ dữ liệu của lớp học này sẽ bị xóa bỏ khỏi hệ thống!",
      "btn_delete": "XÁC NHẬN XÓA LỚP",
      "success_deleted": "Đã xóa lớp thành công!",
      "msg_error": "Lỗi kết nối đến máy chủ. Vui lòng thử lại.",
      "unassigned": "Chưa cập nhật"
    },
    "en": {
      "title": "Class Management",
      "subtitle": "Create classes, assign teachers, and manage students.",
      "tab_create": "Create Class",
      "tab_manage": "Manage Classes",
      "form_create_header": "New Class Information",
      "input_name": "Class Name (*)",
      "input_desc": "Internal Notes",
      "input_teacher": "Assigned Teacher (*)",
      "warn_no_teacher": "No valid teachers found.",
      "btn_create": "CREATE CLASS",
      "err_fields": "⚠️ Please fill in all required fields (*)",
      "success_created": "✅ Class created successfully!",
      "select_class": "Select a class to manage:",
      "sub_students": "Students List",
      "sub_edit": "Update Info",
      "sub_delete": "Delete Class",
      "lbl_teacher": "Change Teacher:",
      "no_classes": "No classes available in the system.",
      "no_students": "There are no students in this class currently.",
      "btn_remove": "Remove",
      "success_removed": "Student removed successfully!",
      "btn_save": "SAVE CHANGES",
      "success_updated": "Class updated successfully!",
      "warn_delete": "WARNING: This action is permanent and cannot be undone. All data will be erased!",
      "btn_delete": "CONFIRM DELETE",
      "success_deleted": "Class deleted successfully!",
      "msg_error": "Server connection error. Please try again.",
      "unassigned": "Unassigned"
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
      // ✅ ĐỌC NGÔN NGỮ TỪ BỘ NHỚ LÚC KHỞI TẠO
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

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
      var res = await http.get(Uri.parse('${AppConfig.apiTv1}/teachers'), headers: headers).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        var data = jsonDecode(utf8.decode(res.bodyBytes));
        if (data is List && data.isNotEmpty) {
          _teachers = data;
          return;
        }
      }
      
      res = await http.get(Uri.parse('${AppConfig.apiAuth}/users'), headers: headers).timeout(const Duration(seconds: 5));
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
      final res = await http.get(Uri.parse('${AppConfig.apiTv1}/classes')).timeout(const Duration(seconds: 10));
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
      final headers = {"Authorization": "Bearer $_token"};
      final res = await http.get(Uri.parse('${AppConfig.apiTv1}/classes/$classId/students/details'), headers: headers);
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

  Future<void> _createClass() async {
    final labels = _locales[_lang]!;
    if (_createNameCtrl.text.trim().isEmpty || _createTeacherId == null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["err_fields"]!), backgroundColor: Colors.orange));
      return;
    }

    setState(() => _isLoading = true);
    try {
      final teacher = _teachers.firstWhere((t) => (t['id'] ?? t['_id']).toString() == _createTeacherId);
      final payload = {
        "class_name": _createNameCtrl.text.trim(),
        "subject": "Unassigned",
        "teacher_id": _createTeacherId,
        "teacher_name": teacher['name'] ?? teacher['full_name'],
        "student_ids": [],
        "is_public": false,
        "description": _createDescCtrl.text.trim(),
        "status": "active"
      };

      final res = await http.post(
        Uri.parse('${AppConfig.apiTv1}/classes/create'),
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
    final labels = _locales[_lang]!;
    if (_editNameCtrl.text.trim().isEmpty) {
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
        Uri.parse('${AppConfig.apiTv1}/classes/$_selectedClassId'),
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
    final labels = _locales[_lang]!;
    setState(() => _isLoading = true);
    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiTv1}/classes/$_selectedClassId'),
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
    final labels = _locales[_lang]!;
    setState(() => _isLoading = true);
    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiTv1}/classes/$_selectedClassId/students/$studentId'),
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

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          backgroundColor: Colors.indigo,
          foregroundColor: Colors.white,
          actions: [
            // ✅ ĐÃ SỬA: Nút chuyển đổi ngôn ngữ ghi vào bộ nhớ
            TextButton(
              onPressed: () async {
                setState(() => _lang = _lang == "vi" ? "en" : "vi");
                await _storage.write(key: 'app_lang', value: _lang);
              },
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
                    height: 50,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                      onPressed: _createClass,
                      child: Text(labels["btn_create"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, letterSpacing: 1.2)),
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
      return Center(child: Text(labels["no_classes"]!, style: TextStyle(color: Colors.grey[600])));
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
              Text(labels["select_class"]!, style: const TextStyle(fontSize: 13, color: Colors.grey, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                isExpanded: true,
                value: _selectedClassId,
                decoration: const InputDecoration(border: OutlineInputBorder(), contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 10)),
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
                      if (!_teachers.any((t) => (t['id'] ?? t['_id']).toString() == _editTeacherId)) {
                        _editTeacherId = null; 
                      }
                    });
                    _fetchClassStudents(val);
                  }
                },
              )
            ],
          ),
        ),

        if (_selectedClassId != null) ...[
          // Thanh Sub-tabs
          Padding(
            padding: const EdgeInsets.all(12),
            child: Container(
              decoration: BoxDecoration(color: Colors.indigo[50], borderRadius: BorderRadius.circular(10)),
              child: Row(
                children: [
                  _buildSubTabBtn(0, Icons.people, labels["sub_students"]!),
                  _buildSubTabBtn(1, Icons.edit, labels["sub_edit"]!),
                  _buildSubTabBtn(2, Icons.delete_forever, labels["sub_delete"]!),
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
              const SizedBox(height: 4),
              Text(title, textAlign: TextAlign.center, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isSelected ? Colors.white : Colors.indigo[300])),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSubTabContent(Map<String, String> labels) {
    if (_subTabIndex == 0) {
      if (_studentsInClass.isEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.only(top: 40), 
            child: Column(
              children: [
                Icon(Icons.person_off, size: 60, color: Colors.grey.shade400),
                const SizedBox(height: 10),
                Text(labels["no_students"]!, style: const TextStyle(color: Colors.grey, fontSize: 16)),
              ],
            )
          )
        );
      }
      
      return ListView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: _studentsInClass.length,
        itemBuilder: (context, index) {
          final student = _studentsInClass[index];
          String sId = student['Mã HS']?.toString() ?? student['id']?.toString() ?? student['_id']?.toString() ?? '';
          String sName = student['Tên Học Sinh']?.toString() ?? student['name']?.toString() ?? labels["unassigned"]!;
          
          return Card(
            margin: const EdgeInsets.only(bottom: 10),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            child: ListTile(
              leading: const CircleAvatar(backgroundColor: Colors.indigo, child: Icon(Icons.person, color: Colors.white)),
              title: Text(sName, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text("ID: $sId"),
              trailing: IconButton(
                icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
                tooltip: labels["btn_remove"],
                onPressed: () => _removeStudent(sId),
              ),
            ),
          );
        },
      );

    } else if (_subTabIndex == 1) {
      return Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(controller: _editNameCtrl, decoration: InputDecoration(labelText: labels["input_name"])),
              const SizedBox(height: 10),
              TextField(controller: _editDescCtrl, maxLines: 3, decoration: InputDecoration(labelText: labels["input_desc"])),
              const SizedBox(height: 20),
              DropdownButtonFormField<String>(
                decoration: InputDecoration(labelText: labels["lbl_teacher"]),
                value: _editTeacherId,
                items: _teachers.map((t) {
                  String tId = (t['id'] ?? t['_id']).toString();
                  String tName = t['name'] ?? t['full_name'] ?? labels["unassigned"]!;
                  return DropdownMenuItem(value: tId, child: Text(tName));
                }).toList(),
                onChanged: (val) => setState(() => _editTeacherId = val),
              ),
              const SizedBox(height: 25),
              SizedBox(
                width: double.infinity,
                height: 45,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.save),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white),
                  onPressed: _updateClass,
                  label: Text(labels["btn_save"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
              )
            ],
          ),
        ),
      );

    } else {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: Colors.red[50], borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.red[200]!)),
        child: Column(
          children: [
            const Icon(Icons.warning_amber_rounded, color: Colors.red, size: 60),
            const SizedBox(height: 15),
            Text(labels["warn_delete"]!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red, fontSize: 14)),
            const SizedBox(height: 25),
            SizedBox(
              width: double.infinity,
              height: 45,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.delete_forever),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
                onPressed: _deleteClass,
                label: Text(labels["btn_delete"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              ),
            )
          ],
        ),
      );
    }
  }
}