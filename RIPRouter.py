import socket
import threading
import time

import netifaces as ni
import select
import json

# forwading_table
forwarding_table = {}
# sockets that should be input or output to
input_sockets = []
output_sockets = []
# The dictionary stores the information about client/host in format {(client_ip, port number):socket_connection}.
client_connections = {}
# The list stores the socket of the neighbour routers.
router_connections = []
t0 = None
t1 = None

"""
This function receives forwarding tables from neighbor routers and updates the
router's forwarding table based on received data. 
Example:
received: {h1: (xxx.xxx.xxx.xxx, 0)} from interface yyy.yyy.yyy.yyy
updates: {... h1: (yyy.yyy.yyy.yyy, 1)}
"""
def receive_advertise():
    global input_sockets
    global output_sockets
    global router_connections
    global t1, t0
    tIntfs = ni.interfaces()
    changed = False
    receive_from = []
    nearby_router = []
    bip_to_inet = {}
    for intf in tIntfs:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
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
        readable, writable, exceptional = select.select(receive_from, [], [])
        if readable:
            for s in readable:
                sourcedata, sourceAddress = s.recvfrom(1024)
                if sourceAddress[0] != bip_to_inet[s.getsockname()[0]]:
                    receivedData = json.loads(sourcedata.decode())
                    for (key, value) in receivedData.items():
                        if key not in forwarding_table.keys() or (key in forwarding_table.keys() and value[1] + 1 < forwarding_table[key][1]):
                            forwarding_table[key] = (sourceAddress[0], value[1] + 1)
                            changed = True
                            t1 = time.time()
                            print(t1-t0)
                    if changed:
                        print("Forwarding_table: ")
                        print(forwarding_table)
                        changed = False
                        t0 = t1

                    if sourceAddress[0] not in nearby_router:
                        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        new_socket.bind((bip_to_inet[s.getsockname()[0]], 9005))
                        new_socket.connect((sourceAddress[0], 9000))
                        input_sockets.append(new_socket)
                        output_sockets.append(new_socket)
                        router_connections.append(new_socket)
                        nearby_router.append(sourceAddress[0])
"""
This function broadcasts the router's forwarding table to neighbor routers every
30 seconds. The format of the forwarding table is {destination: (interface_to_send, distance to the destination)...}
"""
def advertise():
    global input_sockets
    global output_sockets
    global router_connections
    tIntfs = ni.interfaces()
    broadcasts = []
    socket_b_ip = {}
    for intf in tIntfs:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
            broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast.bind((ip, 9001))
            broadcasts.append(broadcast)
            socket_b_ip[broadcast] = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']

    while True:
        readable, writable, exceptional = select.select([], broadcasts, [])
        for s in writable:
            s.sendto(str.encode(json.dumps(forwarding_table)), (socket_b_ip[s], 9002))
        time.sleep(30)


if __name__ == "__main__":
    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    end_to_end_sockets = {}
    interfaces = ni.interfaces()
    # dictionary that map broadcast ip to inet addr
    broadcast_to_tcp = {}
    # dictionary the map client/router ip address to a specific socket

    ip_to_intf = {}
    # Assign some sockets to all interfaces' broadcast IP
    for intf in interfaces:
        if intf != 'lo':
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
    threading.Thread(target=receive_advertise).start()
    threading.Thread(target=advertise).start()

    while True:

        readable, writable, exceptional = select.select(input_sockets,
                                                        output_sockets,
                                                        [])
        for s in readable:
            if s.proto == 17:
                data, address = s.recvfrom(1024)
                interface_ip = broadcast_to_tcp[s.getsockname()[0]]
                forwarding_table[address[0]] = (interface_ip, 0)
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
                input_sockets.append(new_connection)
                output_sockets.append(new_connection)

            if s in client_connections.values() or s in router_connections:
                received = s.recv(1024)
                data = json.loads(received.decode())
                ttl = int(data['ttl'])
                destination = data['destination']
                port = data['port']
                print(data)
                ttl -= 1
                data['ttl'] = ttl
                sent = json.dumps(data)
                if (destination, int(port)) in client_connections and ttl > 0:
                    client_connections[(destination, int(port))].send(str.encode(sent))
                elif destination in forwarding_table and ttl > 0:
                    print("sending to other router")
                    client_connections[(forwarding_table[destination][0], 9005)].send(str.encode(sent))
                else:
                    s.send(str.encode(json.dumps("The destination is unreachable")))
