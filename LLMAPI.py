

import os
from openai import OpenAI

# -------------------------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "API키 넣어주세요") 
MODEL = "gpt-4o-mini"  

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------------------------------------------------------------------------
CATEGORY_FOCUS = {
    "장학":    "신청 자격, 장학금 금액, 신청 기간(마감일)을 중심으로",
    "학사":    "대상 학생, 신청 기간, 처리 절차(방법)를 중심으로",
    "취업":    "모집 대상, 지원 방법, 마감일을 중심으로",
    "행사":    "행사 일시, 장소, 참가 대상 및 신청 방법을 중심으로",
    "프로그램": "프로그램 내용, 참가 대상, 신청 기간을 중심으로",
    "기타":    "핵심 내용과 학생이 바로 행동해야 할 사항을 중심으로",
}

SYSTEM_PROMPT = (
    "당신은 경희대학교 공지사항을 학생들에게 핵심만 간결하게 전달하는 도우미입니다. "
    "요약은 항상 3줄로 작성하고, 각 줄은 '- '으로 시작합니다. "
    "날짜·마감·금액·장소처럼 학생이 바로 확인해야 할 정보를 반드시 포함하세요."
)


# -------------------------------------------------------------------------------------------
def summarize_notice(notice: dict, category: str = "기타") -> str:
    
    title   = notice.get("title", "제목 없음")
    content = notice.get("content", "")
    content = content[:2000]  

    focus = CATEGORY_FOCUS.get(category, CATEGORY_FOCUS["기타"])

    user_prompt = f"""다음 공지사항을 {focus} 3줄로 요약해 주세요.

[카테고리] {category}
[제목] {title}
[내용]
{content}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[summarizer] 요약 실패 - {title[:30]}... / 오류: {e}")
        return None


def summarize_batch(notices: list[dict]) -> list[dict]:
    
    results = []
    total = len(notices)

    for i, notice in enumerate(notices, 1):
        category = notice.get("category", "기타")
        title    = notice.get("title", "")[:40]
        print(f"[{i}/{total}] 요약 중: [{category}] {title}...")

        summary = summarize_notice(notice, category=category)
        results.append({**notice, "summary": summary})

    return results


# -------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import csv

    def _guess_category(title: str) -> str:
        if any(k in title for k in ["장학", "장학금"]):        return "장학"
        if any(k in title for k in ["수강", "학사", "재입학"]): return "학사"
        if any(k in title for k in ["취업", "인턴", "채용"]):  return "취업"
        if any(k in title for k in ["챌린지", "해커톤", "대회", "행사"]): return "행사"
        if any(k in title for k in ["프로그램", "교육"]):       return "프로그램"
        return "기타"

    csv_path = "notices.csv"
    if not os.path.exists(csv_path):
        print(f"테스트용 CSV 없음: {csv_path}")
        exit()

    with open(csv_path, encoding="utf-8-sig") as f:
        all_notices = list(csv.DictReader(f))

    seen_cats = set()
    samples = []
    for n in all_notices:
        cat = _guess_category(n["title"])
        if cat not in seen_cats:
            n["category"] = cat
            samples.append(n)
            seen_cats.add(cat)
        if len(seen_cats) == len(CATEGORY_FOCUS):
            break

    print("=" * 60)
    print("카테고리별 요약 테스트")
    print("=" * 60)

    for notice in samples:
        cat   = notice["category"]
        title = notice["title"]
        date  = notice.get("date", "")
        print(f"\n[{cat}] {title}")
        print(f"날짜: {date}")
        summary = summarize_notice(notice, category=cat)
        if summary:
            print(f"요약:\n{summary}")
        print("-" * 60)
