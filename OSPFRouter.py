import socket
import threading
import time

import netifaces as ni
import select
import json

forwarding_table = {}
# sockets that should be input or output to
input_sockets = []
output_sockets = []
client_connections = {}
router_connections = []
neighbor_routers = {}
# forwarding_table_to_send[0] is a dictionary of the form {'source': 'neighbour}
# forwarding_table_to_send[1] is a list of all host ips this router is connected to
forwarding_table_to_send = [{}, []]
# previous version of send_forwarding_table
old_forwarding_table_to_send = [{}, []]
t0 = None
t1 = None

def get_neighbour():
    global input_sockets
    global output_sockets
    global router_connections
    global neighbor_routers
    global forwarding_table_to_send
    tIntfs = ni.interfaces()
    broadcasts = []
    receive_from = []
    socket_b_ip = {}
    nearby_router = []
    bip_to_inet = {}
    for intf in tIntfs:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
            broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast.bind((ip, 9001))
            broadcasts.append(broadcast)
            socket_b_ip[broadcast] = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']

            ip_b = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                    socket.IPPROTO_UDP)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                               str(intf).encode('utf-8'))
            receive.bind((ip_b, 9002))
            receive_from.append(receive)

            bip_to_inet[ip_b] = ip

    while True:
        readable, writable, exceptional = select.select(receive_from, broadcasts, [])
        if readable:
            for s in readable:
                sourcedata, sourceAddress = s.recvfrom(1024)
                if sourceAddress[0] != bip_to_inet[s.getsockname()[0]]:
                    receivedData = json.loads(sourcedata.decode())
                    neighbor_routers[bip_to_inet[s.getsockname()[0]]] = sourceAddress[0]
                    forwarding_table_to_send[0] = neighbor_routers

                    if sourceAddress[0] not in nearby_router:
                        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        new_socket.bind((bip_to_inet[s.getsockname()[0]], 9005))
                        new_socket.connect((sourceAddress[0], 9000))
                        input_sockets.append(new_socket)
                        output_sockets.append(new_socket)
                        router_connections.append(new_socket)
                        nearby_router.append(sourceAddress[0])
        else:
            for s in writable:
                s.sendto(str.encode(json.dumps('hello there')), (socket_b_ip[s], 9002))
                time.sleep(5)


def print_forwarding_table():
    print("Forwarding Table:")
    print(forwarding_table)


'''
This function creates a socket to OSPFMonitor and writes the forwarding table to it.
Only use golable variables forwards_table 
'''
def send_forwarding_table():
    tIntfs = ni.interfaces()
    global forwarding_table_to_send
    global old_forwarding_table_to_send
    b_ip = 0
    send_to = []
    for intf in tIntfs:
        if 'eth10' in intf:
            b_ip = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            monitor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            monitor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            monitor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(intf).encode('utf-8'))
            monitor_socket.bind((ip, 8002))
            send_to.append(monitor_socket)

    while True:
        if old_forwarding_table_to_send != forwarding_table_to_send:
            readable, writable, exceptional = select.select([], send_to, [])
            if writable:
                for s in writable:
                    s.sendto(str.encode(json.dumps(forwarding_table_to_send)), (b_ip, 8002))
                old_forwarding_table_to_send = forwarding_table_to_send.copy()


def get_forwarding_table():
    global forwarding_table, t0, t1
    interfaces = ni.interfaces()
    monitor = []
    changed = False
    for intf in interfaces:
        if 'eth10' in intf:
            ip2 = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            monitor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            monitor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(intf).encode('utf-8'))
            monitor_socket.bind((ip2, 8005))
            monitor.append(monitor_socket)

    while True:
        readable, writable, exceptional = select.select(monitor, [], [])
        if readable:
            for s in readable:
                received, address = s.recvfrom(1024)
                data = json.loads(received.decode())
                print(data)
                for host, dest in data.items():
                    if host not in forwarding_table:
                        changed = True
                        forwarding_table[host] = dest
                        t1 = time.time()
                    else:
                        if forwarding_table[host] != dest:
                            changed = True
                            forwarding_table[host] = dest
                            t1 = time.time()
                if changed:
                    print(t1-t0)
                    changed = False
                    t0 = t1
                    print("Forwarding_table: ")
                    print(forwarding_table)


if __name__ == "__main__":
    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    end_to_end_sockets = {}
    interfaces = ni.interfaces()
    # dictionary that map broadcast ip to inet addr
    broadcast_to_tcp = {}
    # dictionary the map client/router ip address to a specific socket

    ip_to_intf = {}
    myIntf_to_destIntf = {}
    # Assign some sockets to all interfaces' broadcast IP
    for intf in interfaces:
        if intf != 'lo' and 'eth10' not in intf:
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            listen_sockets[ip] = socket.socket(socket.AF_INET,
                                               socket.SOCK_DGRAM,
                                               socket.IPPROTO_UDP)
            listen_sockets[ip].setsockopt(socket.SOL_SOCKET,
                                          socket.SO_REUSEADDR, 1)
            listen_sockets[ip].setsockopt(socket.SOL_SOCKET,
                                          socket.SO_BINDTODEVICE,
                                          str(intf).encode('utf-8'))
            listen_sockets[ip].bind((ip, 9000))

            ip2 = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            end_to_end_sockets[ip2] = socket.socket(socket.AF_INET,
                                                    socket.SOCK_STREAM)
            end_to_end_sockets[ip2].setsockopt(socket.SOL_SOCKET,
                                               socket.SO_REUSEADDR, 1)
            end_to_end_sockets[ip2].setsockopt(socket.SOL_SOCKET,
                                               socket.SO_BINDTODEVICE,
                                               str(intf).encode('utf-8'))
            end_to_end_sockets[ip2].bind((ip2, 9000))
            end_to_end_sockets[ip2].listen(5)

            broadcast_to_tcp[ip] = ip2

            ip_to_intf[ip2] = intf

    input_sockets = list(listen_sockets.values()) + list(
        end_to_end_sockets.values())

    t0 = time.time()
    threading.Thread(target=get_neighbour).start()
    threading.Thread(target=get_forwarding_table).start()
    threading.Thread(target=send_forwarding_table).start()

    while True:

        readable, writable, exceptional = select.select(input_sockets,
                                                        output_sockets,
                                                        [])
        for s in readable:
            if s.proto == 17:
                data, address = s.recvfrom(1024)
                interface_ip = broadcast_to_tcp[s.getsockname()[0]]
                forwarding_table[address[0]] = interface_ip
                forwarding_table_to_send[1] = list(forwarding_table.keys())
                s.sendto(str.encode(interface_ip), (address[0], address[1]))
                if t1 is not None:
                    t0 = t1
                else:
                    t0 = time.time()
                print("Forwarding_table (added host): ")
                print(forwarding_table)

            if s in end_to_end_sockets.values():
                new_connection, client_ip = s.accept()
                new_connection.setsockopt(socket.SOL_SOCKET,
                                          socket.SO_BINDTODEVICE, str(
                        ip_to_intf[s.getsockname()[0]]).encode('utf-8'))
                client_connections[client_ip] = new_connection
                myIntf_to_destIntf[s.getsockname()[0]] = client_ip[0]
                input_sockets.append(new_connection)
                output_sockets.append(new_connection)

            if s in client_connections.values() or s in router_connections:
                received = s.recv(1024)
                data = json.loads(received.decode())
                ttl = int(data['ttl'])
                ttl -= 1
                print(data)
                destination = data['destination']
                port = data['port']
                data['ttl'] = ttl
                sent = json.dumps(data)
                if (destination, int(port)) in client_connections and ttl > 0:
                    client_connections[(destination, int(port))].send(str.encode(sent))
                elif destination in forwarding_table and ttl > 0:
                    print("sending to other router")
                    client_connections[(myIntf_to_destIntf[forwarding_table[destination]], 9005)].send(str.encode(sent))
                else:
                    s.send(str.encode(json.dumps("The destination is unreachable")))
