import os, paramiko, textwrap
from socket import timeout as SocketTimeout

ROUTER = {
    "host": os.getenv("ROUTER_HOST", "192.168.1.1"),
    "port": int(os.getenv("ROUTER_PORT", 22)),
    "username": os.getenv("ROUTER_USER", "python"),
    "password": os.getenv("ROUTER_PASS", "Huawei@123"),
}

CMDS = [
    "display version",
    "display cpu-usage",
    "display memory",
    "display interface brief",
    "display ip routing-table",
    "display logbuffer | include ERROR",
]

def collect():
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect(
            **ROUTER,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )
        out = []
        for cmd in CMDS:
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            out.append(f"---- {cmd} ----\n{stdout.read().decode(errors='ignore').strip()}")
        return "\n".join(out)
    except paramiko.AuthenticationException:
        return "采集失败: SSH 认证失败，请检查用户名和密码"
    except paramiko.SSHException as e:
        return f"采集失败: SSH 连接错误 - {str(e)}"
    except SocketTimeout:
        return "采集失败: 连接超时"
    except Exception as e:
        return f"采集失败: {str(e)}"
    finally:
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass

if __name__ == "__main__":
    print(collect())