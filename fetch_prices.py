# -*- coding: utf-8 -*-
"""
기능 : 네이버 금융 비공식 API에서 국내 주식 시세를 받아 prices.json으로 저장
사용 : python fetch_prices.py  (GitHub Actions가 장중 주기적으로 자동 실행)
주의 : 표준 라이브러리만 사용 (별도 설치 불필요)
"""
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta

# 기능 : 학생들이 거래할 종목 목록 정의 (코드, 시장 구분)
# 참고 : 기업가치 탐험대(invest_learning_app.html)의 실시간 주가 연동을 위해
#        해당 프로그램에 등장하는 20개 기업이 모두 포함되도록 구성했습니다.
STOCKS = [
    ("005930", "KOSPI"),   # 삼성전자
    ("000660", "KOSPI"),   # SK하이닉스
    ("373220", "KOSPI"),   # LG에너지솔루션
    ("006400", "KOSPI"),   # 삼성SDI
    ("207940", "KOSPI"),   # 삼성바이오로직스
    ("068270", "KOSPI"),   # 셀트리온
    ("005380", "KOSPI"),   # 현대차
    ("000270", "KOSPI"),   # 기아
    ("035420", "KOSPI"),   # NAVER
    ("035720", "KOSPI"),   # 카카오
    ("005490", "KOSPI"),   # POSCO홀딩스
    ("004020", "KOSPI"),   # 현대제철
    ("105560", "KOSPI"),   # KB금융
    ("055550", "KOSPI"),   # 신한지주
    ("352820", "KOSPI"),   # 하이브
    ("329180", "KOSPI"),   # HD현대중공업
    ("042660", "KOSPI"),   # 한화오션
    ("017670", "KOSPI"),   # SK텔레콤
    ("030200", "KOSPI"),   # KT
    ("035900", "KOSDAQ"),  # JYP Ent.
]

HEADERS = {"User-Agent": "Mozilla/5.0 (classroom stock simulator; educational use)"}


def fetch_one(code):
    """기능 : 종목 1개의 현재가/등락률을 네이버 모바일 API에서 조회"""
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode("utf-8"))
    price = int(str(data["closePrice"]).replace(",", ""))
    rate = float(str(data.get("fluctuationsRatio", "0")).replace(",", ""))
    # 기능 : 하락이면 등락률 부호를 음수로 보정
    direction = str(data.get("compareToPreviousClosePrice", "0")).replace(",", "")
    if direction.startswith("-") and rate > 0:
        rate = -rate
    name = data.get("stockName", code)
    return name, price, rate


def main():
    """기능 : 전체 종목 시세를 수집해 prices.json으로 기록"""
    results = []
    for code, market in STOCKS:
        try:
            name, price, rate = fetch_one(code)
            results.append({
                "code": code, "name": name, "market": market,
                "price": price, "changeRate": rate,
            })
            print(f"OK  {code} {name} {price:,} ({rate:+.2f}%)")
        except Exception as e:
            print(f"FAIL {code}: {e}")
        time.sleep(0.3)  # 기능 : 요청 간격을 두어 서버 부담 최소화

    if not results:
        # 기능 : 전부 실패하면 기존 prices.json을 유지 (덮어쓰지 않음)
        print("모든 종목 조회 실패. prices.json을 갱신하지 않습니다.")
        raise SystemExit(1)

    kst = timezone(timedelta(hours=9))
    output = {
        "updated": datetime.now(kst).isoformat(timespec="seconds"),
        "source": "naver-finance (unofficial, delayed)",
        "stocks": results,
    }
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"prices.json 저장 완료 ({len(results)}종목)")


if __name__ == "__main__":
    main()
