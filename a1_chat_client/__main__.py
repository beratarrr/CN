#!/usr/bin/env python3
from argparse import Namespace, ArgumentParser
import threading
import socket
from logging.config import valid_ident


def parse_arguments() -> Namespace:
    """
    Parse command line arguments for the chat client.
    The two valid options are:
        --address: The host to connect to. Default is "0.0.0.0"
        --port: The port to connect to. Default is 5378
    """
    parser = ArgumentParser(
        prog="python -m a1_chat_client",
        description="A1 Chat Client assignment for the VU Computer Networks course.",
        epilog="Authors: Berat Aras, Senanur nogwat"
    )
    parser.add_argument("-a", "--address", type=str, help="Set server address", default="0.0.0.0")
    parser.add_argument("-p", "--port", type=int, help="Set server port", default=5378)
    return parser.parse_args()


# Define forbidden characters for a valid username.
forbidden_chars = '!@#$%^&* '


def sender(sock: socket.socket, string_bytes: bytes):
    bytes_len = len(string_bytes)
    num_bytes_to_send = bytes_len
    while num_bytes_to_send > 0:
        num_bytes_to_send -= sock.send(string_bytes[bytes_len-num_bytes_to_send:])

def receiver(sock_file, is_running):
    while is_running():
        # user_input = input().strip()
        # if user_input == "!quit"
        #     break
        line = sock_file.readline()
        if not line:
            break
        line = line.strip()
        if line == "SEND-OK":
            print("The message was sent successfully")
        elif line == "BAD-DEST-USER":
            print("The destination user does not exist")
        elif "DELIVERY" in line:
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                from_username = parts[1]
                message = parts[2]
                print(f"From {from_username}: {message}")
        elif "LIST-OK" in line:
            parts = line.split()
            users = parts[1:]
            print(f"There are {len(users[0].split(','))} online users:")
            for user in users[0].split(','):
                print(user)
        elif line == "BUSY":
            print("Cannot log in. The server is full!")
        elif line == "BAD-RQST-HDR":
            print("Error: Unknown issue in previous message header.")
        elif line == "BAD-RQST-BDY":
            print("Error: Unknown issue in previous message body.")


def main() -> None:
    args: Namespace = parse_arguments()
    host: str = args.address
    port: int = args.port

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_port = (host,port)
    sock.connect(host_port)

    sock_file = sock.makefile("r", encoding="utf-8")

    while True:
        print("Welcome to Chat Client. Enter your login:")
        username = input().strip()

        valid_username = True
        for i in forbidden_chars:
            if i in username:
                print(f"Cannot log in as {username}. That username contains disallowed characters.")
                valid_username = False
                break

        if not valid_username:
            continue

        login_command = f"HELLO-FROM {username}\n"
        sender(sock, login_command.encode("utf-8"))

        response = sock_file.readline()
        if not response:
            print("Server closed the connection.")
            sock.close()
            return
        response = response.strip()

        if "HELLO" in response:
            print(f"Successfuly logged in as {username}!")
            break
        elif "IN-USE" in response:
            print(f"Cannot log in as {username}. That username is already in use.")
        elif "BUSY" in response:
            print("Cannot log in. The server is full!")
            sock.close()
            return
        elif "BAD" in response:
            print(f"Cannot log in as {username}. That username contains disallowed characters.")

    running_flag = [True]

    def is_running():
        return running_flag[0]

    receiver_thread = threading.Thread(target=receiver, args=(sock_file, is_running))
    receiver_thread.daemon = True
    receiver_thread.start()

    while True:
        user_input = input().strip()
        if user_input == "":
            continue
        if user_input == "!quit":
            break
        elif user_input == "!who":
            sender(sock, "LIST\n".encode("utf-8"))
        elif user_input.startswith("@"):
            if " " not in user_input:
                continue
            at_index = user_input.find(" ")
            target_username = user_input[1:at_index].strip()
            message = user_input[at_index + 1:].strip()
            if target_username == "" or message == "":
                continue
            send_command = f"SEND {target_username} {message}\n"
            sender(sock, send_command.encode("utf-8"))

    running_flag[0] = False

    #needed to quit all comms doesnt work without it
    sock.shutdown(socket.SHUT_RDWR)
    receiver_thread.join()

    sock.close()



if __name__ == "__main__":
    main()
