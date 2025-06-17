import json

def create_html_viewer():
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>JSONL構造ビューア</title>
    <style>
        body { font-family: monospace; margin: 20px; }
        .line-header { background: #f0f0f0; padding: 10px; margin: 10px 0; }
        .json-content { background: #f8f8f8; padding: 15px; border-left: 3px solid #007acc; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>JSONLファイル構造ビューア</h1>
"""
    
    with open('metric.jsonl','r') as f:
        lines = f.readlines()
    
    html_content += f"<p>総行数: {len(lines)}</p>"
    
    for i in range(min(3, len(lines))):
        if lines[i].strip():
            html_content += f'<div class="line-header">--- 行 {i+1} ---</div>'
            try:
                data = json.loads(lines[i].strip())
                formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                html_content += f'<div class="json-content"><pre>{formatted_json}</pre></div>'
            except json.JSONDecodeError as e:
                html_content += f'<div class="json-content">JSON解析エラー: {e}</div>'
    
    html_content += "</body></html>"
    
    # ← 重要！HTMLファイルに保存
    with open('jsonl_viewer.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("HTMLファイルが作成されました: jsonl_viewer.html")

#テスト用の関数を定義
if __name__ == "__main__":
    create_html_viewer()