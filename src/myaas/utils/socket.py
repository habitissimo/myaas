import socket


def reserve_port():
    """
    This function finds a free port number for new containers to be created,
    it releases the port just before returning the port number, so there is
    a chance for another process to get it, let's see if it works.

    This requires the myaas container to be running with --net=host otherwise
    the port returned by this method will be a free port inside the container,
    but may not be free on the host machine.
    """
    s = socket.socket()
    s.bind(("", 0))
    (ip, port) = s.getsockname()
    s.close()

    return port


def test_tcp_connection(ip, port):
    """
    Tries to establish a TCP connection, returns a boolean indicating if the
    connection succeded.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    sock.close()

    return result == 0
