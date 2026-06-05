import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 깨짐 방지 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
GROUPED_DIR = r"./data/grouped_csv"
CHARTS_DIR = r"./data/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

print("📈 [빅데이터 분석] 1일 데이터 전처리 및 시각화 가동 (오류 방어 모드)...")

# ==========================================
# [분석 1] 시간대별 전체 개발 활동량 분석
# ==========================================
print("💡 1. 시간대별 활동량 분석 중...")
all_hours = []

for file_name in os.listdir(GROUPED_DIR):
    if file_name.endswith(".csv"):
        file_path = os.path.join(GROUPED_DIR, file_name)
        try:
            # 💡 [핵심 수정] engine="pyarrow"를 제거하고,on_bad_lines='skip'을 추가하여 
            # 깨지거나 뒤틀린 줄(Row)이 있으면 에러를 내지 않고 자동으로 건너뛰도록 처리합니다.
            df = pd.read_csv(file_path, on_bad_lines='skip', usecols=["created_at"])
            
            if df.empty:
                continue
                
            # 전처리: 시간 특성 공학
            df["hour"] = pd.to_datetime(df["created_at"]).dt.hour
            all_hours.append(df["hour"])
        except Exception as e:
            print(f"⚠️ {file_name} 읽기 중 일부 행 건너뜀 또는 에러 발생: {e}")

if all_hours:
    # 모든 그룹의 시간 데이터를 하나로 결합
    total_hours_df = pd.DataFrame(pd.concat(all_hours, ignore_index=True), columns=["hour"])

    # 시각화 1: 라인 차트
    plt.figure(figsize=(10, 5))
    countdown = total_hours_df["hour"].value_counts().sort_index()
    sns.lineplot(x=countdown.index, y=countdown.values, marker="o", color="b", linewidth=2)
    plt.title("⏰ 24시간 개발자 활동 타임라인 분석", fontsize=14, fontweight="bold")
    plt.xlabel("시간 (Hour)", fontsize=11)
    plt.ylabel("이벤트 발생 건수", fontsize=11)
    plt.xticks(range(0, 24))
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig(os.path.join(CHARTS_DIR, "1_hourly_activity.png"), dpi=300)
    plt.close()
else:
    print("❌ 분석할 시간 데이터가 없습니다.")


# ==========================================
# [분석 2] 가장 핫한 상위 10개 레포지토리
# ==========================================
push_file = os.path.join(GROUPED_DIR, "Group5_Push.csv")
if os.path.exists(push_file):
    print("💡 2. 인기 레포지토리 트렌드 분석 중...")
    try:
        # 💡 여기도 bad lines 건너뛰기 적용
        df_push = pd.read_csv(push_file, on_bad_lines='skip', usecols=["repo"])
        top_repos = df_push["repo"].value_counts().head(10)
        
        if not top_repos.empty:
            plt.figure(figsize=(10, 6))
            sns.barplot(x=top_repos.values, y=top_repos.index, hue=top_repos.index, palette="viridis", legend=False)
            plt.title("🔥 가장 코드 커밋이 활발한 Top 10 레포지토리", fontsize=14, fontweight="bold")
            plt.xlabel("커밋(Push) 횟수", fontsize=11)
            plt.ylabel("레포지토리 이름", fontsize=11)
            plt.tight_layout()
            plt.savefig(os.path.join(CHARTS_DIR, "2_top_repositories.png"), dpi=300)
            plt.close()
    except Exception as e:
        print(f"⚠️ Push 파일 분석 중 오류 발생: {e}")


# ==========================================
# [분석 3] 이슈(Issues) 상태 및 소통 텍스트 길이 분석
# ==========================================
issues_file = os.path.join(GROUPED_DIR, "Group1_Issues.csv")
if os.path.exists(issues_file):
    print("💡 3. 이슈 소통 텍스트 마이닝 전처리 및 분석 중...")
    try:
        # 💡 마찬가지로 안정적인 로드 방식으로 변경
        df_issues = pd.read_csv(issues_file, on_bad_lines='skip', usecols=["state", "title"])
        df_issues = df_issues.dropna(subset=["title"])
        
        if not df_issues.empty:
            # 특성 공학: 글자 수 특성 생성
            df_issues["title_length"] = df_issues["title"].apply(lambda x: len(str(x)))
            
            plt.figure(figsize=(8, 5))
            sns.boxplot(x="state", y="title_length", data=df_issues, hue="state", palette="Set2", showfliers=False, legend=False)
            plt.title("📝 이슈 상태별 제목 글자 수 분포 비교", fontsize=14, fontweight="bold")
            plt.xlabel("이슈 상태 (State)", fontsize=11)
            plt.ylabel("제목 글자 수 (Title Length)", fontsize=11)
            plt.savefig(os.path.join(CHARTS_DIR, "3_issue_title_length.png"), dpi=300)
            plt.close()
    except Exception as e:
        print(f"⚠️ Issues 파일 분석 중 오류 발생: {e}")

print(f"\n🎉 빅데이터 시각화 리포트 생성 완료!")
print(f"📂 저장된 차트 폴더: {CHARTS_DIR}")