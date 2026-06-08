class UserCreate {
  final String name;
  final String email;
  final String password;
  final String role;
  final String? phoneNumber;
  final String? birthDate;

  UserCreate({
    required this.name,
    required this.email,
    required this.password,
    required this.role,
    this.phoneNumber,
    this.birthDate,
  });

  Map<String, dynamic> toJson() => {
    "name": name,
    "email": email,
    "password": password,
    "role": role,
    "phone_number": phoneNumber,
    "birth_date": birthDate,
  };
}