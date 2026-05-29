import requests
import gzip
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 1. 설정
YEAR = "2026"
MONTH = "05"
DAYS_IN_MONTH = 31

output_file_path = f"data\\df_{YEAR}_{MONTH}.json"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
file_lock = threading.Lock()

# 💡 [핵심 조치 1] 속도 조절
# i9 성능이 아깝지만, 서버 차단을 피하려면 동시 요청을 8~12개 정도로 낮추는 것이 결국 가장 빠릅니다.
MAX_WORKERS = 8 

def create_retry_session():
    """네트워크 불안정 및 서버 차단을 극복하기 위한 스마트 재시도 세션 생성"""
    session = requests.Session()
    
    # 💡 [핵심 조치 2] 지수 백오프(Exponential Backoff) 설정
    # 500, 502, 503, 504 서버 에러 및 타임아웃 시 자동 재시도
    # backoff_factor=2 설정으로 인해 에러 발생 시 [2초, 4초, 8초...] 쉬었다가 재시도합니다.
    retries = Retry(
        total=5,  # 최대 5번 재시도
        backoff_factor=2, 
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    
    # 세션에 재시도 로직 적용
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

print(f"🚀 {YEAR}년 {MONTH}월 GH Archive 스마트 멀티스레드 정제 시작...")

def process_hour(day, hour):
    day_str = f"{day:02d}"
    hour_str = f"{hour:02d}"
    url = f"https://data.gharchive.org/{YEAR}-{MONTH}-{day_str}-{hour}.json.gz"
    
    # 스레드별 독립된 재시도 세션 사용
    session = create_retry_session()
    
    try:
        # 💡 연결 타임아웃은 15초, 읽기 타임아웃은 60초로 넉넉하게 설정
        response = session.get(url, stream=True, timeout=(1500, 6000))
        print("📦 ",day,"일 " ,hour,"시간 탐색 중")
        if response.status_code == 200:
            local_buffer = []
            with gzip.GzipFile(fileobj=response.raw) as f:
                for line in f:
                    event = json.loads(line.decode('utf-8'))
                    
                    # 봇 필터
                    actor_name = event.get('actor', {}).get('login', '').lower()
                    if 'bot' in actor_name or '[bot]' in actor_name:
                        continue
                    
                    refined_event = {
                        "id": event.get("id"),
                        "type": event.get("type"),
                        "actor": event.get("actor", {}).get("login"),
                        "repo": event.get("repo", {}).get("name"),
                        "created_at": event.get("created_at"),
                        "payload": event.get("payload")
                    }
                    local_buffer.append(json.dumps(refined_event, ensure_ascii=False) + "\n")
            
            if local_buffer:
                with file_lock:
                    with open(output_file_path, "a", encoding="utf-8") as out_f:
                        out_f.writelines(local_buffer)
            
            print(f"✅ 완료: {YEAR}-{MONTH}-{day_str}-{hour_str}.json.gz")
            
        elif response.status_code == 404:
            print(f"⚠️ 파일을 찾을 수 없습니다 (404): {url}")
        else:
            print(f"❌ 서버 응답 에러 (상태코드 {response.status_code}): {url}")
            
    except Exception as e:
        # 세션 재시도까지 모두 실패했을 때만 최종 에러 출력
        print(f"💥 최종 실패 [{day_str}일 {hour_str}시]: {e}")

# 2. 작업 리스트 생성 (예시로 1일치 설정)
tasks = []
for day in range(1, 29): 
    for hour in range(24):
        tasks.append((day, hour))

# 3. 멀티스레드 실행
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    executor.map(lambda p: process_hour(*p), tasks)

print(f"🎉 모든 정제가 완료되었습니다! 결과 파일: {output_file_path}")