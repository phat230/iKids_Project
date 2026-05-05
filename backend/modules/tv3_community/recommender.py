from datetime import datetime

async def generate_smart_recommendation(db, student_id: int):
    """
    Phân tích kết quả học tập từ TV2 để gợi ý bài học.
    """
    last_quiz = await db.quiz_results.find_one(
        {"student_id": student_id},
        sort=[("submitted_at", -1)]
    )

    if not last_quiz:
        return None

    if last_quiz['score'] < 50:
        recommendation = {
            "student_id": student_id,
            "material_id": last_quiz['material_id'],
            "reason": "weak_topic",
            "status": "new",
            "created_at": datetime.now()
        }
        await db.smart_recommendations.insert_one(recommendation)
        return recommendation
    
    return None