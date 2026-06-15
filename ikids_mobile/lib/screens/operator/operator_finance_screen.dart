import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
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

  List<dynamic> _allTransactions = [];
  List<dynamic> _walletTransactions = [];
  List<dynamic> _buyTransactions = [];

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
    try {
      final res = await http.delete(
        Uri.parse('${AppConfig.apiUrl}/api/finance/transactions/$id'),
        headers: {"Authorization": "Bearer $_token"},
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đã xóa giao dịch!"), backgroundColor: Colors.green));
        _fetchTransactions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xóa thất bại!"), backgroundColor: Colors.red));
      }
    } catch (e) {
      debugPrint("Lỗi xóa: $e");
    }
  }

  Future<void> _updateTransaction(String id, Map<String, dynamic> payload) async {
    try {
      final res = await http.put(
        Uri.parse('${AppConfig.apiUrl}/api/finance/transactions/$id'),
        headers: {"Content-Type": "application/json", "Authorization": "Bearer $_token"},
        body: jsonEncode(payload),
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Đã cập nhật giao dịch!"), backgroundColor: Colors.green));
        _fetchTransactions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Cập nhật thất bại!"), backgroundColor: Colors.red));
      }
    } catch (e) {
      debugPrint("Lỗi cập nhật: $e");
    }
  }

  // --- HỘP THOẠI SỬA VÍ TIỀN ---
  void _showEditWalletDialog(Map<String, dynamic> item) {
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
        title: const Text("Sửa giao dịch Ví", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: amountCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: "Số tiền")),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: selectedType,
                decoration: const InputDecoration(labelText: "Loại giao dịch"),
                items: types.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: (val) => selectedType = val!,
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: const InputDecoration(labelText: "Trạng thái"),
                items: statuses.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: (val) => selectedStatus = val!,
              ),
              const SizedBox(height: 10),
              TextField(controller: noteCtrl, decoration: const InputDecoration(labelText: "Ghi chú")),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Hủy", style: TextStyle(color: Colors.grey))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              Navigator.pop(ctx);
              _deleteTransaction(item['id'].toString());
            },
            child: const Text("Xóa", style: TextStyle(color: Colors.white)),
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
            child: const Text("Lưu", style: TextStyle(color: Colors.white)),
          ),
        ],
      )
    );
  }

  // --- HỘP THOẠI SỬA MUA ĐỒ ---
  void _showEditBuyDialog(Map<String, dynamic> item) {
    final nameCtrl = TextEditingController(text: item['item_name'] ?? item['product_name'] ?? item['name'] ?? "");
    final qtyCtrl = TextEditingController(text: (item['quantity'] ?? 1).toString());
    final totalCtrl = TextEditingController(text: _getMoneyValue(item).toStringAsFixed(0));
    String selectedStatus = item['status'] ?? "success";
    final statuses = ["success", "pending", "cancelled", "approved", "rejected"];
    if (!statuses.contains(selectedStatus)) selectedStatus = "success";

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Sửa Đơn Mua", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: "Tên dụng cụ")),
              const SizedBox(height: 10),
              TextField(controller: qtyCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: "Số lượng")),
              const SizedBox(height: 10),
              TextField(controller: totalCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: "Tổng tiền")),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: const InputDecoration(labelText: "Trạng thái"),
                items: statuses.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: (val) => selectedStatus = val!,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Hủy", style: TextStyle(color: Colors.grey))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              Navigator.pop(ctx);
              _deleteTransaction(item['id'].toString());
            },
            child: const Text("Xóa", style: TextStyle(color: Colors.white)),
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
            child: const Text("Lưu", style: TextStyle(color: Colors.white)),
          ),
        ],
      )
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: Colors.grey[100],
        appBar: AppBar(
          title: const Text("Quản lý Giao Dịch", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          backgroundColor: Colors.teal,
          foregroundColor: Colors.white,
          actions: [
            IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchTransactions),
            IconButton(
              icon: const Icon(Icons.download), 
              onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Tính năng xuất Excel khả dụng trên Web.")))
            ),
          ],
          bottom: const TabBar(
            isScrollable: true,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white60,
            indicatorColor: Colors.amber,
            indicatorWeight: 3,
            tabs: [
              Tab(icon: Icon(Icons.account_balance_wallet), text: "Ví Tiền"),
              Tab(icon: Icon(Icons.shopping_cart), text: "Cửa Hàng"),
              Tab(icon: Icon(Icons.analytics), text: "Thống Kê"),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Colors.teal))
            : TabBarView(
                children: [
                  _buildListTab(_walletTransactions, true),
                  _buildListTab(_buyTransactions, false),
                  _buildStatsTab(),
                ],
              ),
      ),
    );
  }

  // --- HÀM RENDER DANH SÁCH GIAO DỊCH ---
  Widget _buildListTab(List<dynamic> list, bool isWallet) {
    if (list.isEmpty) {
      return const Center(child: Text("Chưa có dữ liệu giao dịch."));
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
                const Text("Chạm để sửa", style: TextStyle(fontSize: 10, color: Colors.grey)),
              ],
            ),
            onTap: () => isWallet ? _showEditWalletDialog(item) : _showEditBuyDialog(item),
          ),
        );
      },
    );
  }

  // --- HÀM RENDER BIỂU ĐỒ & THỐNG KÊ ---
  Widget _buildStatsTab() {
    double totalAmount = _allTransactions.fold(0.0, (sum, item) => sum + _getMoneyValue(item));
    int uniqueGroups = _allTransactions.map((t) => t['group']).toSet().length;

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
              Expanded(child: _buildMetricCard("Tổng giao dịch", "${_allTransactions.length}", Icons.receipt_long, Colors.blue)),
              const SizedBox(width: 10),
              Expanded(child: _buildMetricCard("Tổng dòng tiền", "${totalAmount.toStringAsFixed(0)}đ", Icons.attach_money, Colors.orange)),
            ],
          ),
          const SizedBox(height: 30),

          // Biểu đồ Donut (Số lượng)
          const Text("📌 Tỷ trọng giao dịch theo nhóm", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
          const Text("💰 Tổng tiền theo nhóm", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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