import os
import sqlite3
import openai
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

# ───────── 설정 ─────────
openai.api_key = "OPEN_API"  # OpenAI API 키 설정
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

def extract_filters(user_input):
    filters = {}
    compact_input = user_input.replace(" ", "")

    # 🎓 졸업 요건
    if any(kw in user_input for kw in [
        "졸업", "졸업요건", "졸업 기준", "졸업 조건", "졸업학점", "이수학점", 
        "졸업하려면", "총 몇 학점", "졸업 요건 알려줘", "학점 조건"
    ]):
        filters["table"] = "graduation_credits"
        if "신입" in user_input or "신입생" in user_input:
            filters["entry_type"] = "신입"
        elif "편입" in user_input or "편입생" in user_input:
            filters["entry_type"] = "편입"
        elif "전과" in user_input or "학과 변경" in user_input:
            filters["entry_type"] = "전과"

        if "인공지능" in user_input:
            filters["program"] = "인공지능융합학부"
        elif "건축" in user_input or "건축학" in user_input:
            filters["program"] = "건축학과"
        elif "약학" in user_input or "약대" in user_input:
            filters["program"] = "약학과"
        else:
            filters["program"] = "일반 학과"
        if "entry_type" not in filters or "program" not in filters:
            return None

    # 🍽️ 식당 추천
    elif any(kw in user_input for kw in [
        "식당", "맛집", "메뉴", "점심", "저녁", "밥", "뭐 먹지", "학교 근처 음식", 
        "근처 맛집", "음식 추천", "가까운 식당", "카페", "혼밥", "식사 장소", "추천 식당"
    ]):
        filters["table"] = "restaurants"

    # 📚 교양 과목
    elif any(kw in user_input for kw in [
        "교양", "교양 과목", "추천 과목", "인기 교양", "교양 추천", "쉬운 교양", 
        "재밌는 교양", "과탑 교양", "교양 수업", "좋은 교양", "교양 선택", "교양 평가"
    ]):
        filters["table"] = "liberal_arts"

    # 📂 이수체계도
    elif any(kw in user_input for kw in [
    "이수체계도", "과목 흐름", "커리큘럼", "전공 순서", "과목 순서", "전공 과목 흐름",
    "로드맵", "과정 안내", "이수 로드맵", "졸업까지 과목", "학과별 과목"
    ]):
        filters["table"] = "department_curriculum"

    if "인공지능" in user_input or "인지융" in user_input:
        filters["dept_name"] = "인공지능융합학부"
    elif "컴퓨터" in user_input or "컴공" in user_input:
        filters["dept_name"] = "컴퓨터공학부"
    elif "자전" in user_input or "자유전공학부" in user_input:
        filters["dept_name"] = "자유전공학부"
    elif "화생" in user_input or "화학생명과학" in user_input:
        filters["dept_name"] = "화학생명과학과"
    elif "데이터클라우드" in user_input or "데이터클라우드학부" in user_input:
        filters["dept_name"] = "데이터클라우드공학과"
    elif "항공" in user_input or "항공관광외국어학부" in user_input:
        filters["dept_name"] = "항공관광외국어학부"
    elif "바이오" in user_input or "바이오융합공학부" in user_input:
        filters["dept_name"] = "바이오융합공학과"
    elif "체육" in user_input or "체육학부" in user_input:
        filters["dept_name"] = "체육학과"
    elif "물치" in user_input or "물리치료" in user_input:
        filters["dept_name"] = "물리치료학과"
    elif "상심" in user_input or "상담심리학부" in user_input:
        filters["dept_name"] = "상담심리학과"
    elif "아디" in user_input or "아트앤디자인학부" in user_input:
        filters["dept_name"] = "아트앤디자인학과"
    elif "보건" in user_input or "보건관리" in user_input:
        filters["dept_name"] = "보건관리학과"
    elif "환디" in user_input or "환경디자인" in user_input:
        filters["dept_name"] = "환경디자인원예학과"
    elif "식영" in user_input or "식품영양" in user_input:
        filters["dept_name"] = "식품영양학과"
    elif "동생자" in user_input or "동물자원" in user_input or "동물생명" in user_input:
        filters["dept_name"] = "동물자원학과"
    elif "약학" in user_input or "약대" in user_input:
        filters["dept_name"] = "약학과"


    # 📅 학사 일정
    elif any(kw in compact_input for kw in [
        "2025 학사일정","2026 학사일정","학사일정", "학기일정", "캘린더", "개강일", "개강날짜","일정",
        "중간고사", "기말고사", "수강신청", "성적입력", "방학기간",
        "휴강일", "공휴일", "수업일정", "종강", "학사캘린더"
    ]):
        filters["table"] = "academic_calendar"
        match = re.search(r"(\d{1,2})월", user_input)
        if match:
            filters["month"] = int(match.group(1))

    # # 👨‍🏫 교직 이수
    # elif any(kw in user_input for kw in [
    #     "교직", "교직이수", "교직 과목", "교직 요건", "교직 수강", "교직 관련", 
    #     "교사 자격", "교직 학점", "교직 커리큘럼", "교직 조건", "교육학"
    # ]):
    #     filters["table"] = "teacher_education"

    # 💰 장학금 정보
    elif any(kw in user_input for kw in [
        "장학금", "장학", "학비 지원", "장학금 신청", "특별 장학금", "근로 장학금",
        "성적 장학금", "지원금", "등록금 지원", "학비 감면", "수혜 조건", "장학 요건"
    ]):
        filters["table"] = "scholarships"
    # 🏣 증명서 발급 방식
    elif any(kw in user_input for kw in [
        "증명서 발급", "무인 발급기", "팩스 발급", "인터넷 발급", "우편 발급", 
        "발급 방법", "신청 방법", "서류 받는 법", "학교에서 받는 법", "증명서 신청",
        "어디서 발급", "발급 시간", "증명서"
    ]):
        filters["table"] = "certificate_issuance"
    
    # 📄 증명서 종류
    elif any(kw in user_input for kw in [
        "증명서", "성적표", "재학증명서", "졸업증명서", "휴학증명서", "수료증명서", 
        "서류", "학교 서류", "확인서", "영문 증명서", "한글 증명서", "증빙서류"
    ]):
        filters["table"] = "certificates"

    # graduation_credits만 조건 필수
    if filters.get("table") == "graduation_credits":
        if "entry_type" not in filters or "program" not in filters:
            return None

    return filters if "table" in filters else None




# ───────── 테이블별 fetch 및 포맷 ─────────
def fetch_and_format(table, user_input, filters):
    def wrap_prompt(data_text):
        return f"사용자 질문: '{user_input}'\n\n다음은 검색된 정보입니다:\n\n{data_text}\n\n위 내용을 바탕으로 자연스럽고 이해하기 쉽게 요약해서 설명해줘."

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
            return "졸업요건 정보를 찾지 못했습니다."
        data = "\n".join([
            f"🡩‍🎓 {r[1]} ({r[0]})\n- 총 학점: {r[3]}, 교양 필수: {r[4]}, 전공: {r[6]}, 자유학점: {r[15]}"
            for r in rows
        ])
        print(data)
        return ask_gpt(wrap_prompt(data))

    elif table == "department_curriculum":
        if "dept_name" in filters:
            rows = query_db("SELECT dept_name, curriculum_url FROM department_curriculum WHERE dept_name LIKE ?",
                            (f"%{filters['dept_name']}%",))
        else:
            rows = query_db("SELECT dept_name, curriculum_url FROM department_curriculum")
        if not rows:
            return "커리큘럼 정보를 찾지 못했습니다."
        data = "\n".join([f"📂 {r[0]}: {r[1]}" for r in rows])
        print(data)
        return ask_gpt(wrap_prompt(data))

    elif table == "restaurants":
        rows = query_db("SELECT name, category, distance_min, tags, description FROM restaurants")
        if not rows:
            return "식당 정보를 찾지 못했습니다."
        data = "\n\n".join([
            f"🍽️ {r[0]} ({r[1]})\n- 거리: {r[2]}분, 태그: {r[3]}\n- 설명: {r[4]}"
            for r in rows
        ])
        print(data)
        return ask_gpt(wrap_prompt(data))

    elif table == "liberal_arts":
        rows = query_db("SELECT name, professor, category, grade_level, review FROM liberal_arts")
        if not rows:
            return "교양 수업 정보를 찾지 못했습니다."
        data = "\n\n".join([
            f"📘 {r[0]} ({r[1]})\n- 분류: {r[2]}, 학년: {r[3]}\n- 리뷰: {r[4]}"
            for r in rows
        ])
        print(data)
        return ask_gpt(wrap_prompt(data))

    elif table == "academic_calendar":
        rows = query_db("SELECT year, month, start_date, end_date, event FROM academic_calendar ORDER BY year, month, start_date")
        data = "\n\n".join([
            f"🗓️ {r[0]}년 {r[1]}월 {r[2]}~{r[3]}: {r[4]}"
            for r in rows
        ])
        print(data)
        return ask_gpt(wrap_prompt(data))

    elif table == "scholarships":
        rows = query_db("SELECT category, name, app_period, dist_period, eligibility, remarks FROM scholarships")
        data = "\n\n".join([
            f"🎓 {r[1]} ({r[0]})\n- 신청기간: {r[2]} / 배부기간: {r[3]}\n- 자격: {r[4]}\n- 비고: {r[5]}"
            for r in rows
        ])
        print(data)
        return ask_gpt(wrap_prompt(data))

    elif table == "certificates":
        rows = query_db("SELECT target, department, korean_name, english_name FROM certificates")
        data = "\n\n".join([
            f"📄 대상: {r[0]} / 부서: {r[1]}\n- 한국어: {r[2]} / 영어: {r[3]}"
            for r in rows
        ])
        print(data)
        return ask_gpt(wrap_prompt(data))

    elif table == "certificate_issuance":
        rows = query_db("SELECT channel, method, hours, processing_time, fee_info, payment_method, extra_info FROM certificate_issuance")
        data = "\n\n".join([
            f"📌 {r[0]} ({r[1]})\n- 이용 시간: {r[2]}\n- 처리 시간: {r[3]}\n- 수수료: {r[4]}\n- 결제 수단: {r[5]}\n- 비고: {r[6]}"
            for r in rows
        ])
        print(data)
        return ask_gpt(wrap_prompt(data))

    return "해당 정보를 찾지 못했습니다."


def ask_gpt(prompt):
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 친직하고 전문적인 삼육대학교 AI 채트보트입니다. 사용자에게 정확하고 이해하기 쉬운 결과를 설명해주세요."},
                {"role": "user", "content": prompt}
            ]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ───────── GPT 호출 ─────────
def ask_gpt(prompt):
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 친직하고 전문적인 삼육대학교 AI 채트보트입니다. 사용자에게 정확하고 이해하기 쉬운 결과를 설명해주세요."},
                {"role": "user", "content": prompt}
            ]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"GPT 호출 오류: {e}"

# ───────── POST /api/ask ─────────
@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")
    filters = extract_filters(question)

    if filters and "table" in filters:
        table = filters["table"]
        response_text = fetch_and_format(table, question, filters)
        return jsonify({"answer": response_text})

    answer = ask_gpt(question)
    return jsonify({"answer": answer})




# ───────── 서버 기동 ─────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=True)
