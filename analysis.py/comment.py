import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import pipeline

# 한글 깨짐 방지 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 안전한 오픈소스 AI 모델 로드 (Hugging Face 토큰 필요 없음)
print("🤖 1. 오픈소스 질적 분석(감성) 모델 로딩 중...")
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

print("🌐 2. 오픈소스 다국어 언어 감지 모델 로딩 중... (Facebook Open Model)")
lang_detector = pipeline("text-classification", model="papluca/xlm-roberta-base-language-detection")

# 2. 데이터를 파싱하는 공통 함수 정의
def analyze_comment_event(file_path, sample_size=200):
    if not os.path.exists(file_path):
        print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    parsed_data = []
    
    filename = os.path.basename(file_path)
    print(f"📊 {filename} 분석 진행 중...")
    
    # 데이터가 너무 많으면 연산 시간이 걸리므로 head로 조절
    for idx, row in df.head(sample_size).iterrows(): 
        try:
            payload_str = row['payload']
            if pd.isna(payload_str): continue
            payload = json.loads(payload_str)
            
            if payload.get('action') == 'created':
                user_name = payload['sender']['login'] if 'sender' in payload else row.get('actor')
                comment_body = payload['comment']['body'] if 'comment' in payload else None
                
                if user_name and comment_body:
                    text_to_analyze = str(comment_body).strip()[:512]
                    if not text_to_analyze: continue
                    
                    # [AI 1: 질적 점수]
                    s_res = sentiment_analyzer(text_to_analyze)[0]
                    quality_score = s_res['score'] if s_res['label'] == 'POSITIVE' else (1 - s_res['score'])

                    l_res = lang_detector(text_to_analyze)[0]
                    raw_label = l_res['label'].lower()

                    if raw_label == 'ko':
                        detected_lang = 'KO'
                    elif raw_label == 'en':
                        detected_lang = 'EN'
                    else:
                        detected_lang = raw_label.upper()                           
                    
                    parsed_data.append({
                        'User': user_name, 
                        'AI_Quality_Score': quality_score,
                        'Language': detected_lang
                    })
        except:
            continue
            
    if not parsed_data:
        return pd.DataFrame()
        
    analysis_df = pd.DataFrame(parsed_data)
    
    # 최소 2회 이상 참여한 액티브 유저 대상 정제
    user_counts = analysis_df['User'].value_counts()
    active_users = user_counts[user_counts >= 2].index
    filtered_df = analysis_df[analysis_df['User'].isin(active_users)]
    
    if filtered_df.empty:
        return pd.DataFrame()
        
    # 유저별 평균 점수 및 최빈 언어 결합
    def get_main_lang(series):
        return series.mode().iloc[0] if not series.empty else 'UNKNOWN'
        
    user_stats = filtered_df.groupby('User').agg({
        'AI_Quality_Score': 'mean',
        'Language': get_main_lang
    }).reset_index()
    
    top_users = user_stats.sort_values(by='AI_Quality_Score', ascending=False).head(10).copy()
    top_users['User_with_Lang'] = top_users.apply(lambda r: f"{r['User']} ({r['Language']})", axis=1)
    return top_users


# 3. 각각의 이벤트 파일 분석 실행
issue_top_users = analyze_comment_event(r'C:\Users\6-112\Desktop\pre\bigdata_presentation\data\split_csv\IssueCommentEvent.csv', sample_size=200)
pr_top_users = analyze_comment_event(r'C:\Users\6-112\Desktop\pre\bigdata_presentation\data\split_csv\PullRequestReviewCommentEvent.csv', sample_size=200)


# 4. 2단 분할 그래프 시각화
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# --- 왼쪽: IssueCommentEvent 결과 ---
if not issue_top_users.empty:
    sns.barplot(x='AI_Quality_Score', y='User_with_Lang', data=issue_top_users, ax=axes[0], palette='magma')
    axes[0].set_title("💬 Issue 댓글 소통왕 Top 10 (일반 토론 및 질의응답)", fontsize=13, fontweight='bold', pad=15)
    axes[0].set_xlabel('AI 소통 질적 점수 (평균)')
    axes[0].set_ylabel('유저 ID (주 사용 언어)')
    axes[0].set_xlim(0, 1.1)
    for index, row in issue_top_users.reset_index(drop=True).iterrows():
        axes[0].text(row['AI_Quality_Score'] + 0.01, index, f"{row['AI_Quality_Score']*100:.1f}점", va='center', fontsize=9, fontweight='bold')
else:
    axes[0].text(0.5, 0.5, 'Issue 댓글 데이터가 부족합니다.', ha='center', va='center', fontsize=12)

# --- 오른쪽: PullRequestReviewCommentEvent 결과 ---
if not pr_top_users.empty:
    sns.barplot(x='AI_Quality_Score', y='User_with_Lang', data=pr_top_users, ax=axes[1], palette='viridis')
    axes[1].set_title("🔍 PR 리뷰 댓글 소통왕 Top 10 (코드 리뷰 및 피드백)", fontsize=13, fontweight='bold', pad=15)
    axes[1].set_xlabel('AI 소통 질적 점수 (평균)')
    axes[1].set_ylabel('유저 ID (주 사용 언어)')
    axes[1].set_xlim(0, 1.1)
    for index, row in pr_top_users.reset_index(drop=True).iterrows():
        axes[1].text(row['AI_Quality_Score'] + 0.01, index, f"{row['AI_Quality_Score']*100:.1f}점", va='center', fontsize=9, fontweight='bold')
else:
    axes[1].text(0.5, 0.5, 'PR 리뷰 댓글 데이터가 부족합니다.', ha='center', va='center', fontsize=12)

# 전체 메인 타이틀
fig.suptitle('🏆 이달의 채널별 소통왕: Issue vs PR 코드 리뷰 질적 비교분석', fontsize=16, fontweight='bold', color='darkgreen', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])

plt.savefig('./pullandissuecommentMvP.png', dpi=300, bbox_inches='tight')

plt.show()