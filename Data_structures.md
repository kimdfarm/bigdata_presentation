# data 
- "id": event.get("id"),
- "type": event.get("type"),
- "actor": event.get("actor"), 
- "repo": event.get("repo"), 
- "created_at": event.get("created_at"),
- "payload"

## IssueCommentEvent
IssueCommentEvent
- actor
- - ['id', 'login', 'display_login', 'gravatar_id', 'url', 'avatar_url']
- - - usecolumns : login
- repo
- - ['id', 'name', 'url']
- - - usecolumns : name
- payload
- - ['action', 'issue', 'comment']
- - - issue
- - - - ['url', 'repository_url', 'labels_url', 'comments_url', 'events_url',
       'html_url', 'id', 'node_id', 'number', 'title', 'user', 'labels',
       'state', 'locked', 'assignees', 'milestone', 'comments', 'created_at',
       'updated_at', 'closed_at', 'assignee', 'type', 'active_lock_reason',
       'draft', 'pull_request', 'body', 'reactions', 'timeline_url',
       'performed_via_github_app', 'state_reason', 'sub_issues_summary',
       'issue_dependencies_summary', 'pinned_comment', 'issue_field_values',
       'parent_issue_url']
- - - - - ['title','body']
- - - - - locked는 일단 안넣어봄
