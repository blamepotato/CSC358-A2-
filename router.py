import socket
import netifaces as ni
import select
import json

forwarding_table = {}
if __name__ == "__main__":

    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    end_to_end_sockets = {}
    interfaces = ni.interfaces()
    # sockets that should be input or output to
    input_sockets = []
    output_sockets = []
    # dictionary that map broadcast ip to inet addr
    broadcast_to_tcp = {}
    # dictionary the map client ip address to a specific socket
    client_connections = {}
    ip_to_intf = {}
    # Assign some sockets to all interfaces' broadcast IP
    for intf in interfaces:
        if intf != 'lo':
            print(ni.ifaddresses(intf)[ni.AF_INET])
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            listen_sockets[ip] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            listen_sockets[ip].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_sockets[ip].setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(intf).encode('utf-8'))
            listen_sockets[ip].bind((ip, 9000))

            ip2 = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            end_to_end_sockets[ip2] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            end_to_end_sockets[ip2].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            end_to_end_sockets[ip2].setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(intf).encode('utf-8'))
            end_to_end_sockets[ip2].bind((ip2, 9000))
            end_to_end_sockets[ip2].listen(5)

            broadcast_to_tcp[ip] = ip2

            ip_to_intf[ip2] = intf

    input_sockets = list(listen_sockets.values()) + list(end_to_end_sockets.values())
    print(input_sockets)
    while True:

        readable, writable, exceptional = select.select(input_sockets,
                                                        output_sockets,
                                                        [])
        for s in readable:
            if s.proto == 17:
                data, address = s.recvfrom(1024)
                interface_ip = broadcast_to_tcp[s.getsockname()[0]]
                forwarding_table[address[0]] = interface_ip
                s.sendto(str.encode(interface_ip), (address[0], address[1]))

            if s in end_to_end_sockets.values():
                print("new connection come in")
                new_connection, client_ip = s.accept()
                new_connection.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(ip_to_intf[s.getsockname()[0]]).encode('utf-8'))
                client_connections[client_ip] = new_connection
                input_sockets.append(new_connection)
                output_sockets.append(new_connection)
                print(client_connections)
                print("connection established on ip ", client_ip)

            if s in client_connections.values():
                received = s.recv(1024)
                data = json.loads(received.decode())
                print(data)
                destination = data['destination']
                ttl = int(data['ttl'])
                ttl -= 1
                port = data['port']
                if (destination, int(port)) not in client_connections:
                    s.send(str.encode("The destination is unreachable"))
                data['ttl'] = ttl
                sent = json.dumps(data)
                client_connections[(destination, int(port))].send(str.encode(sent))

