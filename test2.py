import pandas as pd
import json 
df = pd.read_csv(r"F:\data\df_IssueCommentEvent_1000.csv")
# 2. 만약 payload 컬럼 내부의 값들을 다 분리해서 컬럼으로 만들고 싶다면:
payload_df = pd.DataFrame(df['payload'].tolist())
print(payload_df.head())
import ast
import pandas as pd

# 1. 안전하게 문자열을 진짜 파이썬 딕셔너리 객체로 강제 변환
df['payload_clean'] = df['payload'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# 2. 변환된 객체를 표 형태로 쫙 펼치기
refined_df = pd.DataFrame(df['payload_clean'].tolist())
refined_df2 = pd.DataFrame(refined_df['issue'].apply(lambda x: pd.Series(x) if isinstance(x, dict) else pd.Series()))
refined_df3 = pd.DataFrame(refined_df2['user'].apply(lambda x: pd.Series(x) if isinstance(x, dict) else pd.Series()))
print(refined_df2.columns)
# print(refined_df3.columns)
print(refined_df2.sample(10)[['assignee', 'type', 'active_lock_reason']])
# print(refined_df3.head()[['login','id','type']])