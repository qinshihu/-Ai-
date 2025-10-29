import os
import paramiko
import time
import logging
from src.progress import progress_queue  # 导入正确的Queue对象

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('collector')

def collect():
    """执行设备命令采集数据，返回整理后的结果"""
    ssh = None
    shell = None
    try:
        # 从环境变量获取设备连接信息
        ssh_params = {
            "hostname": os.getenv("ROUTER_HOST", "192.168.31.199"),
            "port": int(os.getenv("ROUTER_PORT", 22)),
            "username": os.getenv("ROUTER_USER", "python"),
            "password": os.getenv("ROUTER_PASS", "Ai@#2323"),
            "look_for_keys": False,
            "allow_agent": False,
            "timeout": 15,
            "banner_timeout": 15
        }

        # 初始化SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 尝试SSH连接（最多3次重试）
        connect_success = False
        for attempt in range(3):
            try:
                # 使用put()方法发送消息到队列
                progress_queue.put(
                    f'{{"status": "collect", "message": "🔗 第 {attempt+1}/3 次尝试连接 {ssh_params["hostname"]}:{ssh_params["port"]}..."}}'
                )
                logger.info(f"第 {attempt+1}/3 次尝试连接 {ssh_params['hostname']}")
                
                ssh.connect(**ssh_params)
                connect_success = True
                progress_queue.put(
                    f'{{"status": "collect", "message": "✅ 成功连接到 {ssh_params["hostname"]}（用户名：{ssh_params["username"]}）"}}'
                )
                logger.info(f"成功连接到 {ssh_params['hostname']}")
                break
            
            except Exception as e:
                err_msg = f"连接失败：{str(e)}"
                progress_queue.put(
                    f'{{"status": "collect", "message": "⚠️ 第 {attempt+1}/3 次连接失败：{err_msg}"}}'
                )
                logger.error(f"第 {attempt+1} 次连接失败：{err_msg}")
                if attempt == 2:
                    raise Exception(f"SSH连接多次失败：{err_msg}")
                time.sleep(2)

        if not connect_success:
            raise Exception("未成功建立SSH连接")

        # 初始化交互式Shell
        shell = ssh.invoke_shell()
        time.sleep(1)
        # 清空初始输出
        while shell.recv_ready():
            shell.recv(65535)
        progress_queue.put('{"status": "collect", "message": "⚙️ 交互式Shell初始化完成，开始执行命令..."}')
        logger.info("交互式Shell初始化完成")

        # 定义需要执行的设备命令列表
        CMDS = [
            "display version",
            "display cpu-usage",
            "display memory-usage",
            "display interface brief",
            "display ip routing-table",
            "display logbuffer | include ERROR"
        ]
        
        # 存储命令执行结果
        device_data = []
        
        # 逐个执行命令
        for i, cmd in enumerate(CMDS):
            cmd_index = i + 1
            total_cmds = len(CMDS)
            
            progress_queue.put(
                f'{{"status": "collect", "message": "📝 执行命令 {cmd_index}/{total_cmds}：{cmd}"}}'
            )
            logger.info(f"执行命令 {cmd_index}/{total_cmds}：{cmd}")
            
            try:
                shell.send(f"{cmd}\n")
                time.sleep(1)
                
                # 接收命令输出（处理分页）
                result = ""
                start_time = time.time()
                # 单条命令超时控制（30秒）
                while time.time() - start_time < 30:
                    if shell.recv_ready():
                        part = shell.recv(65535).decode('utf-8', errors='ignore')
                        result += part
                        if "---- More ----" in part:
                            progress_queue.put(
                                f'{{"status": "collect", "message": "📄 命令 {cmd} 输出过长，加载下一页..."}}'
                            )
                            shell.send(" ")
                            time.sleep(0.5)
                    else:
                        time.sleep(0.3)
                        if time.time() - start_time > 2 and not shell.recv_ready():
                            break
                
                if time.time() - start_time >= 30:
                    raise Exception(f"命令执行超时（超过30秒）")
                
                # 清理输出
                cleaned_result = result.replace(cmd, "", 1).replace("---- More ----", "").strip()
                device_data.append(f"=== 命令 {cmd_index}/{total_cmds}：{cmd} ===\n{cleaned_result}")
                
                progress_queue.put(
                    f'{{"status": "collect", "message": "✅ 命令 {cmd_index}/{total_cmds} 执行完成（输出长度：{len(cleaned_result)}字符）"}}'
                )
                logger.info(f"命令 {cmd_index}/{total_cmds} 执行完成，输出长度：{len(cleaned_result)}字符")
            
            except Exception as e:
                err_msg = f"执行命令 {cmd} 失败：{str(e)}"
                progress_queue.put(f'{{"status": "collect", "message": "❌ {err_msg}"}}')
                logger.error(err_msg)
                raise Exception(err_msg)
            
            time.sleep(1)

        # 计算总数据长度并推送完成消息
        total_length = len("\n".join(device_data))
        progress_queue.put(f'{{"status": "collect", "message": "📊 所有{total_cmds}条命令执行完成，共采集数据约{total_length}字符"}}')
        logger.info(f"所有{total_cmds}条命令执行完成，总数据长度：{total_length}字符")
        
        return "\n\n".join(device_data)

    except Exception as e:
        logger.error(f"数据采集过程异常：{str(e)}")
        raise

    finally:
        if shell:
            try:
                shell.close()
                logger.info("交互式Shell已关闭")
            except Exception as e:
                logger.warning(f"关闭Shell失败：{str(e)}")
        if ssh:
            try:
                ssh.close()
                logger.info("SSH连接已关闭")
            except Exception as e:
                logger.warning(f"关闭SSH连接失败：{str(e)}")
