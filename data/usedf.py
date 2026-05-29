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

# 💡 GH Archive 표준 전체 컬럼 목록 (자세한 정보를 모두 담기 위해 정의)
fields = ["id", "type", "actor", "repo", "payload", "public", "created_at"]

print("🏎️ [전체 상세 정보 포함] 초고속 싱글 패스 분할 가동")
print("💡 모든 세부 데이터를 유지한 채 이벤트별로 쪼갭니다.\n")

file_size = os.path.getsize(file_path)
start_time = time.time()
line_count = 0

try:
    with open(file_path, "r", encoding="utf-8") as f:
        with tqdm(total=file_size, unit="B", unit_scale=True, desc="⚡ 데이터 분할 중") as pbar:
            
            for line in f:
                pbar.update(len(line.encode('utf-8')))
                line_count += 1
                
                if line_count % 1000000 == 0:
                    pbar.write(f"ℹ️ 현재 {line_count // 1000000}백만 줄(줄 번호: {line_count:,}) 처리 중...")
                
                try:
                    data = json.loads(line)
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
                    
                    # 💡 [핵심 가공] actor, repo, payload 같이 내부 구조가 복잡한 딕셔너리들은 
                    # 텍스트가 깨지거나 누락되지 않도록 그대로 다시 JSON 문자열로 변환해서 이쁘게 저장합니다.
                    actor_data = json.dumps(data.get("actor", {})) if isinstance(data.get("actor"), dict) else str(data.get("actor", ""))
                    repo_data = json.dumps(data.get("repo", {})) if isinstance(data.get("repo"), dict) else str(data.get("repo", ""))
                    payload_data = json.dumps(data.get("payload", {})) if isinstance(data.get("payload"), dict) else str(data.get("payload", ""))
                    
                    # 정의된 모든 상세 필드 순서대로 CSV에 한 행 추가
                    csv_writers[event_type].writerow([
                        data.get("id", ""),
                        event_type,
                        actor_data,      # 유저 상세 정보 포함
                        repo_data,       # 레포지토리 상세 정보 포함
                        payload_data,    # ⭐️ 이벤트별 모든 세부 내용 통째로 포함
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
print(f"\n🎉 초고속 상세 분할 완수! 총 {line_count:,}줄 처리 완료.")
print(f"⏱️ 총 소요 시간: {end_time - start_time:.2f}초")
print(f"📂 저장된 폴더: {output_dir}")