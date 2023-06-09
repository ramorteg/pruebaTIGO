import paramiko
import re
import sqlite3
from datetime import datetime
import asyncio
from telegram import Bot

# This is a sample Python script.

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def define_conn(host, user, key_fn):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, username=user, key_filename=key_fn)
    return ssh_client


def get_memory(ssh_client):
    command = "free"
    stdin, stdout, stderr = ssh_client.exec_command(command)
    memory_line = re.search(r"Mem:\s+(\d+)\s+(\d+)", stdout.read().decode('utf-8'))
    total_memory = int(memory_line.group(1))
    used_memory = int(memory_line.group(2))
    return total_memory, used_memory


def get_hostname(ssh_client):
    command = "hostname"
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode('utf-8')
    return output.replace("\n", "")


def get_cpu(ssh_client):
    # command = 'top -b -n 1 | grep "Cpu(s)"'
    command = "top -bn 1 | grep '%Cpu' | awk '{print $2}'"
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode('utf-8').replace("\n", "")
    # return float((output.replace("\n", "")).split()[7])
    return float((output))


def get_disk(ssh_client):
    command = 'df --total -h | grep "total"'
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode('utf-8')
    output = float(output.split()[4].rstrip('%'))
    return output


def insert_measure(servidor, elemento, medida):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO graphs_measure (server_id, element_id, measure, date) "
                   "VALUES (?, ?, ?, ?)",
                   (servidor, elemento, medida, datetime.now()))
    conn.commit()
    conn.close()
    
    
def send_instagram(mensaje):
    token = '5980394724:AAEE5TNmRV1Y0ogzQ7Bw4G8qltZIGVO-7iU'
    chat_id = '6218768145'
    bot = Bot(token=token)

    asyncio.run(enviar_mensaje(chat_id,mensaje,bot))


async def enviar_mensaje(chat_id, mensaje, bot):
    await bot.send_message(chat_id=chat_id, text=mensaje)


def execute():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id,ip,user_name,file_key FROM graphs_server")
    rows = cursor.fetchall()
    for row in rows:
        id = row[0]
        ip = row[1]
        user = row[2]
        file = row[3]
        
        print(f'La salida es {id}-{ip}-{user}-{file}')
        
        conn = define_conn(ip, user, file)

        hn = get_hostname(conn)
        #print(f'El nombre del host: {hn} ')

   
        total, used = get_memory(conn)
        mem = (used/total) * 100
        #print(f'La memoria total es {total} y la usada es {used}')
        insert_measure(id, 1, mem )
        if mem > 75:
            send_instagram(f'El umbral de uso de memoria para el servidor {hn} superó el límite')

        cpu = get_cpu(conn)
        #print(f'El uso de CPU es: {cpu} ')
        insert_measure(id, 2, cpu)
        if cpu > 75:
            send_instagram(f'El umbral de uso de CPU para el servidor {hn} superó el límite')

        disco = get_disk(conn)
        #print(f'El uso de disco es: {disco} ')
        insert_measure(id, 3, disco)
        if disco > 75:
            send_instagram(f'El umbral de capacidad de disco para el servidor {hn} superó el límite')

    conn.close()



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    execute()
