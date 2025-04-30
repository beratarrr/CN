#!/usr/bin/env python3
from argparse import Namespace, ArgumentParser
import threading
import socket

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
        epilog="Authors: Berat Aras, Senanur"
    )
    parser.add_argument("-a", "--address", type=str, help="Set server address", default="0.0.0.0")
    parser.add_argument("-p", "--port", type=int, help="Set server port", default=5378)
    return parser.parse_args()


forbidden_chars = '!@#$%^&* '


def sender(sock: socket.socket, string_bytes: bytes):
    bytes_len = len(string_bytes)
    num_bytes_to_send = bytes_len
    while num_bytes_to_send > 0:
        num_bytes_to_send -= sock.send(string_bytes[bytes_len - num_bytes_to_send:])


def receiver(sock: socket.socket, is_running):
    buffer = ""
    while is_running():
        data = sock.recv(4096)
        if not data:
            print("Connection closed by server.")
            break
        buffer += data.decode("utf-8")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            if line == "SEND-OK":
                print("The message was sent successfully")
            elif "DELIVERY" in line:
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    from_username = parts[1]
                    message = parts[2]
                    print(f"From {from_username}: {message}")
            elif "LIST-OK" in line:
                parts = line.split()
                users = parts[1:] if len(parts) > 1 else []
                user_list = []
                for item in users:
                    user_list.extend(item.split(","))
                user_list = [u for u in user_list if u]
                print(f"There are {len(user_list)} online users:")
                for user in user_list:
                    print(user)
            elif line == "BAD-DEST-USER":
                print("The destination user does not exist")
            elif line == "BAD-RQST-HDR":
                print("Error: Unknown issue in previous message header.")
            elif line == "BAD-RQST-BODY":
                print("Error: Unknown issue in previous message body.")
            elif line == "BUSY":
                print("Cannot log in. The server is full!")
            else:
                print(f"Error: Unknown message header '{line}'")



def main() -> None:
    args: Namespace = parse_arguments()
    host: str = args.address
    port: int = args.port

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_port = (host, port)
    sock.connect(host_port)

    while True:
        print("Welcome to Chat Client. Enter your login: ")
        username = input().strip()
        if username == "!quit":
            sock.close()
            return

        if not username or any(char in forbidden_chars for char in username):
            print(f"Cannot log in as {username}. That username contains disallowed characters.")
            continue

        login_command = f"HELLO-FROM {username}\n"
        sender(sock, login_command.encode("utf-8"))

        buffer = ""
        while "\n" not in buffer:
            data = sock.recv(1)
            if not data:
                print("Server closed the connection.")
                sock.close()
                return
            buffer += data.decode("utf-8")
        response = buffer.strip()

        if "HELLO" in response:
            print(f"Successfully logged in as {username}!")
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

    receiver_thread = threading.Thread(target=receiver, args=(sock, is_running))
    receiver_thread.daemon = True
    receiver_thread.start()

    while True:
        user_input = input().strip()
        if user_input == "!quit":
            break
        elif user_input == "!who":
            sender(sock, b"LIST\n")
        elif user_input.startswith("@"):
            parts = user_input.split(maxsplit=1)
            target = parts[0][1:]
            if len(parts) > 1:
                message = parts[1].strip()
            else:
                message = ""
            full_message = f"SEND {target} {message}\n"
            sender(sock, full_message.encode("utf-8"))
        else:
            print("Invalid input. Use !who, !quit, or @username <message>.")

    running_flag[0] = False
    sock.shutdown(socket.SHUT_RDWR)
    receiver_thread.join()
    sock.close()


if __name__ == "__main__":
    main()
