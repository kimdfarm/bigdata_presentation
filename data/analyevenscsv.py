import os
import pandas as pd

# 1. 'split_csv' 폴더 경로 설정 (환경에 맞게 수정하세요)
folder_path = r'C:\Users\6-112\Desktop\pre\bigdata_presentation\data\split_csv'

data_list = []
total_rows = 0

# 2. 폴더 내의 모든 CSV 파일 순회하며 개수 확인
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        
        # 파일이 비어있을 경우를 대비해 예외 처리
        try:
            # 전체 데이터를 다 로드하지 않고 행 개수만 빠르게 파악
            row_count = sum(1 for _ in open(file_path, encoding='utf-8')) - 1 # 헤더 제외
            if row_count < 0: row_count = 0
        except Exception:
            # encoding 에러 등이 날 경우 pandas로 읽기
            try:
                row_count = len(pd.read_csv(file_path))
            except:
                row_count = 0
        
        event_name = filename.replace('.csv', '')
        data_list.append({'Event': event_name, 'Count': row_count})
        total_rows += row_count

# 3. 데이터프레임 생성 및 비율(%) 계산
df = pd.DataFrame(data_list)

if total_rows > 0:
    df['Percentage (%)'] = (df['Count'] / total_rows) * 100
else:
    df['Percentage (%)'] = 0

# 개수 기준 내림차순 정렬
df = df.sort_values(by='Count', ascending=False).reset_index(drop=True)

# 4. 결과 출력
print(f"=== 총 이벤트 개수: {total_rows:,} 개 ===\n")
print(df.to_string(index=False, formatters={'Count': '{:,}'.format, 'Percentage (%)': '{:.2f}%'.format}))