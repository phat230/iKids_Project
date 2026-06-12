import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart';
import '../../core/config.dart';

class ParentChildManagementScreen extends StatefulWidget {
  const ParentChildManagementScreen({super.key});

  @override
  State<ParentChildManagementScreen> createState() => _ParentChildManagementScreenState();
}

class _ParentChildManagementScreenState extends State<ParentChildManagementScreen> {
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = true;
  String _lang = "vi";
  String _parentId = "";
  String _token = "";
  double _parentBalance = 0.0;

  List<dynamic> _children = [];
  List<dynamic> _purchaseRequests = [];
  List<dynamic> _transactionHistory = [];

  // Controllers cho Tab Thêm bé
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  DateTime _selectedDate = DateTime(2018, 1, 1);

  // Bộ từ điển (Rút gọn cho Mobile)
  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Quản Lý Con Em",
      "tab_list": "Danh sách",
      "tab_approve": "Phê duyệt",
      "tab_add": "Thêm bé",
      "tab_history": "Lịch sử",
      "lbl_wallet": "Số dư của bạn:",
      "btn_deposit": "Nạp tiền",
      "no_child": "Bạn chưa liên kết tài khoản con.",
      "lbl_child_wallet": "Ví của con:",
      "btn_send": "Gửi tiền",
      "btn_withdraw": "Rút tiền",
      "no_requests": "🎉 Không có yêu cầu mua sắm nào.",
      "wants_buy": "muốn mua",
      "lbl_price": "Giá:",
      "btn_approve": "Duyệt",
      "btn_reject": "Từ chối",
      "lbl_create_acc": "Tạo tài khoản cho bé",
      "btn_create": "Tạo & Liên kết",
      "success_created": "Tạo tài khoản thành công!",
      "no_history": "Chưa có lịch sử giao dịch."
    },
    "en": {
      "title": "Manage Children",
      "tab_list": "Directory",
      "tab_approve": "Approvals",
      "tab_add": "Add Child",
      "tab_history": "History",
      "lbl_wallet": "Your Balance:",
      "btn_deposit": "Top Up",
      "no_child": "No linked child accounts.",
      "lbl_child_wallet": "Child's Wallet:",
      "btn_send": "Send",
      "btn_withdraw": "Withdraw",
      "no_requests": "🎉 No pending purchase requests.",
      "wants_buy": "wants to buy",
      "lbl_price": "Price:",
      "btn_approve": "Approve",
      "btn_reject": "Reject",
      "lbl_create_acc": "Create Child Account",
      "btn_create": "Create & Link",
      "success_created": "Account created successfully!",
      "no_history": "No transaction history."
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
      _parentId = await _storage.read(key: 'user_id') ?? "";

      if (_token.isEmpty || _parentId.isEmpty) return;
      final headers = {"Authorization": "Bearer $_token", "parent-id": _parentId};

      // Gọi đồng loạt 4 API
      final responses = await Future.wait([
        http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/gamification/profile/$_parentId'), headers: headers),
        http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/parent/my-children'), headers: headers),
        http.get(Uri.parse('${AppConfig.apiUrl}/api/tv3/parent/purchase-requests'), headers: headers),
        http.get(Uri.parse('${AppConfig.apiUrl}/api/finance/parent/history'), headers: headers),
      ]);

      if (mounted) {
        setState(() {
          if (responses[0].statusCode == 200) _parentBalance = (jsonDecode(responses[0].body)['balance'] ?? 0).toDouble();
          if (responses[1].statusCode == 200) _children = jsonDecode(utf8.decode(responses[1].bodyBytes));
          if (responses[2].statusCode == 200) _purchaseRequests = jsonDecode(utf8.decode(responses[2].bodyBytes));
          if (responses[3].statusCode == 200) _transactionHistory = jsonDecode(utf8.decode(responses[3].bodyBytes));
        });
      }
    } catch (e) {
      debugPrint("Lỗi tải dữ liệu Quản lý: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // --- API Gửi / Rút tiền ---
  Future<void> _handleMoney(String endpoint, String childId, String title) async {
    final amtCtrl = TextEditingController();
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: TextField(controller: amtCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: "Số tiền (VNĐ)", border: OutlineInputBorder())),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Hủy")),
          ElevatedButton(
            onPressed: () async {
              double amount = double.tryParse(amtCtrl.text) ?? 0;
              if (amount <= 0) return;
              Navigator.pop(ctx);
              
              showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator()));
              try {
                final res = await http.post(
                  Uri.parse('${AppConfig.apiUrl}/api/tv3/parent/$endpoint'),
                  headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
                  body: jsonEncode({"child_id": childId, "amount": amount})
                );
                Navigator.pop(context);
                if (res.statusCode == 200) _initData(); // Cập nhật lại list
              } catch (e) {
                Navigator.pop(context);
              }
            },
            child: const Text("Xác nhận"),
          )
        ],
      )
    );
  }

  // --- API Duyệt yêu cầu ---
  Future<void> _handleApproval(String reqId, String action) async {
    try {
      final res = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/tv3/parent/approve-purchase/$reqId'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode({"action": action})
      );
      if (res.statusCode == 200) _initData();
    } catch (e) {
      debugPrint("Lỗi duyệt: $e");
    }
  }

  // --- API Tạo tài khoản con ---
  Future<void> _createChild() async {
    if (_nameController.text.isEmpty || _emailController.text.isEmpty || _passController.text.isEmpty) return;
    showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator()));
    
    try {
      final payload = {
        "name": _nameController.text.trim(),
        "email": _emailController.text.trim().toLowerCase(),
        "password": _passController.text,
        "role": "student",
        "birth_date": DateFormat('yyyy-MM-dd').format(_selectedDate),
      };

      final res = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/auth/parent/create-student'),
        headers: {"Content-Type": "application/json", "parent-id": _parentId},
        body: jsonEncode(payload)
      );
      
      Navigator.pop(context);
      if (res.statusCode == 200) {
        _nameController.clear(); _emailController.clear(); _passController.clear();
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_labels[_lang]!["success_created"]!), backgroundColor: Colors.green));
        _initData();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lỗi tạo tài khoản!"), backgroundColor: Colors.red));
      }
    } catch (e) {
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return DefaultTabController(
      length: 4,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          backgroundColor: Colors.indigo,
          foregroundColor: Colors.white,
          actions: [
            TextButton(onPressed: () => setState(() => _lang = _lang == "vi" ? "en" : "vi"), child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white)))
          ],
          bottom: TabBar(
            isScrollable: true,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white60,
            indicatorColor: Colors.amber,
            indicatorWeight: 3,
            tabs: [
              Tab(icon: const Icon(Icons.people), text: labels["tab_list"]),
              Tab(icon: const Icon(Icons.check_circle), text: labels["tab_approve"]),
              Tab(icon: const Icon(Icons.person_add), text: labels["tab_add"]),
              Tab(icon: const Icon(Icons.history), text: labels["tab_history"]),
            ],
          ),
        ),
        body: _isLoading 
          ? const Center(child: CircularProgressIndicator()) 
          : TabBarView(
              children: [
                _buildListTab(labels),
                _buildApproveTab(labels),
                _buildAddChildTab(labels),
                _buildHistoryTab(labels),
              ],
            ),
      ),
    );
  }

  // ================= TAB 1: DANH SÁCH & VÍ TIỀN =================
  Widget _buildListTab(Map<String, String> labels) {
    return Column(
      children: [
        // Banner Số dư
        Container(
          padding: const EdgeInsets.all(15),
          color: Colors.indigo[50],
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("${labels['lbl_wallet']} ${_parentBalance.toStringAsFixed(0)} VNĐ", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.indigo)),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(horizontal: 10)),
                icon: const Icon(Icons.add, size: 16),
                label: Text(labels["btn_deposit"]!),
                onPressed: () => Navigator.pop(context), // Đóng màn hình này để phụ huynh tự ấn vào mục Học Phí ở ngoài
              )
            ],
          ),
        ),
        Expanded(
          child: _children.isEmpty 
            ? Center(child: Text(labels["no_child"]!))
            : ListView.builder(
                padding: const EdgeInsets.all(12),
                itemCount: _children.length,
                itemBuilder: (context, index) {
                  final child = _children[index];
                  String cId = child['id'] ?? child['_id'];
                  return Card(
                    elevation: 2,
                    child: ExpansionTile(
                      leading: const CircleAvatar(backgroundColor: Colors.amber, child: Icon(Icons.face, color: Colors.white)),
                      title: Text(child['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text("${labels['lbl_child_wallet']} ${child['balance'] ?? 0} VNĐ", style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                      childrenPadding: const EdgeInsets.all(15),
                      children: [
                        Row(
                          children: [
                            Expanded(child: OutlinedButton(onPressed: () => _handleMoney("withdraw-from-child", cId, "Rút tiền từ con"), child: Text(labels["btn_withdraw"]!))),
                            const SizedBox(width: 10),
                            Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white), onPressed: () => _handleMoney("transfer-to-child", cId, "Gửi tiền cho con"), child: Text(labels["btn_send"]!))),
                          ],
                        )
                      ],
                    ),
                  );
                },
              ),
        )
      ],
    );
  }

  // ================= TAB 2: PHÊ DUYỆT MUA SẮM =================
  Widget _buildApproveTab(Map<String, String> labels) {
    if (_purchaseRequests.isEmpty) return Center(child: Text(labels["no_requests"]!));

    return ListView.builder(
      padding: const EdgeInsets.all(15),
      itemCount: _purchaseRequests.length,
      itemBuilder: (context, index) {
        final req = _purchaseRequests[index];
        return Card(
          elevation: 2,
          margin: const EdgeInsets.only(bottom: 15),
          child: Padding(
            padding: const EdgeInsets.all(15),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("👤 ${req['child_name']} ${labels['wants_buy']} ${req['product_name']}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                const SizedBox(height: 5),
                Text("${labels['lbl_price']} ${req['price']} VNĐ", style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
                const Divider(),
                Row(
                  children: [
                    Expanded(child: OutlinedButton(onPressed: () => _handleApproval(req['id'], "reject"), style: OutlinedButton.styleFrom(foregroundColor: Colors.red), child: Text(labels["btn_reject"]!))),
                    const SizedBox(width: 10),
                    Expanded(child: ElevatedButton(onPressed: () => _handleApproval(req['id'], "approve"), style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white), child: Text(labels["btn_approve"]!))),
                  ],
                )
              ],
            ),
          ),
        );
      },
    );
  }

  // ================= TAB 3: TẠO TÀI KHOẢN CON =================
  Widget _buildAddChildTab(Map<String, String> labels) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Card(
        elevation: 2,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(labels["lbl_create_acc"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 20),
              TextField(controller: _nameController, decoration: const InputDecoration(labelText: "Họ và tên bé (*)", border: OutlineInputBorder())),
              const SizedBox(height: 15),
              TextField(controller: _emailController, decoration: const InputDecoration(labelText: "Email đăng nhập (*)", border: OutlineInputBorder())),
              const SizedBox(height: 15),
              TextField(controller: _passController, obscureText: true, decoration: const InputDecoration(labelText: "Mật khẩu (*)", border: OutlineInputBorder())),
              const SizedBox(height: 15),
              InkWell(
                onTap: () async {
                  final DateTime? picked = await showDatePicker(context: context, initialDate: _selectedDate, firstDate: DateTime(2000), lastDate: DateTime.now());
                  if (picked != null) setState(() => _selectedDate = picked);
                },
                child: Container(
                  padding: const EdgeInsets.all(15),
                  decoration: BoxDecoration(border: Border.all(color: Colors.grey), borderRadius: BorderRadius.circular(4)),
                  child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Text("Ngày sinh: ${DateFormat('dd/MM/yyyy').format(_selectedDate)}"), const Icon(Icons.calendar_today)]),
                ),
              ),
              const SizedBox(height: 25),
              SizedBox(width: double.infinity, height: 45, child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white), onPressed: _createChild, child: Text(labels["btn_create"]!)))
            ],
          ),
        ),
      ),
    );
  }

  // ================= TAB 4: LỊCH SỬ GIAO DỊCH =================
  Widget _buildHistoryTab(Map<String, String> labels) {
    if (_transactionHistory.isEmpty) return Center(child: Text(labels["no_history"]!));

    return ListView.builder(
      padding: const EdgeInsets.all(10),
      itemCount: _transactionHistory.length,
      itemBuilder: (context, index) {
        final item = _transactionHistory[index];
        double amount = (item['amount'] ?? item['price'] ?? item['total_amount'] ?? 0).toDouble();
        String group = item['group'] ?? 'Khác';
        
        return Card(
          child: ListTile(
            leading: const CircleAvatar(backgroundColor: Colors.indigo, child: Icon(Icons.receipt_long, color: Colors.white)),
            title: Text(group, style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(item['created_at']?.toString().substring(0, 10) ?? ''),
            trailing: Text("${amount > 0 ? '+' : ''}${amount.toStringAsFixed(0)} VNĐ", style: TextStyle(color: amount >= 0 ? Colors.green : Colors.red, fontWeight: FontWeight.bold, fontSize: 14)),
          ),
        );
      },
    );
  }
}