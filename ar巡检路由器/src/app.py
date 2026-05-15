import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="paramiko.*")

from flask import Flask, render_template, Response
import queue, threading, os
from . import collector, inspect_tool

app = Flask(__name__)

def generate(q):
    try:
        q.put("开始采集路由器数据…")
        raw = collector.collect()
        if raw.startswith("采集失败"):
            q.put(raw)
            return
        
        q.put("采集完成，正在调用 AI 模型…")
        report = inspect_tool.ai_inspect(raw)
        if report.startswith("AI 分析失败"):
            q.put(report)
            return
        
        for line in report.splitlines():
            q.put(line)
        q.put("AI 巡检结束。")
    except Exception as e:
        q.put(f"处理异常: {str(e)}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stream")
def stream():
    def event():
        q = queue.Queue()
        thread = threading.Thread(target=generate, args=(q,), daemon=True)
        thread.start()
        
        timeout_count = 0
        max_timeout = 300  # 5分钟超时
        
        while True:
            try:
                msg = q.get(timeout=1)
                timeout_count = 0
                yield f"data: {msg}\n\n"
                if "AI 巡检结束" in msg or "失败" in msg:
                    break
            except queue.Empty:
                timeout_count += 1
                if timeout_count >= max_timeout:
                    yield "data: 处理超时，请重试\n\n"
                    break
    return Response(event(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)