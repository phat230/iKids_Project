import 'package:flutter/material.dart'; 
import 'package:google_fonts/google_fonts.dart';
import '../../services/api_service.dart'; 

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  final _nameController = TextEditingController(); 
  final _otpController = TextEditingController();
  bool _isOtpStep = false; 
  bool _isLoading = false;

  void _register() async {
    if (_nameController.text.isEmpty || _emailController.text.isEmpty || _passController.text.isEmpty) {
      _showToast("⚠️ Please fill in all required fields.", Colors.orange);
      return;
    }
    setState(() => _isLoading = true);
    try {
      await ApiService().register({
        "name": _nameController.text, 
        "email": _emailController.text,
        "password": _passController.text,
        "role": "student"
      });
      setState(() => _isOtpStep = true);
      _showToast("✅ OTP sent to your email!", Colors.green);
    } catch (e) {
      _showToast("❌ ${e.toString().replaceFirst("Exception: ", "")}", Colors.redAccent);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _verifyOtp() async {
    setState(() => _isLoading = true);
    try {
      await ApiService().verifyOtp(_emailController.text, _otpController.text);
      if (mounted) {
        _showToast("🎉 Account Activated!", Colors.green);
        Navigator.pop(context);
      }
    } catch (e) {
      _showToast("❌ Invalid or expired OTP!", Colors.redAccent);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showToast(String msg, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg, style: GoogleFonts.quicksand(fontWeight: FontWeight.bold)),
      backgroundColor: color,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white), onPressed: () => Navigator.pop(context)),
      ),
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topRight, end: Alignment.bottomLeft,
            colors: [Color(0xFF8B5CF6), Color(0xFF6366F1), Color(0xFF3B82F6)], // Gradient tím xanh đẹp
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 20),
            child: Column(
              children: [
                Icon(_isOtpStep ? Icons.mark_email_read_rounded : Icons.person_add_alt_1_rounded, size: 80, color: Colors.white),
                const SizedBox(height: 20),
                Text(_isOtpStep ? "Verify Your Account" : "Create New Account", style: GoogleFonts.quicksand(fontSize: 32, fontWeight: FontWeight.w800, color: Colors.white)),
                const SizedBox(height: 10),
                Text(_isOtpStep ? "Enter the 6-digit code sent to your email" : "Join iKids to start your learning journey", textAlign: TextAlign.center, style: GoogleFonts.quicksand(fontSize: 15, color: Colors.white70, fontWeight: FontWeight.w500)),
                const SizedBox(height: 40),

                Container(
                  padding: const EdgeInsets.all(25),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(25),
                    border: Border.all(color: Colors.white.withOpacity(0.2), width: 1.5),
                  ),
                  child: _isOtpStep ? _buildOtpForm() : _buildRegisterForm(),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRegisterForm() {
    return Column(
      children: [
        _buildInputField(controller: _nameController, icon: Icons.badge_outlined, hint: "Full Name"),
        const SizedBox(height: 20),
        _buildInputField(controller: _emailController, icon: Icons.email_outlined, hint: "Email Address", keyboardType: TextInputType.emailAddress),
        const SizedBox(height: 20),
        _buildInputField(controller: _passController, icon: Icons.lock_outline, hint: "Password", isPassword: true),
        const SizedBox(height: 35),
        SizedBox(
          width: double.infinity, height: 55,
          child: ElevatedButton(
            onPressed: _isLoading ? null : _register,
            style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.indigo, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))),
            child: _isLoading ? const CircularProgressIndicator() : Text("Register", style: GoogleFonts.quicksand(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  Widget _buildOtpForm() {
    return Column(
      children: [
        _buildInputField(controller: _otpController, icon: Icons.pin_outlined, hint: "6-Digit OTP Code", keyboardType: TextInputType.number),
        const SizedBox(height: 35),
        SizedBox(
          width: double.infinity, height: 55,
          child: ElevatedButton(
            onPressed: _isLoading ? null : _verifyOtp,
            style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.indigo, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))),
            child: _isLoading ? const CircularProgressIndicator() : Text("Verify & Activate", style: GoogleFonts.quicksand(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
        ),
        TextButton(
          onPressed: () => setState(() => _isOtpStep = false),
          child: Text("Change Email", style: GoogleFonts.quicksand(color: Colors.white70, decoration: TextDecoration.underline)),
        )
      ],
    );
  }

  Widget _buildInputField({required TextEditingController controller, required IconData icon, required String hint, bool isPassword = false, TextInputType? keyboardType}) {
    return TextField(
      controller: controller, obscureText: isPassword, keyboardType: keyboardType,
      style: GoogleFonts.quicksand(color: Colors.white, fontWeight: FontWeight.w600),
      decoration: InputDecoration(
        hintText: hint, hintStyle: GoogleFonts.quicksand(color: Colors.white54),
        prefixIcon: Icon(icon, color: Colors.white),
        filled: true, fillColor: Colors.black.withOpacity(0.15),
        contentPadding: const EdgeInsets.symmetric(vertical: 18),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: const BorderSide(color: Colors.white, width: 2)),
      ),
    );
  }
}