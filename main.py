# coding:utf-8
'''
In preparation for your interview, we would like you to prepare the following coding project.
Build a simple API server to handle user audio projects. Your server should provide endpoints that allow a user to perform the following actions:
1. POST raw audio data and store it.
Eg: $ curl -X POST --data-binary @myfile.wav
http://localhost/post
2. GET a list of stored files, GET the content of stored files, and GET metadata of stored files, such as the duration of the audio. The GET endpoint(s) should accept a query parameter that allows the user to filter results. Results should be returned as JSON.
Eg: $ curl http://localhost/download?name=myfile.wav
Eg: $ curl http://localhost/list?maxduration=300
Eg: $ curl http://localhost/info?name=myfile.wav
When you arrive for your interview, we will ask you to present your code and elaborate on some of the design decisions you have made, some of the things you would have done differently if you had more time, some things you learned about libraries you used.
Your code should minimally be able to handle the GET and POST requests described above. Additionally, here are some features and questions you might want to think about:
How to handle user authentication and data security?
How to build a simple browser UI to interface with your API?
How do you want to store audio data? For the purposes of this interview, just keeping them in memory is fine, but how else would you want to keep and serve audio data?
How to handle data integrity? How to make sure that users can't break your API by uploading rogue text data? How to make sure the metadata you calculate is correct and not thrown off by unmet expectations on the backend?
'''

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
            duration_filter = float(method[1][len(pattern):])
        except:
            duration_filter = -1
        print('parsed duration:', duration_filter)
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
                        if duration <= duration_filter:
                            info[it] = duration
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
    with open(dir + name, "wb+") as f:
        f.write(request_data)
    response_start_line = "HTTP/1.1 404 Not Found\r\n"
    response_headers = "Server: My server\r\n"
    response_body = "Save as:" + name

    return response_start_line, response_headers, response_body


def handle_download_or_info(method, typ):
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
                if typ == 'info':
                    try:
                        file.close()
                        with contextlib.closing(wave.open(dir + file_name, 'r')) as f:
                            frames = f.getnframes()
                            rate = f.getframerate()
                            duration = frames / float(rate)
                            response_body = 'file name:' + str(file_name) + ' duration:' + str(duration) + 's'
                    except Exception as e:
                        print('exception caught', repr(e))
                        response_body = 'file name:' + str(file_name) + ' duration not found'
                else:
                    file_data = file.read()
                    file.close()
                    response_body = file_data.decode()
    return response_start_line, response_headers, response_body


def handle_client(client_socket, client_address):
    request_data = b""
    while True:
        temp_data = client_socket.recv(1024)
        print('recv:',temp_data)
        request_data += temp_data
        if len(temp_data) < 1024:
            break
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
        response_start_line, response_headers, response_body = handle_download_or_info(method, 'download')
    elif method[0] == "/list":
        response_start_line, response_headers, response_body = handle_list(method)
    elif method[0] == "/info":
        response_start_line, response_headers, response_body = handle_download_or_info(method, 'info')
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
