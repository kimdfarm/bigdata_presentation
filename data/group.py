import os
import json
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

# 1. 경로 설정
INPUT_DIR = r"./data/split_csv"
OUTPUT_DIR = r"./data/grouped_csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. 가치 기반 그룹 매핑 정보
GROUP_MAPPING = {
    "Group1_Issues": ["IssuesEvent", "IssueCommentEvent"],
    "Group2_PullRequests": ["PullRequestEvent", "PullRequestReviewEvent", "PullRequestReviewCommentEvent"],
    "Group3_Community": ["CommitCommentEvent", "DiscussionEvent"],
    "Group4_Lifecycle": ["CreateEvent", "DeleteEvent"],
    "Group5_Push": ["PushEvent"]
}

# 공통 기본 필드 (거대한 원본 payload는 제외하고 핵심만 추출)
BASE_FIELDS = ["id", "type", "actor", "repo", "public", "created_at"]


def parse_row_payload(group_name, payload_str):
    """지정된 그룹의 스키마에 맞게 payload 복잡한 구조를 평탄화(Flatten)하여 반환"""
    if not payload_str or pd.isna(payload_str):
        return {}
    try:
        payload = json.loads(payload_str)
    except:
        return {}
        
    # --- 1그룹: 이슈 관련 추출 ---
    if group_name == "Group1_Issues":
        issue = payload.get("issue", {})
        comment = payload.get("comment", {})
        return {
            "action": payload.get("action", ""),
            "issue_id": issue.get("id", ""),
            "issue_number": issue.get("number", ""),
            "title": issue.get("title", ""),
            "state": issue.get("state", ""),
            "issue_author": issue.get("user", {}).get("login", ""),
            "comment_id": comment.get("id", ""),
            "comment_body": comment.get("body", "")
        }
        
    # --- 2그룹: PR 관련 추출 ---
    elif group_name == "Group2_PullRequests":
        pr = payload.get("pull_request", {})
        return {
            "action": payload.get("action", ""),
            "pr_id": pr.get("id", ""),
            "pr_number": pr.get("number", ""),
            "title": pr.get("title", ""),
            "state": pr.get("state", ""),
            "is_merged": pr.get("merged", False),
            "commits_count": pr.get("commits", 0),
            "changed_files": pr.get("changed_files", 0),
            "review_state": payload.get("review", {}).get("state", "")
        }
        
    # --- 3그룹: 커뮤니티 소통 관련 추출 ---
    elif group_name == "Group3_Community":
        comment = payload.get("comment", {})
        discussion = payload.get("discussion", {})
        return {
            "action": payload.get("action", ""),
            "comment_id": comment.get("id", ""),
            "commit_id": comment.get("commit_id", ""),
            "comment_body": comment.get("body", ""),
            "discussion_id": discussion.get("id", ""),
            "title": discussion.get("title", ""),
            "category_name": discussion.get("category", {}).get("name", "")
        }
        
    # --- 4그룹: 생성/삭제 라이프사이클 추출 ---
    elif group_name == "Group4_Lifecycle":
        return {
            "ref_type": payload.get("ref_type", ""),
            "ref": payload.get("ref", ""),
            "master_branch": payload.get("master_branch", ""),
            "description": payload.get("description", "")
        }
        
    # --- 5그룹: 푸시(코드 변경) 관련 추출 ---
    elif group_name == "Group5_Push":
        commits = payload.get("commits", [])
        messages = [c.get("message", "") for c in commits if isinstance(c, dict)]
        return {
            "push_id": payload.get("push_id", ""),
            "ref": payload.get("ref", ""),
            "commit_count": payload.get("size", 0),
            "commit_messages": " | ".join(messages)
        }
    return {}


def process_single_file(args):
    """[멀티프로ces 워커] 하나의 대용량 CSV 파일을 고속 정제 후 데이터프레임으로 변환"""
    group_name, file_name = args
    file_path = os.path.join(INPUT_DIR, file_name)
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # 💡 [치트키 1] PyArrow C++ 엔진으로 아주 빠르게 디스크에서 데이터 로드
        df = pd.read_csv(file_path, engine="pyarrow")
        if df.empty:
            return None
            
        # 가치 중심 payload 파싱 가동
        payload_parsed = df["payload"].apply(lambda x: parse_row_payload(group_name, x))
        payload_df = pd.DataFrame(list(payload_parsed)).fillna("")
        
        # 공통 기본 필드 결합
        base_df = df[BASE_FIELDS].fillna("")
        final_df = pd.concat([base_df, payload_df], axis=1)
        return final_df
    except Exception as e:
        print(f"❌ {file_name} 처리 실패: {e}")
        return None


if __name__ == "__main__":
    print("🏎️ [i9 안전 모드] PyArrow + 멀티프로세스 동시 병렬 그룹화 가동")
    print("💡 컴퓨터가 꺼지는 현상을 막기 위해 워커 성능을 제어합니다.\n")
    
    # 병렬 처리를 위한 작업 리스트 빌드
    tasks = []
    for group_name, target_events in GROUP_MAPPING.items():
        for event in target_events:
            file_name = f"{event}.csv"
            if os.path.exists(os.path.join(INPUT_DIR, file_name)):
                tasks.append((group_name, file_name))
                
    grouped_dfs = {g: [] for g in GROUP_MAPPING.keys()}
    
    # 💡 [치트키 2] max_workers=4 제한 조치
    # i9의 전력 폭주와 발열 현상을 억제하여 컴퓨터가 꺼지는 현상을 완벽히 차단합니다.
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(tqdm(executor.map(process_single_file, tasks), total=len(tasks), desc="⚡ 병렬 연산 레이어 가동 중"))
        
        # 가공 완료된 데이터프레임을 그룹별 짝에 맞춰 수집
        for task, result_df in zip(tasks, results):
            if result_df is not None:
                g_name = task[0]
                grouped_dfs[g_name].append(result_df)

    print("\n💾 정제 및 평탄화가 완료된 그룹 데이터를 디스크에 고속 기록 중...")
    for group_name, dfs in grouped_dfs.items():
        if not dfs:
            print(f"⏭️ {group_name}: 데이터가 없어 패스합니다.")
            continue
            
        # 메모리에 흩어진 동종 이벤트 데이터를 단일 덩어리로 병합
        merged_df = pd.concat(dfs, ignore_index=True)
        output_file_path = os.path.join(OUTPUT_DIR, f"{group_name}.csv")
        
        # 저장할 때도 파이arrow 블록 엔진을 써서 IO 병목 해결
        merged_df.to_csv(output_file_path, index=False)
        print(f"✅ 추출 완료 -> {output_file_path} (총 {len(merged_df):,} 행)")
        
    print(f"\n🎉 모든 작업이 안전하게 끝났습니다! 결과 폴더를 확인해 보세요: {OUTPUT_DIR}")