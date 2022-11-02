# coding:utf-8

import socket
import time
import re
import json
import os
import wave
import contextlib

from multiprocessing import Process

# dir = '/Users/mczhuang/MIX/debug/'
dir = './server_file/'

def handle_list(method):
    pattern = 'maxduration='
    print('handling list', method)
    if len(method) < 2 or len(str(method[1])) <= len(pattern) or str(method[1])[:len(pattern)] != pattern:
        response_start_line = "HTTP/1.1 404 Not Found\r\n"
        response_headers = "Server: My server\r\n"
        response_body = "Invalid Parameter"
    else:
        try:
            duration_filter=float(method[1][len(pattern):])
        except:
            duration_filter = -1
        print('parsed duration:',duration_filter)
        f = os.walk(dir)
        info = dict()
        for dirpath, dirnames, filenames in f:
            print(dirpath)
            print(dirnames)
            print(filenames)
            for it in filenames:
                print(it)
                try:
                    with contextlib.closing(wave.open(dir + it, 'r')) as f:
                        frames = f.getnframes()
                        rate = f.getframerate()
                        duration = frames / float(rate)
                        if duration<=duration_filter:
                            info[it]=duration
                        print(duration)
                except Exception as e:
                    print('catch error:', repr(e))

        # with open('/Users/mczhuang/MIX/debug/' + name, "wb") as f:
        #     f.write(request_data)
        response_start_line = "HTTP/1.1 404 Not Found\r\n"
        response_headers = "Server: My server\r\n"
        response_body = str(json.dumps(info))

    return response_start_line, response_headers, response_body


def handle_post(method, request_data, source):
    print('handling post', method)
    request_data = request_data[request_data.find(b'\r\n\r\n') + 4:]
    print('request_data', request_data)
    name = str(time.time()) + '@' + str(source) + '.wav'
    with open(dir + name, "wb") as f:
        f.write(request_data)
    response_start_line = "HTTP/1.1 404 Not Found\r\n"
    response_headers = "Server: My server\r\n"
    response_body = "Save as:" + name

    return response_start_line, response_headers, response_body


def handle_download_or_info(method,typ):
    print('handling download_or_info', method, typ)
    if len(method) < 2 or len(str(method[1])) < len("name=1.wav") or str(method[1])[:5] != "name=":
        response_start_line = "HTTP/1.1 404 Not Found\r\n"
        response_headers = "Server: My server\r\n"
        response_body = "Invalid Parameter"
    else:
        file_name = str(method[1])[5:]
        if file_name[-4:] != ".wav":
            response_start_line = "HTTP/1.1 404 Not Found\r\n"
            response_headers = "Server: My server\r\n"
            response_body = "Request File not .wav"
        else:
            try:
                file = open(dir + file_name, "rb")
            except IOError:
                response_start_line = "HTTP/1.1 404 Not Found\r\n"
                response_headers = "Server: My server\r\n"
                response_body = "The file is not found!"
            else:
                response_start_line = "HTTP/1.1 200 OK\r\n"
                response_headers = "Server: My server\r\n"
                if typ=='info':
                    try:
                        file.close()
                        with contextlib.closing(wave.open(dir + file_name, 'r')) as f:
                            frames = f.getnframes()
                            rate = f.getframerate()
                            duration = frames / float(rate)
                            response_body = 'file name:'+str(file_name)+' duration:'+str(duration)+'s'
                    except Exception as e:
                        print('exception caught',repr(e))
                        response_body = 'file name:' + str(file_name) + ' duration not found'
                else:
                    file_data = file.read()
                    file.close()
                    response_body = file_data.decode()
    return response_start_line, response_headers, response_body


def handle_client(client_socket, client_address):
    request_data = client_socket.recv(1024)
    print("request data:", request_data)
    request_lines = request_data.splitlines()
    print('lines:', request_lines)

    request_start_line = request_lines[0]
    print('request_start_line', request_start_line)
    parameter = str(request_start_line).split(' ')[1]
    print('par', parameter)
    method = parameter.split('?')
    print('method', method)
    if method[0] == "/post":
        response_start_line, response_headers, response_body = handle_post(method, request_data, client_address)
    elif method[0] == "/download":
        response_start_line, response_headers, response_body = handle_download_or_info(method,'download')
    elif method[0] == "/list":
        response_start_line, response_headers, response_body = handle_list(method)
    elif method[0] == "/info":
        response_start_line, response_headers, response_body = handle_download_or_info(method,'info')
    else:
        response_start_line = "HTTP/1.1 404 Not Found\r\n"
        response_headers = "Server: My server\r\n"
        response_body = "Invalid Request"

    response = response_start_line + response_headers + "\r\n" + response_body
    print("response data:", response)
    client_socket.send(bytes(response, "utf-8"))
    client_socket.close()


if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 8888))
    server_socket.listen(128)

    while True:
        client_socket, client_address = server_socket.accept()
        print('connected', client_address)
        handle_client_process = Process(target=handle_client, args=(client_socket, client_address))
        handle_client_process.start()
        client_socket.close()
