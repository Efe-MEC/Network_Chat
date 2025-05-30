import socket
import json
import os
import time
import pyDes
import base64
from datetime import datetime

ip_file = "ips.json"
log_file = "logs.json"

p = 19
g = 2

socket_number = 6001

def load_users():
	if os.path.exists(ip_file):
		with open(ip_file, "r") as f:
			ips = json.load(f)
	else:
		ips = {}
	now = time.time()
	for ip, data in ips.items():
		if now - data["time"] <= 10:
			print(f"{data['name']} (Online)")
		elif now - data["time"] <= 900:
			print(f"{data['name']} (Away)")


def save_log(op_type, chat_type, message, ip):

	time_now = time.time()

	logs = {
		"time": time_now,
		"ip": ip,
		"op_type": op_type,
		"chat_type": chat_type,
		"message": message,
	}

	with open(log_file, "a") as f:
		f.write(json.dumps(logs) + "\n")

	print(f"Log saved.")


def secure_chat(ip):

	print(f"Secure chat selected.")

	while True:
		private_nbr = input("Please enter the encrypted key number (must be digits only):  \n")

		if private_nbr.isdigit():
			break
		else:
			print("Invalid input. Please enter digits only.")

	pub_nbr = (g ** int(private_nbr)) % p

	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((ip, socket_number))

		message_key = {
    	"key": pub_nbr,
    	}

		sock.send(json.dumps(message_key).encode())

		print(f"My public key sent: {pub_nbr}, waiting for response key...")
		save_log("SENT", "Secure", {"key": pub_nbr}, ip)

		data = sock.recv(1024).decode()

		peer_public_key = int(json.loads(data)["key"])
		print(f"Peer public key received: {peer_public_key}")

		save_log("RECEIVED", "Secure", {"key": peer_public_key}, ip)

		peer_common_key = (peer_public_key ** int(private_nbr)) % p
		print(f"Peer common key calculated: {peer_common_key}")

		while True:
			message = input("Please enter your message:\n")

			if message.isascii():
				break
			else:
				print("Invalid input. ASCII characters valid only.")

		encrypted_message = pyDes.triple_des(str(peer_common_key).ljust(24)).encrypt(message, padmode=2)
		encbase64 = base64.b64encode(encrypted_message).decode()

		enc_message = {
		"encrypted_message": encbase64,
		}

		print(f"Encrypted message: {encbase64}")
		sock.send(json.dumps(enc_message).encode())
		print(f"Encrypted message sent.")

		save_log("SENT", "Secure", {"encrypted_message": encbase64}, ip)

		sock.close()
		print(f"Connection closed.")


	except socket.error as e:
		print(f"Connection error: {e}")
		return


def unsecure_chat(ip):
	
	print(f"Unsecure chat selected.")
	message_input = input("Please enter your message:\n")

	message = {
	"unencrypted_message": message_input,
	}

	try:
		
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((ip, socket_number))

		sock.send(json.dumps(message).encode())

		sock.close()
	
		print(f"Unencrypted message sent.")

		save_log("SENT", "Unsecure", {"unencrypted_message": message_input}, ip)

	except socket.error as e:
		print(f"Connection error: {e}")


def load_chat():

	in_username = input("Please enter the selected username: \n")
	sec_key = input("Please enter the chat type code: \nSecure Chat (1)\nUnsecure Chat (2)\n")

	if os.path.exists(ip_file):
		with open(ip_file, "r") as f:
			ips = json.load(f)
	else:
		ips = {}

	for ip_address, data in ips.items():
		if data["name"] == in_username:
			ip = ip_address
			break
	else:
		print(f"Username {in_username} not found.")
		return

	if sec_key == "1":
		secure_chat(ip)
	elif sec_key == "2":
		unsecure_chat(ip)
	else:
		print("Invalid chat type code. Enter 1 or 2.")


def view_history():

	if os.path.exists(log_file):
		with open(log_file, "r") as f:
			lines = f.readlines()

		if lines:
			for line in lines:
				data = json.loads(line)
				dt_obj = datetime.fromtimestamp(float(data["time"]))
				time_form = dt_obj.strftime("%Y-%m-%d %H:%M:%S") + f":{dt_obj.microsecond // 1000:03d}"
				print(f"Time: {time_form}")
				print(f"IP Address: {data['ip']}")
				print(f"Chat Type: {data['chat_type']}")
				print(f"Operation Type: {data['op_type']}")
				print(f"Message: {data['message']}\n")
		else:
			print("No logs found.")
	else:
		print("Log file does not exist.")


def main ():

	while True:

		op_code = input("Please enter the operation code:\nUsers (1)\nChat (2)\nHistory (3)\nExit (4)\n")

		if op_code == "1":
			load_users()
		elif op_code == "2":
			load_chat()
		elif op_code == "3":
			view_history()
		elif op_code == "4":
			print("Exiting...")
			break
		else:
			print("Invalid operation code. Enter 1, 2, 3 or 4.")

if __name__ == "__main__":
	main()