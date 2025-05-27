import sqlite3

# DB 파일 경로
db_path = "./chatbot/unibot_extended.db"

# DB 연결 및 커서 생성
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT,
    distance_min INTEGER,
    tags TEXT,
    description TEXT
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS liberal_arts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    professor TEXT,
    category TEXT,
    grade_level TEXT,
    review TEXT
);
""")

restaurants = [
    ('하늘지기', '한식', 5, '가성비, 혼밥', '학교 후문 앞 따뜻한 국밥집'), #4.32
    ('홍원',   '중식', 5, '가성비, 단체', '짜탕면을 파는 중식당'), #4.51
    ('중국관', '중식', 5, '가성비, 빨리나오는', '볶음밥이 맛있는 중식당'), #4.52
    ('호또', '일식당', 6, '일식집, 단체', '오므라이스 맛집'),
    ('린스테이블', '카페', 6, '공부, 조용한', '과제하기 좋은 분위기 좋은 카페'),
    ('신쿵푸마라탕', '중식', 8, '마라탕, 매콤한', '후문 유일 마라탕집'),
    ('토리코코로', '일식', 6, '유명한, 담백한', '후문 유일 라멘집'),
    ('쌀국수 공방', '쌀국수', 10, '매콤한, 담백한', '다양한 음식을 파는 쌀국수집'),
    ('꿈꾸는떡볶이', '분식', 6, '매콤한, 단체, 가성비', '여럿이 먹기 좋은 즉석떡볶이'), #4.39
    ('마녀떡볶이', '분식', 7, '단품메뉴, 매콤한', '즉석 떡볶이와 일품요리 '), #4.39
    ('세상만사 감자탕', '한식', 8, '국물, 조용한', '후문 정류장 바로 앞의 식당'), #4.44
]
liberal_arts = [
    ('클래식 음악과 여행', 'Alexander Park', '인문예술', '전학년', '일찍 끝내주시고 수업내용도 좋은 수업'),
    ('영화속 음악 산책','Alexander Park', '인문예술', '전학년', '일찍 끝내주시고 재미있는 수업'),
    ('연극과 뮤지컬 이해와 감상','최은실', '인문예술', '전학년', '1학기에 연극 2학기에 뮤지컬 수업합니다'),
    ('영화로 읽는 셰익스피어', '이기원', '인문예술', '전학년', '인문학에 관심있는 사람에게 강추하는 수업'),
    ('사고조사이론', '김훈','사회과학', '전학년', '시험을 쉽게 내주시는데 수업 내용도 재미있고 유익해요'),
    ('세계 식문화의 이해',  '김민주', '사회과학', '전학년', '수업양은 많지만 얻어가는게 많은 수업'),
    ('SW중심의 미래사회', '인문/이과', '디지털 리터러시', '전학년', '온라인 강의로 진행하고 시험도 쉬운 수업'),
    ('다문화와 사회통합','김명희', '인성', '전학년', '온강과 대면을 섞어서 편하게 들을 수 있는 수업이에요'),
    ('서비스 마케팅', '조희영', '인문', '전학년', '많은 강의중 가장 수업다운 수업이에요'),
    ('인간과 곤충','김동건', '예술', '전학년', '아주 자세히 설명해주시고 수업도 재밌어요'),
]

cur.executemany("INSERT INTO restaurants (name, category, distance_min, tags, description) VALUES (?, ?, ?, ?, ?)", restaurants)
cur.executemany("INSERT INTO liberal_arts (name, professor, category, grade_level, review) VALUES (?, ?, ?, ? , ?)", liberal_arts)

# 커밋, 연결 종료
conn.commit()
conn.close()

print(f"Fin: {db_path}")

