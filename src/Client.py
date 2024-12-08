import socket
import threading
import sys

from typing import Tuple

from util import *  # Assuming SocketSender is defined in a module


def read_config(filename: str) -> Tuple[Tuple[str, int], Tuple[str, int]]:
    with open(filename, 'r') as file:
        lines = file.readlines()
        server_ip: str = lines[0].split('=')[1].strip()
        server_udp_port: int = int(lines[1].split('=')[1].strip())
        server_tcp_port: int = int(lines[2].split('=')[1].strip())
    return (server_ip, server_udp_port), (server_ip, server_tcp_port)


def register_handler(command, user_ip_addr, sender:SocketSender,rq):
    temp_user = User()
    temp_user.parse_input(command, user_ip_addr,rq,sender.udp_addr,sender.tcp_addr)
    sender.send_udp(temp_user)


def de_register_handler(command, sender,rq):
    temp_deregister = Deregister.build_from_string(command,rq)
    sender.send_udp(temp_deregister)


def looking_for_handler(command, sender,r):
    temp_looking_for = Looking_for.build_from_string(command,r)
    sender.send_udp(temp_looking_for)


def offer_handler(command, sender):
    temp_Offer = Offer.build_from_string(command)
    sender.send_udp(temp_Offer)


def accept_handler(command, sender):
    temp_Accept = Accept.build_from_string(command)
    sender.send_udp(temp_Accept)


def refuse_handler(command, sender):
    temp_refuse = Refuse.build_from_string(command)
    sender.send_udp(temp_refuse)


def cancel_handler(command, sender):
    temp_cancel = Cancel.build_from_string(command)
    sender.send_udp(temp_cancel)


def buy_handler(command, sender):
    temp_Buy = Buy.build_from_string(command)
    sender.send_udp(temp_Buy)

def INFORM_Res_handler(command, sender):
    temp_INFORM_Res = INFORM_Res.build_from_string(command)
    sender.send_tcp(temp_INFORM_Res)


counter = 0


def generate_request_number():
    global counter  # Use the counter defined in the outer function
    counter += 1
    return counter

def main():
    try:
        # Step 1: Read configuration and initialize the user
        ServerUdpAddress, ServerTcpAddress = read_config("config.txt")
        hostname = socket.gethostname()
        user_ip_addr = socket.gethostbyname(hostname)



        sender = SocketSender(ServerUdpAddress,user_ip_addr)

        log = Log(False,sender.udp_addr[1])
        sender.start_listener()
        sender.log=log
        # Step 5: Main loop to accept further commands
        while True:
            try:
                command = input("\nEnter command or 'exit' to quit: \n")
                log.add("Input Command",command)
                if command.upper() == "EXIT":
                    sender.stop()  # Stop the UDP listener thread when 'exit' is entered
                    print("Exiting program...")
                    break  # Exit the loop

                # Handle REGISTER command
                elif command.split("#")[0].upper() == "REGISTER":
                    r=generate_request_number()
                    threading.Thread(target=register_handler, args=(command, user_ip_addr, sender,r,)).start()
                # Handle DE-REGISTER command
                elif command.split("#")[0].upper() == "DE-REGISTER":
                    r=generate_request_number()
                    threading.Thread(target=de_register_handler, args=(command, sender, r,)).start()

                elif command.split("#")[0].upper() == "LOOKING_FOR":
                    r=generate_request_number()
                    threading.Thread(target=looking_for_handler, args=(command, sender,r,)).start()

                elif command.split("#")[0].upper() == "OFFER":
                    threading.Thread(target=offer_handler, args=(command, sender,)).start()

                elif command.split("#")[0].upper() == "ACCEPT":
                    threading.Thread(target=accept_handler, args=(command, sender,)).start()

                elif command.split("#")[0].upper() == "REFUSE":
                    threading.Thread(target=refuse_handler, args=(command, sender,)).start()

                elif command.split("#")[0].upper() == "CANCEL":
                    threading.Thread(target=cancel_handler, args=(command, sender,)).start()

                elif command.split("#")[0].upper() == "BUY":
                    threading.Thread(target=buy_handler, args=(command, sender,)).start()

                elif command.split("#")[0] == "INFORM_Res":
                    threading.Thread(target=INFORM_Res_handler, args=(command, sender,)).start()

            except KeyboardInterrupt:
                print("Shutting down...")  # Graceful shutdown on Ctrl+C
                sender.stop()
                break

    except KeyboardInterrupt:
        print("Program interrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
