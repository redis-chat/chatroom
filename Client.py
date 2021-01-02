import redis
import threading
import time
import queue
from sys import exit

# 连接至Redis服务器，客户端需要配置主机IP和端口。
# 例如： conn = redis.Redis(host='xxx,xxx,xxx,xxx', port=6379, db=0)
conn = redis.Redis()

# 用户昵称
name = ''

# 消息记录缓冲池，每pull一次消息，就清空一次。
mes_queue = queue.Queue()

def _help():
    help_doc = '''pull 拉取消息\ndownline 下线\nusers 拉取当前在线用户\npub <message> 向大厅发布消息\nto <someone> 向某人发送消息'''
    print(help_doc)

def login():
    '''
    登陆，将昵称上传至服务器，保持登陆状态。
    '''
    global name, conn

    name = input("Please input your nickname(Blank is not allowed): ")
    if conn.sismember("users", name):
        print("The user already exists, please rename!")
        login()
    else:
        conn.sadd("users", name)
        print("Welcome! If you do not know the operating instructions, type \"help\" to get")


def orderAnalyse():
    '''
    词法分析，将user输入的命令分词并分析。
    '''
    global name, conn

    while True:
        message = input("Chatroom> ")
        order_list = message.lower().split(' ')

        if order_list[0] == 'pull':
            while not mes_queue.empty():
                print(mes_queue.get())
        elif order_list[0] == 'help':
            _help()
        elif order_list[0] == 'downline':
            conn.srem("users", name)
            print("Thank you")
            exit()
        elif order_list[0] == 'pub':
            mes_list = order_list[1:]
            message = ''
            for word in mes_list:
                message += (word + ' ')
            real_mes = name + ': ' + message
            conn.publish("chat", real_mes.encode("utf-8"))
        elif order_list[0] == 'to':
            if not conn.sismember("users", order_list[1]):
                print("This user does not exist")
                orderAnalyse()
            else:
                message = input(order_list[1] + "> ")
                real_mes = name + ': ' + message
                conn.publish(order_list[1], real_mes.encode("utf-8"))
        elif order_list[0] == 'users':
            users = conn.smembers("users")
            print(users)
        else:
            print("This command does not exist!")
            orderAnalyse()


def subPublic():
    '''
    负责监听公共频道。
    '''
    global mes_queue, conn

    sub = conn.pubsub()
    sub.subscribe(["chat"])
    for msg in sub.listen():
        if msg['data'] == 1:
            pass
        else:
            mes_queue.put(msg['data'].decode('utf-8'))


def subPrivate():
    '''
    负责监听私聊信息。
    '''
    global mes_queue, conn, name

    sub = conn.pubsub()
    sub.subscribe([name])
    for msg in sub.listen():
        if msg['data'] == 1:
            pass
        else:
            real_mes = '----------------------------------\n' +\
                       "whisper!!!!!!!!!!!!!!!!!!!!!!!!!!!\n" +\
                       msg['data'].decode('utf-8') + '\n' +\
                       '----------------------------------'
            mes_queue.put(real_mes)


def run_client():
    '''
    程序入口，设置两个子线程，一个用来监听公共频道，另一个用来监听以自己命名的
    频道，主线程负责接收指令。
    '''
    login()

    subPub_thread = threading.Thread(target=subPublic)
    subPri_thread = threading.Thread(target=subPrivate)
    subPub_thread.setDaemon(True)
    subPub_thread.start()
    subPri_thread.setDaemon(True)
    subPri_thread.start()

    time.sleep(3)
    orderAnalyse()


if __name__ == '__main__':
    try:
        run_client()
    finally:
        if conn.sismember("users", name):
            conn.srem("users", name)
