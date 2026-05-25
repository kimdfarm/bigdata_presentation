import requests
import gzip
import json
import os

# 1. 수집 및 필터링 설정
YEAR = "2026"
MONTH = "05"
DAYS_IN_MONTH = 31  # 5월은 31일까지 있습니다.

# 가치 있는 핵심 이벤트 유형만 정의 (나머지는 버림)
VALUABLE_EVENTS = {
    'WatchEvent',         # Star (트렌드 분석 핵심)
    'ForkEvent',          # 포크 (확산도 분석)
    'PullRequestEvent',   # PR (코드 기여도)
    'IssueCommentEvent',  # 이슈 댓글 (개발자 자연어 대화 데이터)
    'PushEvent'           # 푸시 (개발 활성도)
}

output_file_path = f"data/refined_ghdata_{YEAR}_{MONTH}.json"

print(f"🚀 {YEAR}년 {MONTH}월 GH Archive 데이터 정제 시작...")

# 결과를 저장할 파일 열기
with open(output_file_path, "w", encoding="utf-8") as out_f:
    
    # 2. 1일부터 31일까지 반복
    for day in range(1, DAYS_IN_MONTH + 1):
        day_str = f"{day:02d}"
        
        # 3. 0시부터 23시까지 반복
        for hour in range(24):
            hour_str = f"{hour:02d}"
            
            # GH Archive 타겟 URL 생성
            url = f"https://data.gharchive.org/{YEAR}-{MONTH}-{day_str}-{hour}.json.gz"
            print(f"📦 다운로드 및 분석 중: {YEAR}-{MONTH}-{day_str}-{hour_str}.json.gz")
            
            try:
                # 스트리밍 방식으로 파일 다운로드
                response = requests.get(url, stream=True, timeout=30)
                
                if response.status_code == 200:
                    # 다운로드와 동시에 메모리에서 gzip 압축 해제
                    with gzip.GzipFile(fileobj=response.raw) as f:
                        for line in f:
                            event = json.loads(line.decode('utf-8'))
                            
                            # [필터 1] 가치 없는 이벤트 유형은 패스
                            event_type = event.get('type')
                            if event_type not in VALUABLE_EVENTS:
                                continue
                                
                            # [필터 2] 봇(Bot)이 유발한 자동화 이벤트는 패스
                            actor_name = event.get('actor', {}).get('login', '').lower()
                            if 'bot' in actor_name or '[bot]' in actor_name:
                                continue
                            
                            # [필터 3] PR의 경우 가급적 머지(Merged)된 알짜배기만 남기거나 본문 활용
                            # 필요에 따라 payload 내부를 한 번 더 정제할 수 있습니다.
                            
                            # 정제된 핵심 데이터만 추출하여 딕셔너리 재구성 (용량 추가 다이어트)
                            refined_event = {
                                "id": event.get("id"),
                                "type": event_type,
                                "actor": event.get("actor", {}).get("login"),
                                "repo": event.get("repo", {}).get("name"),
                                "created_at": event.get("created_at"),
                                "payload": event.get("payload") # 상세 정보가 필요 없다면 이 부분을 제외하면 용량이 엄청나게 줄어듭니다.
                            }
                            
                            # 파일에 한 줄씩 JSON으로 저장 (JSON Lines 포맷)
                            out_f.write(json.dumps(refined_event, ensure_ascii=False) + "\n")
                            
                elif response.status_code == 404:
                    # 아직 생성되지 않은 미래의 시간이거나 없는 파일인 경우
                    print(f"⚠️ 파일을 찾을 수 없습니다 (404): {url}")
                else:
                    print(f"❌ 에러 발생 (상태코드 {response.status_code}): {url}")
                    
            except Exception as e:
                print(f"💥 네트워크 또는 파싱 에러 발생: {e}")
                continue

print(f"🎉 모든 정제가 완료되었습니다! 결과 파일: {output_file_path}")