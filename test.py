import json
import pandas as pd
import time
import testUse 
start_time = time.time()
# 정제된 대용량 파일 경로
# 절대 경로로 지정 (가장 확실하게 파일 위치를 지정하는 방법)
file_path = r"C:\_proj\bigdata_presentation\data\df_2026_05.json"
df = pd.read_json(file_path, lines=True)
# 2. 데이터 확인
print("--- 데이터 기본 정보 ---")
print(df.info())

for event_type in testUse.value:
    output_path = f"F:\\data\\df_{event_type}_1000.csv"
    print(f"\n--- {event_type} ---")
    df1000 = df[df['type'] == event_type][:1000]
    df1000.to_csv(output_path, index=False, encoding='utf-8-sig')
    # df.to_csv(r"F:\data\df_csv.csv", index=False, encoding='utf-8-sig')
print("\n--- 샘플 CSV 파일로 저장 완료 ---")
end_time = time.time()
print(f"소요 시간: {end_time - start_time} 초")