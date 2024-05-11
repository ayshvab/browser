import socket
import ssl

# Shell #1
# python3 -m http.server 8000 -d .

# Shell #2
# python3 browser.py http://localhost:8000/


class HttpRequestMessage:
    headers = {
        "User-Agent": "my-browser"
    }

    def __init__(
        self,
        method,
        host,
        path,
        headers={},
        version="1.1",
    ):
        self.method = method
        self.host = host
        self.path = path
        self.version = version

        self.headers.update(headers)
        if self.headers.get("Connection") is None:
            if version == "1.1":
                self.headers["Connection"] = "keep-alive"
            elif version == "1.0":
                self.headers["Connection"] = "close"

    def build(self):
        requestline = "{} {} HTTP/{}\r\n".format(
            self.method, self.path, self.version
        )
        headers = f"Host: {self.host}\r\n"
        for key, value in self.headers.items():
            headers += f"{key}: {value}\r\n"
        message = requestline + headers + "\r\n"
        return message.encode("utf8")


class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        http_req_message = HttpRequestMessage("GET", self.host, self.path)

        print(http_req_message.build())

        s.send(http_req_message.build())
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        s.close()
        return content


def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))
