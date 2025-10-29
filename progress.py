# 正确定义线程安全的队列（使用queue.Queue）
from queue import Queue

# 初始化全局进度队列（多线程安全）
progress_queue = Queue()
