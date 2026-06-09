import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Kết quả học tập"), 
        backgroundColor: Colors.amber, 
        foregroundColor: Colors.black,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            const Card(
              color: Colors.amberAccent,
              child: Padding(
                padding: EdgeInsets.all(20.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    Column(
                      children: [
                        Text("Hạng", style: TextStyle(color: Colors.black54)), 
                        // Đã sửa Colors.bold thành FontWeight.bold
                        Text("Vàng", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    Column(
                      children: [
                        Text("Điểm tích lũy", style: TextStyle(color: Colors.black54)), 
                        // Đã sửa Colors.bold thành FontWeight.bold
                        Text("850 XP", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: ListView(
                children: const [
                  ListTile(
                    leading: Icon(Icons.check_circle, color: Colors.green), 
                    title: Text("Quiz toán tư duy tuần 24"), 
                    trailing: Text("10/10"),
                  ),
                  ListTile(
                    leading: Icon(Icons.check_circle, color: Colors.green), 
                    title: Text("Kiểm tra nói tiếng Anh"), 
                    trailing: Text("9/10"),
                  ),
                ],
              ),
            )
          ],
        ),
      ),
    );
  }
}