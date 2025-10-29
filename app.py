from flask import Flask, render_template, Response, request, jsonify
import time
import threading
import json
import logging
from queue import Empty
from src.progress import progress_queue
from src.collector import collect
from src.inspect_tool import ai_inspect

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
sse_logger = logging.getLogger('sse')
queue_logger = logging.getLogger('queue')

app = Flask(__name__)

# 全局变量：跟踪活跃的SSE连接数
active_sse_connections = 0
sse_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    global active_sse_connections
    
    def generate_progress():
        global active_sse_connections
        connection_id = id(threading.current_thread())
        sse_logger.info(f"SSE连接[{connection_id}]建立，等待进度消息...")
        
        # 增加活跃连接计数
        with sse_lock:
            active_sse_connections += 1
        
        try:
            # 发送连接成功消息
            yield 'data: {"status": "idle", "message": "✅ 实时进度已连接，点击按钮开始巡检"}\n\n'
            
            # 循环获取消息（移除request上下文依赖）
            while True:
                try:
                    # 非阻塞获取消息（超时0.5秒）
                    current_msg = progress_queue.get(timeout=0.5)
                    sse_logger.info(f"SSE连接[{connection_id}]推送消息：{current_msg}")
                    yield f'data: {current_msg}\n\n'
                    progress_queue.task_done()
                except Empty:
                    # 队列空时继续循环，不依赖request判断
                    continue
                except GeneratorExit:
                    # 捕获生成器退出事件（客户端断开连接）
                    sse_logger.info(f"SSE连接[{connection_id}]被客户端主动断开")
                    break
                except Exception as e:
                    sse_logger.error(f"SSE连接[{connection_id}]异常：{str(e)}")
                    break
                
                # 控制循环频率，避免CPU过高
                time.sleep(0.1)
        
        finally:
            # 减少活跃连接计数
            with sse_lock:
                active_sse_connections -= 1
            sse_logger.info(f"SSE连接[{connection_id}]关闭，当前活跃连接：{active_sse_connections}")
    
    # SSE响应配置
    response = Response(
        generate_progress(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache, no-store',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Timeout': '300'
        }
    )
    return response

@app.route('/start_inspection', methods=['POST'])
def start_inspection():
    # 检查是否有正在运行的巡检任务
    running = False
    temp_messages = []
    try:
        while not progress_queue.empty():
            msg = progress_queue.get_nowait()
            temp_messages.append(msg)
            try:
                msg_json = json.loads(msg)
                if msg_json.get("status") in ["start", "collect", "ai"]:
                    running = True
            except:
                pass
    except Exception as e:
        queue_logger.error(f"检查任务状态失败：{str(e)}")
    
    # 放回所有消息
    for msg in temp_messages:
        progress_queue.put(msg)
    
    if running:
        return jsonify({
            "status": "error",
            "message": "已有巡检在进行中，请等待完成"
        }), 400

    def run_full_inspection():
        try:
            progress_queue.put('{"status": "start", "message": "📋 巡检流程启动，正在初始化..."}')
            queue_logger.info("入队：巡检启动")
            
            device_data = collect()
            
            progress_queue.put('{"status": "ai", "message": "🤖 数据采集完成，正在调用AI分析..."}')
            queue_logger.info("入队：AI分析启动")
            
            ai_report = ai_inspect(device_data)
            progress_queue.put(f'{{"status": "done", "message": "✅ 巡检完成！\\n\\nAI巡检报告：\\n{ai_report}"}}')
            queue_logger.info("入队：巡检完成")
            
        except Exception as e:
            error_msg = f'{{"status": "error", "message": "❌ 巡检失败：{str(e)}"}}'
            progress_queue.put(error_msg)
            queue_logger.error(f"巡检异常：{str(e)}")
    
    inspection_thread = threading.Thread(target=run_full_inspection)
    inspection_thread.daemon = True
    inspection_thread.start()
    
    return jsonify({'status': 'success', 'msg': '巡检已启动，进度将实时更新'}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
