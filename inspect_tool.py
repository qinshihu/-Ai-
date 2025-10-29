import os
import time
import requests
import json
import textwrap

OLLAMA_URL = "http://172.17.0.1:11434/api/generate"
TIMEOUT = 600

def rule_based_inspect(raw: str) -> str:
    report = []
    report.append("### 基础巡检报告（AI超时降级）")
    if "display version" in raw:
        model_line = next((line for line in raw.split('\n') if "VRP (R) software" in line), "")
        report.append(f"- 设备型号：{model_line.split(',')[0].strip() if model_line else '未知'}")
        version_line = next((line for line in raw.split('\n') if "Version" in line), "")
        report.append(f"- 软件版本：{version_line.split('Version')[1].strip() if version_line else '未知'}")
    if "display cpu-usage" in raw:
        cpu_lines = [line for line in raw.split('\n') if "CPU utilization" in line]
        cpu_usage = cpu_lines[0].split('%')[0].split()[-1] if cpu_lines and '%' in cpu_lines[0] else "未知"
        report.append(f"- {'⚠️ CPU使用率过高' if (cpu_usage.isdigit() and int(cpu_usage) > 90) else '✅ CPU使用率正常'}：{cpu_usage}%")
    if "display memory-usage" in raw:
        mem_lines = [line for line in raw.split('\n') if "Memory utilization" in line]
        mem_usage = mem_lines[0].split('%')[0].split()[-1] if mem_lines and '%' in mem_lines[0] else "未知"
        report.append(f"- {'⚠️ 内存使用率过高' if (mem_usage.isdigit() and int(mem_usage) > 85) else '✅ 内存使用率正常'}：{mem_usage}%")
    if "display interface brief" in raw:
        down_count = raw.lower().count("down")
        report.append(f"- {'⚠️ 发现' if down_count > 0 else '✅ 所有'}接口状态{'异常' if down_count > 0 else '正常'}：{down_count}个接口DOWN" if down_count > 0 else "")
    if "display logbuffer | include ERROR" in raw:
        error_count = raw.count("ERROR")
        report.append(f"- {'⚠️ 发现' if error_count > 0 else '✅ 无'}错误日志：{error_count}条" if error_count > 0 else "")
    return "\n".join(report)

def ai_inspect(raw: str) -> str:
    if not raw.strip():
        return "❌ 错误：未获取到路由器数据，无法进行AI分析"
    
    prompt = textwrap.dedent(f"""
    你是资深网络运维专家，需快速分析路由器巡检数据并输出报告。请严格按照以下结构回答：
    【整体健康评分】0-100分
    【风险/异常】逐条列出
    【优化建议】逐条给出
    【关键指标汇总】表格形式

    原始数据：
    {raw}
    """).strip()
    
    payload = {
        "model": "deepseek-r1:7b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 2048,
            "num_ctx": 4096
        }
    }
    
    try:
        start_time = time.time()
        rsp = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        rsp.raise_for_status()
        response_data = rsp.json()
        if "response" in response_data and response_data["response"].strip():
            elapsed = int(time.time() - start_time)
            return f"{response_data['response'].strip()}\n\n（AI分析耗时：{elapsed}秒）"
        else:
            return "❌ AI模型返回空结果"
    except requests.exceptions.Timeout:
        fallback_report = rule_based_inspect(raw)
        return f"⚠️ AI分析超时（已等待{TIMEOUT}秒），以下为基础巡检报告：\n{fallback_report}"
    except requests.exceptions.ConnectionError:
        return f"❌ 无法连接到Ollama服务（{OLLAMA_URL}），请检查服务是否运行"
    except Exception as e:
        return f"❌ AI调用异常：{str(e)}"
