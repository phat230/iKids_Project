import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../core/config.dart';

class AdminStaffManagementScreen extends StatefulWidget {
  const AdminStaffManagementScreen({super.key});

  @override
  State<AdminStaffManagementScreen> createState() => _AdminStaffManagementScreenState();
}

class _AdminStaffManagementScreenState extends State<AdminStaffManagementScreen> {
  final _storage = const FlutterSecureStorage();
  bool _isLoading = true;
  String _token = "";
  
  // ✅ ĐÃ SỬA: Đường dẫn chuẩn xác theo Backend FastAPI
  String get _apiBase => '${AppConfig.apiTv1}/staff'; 

  List<dynamic> _allStaff = [];
  List<dynamic> _filteredStaff = [];
  final _searchCtrl = TextEditingController();
  String _selectedFilterRole = "All";

  // Form State
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _pwdCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  String _selectedRole = "teacher";

  // Phụ huynh Logic
  String _linkMode = "existing"; 
  String? _selectedParentId;
  final _pNameCtrl = TextEditingController();
  final _pEmailCtrl = TextEditingController();
  final _pPwdCtrl = TextEditingController();
  final _pPhoneCtrl = TextEditingController();

  final Map<String, String> _roleMap = {
    "Giáo viên (Teacher)": "teacher",
    "Vận hành (Operator)": "operator",
    "Quản trị viên (Admin)": "admin",
    "Phụ huynh (Parent)": "parent",
    "Học sinh (Student)": "student"
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
      await _fetchStaff();
    } catch (e) {
      debugPrint("Lỗi khởi tạo: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _fetchStaff() async {
    final headers = {"Authorization": "Bearer $_token"};
    try {
      final res = await http.get(Uri.parse(_apiBase), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));
        if (data is List) {
          setState(() {
            _allStaff = data;
            _applyFilters();
          });
        }
      } else {
        debugPrint("Lỗi fetch: ${res.statusCode} - ${res.body}");
      }
    } catch (e) {
      debugPrint("Không thể tải danh sách tài khoản: $e");
    }
  }

  void _applyFilters() {
    String query = _searchCtrl.text.toLowerCase().trim();
    setState(() {
      _filteredStaff = _allStaff.where((user) {
        bool matchesSearch = (user['name'] ?? user['full_name'] ?? '').toString().toLowerCase().contains(query) ||
            (user['email'] ?? '').toString().toLowerCase().contains(query);
        bool matchesRole = _selectedFilterRole == "All" || user['role'] == _selectedFilterRole || user['quyen'] == _selectedFilterRole;
        return matchesSearch && matchesRole;
      }).toList();
    });
  }

  // --- API ACTIONS ---
  Future<void> _provisionAccount() async {
    final name = _nameCtrl.text.trim();
    final email = _emailCtrl.text.trim().toLowerCase();
    final pwd = _pwdCtrl.text;
    final phone = _phoneCtrl.text.trim();

    if (name.isEmpty || email.isEmpty || pwd.isEmpty) {
      _showSnackbar("Vui lòng điền đủ thông tin (*)", Colors.orange);
      return;
    }

    setState(() => _isLoading = true);
    String? finalParentId = _selectedParentId;

    try {
      // 1. Tạo phụ huynh mới nếu cần
      if (_selectedRole == "student" && _linkMode == "new") {
        final pName = _pNameCtrl.text.trim();
        final pEmail = _pEmailCtrl.text.trim().toLowerCase();
        
        if (pName.isEmpty || pEmail.isEmpty || _pPwdCtrl.text.isEmpty) {
          _showSnackbar("Thiếu thông tin phụ huynh mới", Colors.orange);
          setState(() => _isLoading = false);
          return;
        }

        final pRes = await http.post(
          Uri.parse('$_apiBase/add'),
          headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
          body: jsonEncode({
            "name": pName, "role": "parent", "email": pEmail, "password": _pPwdCtrl.text, "phone": _pPhoneCtrl.text.trim(), "status": "Đang làm việc", "is_active": true
          })
        );

        if (pRes.statusCode == 200 || pRes.statusCode == 201) {
          await _fetchStaff();
          final freshParent = _allStaff.firstWhere((p) => p['email'] == pEmail, orElse: () => null);
          if (freshParent != null) finalParentId = freshParent['id']?.toString() ?? freshParent['_id']?.toString();
        } else {
          _showSnackbar("Lỗi tạo phụ huynh", Colors.red);
          setState(() => _isLoading = false);
          return;
        }
      }

      if (_selectedRole == "student" && finalParentId == null) {
        _showSnackbar("Học sinh bắt buộc phải có Phụ huynh liên kết", Colors.red);
        setState(() => _isLoading = false);
        return;
      }

      // 2. Tạo tài khoản chính
      final payload = {
        "name": name, "role": _selectedRole, "email": email, "password": pwd, "phone": phone, "status": "Đang làm việc", "is_active": true
      };
      if (_selectedRole == "student" && finalParentId != null) payload["student_id_ref"] = finalParentId;

      final res = await http.post(
        Uri.parse('$_apiBase/add'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload)
      );

      if (res.statusCode == 200 || res.statusCode == 201) {
        _showSnackbar("Tạo tài khoản thành công!", Colors.green);
        _clearFormFields();
        Navigator.pop(context);
        await _fetchStaff();
      } else {
        _showSnackbar("Lỗi máy chủ: ${res.body}", Colors.red);
      }
    } catch (e) {
      _showSnackbar("Có lỗi xảy ra", Colors.red);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _openCreateDialog() {
    _clearFormFields();
    _selectedRole = "teacher";
    _linkMode = "existing";
    _selectedParentId = null;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (BuildContext context, StateSetter setModalState) {
            final availableParents = _allStaff.where((s) => s['role'] == 'parent' || s['quyen'] == 'parent').toList();
            if (_selectedParentId != null && !availableParents.any((p) => (p['id']?.toString() ?? p['_id']?.toString()) == _selectedParentId)) {
              _selectedParentId = null;
            }

            return Container(
              padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 20, right: 20, top: 20),
              decoration: const BoxDecoration(color: Colors.white, borderRadius: BorderRadius.vertical(top: Radius.circular(25))),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Cấp Tài Khoản Mới", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.redAccent)),
                    const SizedBox(height: 15),
                    
                    TextField(controller: _nameCtrl, decoration: const InputDecoration(labelText: "Họ và tên (*)", border: OutlineInputBorder())),
                    const SizedBox(height: 10),
                    
                    DropdownButtonFormField<String>(
                      value: _selectedRole,
                      decoration: const InputDecoration(labelText: "Vai trò hệ thống (*)", border: OutlineInputBorder()),
                      items: _roleMap.entries.map((e) => DropdownMenuItem(value: e.value, child: Text(e.key))).toList(),
                      onChanged: (v) {
                        setModalState(() {
                          _selectedRole = v ?? "teacher";
                          if (_selectedRole != "student") _selectedParentId = null;
                        });
                      },
                    ),
                    const SizedBox(height: 10),

                    if (_selectedRole == "student") ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(color: Colors.indigo[50], borderRadius: BorderRadius.circular(10)),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("🔗 Bảo lãnh Phụ Huynh", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo)),
                            Row(
                              children: [
                                Radio<String>(value: "existing", groupValue: _linkMode, onChanged: (v) => setModalState(() => _linkMode = v ?? "existing")),
                                const Text("Đã có tài khoản"),
                                const SizedBox(width: 10),
                                Radio<String>(value: "new", groupValue: _linkMode, onChanged: (v) => setModalState(() => _linkMode = v ?? "new")),
                                const Text("Phụ huynh mới"),
                              ],
                            ),
                            if (_linkMode == "existing") ...[
                              DropdownButtonFormField<String>(
                                decoration: const InputDecoration(labelText: "Chọn Phụ huynh", filled: true, fillColor: Colors.white),
                                value: _selectedParentId,
                                items: availableParents.map((p) {
                                  return DropdownMenuItem(value: (p['id']?.toString() ?? p['_id']?.toString() ?? ''), child: Text("${p['name'] ?? p['full_name']}"));
                                }).toList(),
                                onChanged: (v) => setModalState(() => _selectedParentId = v),
                              )
                            ] else ...[
                              TextField(controller: _pNameCtrl, decoration: const InputDecoration(labelText: "Tên Phụ huynh (*)", filled: true, fillColor: Colors.white)),
                              const SizedBox(height: 5),
                              TextField(controller: _pEmailCtrl, decoration: const InputDecoration(labelText: "Email Phụ huynh (*)", filled: true, fillColor: Colors.white)),
                              const SizedBox(height: 5),
                              TextField(controller: _pPwdCtrl, obscureText: true, decoration: const InputDecoration(labelText: "Mật khẩu (*)", filled: true, fillColor: Colors.white)),
                            ]
                          ],
                        ),
                      ),
                      const SizedBox(height: 10),
                    ],

                    TextField(controller: _emailCtrl, decoration: const InputDecoration(labelText: "Email Đăng nhập (*)", border: OutlineInputBorder())),
                    const SizedBox(height: 10),
                    TextField(controller: _pwdCtrl, obscureText: true, decoration: const InputDecoration(labelText: "Mật khẩu tạm thời (*)", border: OutlineInputBorder())),
                    const SizedBox(height: 10),
                    TextField(controller: _phoneCtrl, decoration: const InputDecoration(labelText: "Số điện thoại", border: OutlineInputBorder())),
                    
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity, height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                        onPressed: () {
                          setState(() {});
                          _provisionAccount();
                        },
                        child: const Text("TẠO TÀI KHOẢN", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            );
          }
        );
      }
    );
  }

  void _openEditDialog(Map<String, dynamic> user) {
    final nameCtrl = TextEditingController(text: user['name'] ?? user['full_name'] ?? '');
    final phoneCtrl = TextEditingController(text: user['phone'] ?? user['phone_number'] ?? '');
    String status = user['status'] ?? 'Đang làm việc';

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Sửa Thông Tin"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: "Tên")),
            TextField(controller: phoneCtrl, decoration: const InputDecoration(labelText: "Điện thoại")),
            DropdownButtonFormField<String>(
              value: status,
              items: ["Đang làm việc", "Nghỉ phép", "Vô hiệu hóa", "Nghỉ việc"].map((o) => DropdownMenuItem(value: o, child: Text(o))).toList(),
              onChanged: (v) => status = v ?? status,
            )
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Hủy")),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await http.put(
                Uri.parse('$_apiBase/${user['id'] ?? user['_id']}'),
                headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
                body: jsonEncode({"name": nameCtrl.text, "phone": phoneCtrl.text, "status": status})
              );
              _initData();
            },
            child: const Text("Lưu"),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text("Hệ Thống Nhân Sự", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.redAccent,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Colors.redAccent,
        onPressed: _openCreateDialog,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text("Cấp Tài Khoản", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.redAccent))
          : Column(
              children: [
                Container(
                  color: Colors.white,
                  padding: const EdgeInsets.all(15),
                  child: Row(
                    children: [
                      Expanded(
                        flex: 2,
                        child: TextField(
                          controller: _searchCtrl,
                          onChanged: (v) => _applyFilters(),
                          decoration: InputDecoration(
                            hintText: "Tìm kiếm...",
                            prefixIcon: const Icon(Icons.search),
                            contentPadding: const EdgeInsets.symmetric(vertical: 0),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: _selectedFilterRole,
                          decoration: InputDecoration(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          items: ["All", "admin", "operator", "teacher", "parent", "student"]
                              .map((r) => DropdownMenuItem(value: r, child: Text(r.toUpperCase(), style: const TextStyle(fontSize: 12)))).toList(),
                          onChanged: (v) {
                            setState(() {
                              _selectedFilterRole = v ?? "All";
                              _applyFilters();
                            });
                          },
                        ),
                      )
                    ],
                  ),
                ),
                Expanded(
                  child: _filteredStaff.isEmpty
                      ? const Center(child: Text("Không có tài khoản nào.", style: TextStyle(color: Colors.grey)))
                      : ListView.builder(
                          padding: const EdgeInsets.all(15),
                          itemCount: _filteredStaff.length,
                          itemBuilder: (context, index) {
                            final user = _filteredStaff[index];
                            final roleColor = _getRoleColor(user['role'] ?? user['quyen']);
                            final isActive = user['is_active'] == true;

                            return Card(
                              elevation: 2,
                              margin: const EdgeInsets.only(bottom: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                              child: ListTile(
                                leading: CircleAvatar(backgroundColor: roleColor.withOpacity(0.2), child: Icon(Icons.person, color: roleColor)),
                                title: Text(user['name'] ?? user['full_name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const SizedBox(height: 5),
                                    Text(user['email'] ?? '', style: const TextStyle(color: Colors.grey)),
                                    const SizedBox(height: 5),
                                    Row(
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(color: roleColor, borderRadius: BorderRadius.circular(5)),
                                          child: Text((user['role'] ?? user['quyen'] ?? 'Unknown').toString().toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                                        ),
                                        const SizedBox(width: 10),
                                        Icon(Icons.circle, size: 10, color: isActive ? Colors.green : Colors.red),
                                        const SizedBox(width: 5),
                                        Text(isActive ? "Hoạt động" : "Bị khóa", style: TextStyle(fontSize: 10, color: isActive ? Colors.green : Colors.red)),
                                      ],
                                    )
                                  ],
                                ),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    IconButton(icon: const Icon(Icons.edit, color: Colors.blue), onPressed: () => _openEditDialog(user)),
                                    IconButton(
                                      icon: const Icon(Icons.delete, color: Colors.red), 
                                      onPressed: () async {
                                        await http.delete(Uri.parse('$_apiBase/${user['id'] ?? user['_id']}'), headers: {"Authorization": "Bearer $_token"});
                                        _initData();
                                      }
                                    ),
                                  ],
                                )
                              ),
                            );
                          },
                        ),
                )
              ],
            ),
    );
  }

  Color _getRoleColor(String? role) {
    switch (role) {
      case "admin": return Colors.red;
      case "operator": return Colors.orange;
      case "teacher": return Colors.green;
      case "parent": return Colors.purple;
      case "student": return Colors.blue;
      default: return Colors.grey;
    }
  }

  void _showSnackbar(String msg, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: color));
  }

  void _clearFormFields() {
    _nameCtrl.clear(); _emailCtrl.clear(); _pwdCtrl.clear(); _phoneCtrl.clear();
    _pNameCtrl.clear(); _pEmailCtrl.clear(); _pPwdCtrl.clear(); _pPhoneCtrl.clear();
  }
}