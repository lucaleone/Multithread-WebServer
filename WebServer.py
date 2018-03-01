"""
Multithread webServer

!!! PROJECT INCOMPLETE !!!

Revision History:
    date: changes..
"""
from abc import abstractmethod, ABCMeta

__version__ = "0.1"
__date__ = "01/02/2018"
__author__ = "Luca Leone <lucaleone@outlook.com>"
__credits__ = "Luca Leone"
__all__ = "help"
import socket
import multiprocessing
import os
import io


def print_process(function_name, msg):
    print('{} process id {}: {}'.format(function_name, os.getpid(), msg))


class RouteAlreadyExists(Exception):
    pass


class PageNotFound(Exception):
    """Property: requested_page"""
    pass


class WebServerClosed(Exception):
    pass


class WebServer:
    """WebServer class
    Properties:
        Private:
            _backlog
            _is_running
            _closed
            _httpRequestHandler
            _router
            _server_socket
        Constant:
            HOST = HOST
            PORT = PORT
    """
    # multiprocessing.cpu_count()
    def __init__(self, host, port):
        self._backlog = 1024
        self._is_running = False
        self._closed = False
        self._router = Router("{}:{}".format(host, port))
        self._httpRequestHandler = HttpRequestHandler(self._router)
        # Create a IP, TCP socket
        self.HOST = host
        self.PORT = port
        self._server_socket = server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))

    def serve_forever(self):
        # set the TCP backlog
        if self._closed:
            raise WebServerClosed()
        self._server_socket.listen(max(self._backlog, socket.SOMAXCONN))
        print('Web Server process id:', os.getpid())
        print('Serving HTTP on port ', self.PORT)
        self._start()
        while self._is_running and not self._closed:
            (client_socket, client_address) = self._server_socket.accept()
            client_process = multiprocessing.Process(target=self._httpRequestHandler.handle,
                                                     name=str(client_address),
                                                     args=(client_socket,))
            client_process.daemon = True
            client_process.start()
            client_socket.close()

    def _start(self):
        self._is_running = True

    def stop(self):
        self._is_running = False

    def close(self):
        """can raise: OSError"""
        try:
            self._server_socket.close()
            self._closed = True
        except OSError:
            raise OSError()

    def add_route(self, page: str, *matches: list):
        self._router.add_route(page, matches)

    def is_running(self):
        return self._is_running


class Router:
    def __init__(self, endpoint, homepage = "", page404=""):
        self.webserver_endpoint = endpoint
        self._routes = {homepage: ['index', 'index.html']}
        if page404:
            self.page404 = page404
        else:
            self.page404 = homepage

    def add_route(self, page: str, *matches: list):
        print(self._routes)
        if page in self._routes:
            raise RouteAlreadyExists()
        else:
            self._routes[page] = matches

    def get_redirect(self, page_name):
        print(self._routes.values())
        for page in self._routes.keys():
            if page_name in self._routes[page]:
                return page
        return self.page404



class HttpRequestHandler:
    def __init__(self, routes):
        self.current_client_socket = None
        self._routes = routes

    def _get_http_verb(self, line: str):
        return line.split(' ')[0]

    def handle(self, client_socket: socket):
        print_process("Handle_request of ", str(client_socket.getpeername()))
        self.current_client_socket = client_socket
        request = client_socket.recv(1024)
        print(request)
        first_line: str = request.splitlines()[0].decode("ascii")
        verb = self._get_http_verb(first_line).lower()
        http_response = None
        try:
            http_response = IHttpRequest.factory(verb).get_response(request)
        except PageNotFound as err:
            print(err.requested_page)
            redirect_to = self._routes.get_redirect(err.requested_page)
            print(redirect_to)
            http_response = ErrorGetHttpRequest().get_response(redirect_to)
        except Exception as e:
            print(e)
        finally:
            self._respond_to_client(http_response)
            self.current_client_socket.close()

    def _respond_to_client(self, http_response: bytes):
        if http_response:
            self.current_client_socket.sendall(http_response)


class IHttpRequest(metaclass=ABCMeta):

    @abstractmethod
    def get_response(self, request: bytes) -> bytes:
        pass

    @staticmethod
    def factory(verb: str):
        candidate_class = verb.title() + "HttpRequest()"
        try:
            return eval(candidate_class)
        except NameError:
            raise NotImplementedError("{} verb not implemented".format(verb))


class GetHttpRequest(IHttpRequest):
    def _fix_path(self, pagename: str):
        if pagename[0] == "/":
            pagename = pagename[1:]
        if ".html" not in pagename[-5:]:
            pagename = pagename + ".html"
        return pagename


    def get_response(self, request: bytes):
        """raise error if page don't exists  err: RouteNotFound"""
        first_line: str = request.splitlines()[0].decode("ascii")
        verb, page, protocol = first_line.split(" ")
        page = self._fix_path(page)
        print("looking for page: ", page)
        if os.path.exists(page):
            with open(page, "rb") as f:
                http_response = b"HTTP/1.1 200 OK\r\n\r\n" + f.read()
                return http_response
        else:
            error = PageNotFound()
            error.requested_page = page
            raise error


class PostHttpRequest(IHttpRequest):
    def get_response(self, request: bytes):
        pass


class ErrorGetHttpRequest(IHttpRequest):
    def get_response(self, request: str):
        http_response = b"HTTP/1.1 308 Permanent Redirect\r\nLocation: /" + request
        # if request:
        #     http_response = b"HTTP/1.1 308 Permanent Redirect\r\nLocation: /" + request
        # else:
        #     http_response = b"HTTP/1.1 404 Not Found"
        print(http_response)
        return http_response


def main():
    HOST, PORT = '', 8888
    serv = WebServer(HOST, PORT)
    serv.add_route("test", "try")
    serv.serve_forever()



if __name__ == "__main__":
    main()
