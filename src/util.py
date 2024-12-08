import pickle
import threading
import datetime
from dataclasses import fields
from typing import Tuple
import socket
import queue


class BaseUser:
    def __init__(self, Label: str = "Unknown"):
        self.Label: str = Label  # Default label for registration

    def print_basic_user_info(self) -> None:
        print(f"Label: {self.Label}")


class Deregister(BaseUser):
    def __init__(self, RQ_number: int = 0, Label: str = "Unknown", User_Name: str = "Unnamed"):
        """
        deregister constructor
        :param RQ_number: request number
        :param Label: deregister
        :param User_Name: deregister username
        """
        super().__init__(Label)
        self.RQ_number: int = RQ_number
        self.Name: str = User_Name

    def print_extended_user_info(self) -> None:
        """
        print info function in deregister class
        :return:
        """
        self.print_basic_user_info()
        print(f"RQ_number: {self.RQ_number}")
        print(f"User_Name: {self.Name}")

    def to_string(self):
        """
        to string function in deregister class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Name}"

    @classmethod
    def build_from_string(cls, input_str: str, rq):
        """
        syntax: DE-REGISTER#RQ#Name
        input_str: DE-REGISTER#Name
        RQ: autogenerate
        :param input_str:
        :param rq:
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 2:
            raise ValueError("Invalid string format. Expected 'Label#RQ_number#User_Name'")

        try:
            # Create and return an instance of Deregister initialized with parsed values
            label = parts[0].strip()
            rq_number = int(rq)
            user_name = parts[1].strip()
            return cls(rq_number, label, user_name)  # Return a new instance of Deregister
        except ValueError as e:
            raise ValueError("Error parsing the input string: " + str(e))


class User(BaseUser):
    def __init__(self,
                 RQ_number: str = "",
                 Name: str = "Unknown",
                 IP: str = "127.0.0.1",
                 UDP_Socket: int = 0,
                 TCP_Socket: int = 0,
                 Label: str = "REGISTER"):
        """
        Register User
        :param RQ_number: request number
        :param Name: Register user
        :param IP: IP adress
        :param UDP_Socket: random port
        :param TCP_Socket: random port
        :param Label: REGISTER
        """
        super().__init__(Label)
        self.RQ_number = RQ_number if RQ_number else None
        self.Name = Name
        self.IP: str = IP
        self.UDP_Socket: int = UDP_Socket
        self.TCP_Socket: int = TCP_Socket
        self.UDP_address: Tuple[str, int] = (self.IP, self.UDP_Socket)
        self.TCP_address: Tuple[str, int] = (self.IP, self.TCP_Socket)
        self._count: int = 0
        self.registered_once = False
        self.hash = ""

    def to_string(self):
        """
        to string function from register class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Name}#{self.IP}#{self.UDP_Socket}#{self.TCP_Socket}"

    def print_user(self) -> None:
        """
        print info function from register class
        :return:
        """
        self.print_basic_user_info()  # Call the method from BaseUser to print basic info
        print(f"IP: {self.IP}")
        print(f"UDP_Socket: {self.UDP_Socket}")
        print(f"TCP_Socket: {self.TCP_Socket}")
        print(f"UDP_address: {self.UDP_address}")
        print(f"TCP_address: {self.TCP_address}")

    def parse_input(self, user_input: str, user_ip: str, rq, UDP_address, TCP_address) -> bool:
        """
        syntax: REGISTER#RQ#Name#IP Address#UDP Socket#TCP Socket
        user_input: REGISTER#Name
        user_ip: IP Address
        :param user_input:
        :param user_ip:
        :param rq: request number
        :param UDP_address: random port
        :param TCP_address:random port
        :return:
        """
        fields = user_input.split('#')
        if self.registered_once:
            print("Can't register twice")
            return False
        else:
            if len(fields) == 2:
                self.Label = fields[0].strip()
                self.RQ_number = rq
                self.Name = fields[1].strip()
                self.IP = user_ip
                self.UDP_Socket = UDP_address[1]
                self.TCP_Socket = TCP_address[1]
                self.UDP_address = UDP_address
                self.TCP_address = TCP_address
                self.registered_once = True  # Mark as registered
                self.hash = self.__hash__()  # Generate hash
                return True
            else:
                print("Error: Invalid input format.")
                return False


class Looking_for(BaseUser):
    def __init__(self,
                 RQ_number: str = "",
                 Name: str = "Unknown",
                 Item_Name: str = "Unknown",
                 Item_Description: str = "No description",
                 Max_Price: float = 0.0,
                 Label: str = "LOOKING_FOR"):
        """
        Looking for function
        :param RQ_number: request number
        :param Name: user name
        :param Item_Name: item name
        :param Item_Description: item description
        :param Max_Price: buyer price
        :param Label: LOOKING_FOR
        """
        super().__init__(Label)

        # Initialize attributes specific to Looking_for
        self.RQ_number = RQ_number
        self.Name = Name
        self.Item_Name = Item_Name
        self.Item_Description = Item_Description
        self.Max_Price = Max_Price

    def to_string(self):
        """
        to string function from looking for class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Name}#{self.Item_Name}#{self.Item_Description}#{self.Max_Price}"

    def print_extended_info(self):
        """
        print function from looking for class
        :return:
        """
        self.print_basic_user_info()
        print(f"Request Number: {self.RQ_number}")
        print(f"Item Name: {self.Item_Name}")
        print(f"Item Description: {self.Item_Description}")
        print(f"Max Price: {self.Max_Price}")

    @classmethod
    def build_from_string(cls, input_str: str, r):
        """
        syntax: LOOKING_FOR#RQ#Name#Item_Name#Item_Description#Max_Price
        :param input_str: LOOKING_FOR#Name#Item_Name#Item_Description#Max_Price
        :param r: request number generate buy the system
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 5:
            raise ValueError(
                "Invalid string format. Expected 'Label#RQ_number#Name#Item_Name#Item_Description#Max_Price'")

        try:

            label = parts[0].strip()
            rq_number = str(r)
            name = parts[1].strip()
            item_name = parts[2].strip()
            item_description = parts[3].strip()
            max_price = float(parts[4].strip())

            return cls(rq_number, name, item_name, item_description, max_price, label)
        except ValueError as e:
            raise ValueError("Error parsing the input string: " + str(e))


class Offer(BaseUser):
    def __init__(self,
                 RQ_number: str = "",
                 Name: str = "Unknown",
                 Item_Name: str = "Unknown",
                 Price: float = 0.0,
                 Label: str = "OFFER"):
        """
        Offer function
        :param RQ_number: request number
        :param Name:  user name
        :param Item_Name: item name
        :param Price: seller price
        :param Label: OFFER
        """
        super().__init__(Label)

        self.RQ_number = RQ_number
        self.Name = Name
        self.Item_Name = Item_Name
        self.Price = Price

    def to_string(self):
        """
        to string function from offer class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Name}#{self.Item_Name}#{self.Price}"

    def print_extended_info(self) -> None:
        """
        Print function from offer class
        :return:
        """
        self.print_basic_user_info()  # Prints Label from BaseUser
        print(f"RQ_number: {self.RQ_number}")
        print(f"Name: {self.Name}")
        print(f"Item_Name: {self.Item_Name}")
        print(f"Max_Price: {self.Price}")

    @classmethod
    def build_from_string(cls, input_str: str):
        """
        syntax: OFFER#RQ#Name#Item_Name#Price
        :param input_str: OFFER#RQ#Name#Item_Name#Price
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 5:
            raise ValueError("Invalid string format. Expected 'RQ_number#Name#Item_Name#Max_Price'")
        try:

            rq_number = str(parts[1].strip())
            name = parts[2].strip()
            item_name = parts[3].strip()
            max_price = float(parts[4].strip())

            return cls(rq_number, name, item_name, max_price)
        except ValueError as e:
            raise ValueError("Error parsing the input string: " + str(e))


class Search(BaseUser):
    def __init__(self,
                 RQ_number: str = "",
                 Item_Name: str = "Unknown",
                 Item_Description: str = "No description",
                 Label: str = "SEARCH"):
        """
        Search function
        :param RQ_number: request number
        :param Item_Name: item name
        :param Item_Description: item description
        :param Label: SEARCH
        """
        super().__init__(Label)

        self.RQ_number = RQ_number
        self.Item_Name = Item_Name
        self.Item_Description = Item_Description

    def to_string(self):
        """
        to string function in search class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Item_Name}#{self.Item_Description}"

    def print_extended_info(self) -> None:
        """
        print function in search class
        :return:
        """
        self.print_basic_user_info()  # Prints Label from BaseUser
        print(f"RQ_number: {self.RQ_number}")
        print(f"Item_Name: {self.Item_Name}")
        print(f"Item_Description: {self.Item_Description}")

    @classmethod
    def build_from_string(cls, input_str: str):
        """
        syntax: SEARCH#RQ#Item_Name#Item_Description
        :param input_str: SEARCH#RQ#Item_Name#Item_Description
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 4:
            raise ValueError("Invalid string format. Expected 'RQ_number#Item_Name#Item_Description'")
        try:

            rq_number = str(parts[1].strip())
            item_name = parts[2].strip()
            item_description = parts[3].strip()

            return cls(rq_number, item_name, item_description)
        except ValueError as e:
            raise ValueError("Error parsing the input string: " + str(e))


class Accept(BaseUser):
    def __init__(self,
                 Label: str = "ACCEPT",
                 RQ_number: str = "",
                 Item_Name: str = "Unknown",
                 Max_Price: float = 0.0):
        """
        Accept function
        :param Label: ACCEPT
        :param RQ_number: request number
        :param Item_Name: item name
        :param Max_Price: price from buyer
        """
        super().__init__(Label)

        # Initialize attributes specific to Accept
        self.RQ_number = RQ_number
        self.Item_Name = Item_Name
        self.Max_Price = Max_Price

    def to_string(self):
        """
        to string function in accept class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Item_Name}#{self.Max_Price}"

    def print_extended_info(self) -> None:
        """
        Print function from accept class
        :return:
        """
        print(f"Label: {self.Label}")
        print(f"RQ_number: {self.RQ_number}")
        print(f"Item_Name: {self.Item_Name}")
        print(f"Max_Price: {self.Max_Price}")

    @classmethod
    def build_from_string(cls, input_str: str):
        """
        syntax: ACCEPT#RQ##Item_Name#Max_Price
        :param input_str: ACCEPT#RQ##Item_Name#Max_Price
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 4:
            raise ValueError("Invalid string format. Expected 'Label#RQ_number#Item_Name#Max_Price'")
        try:
            label = parts[0].strip()
            rq_number = parts[1].strip()
            item_name = parts[2].strip()
            max_price = float(parts[3].strip())

            return cls(label, rq_number, item_name, max_price)
        except ValueError as e:
            raise ValueError(f"Error parsing the input string: {e}")


class Refuse(BaseUser):
    def __init__(self,
                 Label: str = "REFUSE",
                 RQ_number: str = "",
                 Item_Name: str = "Unknown",
                 Max_Price: float = 0.0):
        """
        Refuse function
        :param Label: REFUSE
        :param RQ_number: request number
        :param Item_Name: item name
        :param Max_Price: price from buyer
        """
        super().__init__(Label)

        # Initialize attributes specific to Accept
        self.RQ_number = RQ_number
        self.Item_Name = Item_Name
        self.Max_Price = Max_Price

    def to_string(self):
        """
        to string function in refuse class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Item_Name}#{self.Max_Price}"

    def print_extended_info(self) -> None:
        """
        print function in refuse class
        :return:
        """
        print(f"Label: {self.Label}")
        print(f"RQ_number: {self.RQ_number}")
        print(f"Item_Name: {self.Item_Name}")
        print(f"Max_Price: {self.Max_Price}")

    @classmethod
    def build_from_string(cls, input_str: str):
        """
        syntax: REFUSE#RQ#Item_Name#Max_Price
        :param input_str: REFUSE#RQ#Item_Name#Max_Price
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 4:
            raise ValueError("Invalid string format. Expected 'Label#RQ_number#Item_Name#Max_Price'")
        try:
            label = parts[0].strip()
            rq_number = parts[1].strip()
            item_name = parts[2].strip()
            max_price = float(parts[3].strip())

            return cls(label, rq_number, item_name, max_price)
        except ValueError as e:
            raise ValueError(f"Error parsing the input string: {e}")


class Cancel(BaseUser):
    def __init__(self,
                 Label: str = "CANCEL",
                 RQ_number: str = "",
                 Item_Name: str = "Unknown",
                 Price: float = 0.0):
        """
        Cancel function
        :param Label: CANCEL
        :param RQ_number: request number
        :param Item_Name: item name
        :param Price: buyer price
        """
        super().__init__(Label)

        self.RQ_number = RQ_number
        self.Item_Name = Item_Name
        self.Price = Price

    def to_string(self):
        """
        to string function from cancel class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Item_Name}#{self.Price}"

    def print_extended_info(self) -> None:
        """
        print function from cancel class
        :return:
        """
        print(f"Label: {self.Label}")
        print(f"RQ_number: {self.RQ_number}")
        print(f"Item_Name: {self.Item_Name}")
        print(f"Price: {self.Price}")

    @classmethod
    def build_from_string(cls, input_str: str):
        """
        syntax: CANCEL#RQ#Item_Name#Price
        :param input_str: CANCEL#RQ#Item_Name#Price
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 4:
            raise ValueError("Invalid string format. Expected 'Label#RQ_number#Item_Name#Max_Price'")
        try:
            label = parts[0].strip()
            rq_number = parts[1].strip()
            item_name = parts[2].strip()
            Price = float(parts[3].strip())

            return cls(label, rq_number, item_name, Price)
        except ValueError as e:
            raise ValueError(f"Error parsing the input string: {e}")


class Buy(BaseUser):
    def __init__(self,
                 Label: str = "BUY",
                 RQ_number: str = "",
                 Item_Name: str = "Unknown",
                 Price: float = 0.0):
        """
        Buy function
        :param Label: BUY
        :param RQ_number: request number
        :param Item_Name: item name
        :param Price: price from seller
        """
        super().__init__(Label)

        self.RQ_number = RQ_number
        self.Item_Name = Item_Name
        self.Price = Price

    def to_string(self):
        """
        to string function from buy class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Item_Name}#{self.Price}"

    def print_extended_info(self) -> None:
        """
        print function from buy class
        :return:
        """
        print(f"Label: {self.Label}")
        print(f"RQ_number: {self.RQ_number}")
        print(f"Item_Name: {self.Item_Name}")
        print(f"Price: {self.Price}")

    @classmethod
    def build_from_string(cls, input_str: str):
        """
        syntax: BUY#RQ#Item_Name#Price
        :param input_str: BUY#RQ#Item_Name#Price
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 4:
            raise ValueError("Invalid string format. Expected 'Label#RQ_number#Item_Name#Max_Price'")
        try:
            label = parts[0].strip()
            rq_number = parts[1].strip()
            item_name = parts[2].strip()
            Price = float(parts[3].strip())

            return cls(label, rq_number, item_name, Price)
        except ValueError as e:
            raise ValueError(f"Error parsing the input string: {e}")


class INFORM_Res(BaseUser):
    def __init__(self,
                 Label: str = "INFORM_Res",
                 RQ_number: str = "",
                 Name: str = "Unknown",
                 CC_num: int = 0,
                 CC_expire_date: str = "",
                 Address: str = ""):
        """
        INFORM_Res function
        :param Label: INFORM_Res
        :param RQ_number: request number
        :param Name: user name
        :param CC_num: credit card number
        :param CC_expire_date: credit card expire code
        :param Address: buyer adress
        """

        super().__init__(Label)

        self.RQ_number = RQ_number
        self.Name = Name
        self.CC_num = CC_num
        self.CC_expire_date = CC_expire_date
        self.Address = Address

    def to_string(self):
        """
        to string function from INFORM_Res class
        :return:
        """
        return f"{self.Label}#{self.RQ_number}#{self.Name}#{self.CC_num}#{self.CC_expire_date}#{self.Address}"

    def print_extended_info(self) -> None:
        """
        print function from INFORM_Res class
        :return:
        """
        print(f"Label: {self.Label}")
        print(f"RQ_number: {self.RQ_number}")
        print(f"Name: {self.Name}")
        print(f"CC_num: {self.CC_num}")
        print(f"CC_expire_date: {self.CC_expire_date}")
        print(f"Address: {self.Address}")

    @classmethod
    def build_from_string(cls, input_str: str):
        """
        syntax: INFORM_Res#RQ#Name#CC#CC Exp_Date#Address
        :param input_str: INFORM_Res#RQ#Name#CC#CC Exp_Date#Address
        :return:
        """
        parts = input_str.split('#')
        if len(parts) != 6:
            raise ValueError("Invalid string format. Expected 'Label#RQ_number#Name#CC_num#CC_expire_date#Address'")
        try:
            label = parts[0].strip()
            rq_number = parts[1].strip()
            name = parts[2].strip()
            cc_num = int(parts[3].strip())
            cc_expire_date = parts[4].strip()
            address = parts[5].strip()

            return cls(label, rq_number, name, cc_num, cc_expire_date, address)
        except ValueError as e:
            raise ValueError(f"Error parsing the input string: {e}")


class SocketSender:
    def __init__(self, server_udp: tuple, user_ip_addr: str):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_udp = server_udp
        self.tcp_socket.bind((user_ip_addr, 0))
        self.udp_socket.bind((user_ip_addr, 0))
        self.udp_addr = self.udp_socket.getsockname()
        self.tcp_addr = self.tcp_socket.getsockname()
        self.listener_running = True
        self.connections = {}
        self.log: Log = None
        self.lock = threading.Lock()

    def tcp_listener(self):
        """Listen for incoming TCP connections and handle CLOSE commands."""
        self.tcp_socket.listen(5)

        while True:
            conn, addr = self.tcp_socket.accept()
            print(f"Connection established with {addr}")
            self.log.add("TCP[Connection", f"Connection established with {addr}")
            threading.Thread(target=self.handle_tcp_client, args=(conn, addr)).start()

    def handle_tcp_client(self, conn, addr):
        """Handle a single TCP client connection."""
        with conn:
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        print(f"Connection closed by {addr}")
                        self.log.add("Connection [closed]", f"Connection closed by {addr}")
                        break

                    message = data.decode()
                    print(f"Received TCP message: {message} from {addr}")
                    self.log.add("Receive[TCP]", f"{message} from {addr}")

                    if message.startswith("INFORM_Req"):
                        parts = message.split("#")
                        if len(parts) >= 2:
                            conn_key = parts[1].strip()
                            with self.lock:
                                self.connections[conn_key] = conn
                            print(f"Added connection with key {conn_key}")

                    elif message.startswith("Shipping_Info"):
                        parts = message.split("#")
                        if len(parts) >= 2:
                            conn_key = parts[1].strip()
                            with self.lock:
                                if conn_key in self.connections:
                                    to_close = self.connections.pop(conn_key)
                                    to_close.shutdown(socket.SHUT_WR)
                                    to_close.close()
                                    print(f"Connection {conn_key} closed and removed.")
                                else:
                                    print(f"Connection {conn_key} not found.")
                            break
                except Exception as e:
                    print(f"Error with connection {addr}: {e}")
                    break

    def udp_listener(self):
        while self.listener_running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                if data:
                    print(f"UDP-RECEIVE: {data.decode()}")
                    self.log.add("Receive[UDP]", f"{data.decode()} from {addr}")
                    try:
                        user = pickle.loads(data)
                        print(f"Received user object: {user}")
                    except pickle.UnpicklingError:
                        pass
            except socket.error as e:
                if not self.listener_running:
                    print("Listener has been stopped.")
                    break
                print(f"Socket error: {e}")

    def send_udp(self, message) -> None:
        try:

            if isinstance(message, str):
                self.udp_socket.sendto(message.encode(), self.server_udp)
            else:
                pickled_user = pickle.dumps(message)
                self.udp_socket.sendto(pickled_user, self.server_udp)
                self.log.add("Executed UDP Command:", f"{message.to_string()} to {self.server_udp}")

                print(f"UDP-SEND: {message.to_string()}")

        except Exception as e:

            print(f"Error occurred while sending/receiving UDP message: {e}")

    def send_tcp(self, message) -> None:
        try:

            if isinstance(message, str):
                ...
                # ignore
            else:
                pickled_user = pickle.dumps(message)
                self.connections[message.RQ_number].sendall(pickled_user)
                self.log.add("Executed TCP Command:", f"{message.to_string()} to server")
                print(f"TCP-SEND: {message.to_string()}")
        except Exception as e:

            print(f"Error occurred while sending/receiving TCP message: {e}")

    def start_listener(self):
        udp_listener_thread = threading.Thread(target=self.udp_listener, daemon=True)
        tcp_listener_thread = threading.Thread(target=self.tcp_listener, daemon=True)
        udp_listener_thread.start()
        tcp_listener_thread.start()
        print("UDP listener started in a separate thread")

    def stop(self):
        self.listener_running = False
        self.udp_socket.close()
        print("UDP listener stopped and socket closed.")


class Log:
    def __init__(self, type: bool, name=None, filename="command_log.txt", ):
        self.type = type
        self.logs = []
        self.filename = filename if type else str(name) + ".txt"
        self.lock = threading.Lock()

    def add(self, label, message):

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{label}] {message}"

        with self.lock:
            self.logs.append(log_entry)
            with open(self.filename, 'a') as file:
                file.write(log_entry + '\n')
                if self.type:
                    print(log_entry)

    def display_logs(self):

        for log in self.logs:
            print(log)
