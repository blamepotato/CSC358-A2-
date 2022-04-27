import getopt, sys
import select
import socket
import json
import threading
from threading import Thread

ip_address = None

long_options = ["Initialize", "Send", "Output ="]

if __name__ == "__main__":
    def recv():
        while True:
            readable, writable, exceptional = select.select([connection, subnet_connection_listener], [], [])

            if connection in readable:
                temp = connection.recv(1024)
                print(temp)
                received = json.loads(temp.decode())
                if not received:
                    sys.exit(0)


            if subnet_connection_listener in readable:
                temp = subnet_connection_listener.accept()[0]
                received = temp.recv(1024).decode()
                print(received)
                temp.close()

    def send():
        while True:
            message = input("Enter Your Message Here: ")
            destination = input("Input Destination IP Address Here: ")
            ttl = int(input("Input TTL Here: "))
            ttl -= 1
            port = 9000

            if destination[:len(destination) - 3] == subnet_address:
                temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp.bind((ip_address, 9002))
                temp.connect((destination, 9001))
                temp.send(str.encode(message))
                temp.close()

            else:
                sent = {'message': message,
                        'source': ip_address,
                        'source port': port,
                        'destination': destination,
                        'port': port,
                        'ttl': ttl}
                data_string = json.dumps(sent)
                connection.send(str.encode(data_string))

    ip_address = sys.argv[1]
    subnet_address = ip_address[:len(ip_address)-3]
    print(subnet_address)
    initialize_msg = b'hello'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_IP, socket.IP_TTL, 1)
    # bind the ip address to the socket with port
    s.bind((ip_address, 9000))
    # send broadcast message
    s.sendto(initialize_msg, (subnet_address+'255', 9000))
    # expected to receive reply and know the IP address of the router
    data, reply_ip = s.recvfrom(1024)
    s.close()

    router_ip = data.decode()
    print(router_ip)
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.bind((ip_address, 9000))
    connection.connect((router_ip, 9000))

    subnet_connection_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    subnet_connection_listener.bind((ip_address, 9001))
    subnet_connection_listener.listen(5)

    t = threading.Thread(target=recv)
    t.start()

    send()





