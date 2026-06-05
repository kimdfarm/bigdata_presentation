import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 깨짐 방지 설정 (Windows 기준, Mac은 'AppleGothic' 사용)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 파일 경로 설정
file_path = r'C:\Users\6-112\Desktop\pre\bigdata_presentation\data\split_csv\WatchEvent.csv'

if not os.path.exists(file_path):
    print(f"파일을 찾을 수 없습니다: {file_path}")
    exit()

# 2. CSV 데이터 로드
# 데이터가 클 수 있으므로 필요한 컬럼만 지정하거나 메모리 에러 시 수정을 위해 전처리
df = pd.read_csv(file_path)

repos = []
users = []

# 2. Payload 파싱
for idx, row in df.iterrows():
    try:
        payload_str = row['payload']
        if pd.isna(payload_str): continue
        payload = json.loads(payload_str)
        
        # 저장소 추출
        if 'repository' in payload and 'full_name' in payload['repository']:
            repos.append(payload['repository']['full_name'])
        elif 'repo' in df.columns:
            repos.append(row['repo'])
            
        # 유저 추출
        if 'sender' in payload and 'login' in payload['sender']:
            users.append(payload['sender']['login'])
        elif 'actor' in df.columns:
            users.append(row['actor'])
    except:
        continue

# 3. 전체 통계 데이터 계산 (텍스트용)
total_unique_repos = len(set(repos))  # 총 중복 없는 저장소 수
total_unique_users = len(set(users))  # 총 중복 없는 유저 수

# 상위 10개 추출
repo_counts = pd.Series(repos).value_counts().head(10).reset_index()
repo_counts.columns = ['Repository', 'Count']

user_counts = pd.Series(users).value_counts().head(10).reset_index()
user_counts.columns = ['User', 'Count']

# 4. 시각화 세팅
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# --- 왼쪽 그래프: 저장소 Top 10 ---
sns.barplot(x='Count', y='Repository', data=repo_counts, ax=axes[0], palette='viridis')
# 요청하신 텍스트 형태 적용 ("X개 저장소 중 상위 10개")
axes[0].set_title(f"★ 총 {total_unique_repos:,}개 저장소 중 가장 Star를 많이 받은 Top 10", 
                  fontsize=13, fontweight='bold', pad=15)
axes[0].set_xlabel('클릭(Star) 횟수')
axes[0].set_ylabel('저장소 이름')

# --- 오른쪽 그래프: 유저 Top 10 ---
sns.barplot(x='Count', y='User', data=user_counts, ax=axes[1], palette='magma')
# 요청하신 텍스트 형태 적용 ("X명의 관심 유저 중 가장 많이 클릭한 유저")
axes[1].set_title(f"👥 총 {total_unique_users:,}명의 관심 유저 중 가장 많이 누른 Top 10", 
                  fontsize=13, fontweight='bold', pad=15)
axes[1].set_xlabel('클릭(Star) 횟수')
axes[1].set_ylabel('유저 ID')

# --- 전체를 관통하는 메인 요약 문구 추가 (그래프 맨 위) ---
summary_text = f"전체 {total_unique_repos:,}개 저장소 중 상위 10개 리포지토리와, 관심 유저 {total_unique_users:,}명 중 헤비 클릭 유저의 분포 데이터입니다."
fig.suptitle(summary_text, fontsize=15, fontweight='bold', color='navy', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95]) # 상단 타이틀 공간 확보
plt.savefig('./watchdataMvP.png', dpi=300, bbox_inches='tight')

plt.show()