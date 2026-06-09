import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:youtube_player_flutter/youtube_player_flutter.dart';

class VideoScreen extends StatefulWidget {
  const VideoScreen({Key? key}) : super(key: key);

  @override
  State<VideoScreen> createState() => _VideoScreenState();
}

class _VideoScreenState extends State<VideoScreen> {
    
final String baseUrl = 'http://10.0.2.2:8000';
  final String apiPrefix = '/api/tv2'; 

  // State quản lý dữ liệu
  List<dynamic> _allVideos = [];
  List<dynamic> _filteredVideos = [];
  bool _isLoading = true;
  String _searchQuery = "";
  String _lang = "vi"; // Mặc định ngôn ngữ tiếng Việt (Hỗ trợ song ngữ giống Web)

  // Quản lý video đang được chọn phát
  Map<String, dynamic>? _selectedVideo;
  YoutubePlayerController? _ytController;
  final TextEditingController _commentController = TextEditingController();

  // Profile học sinh giả lập (Sẽ đồng bộ qua hệ thống auth/session sau)
  Map<String, dynamic> _studentProfile = {
    "name": "Thanh Minh",
    "exp": 0,
    "completed_tasks": []
  };

  // Bộ từ điển song ngữ chuẩn hóa từ file Streamlit
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
      "playlist_title": "📂 Danh Sách Bài Học",
      "author_anonymous": "Ẩn danh"
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
      "playlist_title": "📂 Course Playlist",
      "author_anonymous": "Anonymous"
    }
  };

  @override
  void initState() {
    super.initState();
    _fetchVideos();
  }

  @override
  void dispose() {
    _ytController?.dispose();
    _commentController.dispose();
    super.dispose();
  }

  // Lấy danh sách Video từ API của module TV2 Academic
  Future<void> _fetchVideos() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl$apiPrefix/videos'));
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _allVideos = data;
          _filteredVideos = data;
          _isLoading = false;
        });
      } else {
        _showToast("⚠️ Lỗi kết nối API máy chủ!");
      }
    } catch (e) {
      setState(() => _isLoading = false);
      _showToast("⚠️ Không thể kết nối tới Backend!");
    }
  }

  // Hàm trích xuất ID youtube để lấy ảnh đại diện Thumbnail tự động giống Streamlit
  String _getYtThumbnail(String url) {
    RegExp regExp = RegExp(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*");
    Match? match = regExp.firstMatch(url);
    if (match != null) {
      return "https://img.youtube.com/vi/${match.group(1)}/hqdefault.jpg";
    }
    return "https://via.placeholder.com/320x180.png?text=Video";
  }

  // Khởi tạo trình phát video khi học sinh nhấn vào bài học
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
          flags: const YoutubePlayerFlags(
            autoPlay: true,
            mute: false,
          ),
        );
      });
    } else {
      _showToast(_labels[_lang]!["err_invalid_link"] ?? "Link lỗi");
    }
  }

  // Hàm xử lý tìm kiếm video bài học
  void _filterVideos(String query) {
    setState(() {
      _searchQuery = query;
      _filteredVideos = _allVideos
          .where((v) => v['title'].toString().toLowerCase().contains(query.toLowerCase()))
          .toList();
    });
  }

  // Xử lý sự kiện Like Video lên API Backend
  Future<void> _likeVideo(String vidId) async {
    String realName = _studentProfile["name"];
    try {
      final response = await http.post(
        Uri.parse('$baseUrl$apiPrefix/videos/$vidId/like'),
        headers: {"Content-Type": "application/json"},
        body: json.encode({"username": realName}),
      );
      if (response.statusCode == 200) {
        // Cập nhật lại data video realtime
        _fetchVideos().then((_) {
          if (_selectedVideo != null) {
            setState(() {
              _selectedVideo = _allVideos.firstWhere((element) => element['id'] == vidId);
            });
          }
        });
      }
    } catch (e) {
      _showToast(_labels[_lang]!["toast_api_err"]!);
    }
  }

  // Xử lý sự kiện bấm hoàn thành bài học để nhận +30 EXP
  Future<void> _completeVideo(String vidId) async {
    String encodedName = Uri.encodeComponent(_studentProfile["name"]);
    Map<String, dynamic> payload = {"video_id": vidId, "exp_earned": 30};

    try {
      final response = await http.post(
        Uri.parse('$baseUrl$apiPrefix/student/$encodedName/complete-video'),
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
      // Hỗ trợ lưu local offline nếu backend timeout
      setState(() {
        _studentProfile['completed_tasks'].add(vidId);
        _studentProfile['exp'] += 30;
      });
      _showToast(_labels[_lang]!["toast_success_exp"]!);
    }
  }

  // Bắn dữ liệu bình luận bài học lên MongoDB thông qua Router Backend
  Future<void> _submitComment(String vidId) async {
    String cmtText = _commentController.text.trim();
    if (cmtText.isEmpty) return;

    String realName = _studentProfile["name"];
    Map<String, String> newComment = {"author": realName, "text": cmtText};

    try {
      final response = await http.post(
        Uri.parse('$baseUrl$apiPrefix/videos/$vidId/comments'),
        headers: {"Content-Type": "application/json"},
        body: json.encode(newComment),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        _commentController.clear();
        _fetchVideos().then((_) {
          setState(() {
            _selectedVideo = _allVideos.firstWhere((element) => element['id'] == vidId);
          });
        });
      }
    } catch (e) {
      _showToast("Không gửi được bình luận.");
    }
  }

  void _showToast(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_selectedVideo == null ? _labels[_lang]!["title"]! : _selectedVideo!['title']),
        backgroundColor: Colors.indigo,
        actions: [
          // Nút chuyển đổi nhanh ngôn ngữ (vi/en) đồng bộ trải nghiệm người dùng
          TextButton(
            onPressed: () {
              setState(() {
                _lang = _lang == "vi" ? "en" : "vi";
              });
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
              ? _buildVideoGridList()  // Trình xem danh sách video bài giảng
              : _buildVideoDetailPlayer(), // Trình phát chi tiết (Player, Like, Cmt, Playlist)
    );
  }

  // -------------------------------------------------------------------------
  // GIAO DIỆN DANH SÁCH BÀI HỌC (GRID VIEW)
  // -------------------------------------------------------------------------
  Widget _buildVideoGridList() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: TextField(
            onChanged: _filterVideos,
            decoration: InputDecoration(
              hintText: _labels[_lang]!["search_placeholder"],
              prefixIcon: const Icon(Icons.search),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              contentPadding: const EdgeInsets.symmetric(vertical: 8),
            ),
          ),
        ),
        Expanded(
          child: _filteredVideos.isEmpty
              ? Center(child: Text(_labels[_lang]!["info_empty"]!))
              : GridView.builder(
                  padding: const EdgeInsets.all(10),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2, // Chia thành 2 cột cân xứng trên màn hình Mobile
                    childAspectRatio: 0.82,
                    crossAxisSpacing: 10,
                    mainAxisSpacing: 10,
                  ),
                  itemCount: _filteredVideos.length,
                  itemBuilder: (context, index) {
                    final video = _filteredVideos[index];
                    String vidId = video['id'] ?? "";
                    bool isCompleted = _studentProfile['completed_tasks'].contains(vidId);
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
                                  video['title'] ?? "",
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  isCompleted
                                      ? _labels[_lang]!["lbl_completed"]! + " | 📌 $topic"
                                      : _labels[_lang]!["lbl_reward_hint"]! + " | 📌 $topic",
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
                                    child: Text(_labels[_lang]!["btn_watch"]!, style: const TextStyle(fontSize: 12, color: Colors.white)),
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
  // GIAO DIỆN CHI TIẾT XEM BÀI HỌC (PLAYER + COMMENTS + PLAYLIST)
  // -------------------------------------------------------------------------
  Widget _buildVideoDetailPlayer() {
    String vidId = _selectedVideo!['id'] ?? "";
    bool isCompleted = _studentProfile['completed_tasks'].contains(vidId);
    List<dynamic> likedBy = _selectedVideo!['liked_by'] ?? [];
    int likesCount = _selectedVideo!['likes'] ?? 0;
    bool hasLiked = likedBy.contains(_studentProfile["name"]);

    // Đảo ngược danh sách bình luận để hiển thị cái mới nhất lên đầu giống file Streamlit (.reverse())
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
              // 1. Khung phát Video Youtube lớn
              player,

              Padding(
                padding: const EdgeInsets.all(12.0),
                key: ValueKey(vidId),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Tiêu đề & Thông số bài giảng
                    Text(
                      _selectedVideo!['title'] ?? "",
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      "${_labels[_lang]!['lbl_topic']} ${_selectedVideo!['topic'] ?? 'Khác'} • ${_labels[_lang]!['lbl_level']} ${_selectedVideo!['level'] ?? ''} • ${_labels[_lang]!['lbl_reward']} +30 EXP",
                      style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                    ),
                    const SizedBox(height: 12),

                    // Nhóm nút tương tác: Like & Hoàn thành bài học nhận thưởng
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
                                  ? _labels[_lang]!["btn_like_done"]!.replaceAll("{}", likesCount.toString())
                                  : _labels[_lang]!["btn_like"]!.replaceAll("{}", likesCount.toString()),
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
                              isCompleted
                                  ? _labels[_lang]!["btn_completed_lesson"]!
                                  : _labels[_lang]!["btn_complete_lesson"]!,
                              style: const TextStyle(color: Colors.white),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 30),

                    // 2. Khu vực viết & Hiển thị bình luận bài học
                    Text(
                      "${reversedComments.length} ${_labels[_lang]!['lbl_comments_count']}",
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _commentController,
                            decoration: InputDecoration(
                              hintText: _labels[_lang]!["cmt_placeholder"],
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

                    // Danh sách các bình luận học sinh đã viết
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: reversedComments.length,
                      itemBuilder: (context, cIndex) {
                        final cmt = reversedComments[cIndex];
                        String author = "Ẩn danh";
                        String text = "";

                        if (cmt is Map) {
                          author = cmt["author"] ?? _labels[_lang]!["author_anonymous"];
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

                    // 3. Khối gợi ý danh sách bài học tiếp theo (Playlist liên quan)
                    Text(_labels[_lang]!["playlist_title"]!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
                            title: Text(v['title'] ?? "", maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                            subtitle: const Text("iKids Education", style: TextStyle(fontSize: 12)),
                            trailing: const Icon(Icons.play_circle_outline, color: Colors.indigo),
                            // ĐÃ SỬA TỪ onPressed THÀNH onTap Ở ĐÂY:
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