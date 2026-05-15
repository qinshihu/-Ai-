import os, requests, json, textwrap

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")

def ai_inspect(raw: str) -> str:
    prompt = f"""你是资深网络运维专家，请根据下方原始巡检数据，给出：
1. 整体健康评分（0-100）
2. 存在的风险或异常（逐条）
3. 优化建议（逐条）
4. 用表格形式汇总关键指标

原始数据：
{raw}"""
    payload = {
        "model": "deepseek-r1:7b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 1024},
    }
    try:
        rsp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        rsp.raise_for_status()
        data = rsp.json()
        return data.get("response", "AI 分析失败: 响应中没有结果")
    except requests.exceptions.RequestException as e:
        return f"AI 分析失败: {str(e)}"
    except json.JSONDecodeError:
        return "AI 分析失败: 响应解析失败"
    except KeyError:
        return "AI 分析失败: 响应格式不正确"