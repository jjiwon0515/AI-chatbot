import openai
import sqlite3
import os
import re

# ───────── 설정 ─────────
openai.api_key = os.getenv("OPENAI_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "unibot_extended.db")

# ───────── DB 조회 함수 ─────────
def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql, params)
    col_names = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    conn.close()
    return col_names, rows

# ───────── DB 연결 테스트 ─────────
def test_db():
    print("🗄️ DB 연결 테스트 결과:")
    tables = [
        "restaurants", "liberal_arts", "graduation_credits",
        "department_curriculum", "scholarships", "certificates",
        "certificate_issuance", "teacher_education", "academic_calendar"
    ]
    for tbl in tables:
        try:
            _, rows = query_db(f"SELECT * FROM {tbl} LIMIT 1")
            cnt = query_db(f"SELECT COUNT(*) FROM {tbl}")[1][0]
            print(f"  • {tbl}: {cnt} 건 (샘플 컬럼: {', '.join(query_db(f'SELECT * FROM {tbl} LIMIT 1')[0])})")
        except Exception:
            print(f"  ⚠️ {tbl}: 존재하지 않거나 오류 발생")
    print("────────────────────────────\n")

# ───────── 사용자 입력 → 테이블 감지 ─────────
def detect_query_intent(user_input):
    keywords = {
        "식당": "restaurants", "카페": "restaurants", "음식": "restaurants",
        "맛집": "restaurants", "후문": "restaurants", "추천": "restaurants",
        "교양": "liberal_arts",
        "졸업": "graduation_credits", "졸업요건": "graduation_credits",
        "이수체계": "department_curriculum", "학과별": "department_curriculum",
        "커리큘럼": "department_curriculum", "교과과정": "department_curriculum",
        "장학": "scholarships",
        "증명서": "certificates", "발급": "certificate_issuance",
        "교직": "teacher_education",
        "학사일정": "academic_calendar", "학사 일정": "academic_calendar"
    }

    for word, tbl in keywords.items():
        if word in user_input:
            return tbl
    return None


# ───────── 테이블별 데이터 추출 ─────────
def fetch_data_from_table(table_name, user_input=None):
    """
    모든 테이블에 대해 전체 컬럼과 모든 행을 반환합니다.
    """
    sql = f"SELECT * FROM {table_name}"
    return query_db(sql)

# ───────── GPT 호출 ─────────
def ask_openai(question, chat_log=None):
    if chat_log is None:
        chat_log = []
    messages = chat_log + [{"role": "user", "content": question}]
    try:
        res = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ───────── 채팅 메인 루프 ─────────
import re  # 꼭 파일 상단에 import 추가되어 있어야 해

def chat():
    print("💬 챗봇을 시작합니다. 종료하려면 'exit'을 입력하세요.")
    chat_log = []
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() == "exit":
            print("👋 챗봇을 종료합니다.")
            break

        table = detect_query_intent(user_input)
        et = None

        # graduation_credits 특별 분기
        if table == "graduation_credits":
            if "편입" in user_input:
                et = "편입"
            elif "신입" in user_input:
                et = "신입"
            elif "전과" in user_input:
                et = "전과"
            if et:
                sql = f"SELECT * FROM graduation_credits WHERE entry_type = ?"
                col_names, rows = query_db(sql, (et,))
            else:
                col_names, rows = fetch_data_from_table(table, user_input)

        # academic_calendar 월별 필터링 분기
        elif table == "academic_calendar":
            month_match = re.search(r"(\d{1,2})월", user_input)
            if month_match:
                month = int(month_match.group(1))
                sql = "SELECT * FROM academic_calendar WHERE month = ? ORDER BY year, month, start_date"
                col_names, rows = query_db(sql, (month,))
            else:
                col_names, rows = fetch_data_from_table(table, user_input)

        # 일반 테이블
        elif table:
            col_names, rows = fetch_data_from_table(table, user_input)

        # 테이블 감지 실패
        else:
            col_names, rows = [], []

        # 결과문 생성
        if table and rows:
            result_lines = []
            for r in rows:
                items = [f"{col_names[i]}: {r[i]}" for i in range(len(col_names))]
                result_lines.append(" | ".join(items))
            result_text = "\n\n".join(result_lines)
            gpt_prompt = (
                f"사용자가 '{user_input}'라고 질문했어.\n"
                f"DB '{table}'에서 찾은 정보:\n{result_text}\n\n"
                "이 정보를 바탕으로 삼육대학교 내용만 설명해줘."
            )
        else:
            gpt_prompt = (
                f"사용자가 '{user_input}'이라고 질문했어. "
                "데이터가 없어. 학교 홈페이지 참고해줘."
            )

        # 디버깅
        # print("────────────────────")
        # print("사용자 입력:", user_input)
        # print("감지된 테이블:", table if table else "없음")
        # print("추출된 entry_type:", et if table == "graduation_credits" else "-")
        # print("GPT로 전달된 프롬프트:\n", gpt_prompt)
        # print("────────────────────")

        response = ask_openai(gpt_prompt, chat_log)
        print(f"\n AI Bot: {response}\n")
        chat_log.append({"role": "user", "content": user_input})
        chat_log.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    test_db()
    chat()
