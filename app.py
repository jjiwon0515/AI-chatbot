import os
import sqlite3
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

# ───────── 설정 ─────────
openai.api_key = os.getenv("OPENAI_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "unibot_extended.db")

app = Flask(__name__)
CORS(app)

# ───────── 유틸 함수 ─────────
def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# ───────── RAG용 질문 필터 추출 ─────────
def extract_filters(user_input):
    filters = {}

    if "학점" in user_input or "졸업" in user_input:
        filters["table"] = "graduation_credits"

        if "신입" in user_input:
            filters["entry_type"] = "신입"
        elif "편입" in user_input:
            filters["entry_type"] = "편입"
        elif "전과" in user_input:
            filters["entry_type"] = "전과"

        if "인공지능" in user_input or "인지융" in user_input:
            filters["program"] = "인공지능융합학부"
        elif "건축" in user_input:
            filters["program"] = "건축학과"
        elif "약학" in user_input:
            filters["program"] = "약학과"
        else:
            filters["program"] = "일반 학과"

        # 필수 조건이 빠졌다면 무효
        if "entry_type" not in filters or "program" not in filters:
            return None

    elif "식당" in user_input or "맛집" in user_input:
        filters["table"] = "restaurants"

    elif "교양" in user_input or "추천 과목" in user_input:
        filters["table"] = "liberal_arts"

    elif "이수체계도" in user_input:
        filters["table"] = "department_curriculum"

    elif "학사 일정" in user_input:
        filters["table"] = "academic_calendar"

    elif "교직" in user_input or "교직과목" in user_input:
        filters["table"] = "teacher_education"

    elif "장학금" in user_input:
        filters["table"] = "scholarships"

    elif "증명서 발급" in user_input or "증명서" in user_input:
        filters["table"] = "certificates"

    
    # graduation_credits만 특별히 조건 필요
    if filters.get("table") == "graduation_credits":
        if "entry_type" not in filters or "program" not in filters:
            return None

    return filters if "table" in filters else None


# ───────── 테이블별 fetch 및 포맷 ─────────
def fetch_and_format(table, user_input):
    if table == "restaurants":
        rows = query_db("SELECT name, category, distance_min, tags, description FROM restaurants")
        if not rows:
            return "식당 정보를 찾지 못했습니다."
        result = "\n\n".join([
            f"🍽️ {r[0]} ({r[1]})\n- 거리: {r[2]}분, 태그: {r[3]}\n- 설명: {r[4]}"
            for r in rows
        ])
        return f"'{user_input}'에 대한 음식점 추천 정보입니다:\n\n{result}\n\n요약해서 알려줘."

    elif table == "liberal_arts":
        rows = query_db("SELECT name, professor, category, grade_level, review FROM liberal_arts")
        if not rows:
            return "교양 수업 정보를 찾지 못했습니다."
        result = "\n\n".join([
            f"📘 {r[0]} ({r[1]})\n- 분류: {r[2]}, 학년: {r[3]}\n- 리뷰: {r[4]}"
            for r in rows
        ])
        return f"'{user_input}'에 대한 교양 과목 정보입니다:\n\n{result}\n\n추천 위주로 요약해줘."

    elif table == "department_curriculum":
        rows = query_db("SELECT dept_name, curriculum_url FROM department_curriculum")
        return "\n".join([f"📂 {r[0]}: {r[1]}" for r in rows])

    elif table == "academic_calendar":
        rows = query_db(
            "SELECT year, month, start_date, end_date, event "
            "FROM academic_calendar ORDER BY year, month, start_date"
        )
        result = "\n\n".join([
            f"🗕️ {r[0]}년 {r[1]}월 {r[2]}~{r[3]}: {r[4]}"
            for r in rows
        ])
        return f"'{user_input}'에 대한 학사 일정입니다:\n\n{result}"

    elif table == "teacher_education":
        rows = query_db("SELECT phase, course, credits, note FROM teacher_education")
        result = "\n\n".join([
            f"👨‍🏫 [{r[0]}] {r[1]} ({r[2]}학점): {r[3]}"
            for r in rows
        ])
        return f"'{user_input}'에 대한 교적 이수 과목입니다:\n\n{result}"

    elif table == "scholarships":
        rows = query_db(
            "SELECT category, name, app_period, dist_period, eligibility, remarks "
            "FROM scholarships"
        )
        if not rows:
            return "장학금 정보를 찾지 못했습니다."
        result = "\n\n".join([
            f"🎓 {r[1]} ({r[0]})\n- 신청기간: {r[2]} / 배부기간: {r[3]}"
            f"\n- 자격: {r[4]}\n- 비고: {r[5]}"
            for r in rows
        ])
        return f"'{user_input}'에 대한 장학금 정보입니다:\n\n{result}\n\n간단히 요약해줘."

    elif table == "certificates":
        rows = query_db("SELECT target, department, korean_name, english_name FROM certificates")
        if not rows:
            return "증명서 정보를 찾지 못했습니다."
        result = "\n\n".join([
            f"📄 대상: {r[0]} / 부서: {r[1]}\n- 한국어: {r[2]} / 영어: {r[3]}"
            for r in rows
        ])
        return f"'{user_input}'에 대한 증명서 종류입니다:\n\n{result}"

    return f"'{user_input}'에 대해 일치하는 정보를 찾지 못했습니다."

# ───────── GPT 호출 ─────────
def ask_gpt(prompt):
    try:
        res = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ───────── POST /api/ask ─────────
@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")
    filters = extract_filters(question)

    if filters:
        table = filters["table"]
        if table == "graduation_credits":
            sql = "SELECT * FROM graduation_credits WHERE 1=1"
            params = []
            if "entry_type" in filters:
                sql += " AND entry_type = ?"
                params.append(filters["entry_type"])
            if "program" in filters:
                sql += " AND program LIKE ?"
                params.append(f"%{filters['program']}%")
            rows = query_db(sql, tuple(params))
            if not rows:
                return jsonify({"answer": "졸업요건 정보를 찾지 못했습니다."})
            formatted = "\n".join([
                f"🧑‍🎓 {r[1]} ({r[0]})\n- 총 학점: {r[3]}, 교양 필수: {r[4]}, "
                f"전공: {r[6]}, 자유학점: {r[15]}"
                for r in rows
            ])
            prompt = (
                f"사용자 질문: \"{question}\"\n"
                f"다음은 검색된 졸업요건 정보입니다:\n{formatted}\n"
                "위 데이터를 바탕으로 이해하기 쉽게 설명해줘."
            )
        else:
            prompt = fetch_and_format(table, question)
    else:
        prompt = question

    answer = ask_gpt(prompt)
    return jsonify({"answer": answer})

# ───────── GET API 엔드포인트 ─────────
@app.route("/api/restaurants", methods=["GET"])
def get_restaurants():
    rows = query_db("SELECT name, category, distance_min, tags, description FROM restaurants")
    return jsonify([{
        "name": r[0], "category": r[1], "distanceMin": r[2],
        "tags": r[3], "description": r[4]
    } for r in rows])

@app.route("/api/liberal-arts", methods=["GET"])
def get_liberal_arts():
    rows = query_db("SELECT name, professor, category, grade_level, review FROM liberal_arts")
    return jsonify([{
        "name": r[0], "professor": r[1], "category": r[2],
        "gradeLevel": r[3], "review": r[4]
    } for r in rows])

@app.route("/api/graduation-credits", methods=["GET"])
def get_graduation_credits():
    rows = query_db("SELECT * FROM graduation_credits")
    keys = [
        "entryType", "program", "entryTerm", "totalCredits",
        "genRequired", "genAreaReq", "genMajorFusion",
        "dblMain", "dblSub", "minorMain", "minorSub",
        "teachMain", "teachSub", "lifeMain", "lifeSub",
        "freeCredits"
    ]
    return jsonify([dict(zip(keys, row)) for row in rows])

@app.route("/api/department-curriculum", methods=["GET"])
def get_department_curriculum():
    rows = query_db("SELECT dept_name, curriculum_url FROM department_curriculum")
    return jsonify([{"deptName": r[0], "url": r[1]} for r in rows])

@app.route("/api/academic-calendar", methods=["GET"])
def get_academic_calendar():
    rows = query_db(
        "SELECT year, month, start_date, end_date, event "
        "FROM academic_calendar ORDER BY year, month, start_date"
    )
    return jsonify([{
        "year": r[0], "month": r[1], "startDate": r[2],
        "endDate": r[3], "event": r[4]
    } for r in rows])

@app.route("/api/teacher-education", methods=["GET"])
def get_teacher_education():
    rows = query_db("SELECT phase, course, credits, note FROM teacher_education")
    return jsonify([{
        "phase": r[0], "course": r[1], "credits": r[2], "note": r[3]
    } for r in rows])

@app.route("/api/scholarships", methods=["GET"])
def get_scholarships():
    rows = query_db(
        "SELECT category, name, app_period, dist_period, eligibility, remarks "
        "FROM scholarships"
    )
    return jsonify([{
        "category": r[0], "name": r[1], "appPeriod": r[2],
        "distPeriod": r[3], "eligibility": r[4], "remarks": r[5]
    } for r in rows])

@app.route("/api/certificates", methods=["GET"])
def get_certificates():
    rows = query_db("SELECT target, department, korean_name, english_name FROM certificates")
    return jsonify([{
        "target": r[0], "department": r[1],
        "koreanName": r[2], "englishName": r[3]
    } for r in rows])

@app.route("/api/certificate-issuance", methods=["GET"])
def get_certificate_issuance():
    rows = query_db(
        "SELECT channel, method, hours, processing_time, fee_info, payment_method, extra_info "
        "FROM certificate_issuance"
    )
    return jsonify([{
        "channel": r[0], "method": r[1], "hours": r[2],
        "processingTime": r[3], "feeInfo": r[4],
        "paymentMethod": r[5], "extraInfo": r[6]
    } for r in rows])

# ───────── 서버 기동 ─────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


