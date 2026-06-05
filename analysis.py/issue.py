import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 깨짐 방지 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 파일 로드
file_path = r'C:\Users\6-112\Desktop\pre\bigdata_presentation\data\split_csv\IssuesEvent.csv'

if not os.path.exists(file_path):
    print(f"파일을 찾을 수 없습니다: {file_path}")
    exit()

df = pd.read_csv(file_path)

repos = []
opened_users = []  # 이슈를 '생성(opened)'한 유저만 담을 리스트
all_users = []     # 전체 이벤트 관련 유저

print("IssuesEvent Payload 파싱 및 필터링 중...")
for idx, row in df.iterrows():
    try:
        payload_str = row['payload']
        if pd.isna(payload_str): continue
        payload = json.loads(payload_str)
        
        # [저장소 정보 추출]
        repo_name = None
        if 'repository' in payload and 'full_name' in payload['repository']:
            repo_name = payload['repository']['full_name']
        elif 'repo' in df.columns:
            repo_name = row['repo']
            
        if repo_name:
            repos.append(repo_name)

        # [유저 정보 추출]
        # 이슈와 관련된 행위자(actor) 정보 추출
        user_name = None
        if 'sender' in payload and 'login' in payload['sender']:
            user_name = payload['sender']['login']
        elif 'actor' in df.columns:
            user_name = row['actor']
            
        if user_name:
            all_users.append(user_name)
            # action이 'opened'인 경우만 '이슈를 낸 사람'으로 분류
            if payload.get('action') == 'opened':
                opened_users.append(user_name)
                
    except (json.JSONDecodeError, TypeError, KeyError):
        continue

# 만약 payload에 action 정보가 없어서 opened_users가 비어있을 경우를 대비한 백업
if len(opened_users) == 0:
    opened_users = all_users

# 2. 전체 통계 데이터 계산 (텍스트용)
total_unique_repos = len(set(repos))       # 총 중복 없는 저장소 수
total_unique_creators = len(set(opened_users)) # 총 중복 없는 이슈 생성자 수

# 상위 10개 추출
repo_counts = pd.Series(repos).value_counts().head(10).reset_index()
repo_counts.columns = ['Repository', 'Count']

user_counts = pd.Series(opened_users).value_counts().head(10).reset_index()
user_counts.columns = ['User', 'Count']

# 3. 시각화 세팅
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# --- 왼쪽 그래프: 이슈 발생 저장소 Top 10 ---
sns.barplot(x='Count', y='Repository', data=repo_counts, ax=axes[0], palette='cubehelix')
axes[0].set_title(f"🔥 총 {total_unique_repos:,}개 저장소 중 이슈가 가장 많이 터진 Top 10", 
                  fontsize=13, fontweight='bold', pad=15)
axes[0].set_xlabel('이슈 발생 건수')
axes[0].set_ylabel('저장소 이름')

# --- 오른쪽 그래프: 이슈 생성 유저 Top 10 ---
sns.barplot(x='Count', y='User', data=user_counts, ax=axes[1], palette='flare')
axes[1].set_title(f"✍️ 총 {total_unique_creators:,}명의 유저 중 이슈를 가장 많이 낸 Top 10", 
                  fontsize=13, fontweight='bold', pad=15)
axes[1].set_xlabel('이슈 생성(Opened) 횟수')
axes[1].set_ylabel('유저 ID')

# --- 상단 메인 요약 문구 ---
summary_text = f"전체 {total_unique_repos:,}개 저장소 중 활발한 Top 10 리포지토리와, 이슈를 제기한 {total_unique_creators:,}명 중 핵심 기여 유저의 분포 데이터입니다."
fig.suptitle(summary_text, fontsize=15, fontweight='bold', color='darkred', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('./issueopenMvP.png', dpi=300, bbox_inches='tight')
plt.show()