# -*- coding: utf-8 -*-
"""
기능 : 코스피 + 코스닥 전체 상장종목의 이름·업종과 핵심 투자지표(PER·PBR·EPS·BPS·배당수익률)를
      수집해 all_stocks.csv로 저장합니다. NotebookLM에 CSV 파일로 그대로 업로드할 수 있습니다.
사용 : python fetch_all_stocks.py
      (전체 종목을 1개씩 조회하므로 시간이 오래 걸립니다. 약 15~25분 예상)
주의 : - pandas, lxml 필요 (pip install pandas lxml)
      - 네이버 금융 비공식 API를 종목마다 1회씩 호출합니다. 자주 실행하면 서버에 부담을
        주고 일시적으로 차단될 수 있으니, 학기당 1~2회 정도만 실행하는 것을 권장합니다.
      - fetch_prices.py(10분마다 자동 실행)와는 별개의 스크립트입니다. 이 스크립트는
        수동으로만 실행하세요(자동 스케줄에 넣지 않는 것을 권장).
"""
import json
import time
import urllib.request
import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0 (classroom research tool; educational use)"}


def fetch_listing():
    """기능 : KRX 기업공시채널(KIND)에서 코스피+코스닥 전체 상장법인 목록을 받아옴"""
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
    df = pd.read_html(url, header=0, encoding="euc-kr")[0]
    df = df[["회사명", "종목코드", "업종"]].copy()
    df["종목코드"] = df["종목코드"].astype(str).str.zfill(6)
    df = df.rename(columns={"회사명": "name", "종목코드": "code", "업종": "sector"})
    return df.reset_index(drop=True)


def _to_num(v):
    """기능 : '21.4배', '1,234', '3.2%' 같은 문자열을 숫자로 변환 (실패 시 None)"""
    if v in (None, "", "N/A", "-"):
        return None
    try:
        return float(str(v).replace(",", "").replace("%", "").replace("배", "").strip())
    except ValueError:
        return None


def fetch_metrics(code):
    """기능 : 종목 1개의 현재가·PER·PBR·EPS·BPS·배당수익률을 네이버 모바일 API에서 조회"""
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode("utf-8"))
    info = {row.get("key"): row.get("value") for row in data.get("totalInfos", [])}
    return {
        "price": _to_num(info.get("closePrice") or info.get("lastClosePrice")),
        "per": _to_num(info.get("per")),
        "eps": _to_num(info.get("eps")),
        "pbr": _to_num(info.get("pbr")),
        "bps": _to_num(info.get("bps")),
        "dividendYield": _to_num(info.get("dividendYieldRatio")),
    }


def main():
    print("코스피+코스닥 전체 상장법인 목록을 가져오는 중...")
    listing = fetch_listing()
    total = len(listing)
    print(f"전체 상장법인 {total}개 확인. 종목별 지표 수집을 시작합니다 (시간이 걸립니다)...")

    results = []
    fail_count = 0
    for i, row in listing.iterrows():
        code, name, sector = row["code"], row["name"], row["sector"]
        try:
            m = fetch_metrics(code)
            results.append({"code": code, "name": name, "sector": sector, **m})
        except Exception as e:
            fail_count += 1
            print(f"FAIL {code} {name}: {e}")
        if (i + 1) % 100 == 0:
            print(f"  진행 {i + 1}/{total}...")
        time.sleep(0.25)  # 기능 : 요청 간격을 두어 서버 부담 최소화

    out_df = pd.DataFrame(results)
    out_df.to_csv("all_stocks.csv", index=False, encoding="utf-8-sig")
    print(f"all_stocks.csv 저장 완료 (성공 {len(out_df)}종목 / 실패 {fail_count}종목)")


if __name__ == "__main__":
    main()
