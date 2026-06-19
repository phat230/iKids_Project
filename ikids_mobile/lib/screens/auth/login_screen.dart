import 'package:flutter/material.dart'; 
import 'package:google_fonts/google_fonts.dart';
import '../../services/api_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  final _apiService = ApiService();
  final _storage = const FlutterSecureStorage();
  bool _isLoading = false;
  bool _isObscured = true;
  String _lang = "vi"; // Mặc định là Tiếng Việt giống Web

  // ================= BỘ TỪ ĐIỂN SONG NGỮ =================
  final Map<String, Map<String, String>> _locales = {
    "vi": {
      "title": "Hệ Thống iKids",
      "subtitle": "Đăng nhập để tiếp tục truy cập iKids Portal",
      "email_hint": "ví dụ: phuhuynh@gmail.com",
      "pass_hint": "Mật khẩu",
      "btn_login": "Đăng Nhập",
      "btn_forgot": "Quên mật khẩu?",
      "txt_no_account": "Chưa có tài khoản?",
      "btn_register": "Đăng ký ngay",
      "err_empty": "⚠️ Vui lòng điền đầy đủ email và mật khẩu.",
      "err_auth": "Tài khoản chưa được kích hoạt hoặc bị khóa."
    },
    "en": {
      "title": "iKids System",
      "subtitle": "Sign in to continue to iKids Portal",
      "email_hint": "e.g., parent@gmail.com",
      "pass_hint": "Password",
      "btn_login": "Sign In",
      "btn_forgot": "Forgot Password?",
      "txt_no_account": "Don't have an account?",
      "btn_register": "Register Now",
      "err_empty": "⚠️ Please fill in all fields.",
      "err_auth": "Account is inactive or blocked."
    }
  };

  void _login() async {
    if (_emailController.text.isEmpty || _passController.text.isEmpty) {
      _showError(_locales[_lang]!["err_empty"]!);
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      final data = await _apiService.login(_emailController.text, _passController.text);
      final userInfo = data['user_info'];
      if (userInfo == null) throw Exception("Invalid response data.");
      
      String role = userInfo['role'] ?? 'student';
      if (!mounted) return;

      switch (role) {
        case 'admin': Navigator.pushReplacementNamed(context, '/admin'); break;
        case 'teacher': Navigator.pushReplacementNamed(context, '/teacher'); break;
        case 'operator': Navigator.pushReplacementNamed(context, '/operator'); break;
        case 'parent': Navigator.pushReplacementNamed(context, '/parent'); break;
        case 'student':
        default: Navigator.pushReplacementNamed(context, '/student'); break;
      }
    } catch (e) {
      String errorMsg = e.toString().contains("403") 
          ? _locales[_lang]!["err_auth"]!
          : e.toString().replaceFirst("Exception: ", "");
      _showError("❌ $errorMsg");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg, style: GoogleFonts.quicksand(fontWeight: FontWeight.bold)),
      backgroundColor: Colors.redAccent,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final labels = _locales[_lang]!;

    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF1E3A8A), Color(0xFF4338CA), Color(0xFF06B6D4)], 
          ),
        ),
        child: SafeArea(
          child: Stack(
            children: [
              // --- NÚT CHUYỂN NGÔN NGỮ Ở GÓC TRÊN CÙNG BÊN PHẢI ---
              Positioned(
                top: 10,
                right: 20,
                child: TextButton.icon(
                 onPressed: () async {
                  setState(() {
                  _lang = _lang == "vi" ? "en" : "vi";
                   });
                 await _storage.write(key: 'app_lang', value: _lang);
                  },
                  icon: const Icon(Icons.language, color: Colors.cyanAccent),
                  label: Text(
                    _lang == "vi" ? "EN" : "VI", 
                    style: GoogleFonts.quicksand(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)
                  ),
                  style: TextButton.styleFrom(
                    backgroundColor: Colors.black.withOpacity(0.2),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))
                  ),
                ),
              ),

              // --- NỘI DUNG CHÍNH ---
              Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 30),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withOpacity(0.1)),
                        child: const Icon(Icons.school_rounded, size: 70, color: Colors.white),
                      ),
                      const SizedBox(height: 20),
                      Text(labels["title"]!, style: GoogleFonts.quicksand(fontSize: 34, fontWeight: FontWeight.w800, color: Colors.white, letterSpacing: 1.0)),
                      const SizedBox(height: 8),
                      Text(labels["subtitle"]!, textAlign: TextAlign.center, style: GoogleFonts.quicksand(fontSize: 15, color: Colors.white70, fontWeight: FontWeight.w500)),
                      const SizedBox(height: 40),

                      // --- FORM KÍNH MỜ ---
                      Container(
                        padding: const EdgeInsets.all(25),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(25),
                          border: Border.all(color: Colors.white.withOpacity(0.2), width: 1.5),
                          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 30, offset: const Offset(0, 10))],
                        ),
                        child: Column(
                          children: [
                            _buildInputField(
                              controller: _emailController,
                              icon: Icons.email_outlined,
                              hint: labels["email_hint"]!,
                              keyboardType: TextInputType.emailAddress,
                            ),
                            const SizedBox(height: 20),
                            _buildInputField(
                              controller: _passController,
                              icon: Icons.lock_outline,
                              hint: labels["pass_hint"]!,
                              isPassword: true,
                            ),
                            Align(
                              alignment: Alignment.centerRight,
                              child: TextButton(
                                onPressed: () => Navigator.pushNamed(context, '/forgot-password'),
                                child: Text(labels["btn_forgot"]!, style: GoogleFonts.quicksand(color: Colors.cyanAccent, fontWeight: FontWeight.bold)),
                              ),
                            ),
                            const SizedBox(height: 10),
                            
                            SizedBox(
                              width: double.infinity,
                              height: 55,
                              child: ElevatedButton(
                                onPressed: _isLoading ? null : _login,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.cyanAccent.shade400,
                                  foregroundColor: Colors.indigo.shade900,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                                  elevation: 5,
                                ),
                                child: _isLoading 
                                  ? const SizedBox(width: 25, height: 25, child: CircularProgressIndicator(color: Colors.indigo, strokeWidth: 3))
                                  : Text(labels["btn_login"]!, style: GoogleFonts.quicksand(fontSize: 18, fontWeight: FontWeight.w800)),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 30),

                      // --- FOOTER ĐĂNG KÝ ---
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(labels["txt_no_account"]!, style: GoogleFonts.quicksand(color: Colors.white70)),
                          TextButton(
                            onPressed: () => Navigator.pushNamed(context, '/register'),
                            child: Text(labels["btn_register"]!, style: GoogleFonts.quicksand(color: Colors.white, fontWeight: FontWeight.bold, decoration: TextDecoration.underline)),
                          )
                        ],
                      )
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInputField({required TextEditingController controller, required IconData icon, required String hint, bool isPassword = false, TextInputType? keyboardType}) {
    return TextField(
      controller: controller,
      obscureText: isPassword ? _isObscured : false,
      keyboardType: keyboardType,
      style: GoogleFonts.quicksand(color: Colors.white, fontWeight: FontWeight.w600),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: GoogleFonts.quicksand(color: Colors.white54),
        prefixIcon: Icon(icon, color: Colors.cyanAccent),
        suffixIcon: isPassword 
          ? IconButton(
              icon: Icon(_isObscured ? Icons.visibility_off : Icons.visibility, color: Colors.white54),
              onPressed: () => setState(() => _isObscured = !_isObscured),
            )
          : null,
        filled: true,
        fillColor: Colors.black.withOpacity(0.2),
        contentPadding: const EdgeInsets.symmetric(vertical: 18),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: const BorderSide(color: Colors.cyanAccent, width: 2)),
      ),
    );
  }
}