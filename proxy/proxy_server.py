import socket
import ssl
import threading

class ProxyServer:
    def __init__(self, host, port):
        self.server_host = host
        self.server_port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.server_host, self.server_port))

    def listen_for_clients(self):
        self.server_socket.listen(10)
        print(f"Proxy Server is listening on: {self.server_host}:{self.server_port}")
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

    def handle_client(self, client_socket, client_address):
        request = client_socket.recv(1024)
        print(f"Received request from: {client_address}: {request.decode('utf-8')}")

        # Rozparsovanie HTTP požiadavky a získanie cieľovej URL
        first_line = request.decode('utf-8').split('\n')[0]
        url = first_line.split(' ')[1]

        # Presmerovanie požiadavky
        self.forward_request(request, client_socket, url)

    def forward_request(self, request, client_socket, url):
        # Vytvorenie SSL kontextu
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Vytvorenie socketu pre pripojenie k cieľovému serveru
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_host, target_port = self.get_host_port_from_url(url)

        # Obalenie socketu SSL kontextom, ak je to HTTPS požiadavka
        if url.startswith('https://'):
            target_socket = context.wrap_socket(target_socket, server_hostname=target_host)

        target_socket.connect((target_host, target_port))
        target_socket.sendall(request)

        # Prijatie odpovede od cieľového serveru
        while True:
            response = target_socket.recv(4096)
            if not response:
                break
            client_socket.send(response)

        # Zatvorenie socketov
        target_socket.close()
        client_socket.close()

    def get_host_port_from_url(self, url):
        # Predpokladáme, že URL začína s http:// alebo https://
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos+3):]

        # Získanie portu, ak je uvedený, inak predvolený port
        port_pos = temp.find(":")
        server_pos = temp.find("/")
        if server_pos == -1:
            server_pos = len(temp)
        webserver = ""
        port = -1
        if (port_pos == -1 or server_pos < port_pos):
            port = 80
            webserver = temp[:server_pos]
        else:
            port = int((temp[(port_pos+1):])[:server_pos-port_pos-1])
            webserver = temp[:port_pos]

        return webserver, port

    def shutdown(self):
        self.server_socket.close()

if __name__ == "__main__":
    host = '0.0.0.0'
    port = 8080
    proxy = ProxyServer(host, port)
    try:
        proxy.listen_for_clients()
    except KeyboardInterrupt:
        proxy.shutdown()
