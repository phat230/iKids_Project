import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../../core/config.dart';

class TuitionScreen extends StatefulWidget {
  const TuitionScreen({super.key});

  @override
  State<TuitionScreen> createState() => _TuitionScreenState();
}

class _TuitionScreenState extends State<TuitionScreen> {
  final _storage = const FlutterSecureStorage();

  bool _isLoading = true;
  String _lang = "vi";
  String _token = "";
  String _parentId = "";

  double _balance = 0.0;
  double _totalPending = 0.0;
  double _totalOverdue = 0.0;
  double _totalPaid = 0.0;

  List<dynamic> _children = [];
  List<dynamic> _pendingInvoices = [];
  List<dynamic> _overdueInvoices = [];
  List<dynamic> _paidInvoices = [];
  List<dynamic> _allInvoices = [];
  List<dynamic> _payments = [];

  String _selectedChildId = "__all__";

  String get _apiTuition => "${AppConfig.baseUrl}/api/tuition";

  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "Học Phí",
      "subtitle": "Theo dõi và đóng học phí bằng ví phụ huynh.",
      "wallet": "Số dư ví",
      "pending": "Cần đóng",
      "overdue": "Quá hạn",
      "paid": "Đã đóng",
      "tab_unpaid": "Chưa đóng",
      "tab_paid": "Đã đóng",
      "tab_history": "Lịch sử",
      "tab_all": "Tất cả",
      "all_children": "Tất cả bé",
      "filter_child": "Lọc theo bé",
      "invoice_empty": "Không có hóa đơn nào.",
      "payment_empty": "Chưa có lịch sử thanh toán.",
      "class": "Lớp",
      "student": "Học sinh",
      "period": "Kỳ học phí",
      "amount": "Số tiền",
      "due_date": "Hạn đóng",
      "status": "Trạng thái",
      "paid_at": "Ngày đóng",
      "btn_pay": "Đóng học phí",
      "btn_confirm": "Xác nhận đóng",
      "btn_cancel": "Hủy",
      "confirm_title": "Xác nhận thanh toán",
      "confirm_msg": "Bạn có chắc muốn đóng học phí hóa đơn này?",
      "pay_success": "Đóng học phí thành công!",
      "pay_failed": "Thanh toán thất bại",
      "low_balance": "Số dư ví không đủ.",
      "network_error": "Lỗi kết nối mạng.",
      "status_pending": "Chưa đóng",
      "status_overdue": "Quá hạn",
      "status_paid": "Đã đóng",
      "status_cancelled": "Đã hủy",
      "method": "Phương thức",
      "balance_after": "Số dư sau thanh toán",
      "refresh": "Làm mới",
    },
    "en": {
      "title": "Tuition",
      "subtitle": "Track and pay tuition by parent wallet.",
      "wallet": "Wallet",
      "pending": "Pending",
      "overdue": "Overdue",
      "paid": "Paid",
      "tab_unpaid": "Unpaid",
      "tab_paid": "Paid",
      "tab_history": "History",
      "tab_all": "All",
      "all_children": "All children",
      "filter_child": "Filter by child",
      "invoice_empty": "No invoices found.",
      "payment_empty": "No payment history yet.",
      "class": "Class",
      "student": "Student",
      "period": "Period",
      "amount": "Amount",
      "due_date": "Due date",
      "status": "Status",
      "paid_at": "Paid at",
      "btn_pay": "Pay Tuition",
      "btn_confirm": "Confirm Payment",
      "btn_cancel": "Cancel",
      "confirm_title": "Confirm payment",
      "confirm_msg": "Are you sure you want to pay this invoice?",
      "pay_success": "Tuition paid successfully!",
      "pay_failed": "Payment failed",
      "low_balance": "Insufficient wallet balance.",
      "network_error": "Network error.",
      "status_pending": "Pending",
      "status_overdue": "Overdue",
      "status_paid": "Paid",
      "status_cancelled": "Cancelled",
      "method": "Method",
      "balance_after": "Balance after payment",
      "refresh": "Refresh",
    },
  };

  @override
  void initState() {
    super.initState();
    _initData();
  }

  Future<void> _initData() async {
    final savedLang = await _storage.read(key: 'app_lang');
    final savedToken = await _storage.read(key: 'jwt_token');
    final savedUserId = await _storage.read(key: 'user_id');

    if (!mounted) return;

    setState(() {
      _lang = savedLang ?? "vi";
      _token = savedToken ?? "";
      _parentId = savedUserId ?? "";
    });

    await _fetchAll();
  }

  Map<String, String> get _headers {
    return {
      "Content-Type": "application/json",
      if (_token.isNotEmpty) "Authorization": "Bearer $_token",
      if (_parentId.isNotEmpty) "parent-id": _parentId,
    };
  }

  Future<void> _fetchAll() async {
    if (!mounted) return;

    setState(() => _isLoading = true);

    try {
      final profileFuture = http.get(
        Uri.parse("${AppConfig.apiTv3}/gamification/profile/$_parentId"),
        headers: _headers,
      );

      final childrenFuture = http.get(
        Uri.parse("${AppConfig.apiTv3}/parent/my-children"),
        headers: _headers,
      );

      final summaryFuture = http.get(
        Uri.parse("$_apiTuition/parent/$_parentId/summary"),
        headers: _headers,
      );

      final pendingFuture = http.get(
        Uri.parse("$_apiTuition/parent/$_parentId/invoices?status=pending"),
        headers: _headers,
      );

      final overdueFuture = http.get(
        Uri.parse("$_apiTuition/parent/$_parentId/invoices?status=overdue"),
        headers: _headers,
      );

      final paidFuture = http.get(
        Uri.parse("$_apiTuition/parent/$_parentId/invoices?status=paid"),
        headers: _headers,
      );

      final allFuture = http.get(
        Uri.parse("$_apiTuition/parent/$_parentId/invoices"),
        headers: _headers,
      );

      final paymentsFuture = http.get(
        Uri.parse("$_apiTuition/parent/$_parentId/payments"),
        headers: _headers,
      );

      final responses = await Future.wait([
        profileFuture,
        childrenFuture,
        summaryFuture,
        pendingFuture,
        overdueFuture,
        paidFuture,
        allFuture,
        paymentsFuture,
      ]);

      final profileData = _decodeMap(responses[0]);
      final childrenData = _decodeListOrItems(responses[1]);
      final summaryData = _decodeMapData(responses[2]);

      final pendingData = _decodeListOrItems(responses[3]);
      final overdueData = _decodeListOrItems(responses[4]);
      final paidData = _decodeListOrItems(responses[5]);
      final allData = _decodeListOrItems(responses[6]);
      final paymentsData = _decodeListOrItems(responses[7]);

      if (!mounted) return;

      setState(() {
        _balance = _toDouble(profileData["balance"]);

        _children = childrenData;
        _pendingInvoices = pendingData;
        _overdueInvoices = overdueData;
        _paidInvoices = paidData;
        _allInvoices = allData;
        _payments = paymentsData;

        _totalPending = _toDouble(
          summaryData["total_pending"],
          _sumAmount(_pendingInvoices),
        );
        _totalOverdue = _toDouble(
          summaryData["total_overdue"],
          _sumAmount(_overdueInvoices),
        );
        _totalPaid = _toDouble(
          summaryData["total_paid"],
          _sumAmount(_paidInvoices),
        );

        if (_selectedChildId != "__all__") {
          final stillExists = _children.any(
            (c) => _getChildId(c) == _selectedChildId,
          );
          if (!stillExists) _selectedChildId = "__all__";
        }

        _isLoading = false;
      });
    } catch (e) {
      debugPrint("Lỗi tải học phí: $e");

      if (!mounted) return;

      setState(() => _isLoading = false);
      _showSnack(_labels[_lang]!["network_error"]!, Colors.red);
    }
  }

  Map<String, dynamic> _decodeMap(http.Response response) {
    try {
      if (response.statusCode != 200) return {};
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      if (data is Map<String, dynamic>) return data;
      return {};
    } catch (_) {
      return {};
    }
  }

  Map<String, dynamic> _decodeMapData(http.Response response) {
    try {
      if (response.statusCode != 200) return {};
      final data = jsonDecode(utf8.decode(response.bodyBytes));

      if (data is Map<String, dynamic>) {
        final inner = data["data"];
        if (inner is Map<String, dynamic>) return inner;
        return data;
      }

      return {};
    } catch (_) {
      return {};
    }
  }

  List<dynamic> _decodeListOrItems(http.Response response) {
    try {
      if (response.statusCode != 200) return [];

      final data = jsonDecode(utf8.decode(response.bodyBytes));

      if (data is List) return data;

      if (data is Map<String, dynamic>) {
        final items = data["items"];
        if (items is List) return items;
      }

      return [];
    } catch (_) {
      return [];
    }
  }

  double _toDouble(dynamic value, [double defaultValue = 0.0]) {
    if (value == null) return defaultValue;
    if (value is int) return value.toDouble();
    if (value is double) return value;
    return double.tryParse(value.toString()) ?? defaultValue;
  }

  double _sumAmount(List<dynamic> invoices) {
    double total = 0.0;

    for (final item in invoices) {
      if (item is Map) {
        total += _toDouble(item["amount"]);
      }
    }

    return total;
  }

  String _formatMoney(dynamic value) {
    final number = _toDouble(value);
    return "${number.toStringAsFixed(0)} VNĐ";
  }

  String _formatDateTime(dynamic value) {
    if (value == null) return "---";

    final raw = value.toString();

    try {
      final dt = DateTime.parse(raw);
      final d = dt.day.toString().padLeft(2, '0');
      final m = dt.month.toString().padLeft(2, '0');
      final y = dt.year.toString();
      final h = dt.hour.toString().padLeft(2, '0');
      final min = dt.minute.toString().padLeft(2, '0');
      return "$d/$m/$y $h:$min";
    } catch (_) {
      return raw;
    }
  }

  String _getChildId(dynamic child) {
    if (child is Map) {
      return (child["id"] ?? child["_id"] ?? "").toString();
    }
    return "";
  }

  String _getChildName(dynamic child) {
    final labels = _labels[_lang]!;

    if (child is Map) {
      final id = _getChildId(child);
      final suffix = id.length >= 4 ? id.substring(id.length - 4) : id;
      return (child["full_name"] ?? child["name"] ?? "Bé $suffix").toString();
    }

    return labels["student"]!;
  }

  String _getInvoiceId(dynamic invoice) {
    if (invoice is Map) {
      return (invoice["id"] ?? invoice["_id"] ?? "").toString();
    }
    return "";
  }

  String _getStatusLabel(String status) {
    final labels = _labels[_lang]!;

    switch (status) {
      case "pending":
        return labels["status_pending"]!;
      case "overdue":
        return labels["status_overdue"]!;
      case "paid":
        return labels["status_paid"]!;
      case "cancelled":
        return labels["status_cancelled"]!;
      default:
        return status;
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case "paid":
        return Colors.green;
      case "overdue":
        return Colors.red;
      case "cancelled":
        return Colors.grey;
      default:
        return Colors.orange;
    }
  }

  List<dynamic> _filterByChild(List<dynamic> list) {
    if (_selectedChildId == "__all__") return list;

    return list.where((item) {
      if (item is Map) {
        return item["student_id"]?.toString() == _selectedChildId;
      }
      return false;
    }).toList();
  }

  Future<void> _payInvoice(Map<String, dynamic> invoice) async {
    final labels = _labels[_lang]!;
    final invoiceId = _getInvoiceId(invoice);
    final amount = _toDouble(invoice["amount"]);

    if (_balance < amount) {
      _showSnack(labels["low_balance"]!, Colors.red);
      return;
    }

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(labels["confirm_title"]!),
          content: Text(labels["confirm_msg"]!),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(labels["btn_cancel"]!),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
              child: Text(labels["btn_confirm"]!),
            ),
          ],
        );
      },
    );

    if (confirm != true) return;

    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse("$_apiTuition/invoices/pay"),
        headers: _headers,
        body: jsonEncode({
          "invoice_id": invoiceId,
          "parent_id": _parentId,
        }),
      );

      if (response.statusCode == 200) {
        _showSnack(labels["pay_success"]!, Colors.green);
        await _fetchAll();
      } else {
        String msg = labels["pay_failed"]!;
        try {
          final data = jsonDecode(utf8.decode(response.bodyBytes));
          msg = data["detail"]?.toString() ?? msg;
        } catch (_) {}

        _showSnack(msg, Colors.red);

        if (mounted) setState(() => _isLoading = false);
      }
    } catch (e) {
      debugPrint("Lỗi thanh toán học phí: $e");
      _showSnack(labels["network_error"]!, Colors.red);

      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showSnack(String message, Color color) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _toggleLang() async {
    final newLang = _lang == "vi" ? "en" : "vi";

    setState(() => _lang = newLang);

    await _storage.write(key: 'app_lang', value: newLang);
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(
          labels["title"]!,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            tooltip: labels["refresh"],
            onPressed: _fetchAll,
            icon: const Icon(Icons.refresh),
          ),
          TextButton(
            onPressed: _toggleLang,
            child: Text(
              _lang.toUpperCase(),
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          )
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Colors.green),
            )
          : DefaultTabController(
              length: 4,
              child: Column(
                children: [
                  _buildHeader(labels),
                  _buildChildFilter(labels),
                  Material(
                    color: Colors.white,
                    child: TabBar(
                      labelColor: Colors.green[800],
                      unselectedLabelColor: Colors.black54,
                      indicatorColor: Colors.green,
                      isScrollable: true,
                      tabs: [
                        Tab(text: labels["tab_unpaid"]),
                        Tab(text: labels["tab_paid"]),
                        Tab(text: labels["tab_history"]),
                        Tab(text: labels["tab_all"]),
                      ],
                    ),
                  ),
                  Expanded(
                    child: TabBarView(
                      children: [
                        _buildInvoiceList(
                          _filterByChild([
                            ..._overdueInvoices,
                            ..._pendingInvoices,
                          ]),
                          allowPay: true,
                        ),
                        _buildInvoiceList(
                          _filterByChild(_paidInvoices),
                          allowPay: false,
                        ),
                        _buildPaymentList(
                          _filterByChild(_payments),
                        ),
                        _buildInvoiceList(
                          _filterByChild(_allInvoices),
                          allowPay: true,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildHeader(Map<String, String> labels) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      color: Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            labels["subtitle"]!,
            style: const TextStyle(color: Colors.black54),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildMetricCard(
                  title: labels["wallet"]!,
                  value: _formatMoney(_balance),
                  icon: Icons.account_balance_wallet,
                  color: Colors.green,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildMetricCard(
                  title: labels["pending"]!,
                  value: _formatMoney(_totalPending),
                  icon: Icons.receipt_long,
                  color: Colors.orange,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _buildMetricCard(
                  title: labels["overdue"]!,
                  value: _formatMoney(_totalOverdue),
                  icon: Icons.warning_amber,
                  color: Colors.red,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildMetricCard(
                  title: labels["paid"]!,
                  value: _formatMoney(_totalPaid),
                  icon: Icons.check_circle,
                  color: Colors.blue,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.18)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: color,
                    fontSize: 15,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 11,
                    color: Colors.black54,
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildChildFilter(Map<String, String> labels) {
    final items = <DropdownMenuItem<String>>[
      DropdownMenuItem(
        value: "__all__",
        child: Text(labels["all_children"]!),
      ),
      ..._children.map((child) {
        final id = _getChildId(child);
        return DropdownMenuItem(
          value: id,
          child: Text(_getChildName(child)),
        );
      }),
    ];

    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
      child: DropdownButtonFormField<String>(
        value: _selectedChildId,
        decoration: InputDecoration(
          labelText: labels["filter_child"],
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 10,
          ),
        ),
        items: items,
        onChanged: (value) {
          if (value == null) return;
          setState(() => _selectedChildId = value);
        },
      ),
    );
  }

  Widget _buildInvoiceList(List<dynamic> invoices, {required bool allowPay}) {
    final labels = _labels[_lang]!;

    if (invoices.isEmpty) {
      return RefreshIndicator(
        onRefresh: _fetchAll,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            const SizedBox(height: 160),
            Center(
              child: Text(
                labels["invoice_empty"]!,
                style: const TextStyle(color: Colors.black54),
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchAll,
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(12),
        itemCount: invoices.length,
        itemBuilder: (context, index) {
          final invoice = Map<String, dynamic>.from(invoices[index]);
          return _buildInvoiceCard(invoice, allowPay: allowPay);
        },
      ),
    );
  }

  Widget _buildInvoiceCard(
    Map<String, dynamic> invoice, {
    required bool allowPay,
  }) {
    final labels = _labels[_lang]!;
    final status = invoice["status"]?.toString() ?? "pending";
    final amount = _toDouble(invoice["amount"]);
    final canPay = allowPay && (status == "pending" || status == "overdue");
    final enoughBalance = _balance >= amount;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    invoice["period_label"]?.toString() ?? labels["period"]!,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: _statusColor(status).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    _getStatusLabel(status),
                    style: TextStyle(
                      color: _statusColor(status),
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                )
              ],
            ),
            const SizedBox(height: 10),
            _infoLine(labels["class"]!, invoice["class_name"]?.toString() ?? "---"),
            _infoLine(labels["student"]!, invoice["student_name"]?.toString() ?? invoice["student_id"]?.toString() ?? "---"),
            _infoLine(labels["due_date"]!, invoice["due_date"]?.toString() ?? "---"),
            const Divider(height: 18),
            Row(
              children: [
                Expanded(
                  child: Text(
                    _formatMoney(amount),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                      color: Colors.orange,
                    ),
                  ),
                ),
                if (canPay)
                  ElevatedButton.icon(
                    onPressed: enoughBalance ? () => _payInvoice(invoice) : null,
                    icon: const Icon(Icons.payment, size: 18),
                    label: Text(labels["btn_pay"]!),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                  ),
              ],
            ),
            if (canPay && !enoughBalance)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  labels["low_balance"]!,
                  style: const TextStyle(
                    color: Colors.red,
                    fontSize: 12,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _infoLine(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 88,
            child: Text(
              label,
              style: const TextStyle(
                color: Colors.black54,
                fontSize: 12,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPaymentList(List<dynamic> payments) {
    final labels = _labels[_lang]!;

    if (payments.isEmpty) {
      return RefreshIndicator(
        onRefresh: _fetchAll,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            const SizedBox(height: 160),
            Center(
              child: Text(
                labels["payment_empty"]!,
                style: const TextStyle(color: Colors.black54),
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchAll,
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(12),
        itemCount: payments.length,
        itemBuilder: (context, index) {
          final payment = Map<String, dynamic>.from(payments[index]);

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: Colors.green,
                child: Icon(Icons.check, color: Colors.white),
              ),
              title: Text(
                _formatMoney(payment["amount"]),
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("${labels['method']}: ${payment['payment_method'] ?? 'wallet'}"),
                  Text("${labels['balance_after']}: ${_formatMoney(payment['balance_after'])}"),
                  Text("${labels['paid_at']}: ${_formatDateTime(payment['created_at'])}"),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}