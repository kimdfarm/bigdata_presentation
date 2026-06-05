import os
import json
import csv
import time
from tqdm import tqdm

# 상대 경로 지정
file_path = r"./data/df_2026_05.json"
output_dir = r"./data/split_csv"

os.makedirs(output_dir, exist_ok=True)

file_handlers = {}
csv_writers = {}

# 💡 GH Archive 표준 전체 컬럼 목록
fields = ["id", "type", "actor", "repo", "payload", "public", "created_at"]

# 🔥 중복 검사용 고유 ID 저장소 (Set)
seen_ids = set()

print("🏎️ [전체 상세 정보 포함 + 중복 제거] 초고속 싱글 패스 분할 가동")
print("💡 중복된 이벤트 ID를 자동으로 걸러내며 고유한 데이터만 분할합니다.\n")

file_size = os.path.getsize(file_path)
start_time = time.time()
line_count = 0
duplicate_count = 0  # 중복 제거된 카운트 추적

try:
    with open(file_path, "r", encoding="utf-8") as f:
        with tqdm(total=file_size, unit="B", unit_scale=True, desc="⚡ 데이터 정제 및 분할 중") as pbar:
            
            for line in f:
                pbar.update(len(line.encode('utf-8')))
                line_count += 1
                
                if line_count % 1000000 == 0:
                    pbar.write(f"ℹ️ 현재 {line_count // 1000000}백만 줄(줄 번호: {line_count:,}) 처리 중... (중복 제거: {duplicate_count:,}건)")
                
                try:
                    data = json.loads(line)
                    
                    # 1. 이벤트 고유 ID 가져오기 및 중복 검사
                    event_id = data.get("id")
                    if not event_id:
                        continue
                    
                    # 🔥 [핵심] 이미 본 ID라면 중복이므로 건너뛰기
                    if event_id in seen_ids:
                        duplicate_count += 1
                        continue
                        
                    # 새로운 ID라면 기록에 추가
                    seen_ids.add(event_id)
                    
                    # 2. 이벤트 타입 확인
                    event_type = data.get("type")
                    if not event_type:
                        continue
                    
                    # 새로운 이벤트 타입 등장 시 파일 오픈
                    if event_type not in csv_writers:
                        safe_name = "".join(c for c in event_type if c.isalnum() or c in ('_', '-'))
                        csv_file_path = os.path.join(output_dir, f"{safe_name}.csv")
                        
                        file_handlers[event_type] = open(
                            csv_file_path, "w", encoding="utf-8", newline="", buffering=1024*1024
                        )
                        writer = csv.writer(file_handlers[event_type])
                        writer.writerow(fields)  # 전체 컬럼 헤더 작성
                        csv_writers[event_type] = writer
                    
                    # 💡 내부 구조가 복잡한 딕셔너리들은 깨지지 않게 JSON 문자열로 유지
                    actor_data = json.dumps(data.get("actor", {})) if isinstance(data.get("actor"), dict) else str(data.get("actor", ""))
                    repo_data = json.dumps(data.get("repo", {})) if isinstance(data.get("repo"), dict) else str(data.get("repo", ""))
                    payload_data = json.dumps(data.get("payload", {})) if isinstance(data.get("payload"), dict) else str(data.get("payload", ""))
                    
                    # 정의된 모든 상세 필드 순서대로 CSV에 한 행 추가
                    csv_writers[event_type].writerow([
                        event_id,
                        event_type,
                        actor_data,      # 유저 상세 정보 포함
                        repo_data,       # 레포지토리 상세 정보 포함
                        payload_data,    # 이벤트별 모든 세부 내용 통째로 포함
                        data.get("public", ""),
                        data.get("created_at", "") # 생성 시간 포함
                    ])
                    
                except json.JSONDecodeError:
                    continue

finally:
    print("\n⚙️ 오픈된 파일 핸들러 안전하게 닫는 중...")
    for handler in file_handlers.values():
        handler.close()

end_time = time.time()
print(f"\n🎉 초고속 상세 분할 및 중복 제거 완수!")
print(f"📊 총 읽은 줄 수: {line_count:,} 줄")
print(f"✨ 저장된 고유 데이터: {len(seen_ids):,} 건")
print(f"🗑️ 제거된 중복 데이터: {duplicate_count:,} 건")
print(f"⏱️ 총 소요 시간: {end_time - start_time:.2f}초")
print(f"📂 저장된 폴더: {output_dir}")