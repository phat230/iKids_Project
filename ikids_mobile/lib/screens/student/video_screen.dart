import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:youtube_player_flutter/youtube_player_flutter.dart';
import '../../core/config.dart';

class VideoScreen extends StatefulWidget {
  const VideoScreen({Key? key}) : super(key: key);

  @override
  State<VideoScreen> createState() => _VideoScreenState();
}

class _VideoScreenState extends State<VideoScreen> {
  final _storage = const FlutterSecureStorage();
  final String apiPrefix = '/api/tv2'; 

  // State quản lý dữ liệu
  List<dynamic> _allVideos = [];
  List<dynamic> _filteredVideos = [];
  bool _isLoading = true;
  String _searchQuery = "";
  String _lang = "vi"; 

  // Quản lý video đang được chọn phát
  Map<String, dynamic>? _selectedVideo;
  YoutubePlayerController? _ytController;
  final TextEditingController _commentController = TextEditingController();

  // Profile học sinh thật từ hệ thống
  Map<String, dynamic> _studentProfile = {
    "name": "Học sinh",
    "email_key": "",
    "exp": 0,
    "completed_tasks": []
  };

  // ================= BỘ TỪ ĐIỂN SONG NGỮ ĐẦY ĐỦ =================
  final Map<String, Map<String, String>> _labels = {
    "vi": {
      "title": "🎬 Rạp Chiếu Video AI",
      "search_placeholder": "🔍 Tìm Kiếm Bài Học...",
      "info_empty": "Chưa có video nào phù hợp.",
      "lbl_completed": "✅ Đã xem",
      "lbl_reward_hint": "⭐ +30 EXP",
      "btn_watch": "Xem ngay",
      "lbl_topic": "Chủ đề:",
      "lbl_level": "Trình độ:",
      "lbl_reward": "🎁 Phần thưởng:",
      "btn_like": "👍 Thích ({})",
      "btn_like_done": "❤️ Đã Thích ({})",
      "btn_complete_lesson": "✅ Hoàn thành bài học",
      "btn_completed_lesson": "🔒 Đã hoàn thành bài học",
      "cmt_placeholder": "Viết bình luận của bạn...",
      "lbl_comments_count": "Bình luận",
      "playlist_title": "📂 Danh Sách Bài Học",
      "author_anonymous": "Ẩn danh",
      "err_api": "⚠️ Lỗi kết nối API máy chủ!",
      "err_conn": "⚠️ Không thể kết nối tới Backend!",
      "err_invalid_link": "Link video không hợp lệ.",
      "toast_api_err": "Lỗi hệ thống khi thả tim.",
      "toast_success_exp": "🎉 Nhận thành công +30 EXP!",
      "toast_save_err": "Lỗi lưu dữ liệu.",
      "err_send_cmt": "Không gửi được bình luận.",
      "channel_name": "iKids Education",
      "default_title": "Video bài giảng"
    },
    "en": {
      "title": "🎬 AI Video Theater",
      "search_placeholder": "🔍 Search Video Lessons...",
      "info_empty": "No matching video lessons found.",
      "lbl_completed": "✅ Watched",
      "lbl_reward_hint": "⭐ +30 EXP",
      "btn_watch": "Watch Now",
      "lbl_topic": "Topic:",
      "lbl_level": "Level:",
      "lbl_reward": "🎁 Rewards:",
      "btn_like": "👍 Like ({})",
      "btn_like_done": "❤️ Liked ({})",
      "btn_complete_lesson": "✅ Complete Quest",
      "btn_completed_lesson": "🔒 Completed",
      "cmt_placeholder": "Add a public comment...",
      "lbl_comments_count": "Comments",
      "playlist_title": "📂 Course Playlist",
      "author_anonymous": "Anonymous",
      "err_api": "⚠️ Server API connection error!",
      "err_conn": "⚠️ Cannot connect to Backend!",
      "err_invalid_link": "Invalid video link.",
      "toast_api_err": "System error while liking.",
      "toast_success_exp": "🎉 Successfully claimed +30 EXP!",
      "toast_save_err": "Error saving data.",
      "err_send_cmt": "Failed to send comment.",
      "channel_name": "iKids Education",
      "default_title": "Video Lesson"
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchInitialData();
  }

  @override
  void dispose() {
    _ytController?.dispose();
    _commentController.dispose();
    super.dispose();
  }

  // --- TẢI NGÔN NGỮ VÀ DỮ LIỆU ĐỒNG BỘ ---
  Future<void> _fetchInitialData() async {
    try {
      // 1. Đọc ngôn ngữ từ hệ thống
      String? savedLang = await _storage.read(key: 'app_lang');
      if (savedLang != null) _lang = savedLang;

      // 2. Lấy thông tin user thật đang đăng nhập
      String? userInfo = await _storage.read(key: 'user_info');
      if (userInfo != null) {
        final decodedUser = jsonDecode(userInfo);
        String anchorKey = decodedUser["id"]?.toString() ?? decodedUser["_id"]?.toString() ?? decodedUser["email"]?.toString() ?? "Student";
        String displayName = decodedUser["full_name"]?.toString() ?? decodedUser["name"]?.toString() ?? "Học sinh";
        
        final profRes = await http.get(Uri.parse('${AppConfig.apiUrl}$apiPrefix/student/${Uri.encodeComponent(anchorKey)}/profile'));
        if (profRes.statusCode == 200) {
          _studentProfile = jsonDecode(utf8.decode(profRes.bodyBytes));
          _studentProfile["name"] = displayName;
          _studentProfile["email_key"] = anchorKey;
        }
      }

      // 3. Tải danh sách Video
      final response = await http.get(Uri.parse('${AppConfig.apiUrl}$apiPrefix/videos'));
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        if (mounted) {
          setState(() {
            _allVideos = data;
            _filteredVideos = data;
            _isLoading = false;
          });
        }
      } else {
        _showToast(_labels[_lang]!["err_api"]!);
        setState(() => _isLoading = false);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        _showToast(_labels[_lang]!["err_conn"]!);
      }
    }
  }

  String _getYtThumbnail(String url) {
    RegExp regExp = RegExp(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*");
    Match? match = regExp.firstMatch(url);
    if (match != null) {
      return "https://img.youtube.com/vi/${match.group(1)}/hqdefault.jpg";
    }
    return "https://via.placeholder.com/320x180.png?text=Video";
  }

  void _initializeVideo(Map<String, dynamic> video) {
    String url = video['url'] ?? "";
    RegExp regExp = RegExp(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*");
    Match? match = regExp.firstMatch(url);
    String? videoId = match?.group(1);

    if (videoId != null) {
      setState(() {
        _selectedVideo = video;
        _ytController = YoutubePlayerController(
          initialVideoId: videoId,
          flags: const YoutubePlayerFlags(autoPlay: true, mute: false),
        );
      });
    } else {
      _showToast(_labels[_lang]!["err_invalid_link"]!);
    }
  }

  void _filterVideos(String query) {
    setState(() {
      _searchQuery = query;
      _filteredVideos = _allVideos
          .where((v) => v['title'].toString().toLowerCase().contains(query.toLowerCase()))
          .toList();
    });
  }

  Future<void> _likeVideo(String vidId) async {
    String realName = _studentProfile["name"];
    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}$apiPrefix/videos/$vidId/like'),
        headers: {"Content-Type": "application/json"},
        body: json.encode({"username": realName}),
      );
      if (response.statusCode == 200) {
        // Cập nhật lại data video realtime
        final refreshRes = await http.get(Uri.parse('${AppConfig.apiUrl}$apiPrefix/videos'));
        if (refreshRes.statusCode == 200) {
          final refreshedData = json.decode(utf8.decode(refreshRes.bodyBytes));
          setState(() {
            _allVideos = refreshedData;
            if (_selectedVideo != null) {
              _selectedVideo = _allVideos.firstWhere((e) => e['id'] == vidId);
            }
          });
        }
      }
    } catch (e) {
      _showToast(_labels[_lang]!["toast_api_err"]!);
    }
  }

  Future<void> _completeVideo(String vidId) async {
    String anchorKey = _studentProfile["email_key"] ?? "Student";
    String encodedKey = Uri.encodeComponent(anchorKey);
    Map<String, dynamic> payload = {"video_id": vidId, "exp_earned": 30};

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}$apiPrefix/student/$encodedKey/complete-video'),
        headers: {"Content-Type": "application/json"},
        body: json.encode(payload),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        setState(() {
          _studentProfile['completed_tasks'].add(vidId);
          _studentProfile['exp'] += 30;
        });
        _showToast(_labels[_lang]!["toast_success_exp"]!);
      } else {
        _showToast(_labels[_lang]!["toast_save_err"]!);
      }
    } catch (e) {
      setState(() {
        _studentProfile['completed_tasks'].add(vidId);
        _studentProfile['exp'] += 30;
      });
      _showToast(_labels[_lang]!["toast_success_exp"]!);
    }
  }

  Future<void> _submitComment(String vidId) async {
    String cmtText = _commentController.text.trim();
    if (cmtText.isEmpty) return;

    String realName = _studentProfile["name"];
    Map<String, String> newComment = {"author": realName, "text": cmtText};

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}$apiPrefix/videos/$vidId/comments'),
        headers: {"Content-Type": "application/json"},
        body: json.encode(newComment),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        _commentController.clear();
        final refreshRes = await http.get(Uri.parse('${AppConfig.apiUrl}$apiPrefix/videos'));
        if (refreshRes.statusCode == 200) {
          final refreshedData = json.decode(utf8.decode(refreshRes.bodyBytes));
          setState(() {
            _allVideos = refreshedData;
            _selectedVideo = _allVideos.firstWhere((element) => element['id'] == vidId);
          });
        }
      }
    } catch (e) {
      _showToast(_labels[_lang]!["err_send_cmt"]!);
    }
  }

  void _showToast(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final labels = _labels[_lang]!;
    return Scaffold(
      appBar: AppBar(
        title: Text(_selectedVideo == null ? labels["title"]! : _selectedVideo!['title']),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        actions: [
          TextButton(
            onPressed: () async {
              setState(() => _lang = _lang == "vi" ? "en" : "vi");
              await _storage.write(key: 'app_lang', value: _lang); // LƯU TRẠNG THÁI NGÔN NGỮ KHI CHUYỂN
            },
            child: Text(
              _lang.toUpperCase(),
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _selectedVideo == null
              ? _buildVideoGridList(labels) 
              : _buildVideoDetailPlayer(labels),
    );
  }

  // -------------------------------------------------------------------------
  // GIAO DIỆN DANH SÁCH BÀI HỌC (GRID VIEW)
  // -------------------------------------------------------------------------
  Widget _buildVideoGridList(Map<String, String> labels) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: TextField(
            onChanged: _filterVideos,
            decoration: InputDecoration(
              hintText: labels["search_placeholder"],
              prefixIcon: const Icon(Icons.search),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              contentPadding: const EdgeInsets.symmetric(vertical: 8),
            ),
          ),
        ),
        Expanded(
          child: _filteredVideos.isEmpty
              ? Center(child: Text(labels["info_empty"]!))
              : GridView.builder(
                  padding: const EdgeInsets.all(10),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2, 
                    childAspectRatio: 0.82,
                    crossAxisSpacing: 10,
                    mainAxisSpacing: 10,
                  ),
                  itemCount: _filteredVideos.length,
                  itemBuilder: (context, index) {
                    final video = _filteredVideos[index];
                    String vidId = video['id'] ?? "";
                    bool isCompleted = _studentProfile['completed_tasks']?.contains(vidId) ?? false;
                    String topic = video['topic'] ?? "General";

                    return Card(
                      elevation: 4,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ClipRRect(
                            borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                            child: Image.network(
                              _getYtThumbnail(video['url']),
                              height: 105,
                              width: double.infinity,
                              fit: BoxFit.cover,
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(8.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  video['title'] ?? labels["default_title"]!,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  isCompleted
                                      ? "${labels['lbl_completed']} | 📌 $topic"
                                      : "${labels['lbl_reward_hint']} | 📌 $topic",
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: isCompleted ? Colors.green : Colors.orange,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                SizedBox(
                                  width: double.infinity,
                                  height: 32,
                                  child: ElevatedButton(
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.indigoAccent,
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                    ),
                                    onPressed: () => _initializeVideo(video),
                                    child: Text(labels["btn_watch"]!, style: const TextStyle(fontSize: 12, color: Colors.white)),
                                  ),
                                )
                              ],
                            ),
                          )
                        ],
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  // -------------------------------------------------------------------------
  // GIAO DIỆN CHI TIẾT XEM BÀI HỌC
  // -------------------------------------------------------------------------
  Widget _buildVideoDetailPlayer(Map<String, String> labels) {
    String vidId = _selectedVideo!['id'] ?? "";
    bool isCompleted = _studentProfile['completed_tasks']?.contains(vidId) ?? false;
    List<dynamic> likedBy = _selectedVideo!['liked_by'] ?? [];
    int likesCount = _selectedVideo!['likes'] ?? 0;
    bool hasLiked = likedBy.contains(_studentProfile["name"]);

    List<dynamic> comments = List.from(_selectedVideo!['comments'] ?? []);
    List<dynamic> reversedComments = comments.reversed.toList();

    return YoutubePlayerBuilder(
      player: YoutubePlayer(
        controller: _ytController!,
        showVideoProgressIndicator: true,
        progressIndicatorColor: Colors.blueAccent,
      ),
      builder: (context, player) {
        return SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              player,

              Padding(
                padding: const EdgeInsets.all(12.0),
                key: ValueKey(vidId),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _selectedVideo!['title'] ?? labels["default_title"]!,
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      "${labels['lbl_topic']} ${_selectedVideo!['topic'] ?? 'Khác'} • ${labels['lbl_level']} ${_selectedVideo!['level'] ?? ''} • ${labels['lbl_reward']} +30 EXP",
                      style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                    ),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              foregroundColor: hasLiked ? Colors.red : Colors.indigo,
                              side: BorderSide(color: hasLiked ? Colors.red : Colors.indigo),
                            ),
                            onPressed: () => _likeVideo(vidId),
                            icon: Icon(hasLiked ? Icons.favorite : Icons.thumb_up_alt_outlined),
                            label: Text(
                              hasLiked
                                  ? labels["btn_like_done"]!.replaceAll("{}", likesCount.toString())
                                  : labels["btn_like"]!.replaceAll("{}", likesCount.toString()),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: isCompleted ? Colors.grey : Colors.green,
                            ),
                            onPressed: isCompleted ? null : () => _completeVideo(vidId),
                            child: Text(
                              isCompleted ? labels["btn_completed_lesson"]! : labels["btn_complete_lesson"]!,
                              style: const TextStyle(color: Colors.white),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 30),

                    Text(
                      "${reversedComments.length} ${labels['lbl_comments_count']}",
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _commentController,
                            decoration: InputDecoration(
                              hintText: labels["cmt_placeholder"],
                              border: const OutlineInputBorder(),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            ),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.send, color: Colors.indigo),
                          onPressed: () => _submitComment(vidId),
                        )
                      ],
                    ),
                    const SizedBox(height: 12),

                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: reversedComments.length,
                      itemBuilder: (context, cIndex) {
                        final cmt = reversedComments[cIndex];
                        String author = labels["author_anonymous"]!;
                        String text = "";

                        if (cmt is Map) {
                          author = cmt["author"] ?? labels["author_anonymous"]!;
                          text = cmt["text"] ?? "";
                        } else {
                          text = cmt.toString();
                        }

                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: CircleAvatar(
                            backgroundColor: Colors.orangeAccent,
                            child: Text(author.isNotEmpty ? author[0].toUpperCase() : "U", style: const TextStyle(color: Colors.white)),
                          ),
                          title: Text("@${author.replaceAll(' ', '')}", style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                          subtitle: Text(text, style: const TextStyle(color: Colors.black87)),
                        );
                      },
                    ),
                    const Divider(height: 30),

                    Text(labels["playlist_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 10),
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: _allVideos.length,
                      itemBuilder: (context, pIndex) {
                        final v = _allVideos[pIndex];
                        if (v['id'] == vidId) return const SizedBox.shrink();

                        return Card(
                          margin: const EdgeInsets.symmetric(vertical: 5),
                          child: ListTile(
                            leading: ClipRRect(
                              borderRadius: BorderRadius.circular(6),
                              child: Image.network(_getYtThumbnail(v['url']), width: 80, height: 45, fit: BoxFit.cover),
                            ),
                            title: Text(v['title'] ?? labels["default_title"]!, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                            subtitle: Text(labels["channel_name"]!, style: const TextStyle(fontSize: 12)),
                            trailing: const Icon(Icons.play_circle_outline, color: Colors.indigo),
                            onTap: () {
                              _ytController?.load(YoutubePlayer.convertUrlToId(v['url'])!);
                              setState(() {
                                _selectedVideo = v;
                              });
                            },
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}