import redis
import sqlite3
import threading

# 服务器端。
conn = redis.Redis()


def pub():
    global conn
    while True:
        message = input("Please input message: ")
        real_mes = '\n----------------------------------\n' +\
                   'NOTEING!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' +\
                   'Administrator say: ' + message + '\n' +\
                   '----------------------------------'
        conn.publish("chat", real_mes.encode("utf-8"))

def storeMesLog(raw_info):
    c = sqlite3.connect("meslog.db")
    cur = c.cursor()
    if 'Administrator say:' in raw_info:
        return 

    raw_info_list = raw_info.lower().split(':')
    name = raw_info_list[0].replace(" say", "")
    messsage = ''.join(raw_info_list[1:])
    cur.execute("CREATE TABLE IF NOT EXISTS " + name +\
     " (id INTEGER PRIMARY KEY AUTOINCREMENT, content text, CreatedTime TimeStamp NOT NULL DEFAULT CURRENT_TIMESTAMP)")

    cur.execute("INSERT INTO " + name + " (content) VALUES (?)" , (messsage,))
    c.commit()

    cur.close()
    c.close()

def sub():
    global conn
    sub = conn.pubsub()
    sub.subscribe(["chat"])
    for msg in sub.listen():
        if msg['data'] == 1:
            pass
        else:
            storeMesLog(msg['data'].decode('utf-8'))

def run_server():
    sub_thread = threading.Thread(target=sub)
    sub_thread.setDaemon(True)
    sub_thread.start()
    pub()

if __name__ == '__main__':
    run_server()
