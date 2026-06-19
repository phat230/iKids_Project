import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../services/api_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _emailController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPassController = TextEditingController();
  
  bool _isOtpStep = false; 
  bool _isLoading = false;

  void _sendOtp() async {
    if (_emailController.text.isEmpty) return;
    setState(() => _isLoading = true);
    try {
      bool success = await ApiService().forgotPassword(_emailController.text.trim());
      if (success && mounted) {
        setState(() => _isOtpStep = true);
        _showToast("✅ Verification code sent to your email!", Colors.green);
      }
    } catch (e) {
      _showToast("❌ ${e.toString().replaceFirst("Exception: ", "")}", Colors.redAccent);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _resetPassword() async {
    if (_otpController.text.isEmpty || _newPassController.text.isEmpty) return;
    setState(() => _isLoading = true);
    try {
      bool success = await ApiService().resetPassword(_emailController.text.trim(), _otpController.text.trim(), _newPassController.text);
      if (success && mounted) {
        _showToast("🎉 Password changed successfully!", Colors.green);
        Navigator.pop(context);
      }
    } catch (e) {
      _showToast("❌ ${e.toString().replaceFirst("Exception: ", "")}", Colors.redAccent);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showToast(String msg, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg, style: GoogleFonts.quicksand(fontWeight: FontWeight.bold)), backgroundColor: color, behavior: SnackBarBehavior.floating));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent, elevation: 0,
        leading: IconButton(icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white), onPressed: () => Navigator.pop(context)),
      ),
      body: Container(
        width: double.infinity, height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(begin: Alignment.bottomLeft, end: Alignment.topRight, colors: [Color(0xFFF43F5E), Color(0xFFF97316)]), // Gradient Hồng Cam
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 30),
            child: Column(
              children: [
                const Icon(Icons.lock_reset_rounded, size: 80, color: Colors.white),
                const SizedBox(height: 20),
                Text("Reset Password", style: GoogleFonts.quicksand(fontSize: 32, fontWeight: FontWeight.w800, color: Colors.white)),
                const SizedBox(height: 10),
                Text(_isOtpStep ? "Enter OTP and your new secure password" : "Enter your email to receive a recovery code", textAlign: TextAlign.center, style: GoogleFonts.quicksand(fontSize: 15, color: Colors.white70, fontWeight: FontWeight.w500)),
                const SizedBox(height: 40),

                Container(
                  padding: const EdgeInsets.all(25),
                  decoration: BoxDecoration(color: Colors.white.withOpacity(0.1), borderRadius: BorderRadius.circular(25), border: Border.all(color: Colors.white.withOpacity(0.2), width: 1.5)),
                  child: _isOtpStep ? _buildStep2() : _buildStep1(),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStep1() {
    return Column(
      children: [
        _buildInputField(controller: _emailController, icon: Icons.email_outlined, hint: "Your Email Address"),
        const SizedBox(height: 30),
        SizedBox(
          width: double.infinity, height: 55,
          child: ElevatedButton(
            onPressed: _isLoading ? null : _sendOtp,
            style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.deepOrange, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))),
            child: _isLoading ? const CircularProgressIndicator() : Text("Send Recovery Code", style: GoogleFonts.quicksand(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  Widget _buildStep2() {
    return Column(
      children: [
        Text("Code sent to: ${_emailController.text}", style: GoogleFonts.quicksand(color: Colors.white, fontWeight: FontWeight.bold)),
        const SizedBox(height: 20),
        _buildInputField(controller: _otpController, icon: Icons.pin_outlined, hint: "6-Digit OTP", keyboardType: TextInputType.number),
        const SizedBox(height: 15),
        _buildInputField(controller: _newPassController, icon: Icons.lock_outline, hint: "New Password", isPassword: true),
        const SizedBox(height: 30),
        SizedBox(
          width: double.infinity, height: 55,
          child: ElevatedButton(
            onPressed: _isLoading ? null : _resetPassword,
            style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.deepOrange, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))),
            child: _isLoading ? const CircularProgressIndicator() : Text("Confirm Reset", style: GoogleFonts.quicksand(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
        ),
        TextButton(onPressed: () => setState(() => _isOtpStep = false), child: Text("Change Email", style: GoogleFonts.quicksand(color: Colors.white70, decoration: TextDecoration.underline)))
      ],
    );
  }

  Widget _buildInputField({required TextEditingController controller, required IconData icon, required String hint, bool isPassword = false, TextInputType? keyboardType}) {
    return TextField(
      controller: controller, obscureText: isPassword, keyboardType: keyboardType,
      style: GoogleFonts.quicksand(color: Colors.white, fontWeight: FontWeight.w600),
      decoration: InputDecoration(
        hintText: hint, hintStyle: GoogleFonts.quicksand(color: Colors.white54), prefixIcon: Icon(icon, color: Colors.white),
        filled: true, fillColor: Colors.black.withOpacity(0.15), contentPadding: const EdgeInsets.symmetric(vertical: 18),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: const BorderSide(color: Colors.white, width: 2)),
      ),
    );
  }
}