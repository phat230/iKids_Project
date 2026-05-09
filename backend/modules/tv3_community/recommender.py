from datetime import datetime
from bson import ObjectId

async def generate_smart_recommendation(db, student_id: str):
    """
    Phân tích kết quả học tập từ TV2 (quiz_results) để tự động gợi ý bài ôn tập.
    Mục tiêu Giai đoạn 4: Tự động hóa hỗ trợ học sinh yếu.
    """
    try:
        # 1. Tìm kết quả bài tập gần nhất của học sinh
        # Sắp xếp theo submitted_at giảm dần để lấy bài mới nhất
        last_quiz = await db.quiz_results.find_one(
            {"student_id": student_id},
            sort=[("submitted_at", -1)]
        )

        if not last_quiz:
            return None

        # 2. Kiểm tra nếu điểm dưới 50% (giả sử thang điểm 100)
        # Nếu thang điểm 10, bạn hãy sửa lại thành last_quiz['score'] < 5
        if last_quiz['score'] < 50:
            material_id = last_quiz.get('material_id')
            
            # 3. Kiểm tra xem đã có gợi ý này trong hệ thống chưa (tránh trùng lặp)
            existing = await db.smart_recommendations.find_one({
                "student_id": student_id,
                "material_id": material_id,
                "status": "new"
            })
            
            if not existing:
                recommendation = {
                    "student_id": student_id,
                    "material_id": material_id,
                    "topic_name": last_quiz.get('topic_name', 'Bài học vừa qua'),
                    "score_achieved": last_quiz['score'],
                    "reason": "weak_topic", # Đánh dấu là học sinh yếu phần này
                    "suggestion": "Em nên xem lại tài liệu và làm lại bài tập này để nắm vững kiến thức nhé!",
                    "status": "new",
                    "created_at": datetime.now()
                }
                
                # 4. Lưu vào collection smart_recommendations
                result = await db.smart_recommendations.insert_one(recommendation)
                recommendation["_id"] = str(result.inserted_id)
                return recommendation
            
            return existing # Trả về gợi ý cũ nếu chưa xử lý
            
    except Exception as e:
        print(f"Lỗi Recommender: {str(e)}")
        return None
    
    return None

async def get_list_recommendations(db, student_id: str):
    """
    Hàm bổ trợ để Frontend gọi hiển thị danh sách gợi ý lên Dashboard học sinh.
    """
    return await db.smart_recommendations.find(
        {"student_id": student_id, "status": "new"}
    ).sort("created_at", -1).to_list(length=5)