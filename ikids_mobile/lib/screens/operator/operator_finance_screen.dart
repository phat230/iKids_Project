import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:fl_chart/fl_chart.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../../core/config.dart';

class OperatorFinanceScreen extends StatefulWidget {
  const OperatorFinanceScreen({super.key});

  @override
  State<OperatorFinanceScreen> createState() => _OperatorFinanceScreenState();
}

class _OperatorFinanceScreenState extends State<OperatorFinanceScreen> {
  final _storage = const FlutterSecureStorage();
  bool _isLoading = true;
  String _token = "";
  String _lang = "vi"; // Ngôn ngữ mặc định

  List<dynamic> _allTransactions = [];
  List<dynamic> _walletTransactions = [];
  List<dynamic> _buyTransactions = [];

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Quản lý Giao Dịch",
      "tab_wallet": "Ví Tiền",
      "tab_store": "Cửa Hàng",
      "tab_stats": "Thống Kê",
      "msg_no_export": "Không có dữ liệu để xuất!",
      "csv_header": "Mã GD,Nhóm,Loại GD/Sản phẩm,Số tiền (VNĐ),Trạng thái,Ngày tạo,Ghi chú\n",
      "csv_file_name": "Bao_Cao_Tai_Chinh_iKids.csv",
      "csv_share_text": "Báo cáo Giao dịch Tài chính iKids",
      "msg_export_err": "Lỗi tạo file báo cáo!",
      "edit_wallet_title": "Sửa giao dịch Ví",
      "lbl_amount": "Số tiền",
      "lbl_type": "Loại giao dịch",
      "lbl_status": "Trạng thái",
      "lbl_note": "Ghi chú",
      "btn_cancel": "Hủy",
      "btn_delete": "Xóa",
      "btn_save": "Lưu",
      "edit_buy_title": "Sửa Đơn Mua",
      "lbl_item_name": "Tên dụng cụ",
      "lbl_qty": "Số lượng",
      "lbl_total": "Tổng tiền",
      "msg_no_data": "Chưa có dữ liệu giao dịch.",
      "lbl_tap_edit": "Chạm để sửa",
      "stat_total_trans": "Tổng giao dịch",
      "stat_cash_flow": "Tổng dòng tiền",
      "btn_export": "XUẤT BÁO CÁO (EXCEL/CSV)",
      "chart_ratio": "📌 Tỷ trọng giao dịch theo nhóm",
      "chart_amount": "💰 Tổng tiền theo nhóm",
      "msg_del_success": "Đã xóa giao dịch!",
      "msg_del_fail": "Xóa thất bại!",
      "msg_upd_success": "Đã cập nhật giao dịch!",
      "msg_upd_fail": "Cập nhật thất bại!",
    },
    "en": {
      "title": "Transaction Management",
      "tab_wallet": "Wallet",
      "tab_store": "Store",
      "tab_stats": "Statistics",
      "msg_no_export": "No data to export!",
      "csv_header": "Txn ID,Group,Type/Product,Amount (VND),Status,Created At,Note\n",
      "csv_file_name": "iKids_Financial_Report.csv",
      "csv_share_text": "iKids Financial Transaction Report",
      "msg_export_err": "Error generating report file!",
      "edit_wallet_title": "Edit Wallet Txn",
      "lbl_amount": "Amount",
      "lbl_type": "Transaction Type",
      "lbl_status": "Status",
      "lbl_note": "Note",
      "btn_cancel": "Cancel",
      "btn_delete": "Delete",
      "btn_save": "Save",
      "edit_buy_title": "Edit Purchase Order",
      "lbl_item_name": "Item Name",
      "lbl_qty": "Quantity",
      "lbl_total": "Total Amount",
      "msg_no_data": "No transaction data.",
      "lbl_tap_edit": "Tap to edit",
      "stat_total_trans": "Total Transactions",
      "stat_cash_flow": "Total Cash Flow",
      "btn_export": "EXPORT REPORT (EXCEL/CSV)",
      "chart_ratio": "📌 Transaction Ratio by Group",
      "chart_amount": "💰 Total Amount by Group",
      "msg_del_success": "Transaction deleted!",
      "msg_del_fail": "Delete failed!",
      "msg_upd_success": "Transaction updated!",
      "msg_upd_fail": "Update failed!",
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchTransactions();
  }

  double _getMoneyValue(Map<String, dynamic> row) {
    for (String col in ["amount", "price", "total_amount"]) {
      if (row[col] != null) {
        return double.tryParse(row[col].toString()) ?? 0.0;
      }
    }
    return 0.0;
  }

  Future<void> _fetchTransactions() async {
    setState(() => _isLoading = true);
    try {
      // ✅ ĐỌC NGÔN NGỮ TỪ STORAGE LÚC KHỞI TẠO
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      _token = await _storage.read(key: 'jwt_token') ?? "";
      if (_token.isEmpty) return;

      final res = await http.get(
        Uri.parse('${AppConfig.apiUrl}/api/finance/admin/all-history'),
        headers: {"Authorization": "Bearer $_token"},
      );

      if (res.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(res.bodyBytes));
        
        setState(() {
          _allTransactions = data;
          _walletTransactions = data.where((t) => t['group'] == 'Ví tiền').toList();
          _buyTransactions = data.where((t) => ['Mua đồ', 'Con tự mua', 'Đơn hàng'].contains(t['group'])).toList();
        });
      }
    } catch (e) {
      debugPrint("Lỗi tải giao dịch: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteTransaction(String id) async {
    final labels = _locales[_lang]!;
    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiUrl}/api/finance/transactions/$id'),
        headers: {"Authorization": "Bearer $_token"},
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_del_success"]!), backgroundColor: Colors.green));
        _fetchTransactions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_del_fail"]!), backgroundColor: Colors.red));
      }
    } catch (e) {
      debugPrint("Lỗi xóa: $e");
    }
  }

  Future<void> _updateTransaction(String id, Map<String, dynamic> payload) async {
    final labels = _locales[_lang]!;
    try {
      final res = await http.put(
        Uri.parse('${AppConfig.apiUrl}/api/finance/transactions/$id'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload),
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_upd_success"]!), backgroundColor: Colors.green));
        _fetchTransactions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_upd_fail"]!), backgroundColor: Colors.red));
      }
    } catch (e) {
      debugPrint("Lỗi cập nhật: $e");
    }
  }

  Future<void> _exportToCsv() async {
    final labels = _locales[_lang]!;
    try {
      if (_allTransactions.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_no_export"]!), backgroundColor: Colors.orange));
        return;
      }

      // Tạo tiêu đề cột động theo ngôn ngữ
      String csvData = labels["csv_header"]!;

      // Đổ dữ liệu vào file
      for (var t in _allTransactions) {
        String id = t['id']?.toString() ?? '';
        String group = t['group']?.toString() ?? '';
        String type = t['type']?.toString() ?? t['item_name']?.toString() ?? t['product_name']?.toString() ?? '';
        String amount = _getMoneyValue(t).toStringAsFixed(0);
        String status = t['status']?.toString() ?? '';
        String date = t['created_at']?.toString() ?? '';
        String note = t['note']?.toString() ?? '';

        // Dọn dẹp dữ liệu tránh làm vỡ cấu trúc CSV
        type = type.replaceAll(',', ';');
        note = note.replaceAll(',', ';').replaceAll('\n', ' ');

        csvData += "$id,$group,$type,$amount,$status,$date,$note\n";
      }

      // Lấy đường dẫn lưu trữ tạm thời trên điện thoại
      final directory = await getTemporaryDirectory();
      final String filePath = '${directory.path}/${labels["csv_file_name"]}';
      final File file = File(filePath);

      // Ghi byte BOM (0xEF, 0xBB, 0xBF) để Excel mở ra không bị lỗi Font
      await file.writeAsBytes([0xEF, 0xBB, 0xBF]); 
      await file.writeAsString(csvData, mode: FileMode.append, encoding: utf8);

      // Gọi bảng chia sẻ của thiết bị
      await Share.shareXFiles([XFile(filePath)], text: labels["csv_share_text"]);

    } catch (e) {
      debugPrint("Lỗi xuất file CSV: $e");
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(labels["msg_export_err"]!), backgroundColor: Colors.red));
    }
  }

  // --- HỘP THOẠI SỬA VÍ TIỀN ---
  void _showEditWalletDialog(Map<String, dynamic> item) {
    final labels = _locales[_lang]!;
    final amountCtrl = TextEditingController(text: _getMoneyValue(item).toStringAsFixed(0));
    final noteCtrl = TextEditingController(text: item['note'] ?? "");
    String selectedType = item['type'] ?? "nap_tien";
    String selectedStatus = item['status'] ?? "success";

    final types = ["nap_tien", "chuyen_cho_con", "rut_tu_con", "deposit", "withdraw", "transfer"];
    final statuses = ["success", "pending", "failed"];
    if (!types.contains(selectedType)) selectedType = "nap_tien";
    if (!statuses.contains(selectedStatus)) selectedStatus = "success";

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(labels["edit_wallet_title"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: amountCtrl, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: labels["lbl_amount"])),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: selectedType,
                decoration: InputDecoration(labelText: labels["lbl_type"]),
                items: types.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: (val) => selectedType = val!,
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: InputDecoration(labelText: labels["lbl_status"]),
                items: statuses.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: (val) => selectedStatus = val!,
              ),
              const SizedBox(height: 10),
              TextField(controller: noteCtrl, decoration: InputDecoration(labelText: labels["lbl_note"])),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(labels["btn_cancel"]!, style: const TextStyle(color: Colors.grey))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              Navigator.pop(ctx);
              _deleteTransaction(item['id'].toString());
            },
            child: Text(labels["btn_delete"]!, style: const TextStyle(color: Colors.white)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.teal),
            onPressed: () {
              Navigator.pop(ctx);
              _updateTransaction(item['id'].toString(), {
                "amount": double.tryParse(amountCtrl.text) ?? 0,
                "type": selectedType,
                "status": selectedStatus,
                "note": noteCtrl.text
              });
            },
            child: Text(labels["btn_save"]!, style: const TextStyle(color: Colors.white)),
          ),
        ],
      )
    );
  }

  // --- HỘP THOẠI SỬA MUA ĐỒ ---
  void _showEditBuyDialog(Map<String, dynamic> item) {
    final labels = _locales[_lang]!;
    final nameCtrl = TextEditingController(text: item['item_name'] ?? item['product_name'] ?? item['name'] ?? "");
    final qtyCtrl = TextEditingController(text: (item['quantity'] ?? 1).toString());
    final totalCtrl = TextEditingController(text: _getMoneyValue(item).toStringAsFixed(0));
    String selectedStatus = item['status'] ?? "success";
    final statuses = ["success", "pending", "cancelled", "approved", "rejected"];
    if (!statuses.contains(selectedStatus)) selectedStatus = "success";

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(labels["edit_buy_title"]!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameCtrl, decoration: InputDecoration(labelText: labels["lbl_item_name"])),
              const SizedBox(height: 10),
              TextField(controller: qtyCtrl, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: labels["lbl_qty"])),
              const SizedBox(height: 10),
              TextField(controller: totalCtrl, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: labels["lbl_total"])),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: InputDecoration(labelText: labels["lbl_status"]),
                items: statuses.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: (val) => selectedStatus = val!,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(labels["btn_cancel"]!, style: const TextStyle(color: Colors.grey))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              Navigator.pop(ctx);
              _deleteTransaction(item['id'].toString());
            },
            child: Text(labels["btn_delete"]!, style: const TextStyle(color: Colors.white)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.teal),
            onPressed: () {
              Navigator.pop(ctx);
              double total = double.tryParse(totalCtrl.text) ?? 0;
              _updateTransaction(item['id'].toString(), {
                "item_name": nameCtrl.text,
                "product_name": nameCtrl.text,
                "quantity": int.tryParse(qtyCtrl.text) ?? 1,
                "total_amount": total,
                "price": total,
                "status": selectedStatus
              });
            },
            child: Text(labels["btn_save"]!, style: const TextStyle(color: Colors.white)),
          ),
        ],
      )
    );
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;
    
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: Text(labels["title"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          backgroundColor: Colors.teal,
          foregroundColor: Colors.white,
          actions: [
            IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchTransactions),
            IconButton(
              icon: const Icon(Icons.download), 
              onPressed: _exportToCsv
            ),
            // ✅ ĐÃ THÊM: Nút chuyển đổi ngôn ngữ
            TextButton(
              onPressed: () async {
                setState(() => _lang = _lang == "vi" ? "en" : "vi");
                await _storage.write(key: 'app_lang', value: _lang);
              },
              child: Text(_lang.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            )
          ],
          bottom: TabBar(
            isScrollable: true,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white60,
            indicatorColor: Colors.amber,
            indicatorWeight: 3,
            tabs: [
              Tab(icon: const Icon(Icons.account_balance_wallet), text: labels["tab_wallet"]),
              Tab(icon: const Icon(Icons.shopping_cart), text: labels["tab_store"]),
              Tab(icon: const Icon(Icons.analytics), text: labels["tab_stats"]),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Colors.teal))
            : TabBarView(
                children: [
                  _buildListTab(_walletTransactions, true, labels),
                  _buildListTab(_buyTransactions, false, labels),
                  _buildStatsTab(labels),
                ],
              ),
      ),
    );
  }

  // --- HÀM RENDER DANH SÁCH GIAO DỊCH ---
  Widget _buildListTab(List<dynamic> list, bool isWallet, Map<String, String> labels) {
    if (list.isEmpty) {
      return Center(child: Text(labels["msg_no_data"]!));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final item = list[index];
        final amount = _getMoneyValue(item);
        final status = item['status'] ?? 'N/A';
        final isSuccess = status == 'success' || status == 'approved';
        
        return Card(
          elevation: 2,
          margin: const EdgeInsets.only(bottom: 10),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: isSuccess ? Colors.green[100] : Colors.orange[100],
              child: Icon(isWallet ? Icons.swap_horiz : Icons.shopping_bag, color: isSuccess ? Colors.green : Colors.orange),
            ),
            title: Text(isWallet ? (item['type'] ?? 'Giao dịch') : (item['item_name'] ?? item['product_name'] ?? 'Sản phẩm'), style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text("${item['created_at']?.toString().substring(0, 10) ?? ''} • ${item['status']}"),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text("${amount > 0 ? '+' : ''}${amount.toStringAsFixed(0)}đ", style: TextStyle(fontWeight: FontWeight.bold, color: amount >= 0 ? Colors.green : Colors.red, fontSize: 14)),
                Text(labels["lbl_tap_edit"]!, style: const TextStyle(fontSize: 10, color: Colors.grey)),
              ],
            ),
            onTap: () => isWallet ? _showEditWalletDialog(item) : _showEditBuyDialog(item),
          ),
        );
      },
    );
  }

  // --- HÀM RENDER BIỂU ĐỒ & THỐNG KÊ ---
  Widget _buildStatsTab(Map<String, String> labels) {
    double totalAmount = _allTransactions.fold(0.0, (sum, item) => sum + _getMoneyValue(item));

    // Chuẩn bị dữ liệu biểu đồ
    Map<String, int> countMap = {};
    Map<String, double> moneyMap = {};
    
    for (var t in _allTransactions) {
      String g = t['group'] ?? 'Khác';
      countMap[g] = (countMap[g] ?? 0) + 1;
      moneyMap[g] = (moneyMap[g] ?? 0.0) + _getMoneyValue(t);
    }

    List<Color> colors = [Colors.blue, Colors.green, Colors.orange, Colors.purple, Colors.red];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Thẻ Metrics
          Row(
            children: [
              Expanded(child: _buildMetricCard(labels["stat_total_trans"]!, "${_allTransactions.length}", Icons.receipt_long, Colors.blue)),
              const SizedBox(width: 10),
              Expanded(child: _buildMetricCard(labels["stat_cash_flow"]!, "${totalAmount.toStringAsFixed(0)}đ", Icons.attach_money, Colors.orange)),
            ],
          ),
          const SizedBox(height: 20),

          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.download),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white),
              onPressed: _exportToCsv,
              label: Text(labels["btn_export"]!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
          ),
          const SizedBox(height: 30),

          // Biểu đồ Donut (Số lượng)
          Text(labels["chart_ratio"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 15),
          Container(
            height: 250,
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 5)]),
            child: Row(
              children: [
                Expanded(
                  child: PieChart(
                    PieChartData(
                      sectionsSpace: 2,
                      centerSpaceRadius: 40,
                      sections: countMap.entries.toList().asMap().entries.map((entry) {
                        int idx = entry.key;
                        var e = entry.value;
                        return PieChartSectionData(
                          color: colors[idx % colors.length],
                          value: e.value.toDouble(),
                          title: "${e.value}",
                          radius: 35,
                          titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
                        );
                      }).toList(),
                    ),
                  ),
                ),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: countMap.entries.toList().asMap().entries.map((e) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(children: [Icon(Icons.circle, color: colors[e.key % colors.length], size: 12), const SizedBox(width: 5), Text(e.value.key, style: const TextStyle(fontSize: 12))]),
                    );
                  }).toList(),
                )
              ],
            ),
          ),
          const SizedBox(height: 30),

          // Biểu đồ Cột (Tổng tiền)
          Text(labels["chart_amount"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 15),
          Container(
            height: 300,
            padding: const EdgeInsets.only(top: 20, right: 10, left: 10, bottom: 10),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(15), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 5)]),
            child: BarChart(
              BarChartData(
                alignment: BarChartAlignment.spaceAround,
                barTouchData: BarTouchData(enabled: true),
                titlesData: FlTitlesData(
                  show: true,
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        int idx = value.toInt();
                        if (idx >= 0 && idx < moneyMap.length) {
                          return Padding(
                            padding: const EdgeInsets.only(top: 8.0),
                            child: Text(moneyMap.keys.elementAt(idx), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                          );
                        }
                        return const Text('');
                      },
                    ),
                  ),
                  leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 40)),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: false),
                barGroups: moneyMap.entries.toList().asMap().entries.map((e) {
                  return BarChartGroupData(
                    x: e.key,
                    barRods: [
                      BarChartRodData(
                        toY: e.value.value,
                        color: colors[e.key % colors.length],
                        width: 25,
                        borderRadius: BorderRadius.circular(4),
                      )
                    ],
                  );
                }).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withOpacity(0.3))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 10),
          Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
          Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        ],
      ),
    );
  }
}