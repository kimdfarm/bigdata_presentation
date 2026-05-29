import json
import pandas as pd
import time
import testUse 
start_time = time.time()
# 정제된 대용량 파일 경로
# 절대 경로로 지정 (가장 확실하게 파일 위치를 지정하는 방법)
file_path = r"C:\Users\6-112\Desktop\bigdata_presentation\data\split_csv\CommitCommentEvent.csv"
df = pd.read_csv(file_path, lines=True)
# 2. 데이터 확인
print("--- 데이터 기본 정보 ---")
print(df.info())

print("\n--- 샘플 CSV 파일로 저장 완료 ---")
end_time = time.time()
print(f"소요 시간: {end_time - start_time} 초")