import pickle
import socket
import sys
import signal
import os
import threading
import queue
from logging import exception
from random import random
from typing import Dict, List
import time
import random

waiting_time = 120
from util import *


def save_with_pickle(obj, filename: str = "log.txt"):
    # we create backup file for server's brain in pickle format
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)
        print(f"Server Object saved to {filename}")


def load_with_pickle(filename: str):
    # Check if the file exists,if exist then load else return new object
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        print(f"File '{filename}' does not exist. Nothing to load.")
        return Server()


class Pairs:
    def __init__(self):
        """
        offers: List[Offer]
        looking_for_record: Looking_for
        search_record: Search
        seller: User = None
        buyer: User = None
        releasing_time: float = time.time()
        deal_price: int = 0
        seller_response: bool = None
        buyer_response: bool = None
        offer = None
        seller_tcp_connection: socket.socket = None
        buyer_tcp_connection: socket.socket = None
        seller_Finalizing = False
        buyer_Finalizing = False
        seller_info: INFORM_Res = None
        buyer_info: INFORM_Res = None
        credit_amount: float = 0
        transaction_fee: float = 0
        """
        self.offers: List[Offer] = []
        self.looking_for_record: Looking_for = None
        self.search_record: Search = None
        self.seller: User = None
        self.buyer: User = None
        self.releasing_time: float = time.time()
        self.deal_price: int = 0
        self.seller_response: bool = None
        self.buyer_response: bool = None
        self.offer = None
        self.seller_tcp_connection: socket.socket = None
        self.buyer_tcp_connection: socket.socket = None
        self.seller_Finalizing = False
        self.buyer_Finalizing = False
        self.seller_info: INFORM_Res = None
        self.buyer_info: INFORM_Res = None
        self.credit_amount: float = 0
        self.transaction_fee: float = 0
        self.done = False

    def __getstate__(self):
        """
        this will save the state of the port, because pickle can't save port
        Copy the object's dictionary
        Remove non-pickleable attributes like sockets
        :return:
        """
        state = self.__dict__.copy()
        del state['seller_tcp_connection']
        del state['buyer_tcp_connection']
        return state

    def __setstate__(self, state):
        """
        this will load the state of the port, because pickle can't generate port
        Copy the object's dictionary
        update non-pickleable attributes like sockets
        :return:
        """
        self.__dict__.update(state)
        self.seller_tcp_connection = None
        self.buyer_tcp_connection = None


class Server:
    def __init__(self):
        """
        Server initialization this is the brain of the server
        registed_clients has all registed client
        LS_look_up this is a lookup table for lookingfor and search
        server_dict this is a dictionary for search obj and Pairs
        one udp socket and all tcp and udp message will be put in messafe)queue
        tcp_pairs are the ongoing connection list
        """
        self.server_down = -1
        self.request_number: int = 0
        self.registed_clients: Dict[str, User] = {}
        self.server_dict: Dict[Search, Pairs] = {}
        self.LS_look_up: Dict[Looking_for, Search] = {}
        self.UDP_PORT: int = 8888
        self.hostname: str = socket.gethostname()
        self.user_ip_addr: str = socket.gethostbyname(self.hostname)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.user_ip_addr, self.UDP_PORT))
        self.message_queue: queue = queue.Queue()
        self.tcp_pairs: Dict[str, Pairs] = {}
        self.profit: float = 0

    def __getstate__(self):
        """
        this will save the state of the port and queue, because pickle can't save port and threading queue
        Copy the object's dictionary
        Remove non-pickleable attributes
        :return:
        """
        state = self.__dict__.copy()
        del state['udp_socket']
        del state['message_queue']
        return state

    def __setstate__(self, state):
        """
        this will load the state of the pickle object
        Copy the object's dictionary
        update non-pickleable attributes like sockets
        :return:
        """
        self.__dict__.update(state)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.message_queue = queue.Queue()
        self.udp_socket.bind((self.user_ip_addr, self.UDP_PORT))

    def increment_request_number(self) -> str:
        """
        Increment the request number by 1 and return the updated number.
        SERVER is prefix of the request number.
        """
        self.request_number += 1
        return f"SERVER-{self.request_number}"

    def handle_connection(self, target_address):
        """
        Server will create a new TCP connection whenever this function is called and return a socket.socket() obj
        :param target_address:
        :return:
        """
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect(target_address)
            print(f"Connected to {target_address}")
            # A tcp listener will be called and run in back ground,sadly this is not closed gracefully
            threading.Thread(target=self.tcp_listener, args=(tcp_socket,)).start()
            return tcp_socket

        except Exception as e:
            print(f"Socket closed by the client")

    def tcp_listener(self, tcp_lisner_socket: socket.socket):
        """
        This will keep running for given socket and put received message in the message queue
        :param tcp_lisner_socket: tcp socket
        :return:
        """
        try:
            while True:
                data = tcp_lisner_socket.recv(1024 * 4)
                try:
                    # check if the data is pickleable
                    received_obj = pickle.loads(data)
                    print(f"Received message: '{received_obj}' from {tcp_lisner_socket.getpeername()}")
                    self.message_queue.put((False, received_obj, tcp_lisner_socket.getpeername()))

                except pickle.UnpicklingError:
                    # If unpickling fails, treat data as a plain string
                    decoded_data = data.decode()
                    print(f"Received message: '{decoded_data}' from {tcp_lisner_socket.getpeername()}")
                    self.message_queue.put((False, decoded_data, tcp_lisner_socket.getpeername()))
        except Exception as e:
            print(f"socket closed")
        finally:
            tcp_lisner_socket.close()

    def udp_listener(self):
        """
        Listen for incoming UDP messages and put objects into the message queue.
        """
        print("UDP listener started...")
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                if data:
                    try:
                        # Attempt to unpickle the received data
                        received_obj = pickle.loads(data)
                        print(f"Received object: {received_obj} from {addr}")
                        self.message_queue.put((True, received_obj, addr))

                    except pickle.UnpicklingError:
                        # If unpickling fails, treat data as a plain string
                        decoded_data = data.decode('utf-8')
                        print(f"Received message: '{decoded_data}' from {addr}")
                        self.message_queue.put((True, decoded_data, addr))
                    except Exception as e:
                        print(f"Error processing received data from {addr}: {e}")
                        continue

            except Exception as e:
                print(f"Listener encountered an error: {e}")
                break

    def process_messages(self):
        """
        Process messages from the queue (both UDP and TCP).
        """
        while True:
            if not self.message_queue.empty():
                save_with_pickle(self)
                flag, received_message, addr = self.message_queue.get()
                port = "UDP" if flag else "TCP"
                print(f"Processed {port} message from {addr}: {received_message.to_string()}")
                threading.Thread(target=self.command_handler, args=(received_message, addr)).start()

    def command_handler(self, message, addr):
        log.add("Receive", f"{message.to_string()} from {addr}")
        if message.Label == "REGISTER":
            # Check if the message is an instance of User (subclass of BaseUser)
            if isinstance(message, User):
                if message.Name in self.registed_clients:
                    temp_user: User = self.registed_clients[message.Name]
                    response_message = f"REGISTER-DENIED#{temp_user.RQ_number}#Duplicated_User"
                    self.udp_socket.sendto(response_message.encode(), addr)
                    log.add("Send[UDP]", f"{response_message} to {addr}")
                else:
                    self.registed_clients[message.Name] = message
                    response_message = f"REGISTERED#{message.RQ_number}#User_Registered"
                    self.udp_socket.sendto(response_message.encode(), addr)
                    log.add("Send[UDP]", f"{response_message} to {addr}")
            else:
                print("Received message is not a valid User object.")

        elif message.Label == "DE-REGISTER":
            # Check if the message is an instance of User (subclass of BaseUser)
            if isinstance(message, Deregister):
                if message.Name in self.registed_clients.keys():
                    if addr == self.registed_clients[message.Name].UDP_address:
                        temp_user: User = self.registed_clients.pop(message.Name)
                        response_message = f"DE-REGISTERED--Success!#{temp_user.RQ_number}#{temp_user.Name}"
                        self.udp_socket.sendto(response_message.encode(), addr)
                        log.add("Send[UDP]", f"{response_message} to {addr}")

                else:
                    deregister: Deregister = message
                    response_message = f"DE-REGISTERED--Failed#{deregister.RQ_number}#{deregister.Name}#Not Registed"
                    self.udp_socket.sendto(response_message.encode(), addr)
                    log.add("Send[UDP]", f"{response_message} to {addr}")
            else:
                print("Received message is not a valid User object.")

        elif message.Label == "LOOKING_FOR":
            if isinstance(message, Looking_for):
                if message.Name in self.registed_clients.keys():
                    if self.registed_clients[message.Name].UDP_address == addr:
                        if message.Name + message.Item_Name in self.server_dict:
                            ...
                        else:
                            rq = self.increment_request_number()
                            response_message = f"SEARCH#{rq}#{message.Item_Name}#{message.Item_Description}"
                            temp_search = Search.build_from_string(response_message)
                            self.LS_look_up[message] = temp_search
                            for keys, value in self.registed_clients.items():
                                if keys != message.Name:
                                    self.udp_socket.sendto(response_message.encode(), value.UDP_address)
                                    log.add("Send[UDP]", f"{response_message} to {value.UDP_address}")

                            # self.server_dict: Dict[Search, Pairs] = {}
                            # self.LS_look_up: Dict[Looking_for, Search] = {}
                            self.server_dict[temp_search] = Pairs()
                            self.server_dict[temp_search].buyer = self.registed_clients[message.Name]
                            self.server_dict[temp_search].search_record = temp_search
                            self.server_dict[temp_search].looking_for_record = message
                            # start a timer in the thread
                            save_with_pickle(self)
                            threading.Thread(target=self.select_offer, args=(self.server_dict[temp_search],)).start()

        elif message.Label == "OFFER":
            if isinstance(message, Offer):
                if message.Name in self.registed_clients:
                    if self.registed_clients[message.Name].UDP_address == addr:
                        for key, value in self.server_dict.items():
                            if message.RQ_number == key.RQ_number:
                                if time.time() - value.releasing_time >= waiting_time:
                                    ...
                                    print(f"Ignored")
                                    # ignore
                                else:
                                    if message.Name in value.offers:
                                        ...
                                        print(f"Duplicated offer received:{message.to_string()}")
                                        # ignore duplicated offers
                                    else:
                                        # add to list if not duplicated
                                        value.offers.append(message)


        elif message.Label == "ACCEPT":
            # Check if the message is an instance of User (subclass of BaseUser)
            if isinstance(message, Accept):
                for key, value in self.server_dict.items():
                    if key.RQ_number == message.RQ_number and key.Item_Name == message.Item_Name:
                        value.seller_response = True
                        response_message = f"RESERVE#{value.offer.RQ_number}#{value.offer.Item_Name}#{value.deal_price}"
                        self.udp_socket.sendto(response_message.encode(), value.seller.UDP_address)
                        log.add("Send[UDP]", f"{response_message} to {value.seller.UDP_address}")
                        # found
                        response_message = (
                            f"FOUND#{value.looking_for_record.RQ_number}#{value.looking_for_record.Item_Name}#"
                            f"{value.deal_price}")
                        self.udp_socket.sendto(response_message.encode(), value.buyer.UDP_address)
                        log.add("Send", f"{response_message} to {value.buyer.UDP_address}")
                        break
        elif message.Label == "REFUSE":
            # Check if the message is an instance of User (subclass of BaseUser)
            if isinstance(message, Refuse):
                for key, value in self.server_dict.items():
                    if key.RQ_number == message.RQ_number and key.Item_Name == message.Item_Name:
                        value.seller_response = False
                        value.buyer_response = False
                        response_message = (
                            f"NOT_FOUND#{value.looking_for_record.RQ_number}#{value.looking_for_record.Item_Name}#"
                            f"{value.deal_price}")
                        self.udp_socket.sendto(response_message.encode(), value.buyer.UDP_address)
                        log.add("Send[UDP]", f"{response_message} to {value.buyer.UDP_address}")
                        break


        elif message.Label == "CANCEL":
            # Check if the message is an instance of User (subclass of BaseUser)
            if isinstance(message, Cancel):
                for key, value in self.LS_look_up.items():
                    if key.RQ_number == message.RQ_number and key.Item_Name == message.Item_Name:
                        for it_key, it_value in self.server_dict.items():
                            if value.RQ_number == it_key.RQ_number:
                                it_value.buyer_response = False
                                response_message = (
                                    f"{message.Label}#{it_value.search_record.RQ_number}#"
                                    f"{it_value.search_record.Item_Name}#{message.Price}")
                                self.udp_socket.sendto(response_message.encode(), it_value.seller.UDP_address)
                                log.add("Send[UDP]", f"{response_message} to {it_value.seller.UDP_address}")

                        # ignore if buyer cancle it

        elif message.Label == "BUY":
            # Check if the message is an instance of User (subclass of BaseUser)
            if isinstance(message, Buy):
                print("isinstance")
                for key, value in self.LS_look_up.items():
                    if key.RQ_number == message.RQ_number and key.Item_Name == message.Item_Name:
                        for it_key, it_value in self.server_dict.items():
                            if it_key.RQ_number == value.RQ_number:
                                it_value.buyer_response = True
                                if it_value.seller_response and it_value.buyer_response:
                                    response_message = f"TCP_establish#{it_value.seller}#{it_value.seller.TCP_address}"
                                    self.udp_socket.sendto(response_message.encode(), it_value.seller.UDP_address)
                                    log.add("Send", f"{response_message} to {it_value.seller.UDP_address}")
                                    response_message = f"TCP_establish#{it_value.buyer}#{it_value.buyer.TCP_address}"
                                    self.udp_socket.sendto(response_message.encode(), it_value.buyer.UDP_address)
                                    log.add("Send", f"{response_message} to {it_value.buyer.UDP_address}")
                                    it_value.buyer_tcp_connection = self.handle_connection(it_value.buyer.TCP_address)
                                    it_value.seller_tcp_connection = self.handle_connection(it_value.seller.TCP_address)
                                    rq = self.increment_request_number()
                                    self.tcp_pairs[rq] = it_value
                                    ResponseMessage = (f"INFORM_Req#{rq}#"
                                                       f"{it_value.looking_for_record.Item_Name}#"
                                                       f"{it_value.deal_price}")
                                    self.tcp_pairs[rq].seller_tcp_connection.sendall(ResponseMessage.encode())
                                    log.add("Send[TCP]", f"{ResponseMessage} to {it_value.seller.TCP_address}")
                                    self.tcp_pairs[rq].buyer_tcp_connection.sendall(ResponseMessage.encode())
                                    log.add("Send[TCP]", f"{ResponseMessage} to {it_value.buyer.TCP_address}")
                        break

        elif message.Label == "INFORM_Res":
            # Check if the message is an instance of User (subclass of BaseUser)
            if isinstance(message, INFORM_Res):
                for key, value in self.tcp_pairs.items():
                    if key == message.RQ_number:
                        if message.Name == value.buyer.Name:
                            value.buyer_Finalizing = True
                            value.buyer_info = message
                        elif message.Name == value.seller.Name:
                            value.seller_Finalizing = True
                            value.seller_info = message
                        if value.seller_Finalizing == True and value.buyer_Finalizing == True:
                            # flip a coin
                            p = random.uniform(0, 10)
                            threading.Thread(target=self.flip_it, args=(p / 10 < 0.1, value)).start()
                            break
                        else:
                            break

    def flip_it(self, p: bool, value: Pairs):
        if p:
            try:
                ResponseMessage = (f"CANCEL#{value.buyer_info.RQ_number}#"
                                   f"{value.buyer_info.RQ_number}#"
                                   f"Credit info is not correct")
                log.add("Send[TCP]", f"{ResponseMessage} to {value.seller_tcp_connection.getpeername()}")
                log.add("Send[TCP]", f"{ResponseMessage} to {value.buyer_tcp_connection.getpeername()}")
                value.seller_tcp_connection.sendall(ResponseMessage.encode())
                value.buyer_tcp_connection.sendall(ResponseMessage.encode())
            except Exception as e:
                print(f"Error during communication: {e}")
            finally:
                try:
                    value.seller_tcp_connection.shutdown(socket.SHUT_WR)
                    value.seller_tcp_connection.close()
                except Exception as e:
                    print(f"Error closing seller connection: {e}")

                try:
                    value.buyer_tcp_connection.shutdown(socket.SHUT_WR)
                    value.buyer_tcp_connection.close()
                except Exception as e:
                    print(f"Error closing buyer connection: {e}")
        else:
            value.transaction_fee = value.deal_price * 0.1
            value.credit_amount = value.deal_price * 0.9
            self.profit += value.transaction_fee

            ResponseMessage = (f"Shipping_Info#{value.buyer_info.RQ_number}#"
                               f"{value.buyer_info.Name}#"
                               f"{value.buyer_info.Address}")
            value.seller_tcp_connection.sendall(ResponseMessage.encode())
            log.add("Send[TCP]", f"{ResponseMessage} to {value.seller_tcp_connection.getpeername()}")
            try:
                ResponseMessage = (f"Credit_Card_Info#{value.buyer_info.RQ_number}#"
                                   f"{value.buyer_info.Name}#"
                                   f"credit amount:{value.credit_amount} "
                                   f"transaction fee:{value.transaction_fee}")
                value.buyer_tcp_connection.sendall(ResponseMessage.encode())
                log.add("Send[TCP]", f"{ResponseMessage} to {value.buyer_tcp_connection.getpeername()}")
            except Exception as e:
                print(f"Error during communication: {e}")
            finally:
                try:
                    value.buyer_tcp_connection.shutdown(socket.SHUT_WR)
                    value.buyer_tcp_connection.close()
                except Exception as e:
                    print(f"Error closing seller connection: {e}")

    def select_offer(self, P: Pairs):

        while time.time() - P.releasing_time < waiting_time:
            if len(P.offers) == len(self.registed_clients) - 1:
                break
            else:
                ...
            # self.server_dict: Dict[Search, Pairs] = {}
            # self.LS_look_up: Dict[Looking_for, Search] = {}
        Max_price = P.looking_for_record.Max_Price
        offer_price = sys.float_info.max
        offer = Offer()
        if len(P.offers) == 0:
            ...
            # no offers
            response_message = f"NOT_AVAILABLE#{P.looking_for_record.RQ_number}#{P.looking_for_record.Item_Name}#{P.looking_for_record.Max_Price} "
            self.udp_socket.sendto(response_message.encode(), P.buyer.UDP_address)
            log.add("Send[UDP]", f"{response_message} to {P.buyer.UDP_address}")
        else:
            for it in P.offers:
                if it.Price < offer_price:
                    offer_price = it.Price
                    offer = it

            P.offer = offer
            if offer_price <= Max_price:
                ...
                # reserve
                response_message = f"RESERVE#{offer.RQ_number}#{offer.Item_Name}#{offer.Price}"
                P.deal_price = offer_price
                P.seller = self.registed_clients[offer.Name]
                P.seller_response = True
                self.udp_socket.sendto(response_message.encode(), P.seller.UDP_address)
                log.add("Send[UDP]", f"{response_message} to {P.seller.UDP_address}")
                # found
                response_message = f"FOUND#{P.looking_for_record.RQ_number}#{P.looking_for_record.Item_Name}#{P.deal_price}"
                self.udp_socket.sendto(response_message.encode(), P.buyer.UDP_address)
                log.add("Send[UDP]", f"{response_message} to {P.buyer.UDP_address}")
            else:
                ...
                # negotiate
                response_message = f"NEGOTIATE#{offer.RQ_number}#{offer.Item_Name}#{Max_price}"
                P.deal_price = Max_price
                P.seller = self.registed_clients[offer.Name]
                self.udp_socket.sendto(response_message.encode(), P.seller.UDP_address)
                log.add("Send[UDP]", f"{response_message} to {P.seller.UDP_address}")


# def handle_exit_signal(ser: Server, signal, frame):
#     # Log the time when Ctrl+C is pressed
#     if ser.server_dict is None:
#         ...
#     else:
#         ser.server_down = time.time()
#     sys.exit(0)


# Example of running the server
if __name__ == "__main__":

    # signal.signal(signal.SIGINT, handle_exit_signal)
    server = load_with_pickle("log.txt")
    if server.server_dict is None:
        ...
    else:
        for key, value in server.server_dict.items():
            if time.time() - value.releasing_time < waiting_time:
                threading.Thread(target=server.select_offer, args=(value,)).start()
            # elif time.time() - (value.releasing_time + 120) + (
            #         server.server_down - value.releasing_time) < waiting_time:
            #     threading.Thread(target=server.select_offer, args=(value,)).start()

    log = Log(True)
    # Start the TCP and UDP listeners in separate threads
    # tcp_thread = threading.Thread(target=server.tcp_listener, daemon=True)
    udp_thread = threading.Thread(target=server.udp_listener, daemon=True)
    message_processing_thread = threading.Thread(target=server.process_messages, daemon=True)

    # tcp_thread.start()
    udp_thread.start()
    message_processing_thread.start()

    # Keep the main thread running
    while True:
        pass
