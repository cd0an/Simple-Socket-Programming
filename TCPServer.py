from socket import *
import json
import threading

# Define the 4 users with their passwords and initial balance
users = {
    "A": {"password": "A", "balance": 10, "txs": []},
    "B": {"password": "B", "balance": 10, "txs": []},
    "C": {"password": "C", "balance": 10, "txs": []},
    "D": {"password": "D", "balance": 10, "txs": []},
    "X": {"password": "X", "balance": 0, "txs": []},
}

# To ensure thread safety for data sharing
userLock = threading.Lock()

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(5)

print("The server is ready to receive")

def handleClient(connectionSocket, addr):
    print(f"Received connection from {addr}") # Message

    # Receive login information from client
    information = connectionSocket.recv(1024).decode()
    print(f"Received an authentication request from user {information}") # Message

    username, password = information.split(',')

    # Check if the username exists and password matches
    if username in users and password == users[username]["password"]:
        print(f"User {username} is authenticated.") # Message

        # If authentication is successful
        response = {
            "status": "Authenticated",
            "balance": users[username]["balance"],
            "txs": users[username]["txs"]
        }
        connectionSocket.send(json.dumps(response).encode())

        while True:
            request = connectionSocket.recv(1024).decode()

            # Option 1: To handle the transaction
            if request == "MAKE_TRANSACTION":
                transaction = connectionSocket.recv(1024).decode()
                print(f"Received a transaction from user {username}: {transaction}") # Message

                txData = json.loads(transaction)

                payer = txData['payer']
                amount = float(txData['PayerAmount'])
                payee1 = txData['payee1']
                amount1 = float(txData['Amount1'])
                payee2 = txData['payee2']
                amount2 = float(txData['Amount2'])

                # Checks the Payer's current balance
                with userLock:
                    if users[payer]["balance"] >= amount:
                        print(f"Confirmed a transaction for user {payer}.") # Message

                        # Withdraw the transferring amount from the Payer's balance and update the Payee(s) balance(s)
                        users[payer]["balance"] -= amount # Decrease the Payer's balance
                        users[payee1]["balance"] += amount1 # Increase Payee1's balance
                        if payee2 != "None":
                            users[payee2]["balance"] += amount2 # Increase Payee2's balance

                        # Create unique transaction ID based on payer
                        payer_initial = {"A": 100, "B": 200, "C": 300, "D": 400}
                        tx_id = -1
                        if payer in payer_initial:
                            tx_id = payer_initial[payer] + sum(1 for tx in users[payer]["txs"] if tx["payer"] == payer)

                        # Store confirmed transaction
                        txData["id"] = str(tx_id)
                        txData["status"] = "confirmed"
                        users[payer]["txs"].append(txData)

                        # Also store transaction in the payees' history
                        users[payee1]["txs"].append(txData)
                        if payee2 != "None":
                            users[payee2]["txs"].append(txData)

                        # Deduct 10% fee and send to "X"
                        fee = round(amount * 0.1, 2)
                        users["X"]["balance"] += fee

                        # Store a TX indicating that Payer has paid 10% of the transfer amount to X
                        feeTx = {
                            "id": str(500 + len(users[payer]["txs"])),
                            "payer": payer,
                            "payee1": "X",
                            "Amount1": fee,
                            "payee2": "None",
                            "Amount2": 0,
                            "status": "confirmed",
                        }
                        users["X"]["txs"].append(feeTx)

                        # Respond to client with updated balance
                        response = {
                            "status": "Confirmed",
                            "balance": users[payer]["balance"],
                        }
                        connectionSocket.send(json.dumps(response).encode())
                        print(f"Send the list of transactions to user {payer}.") # Message

                    # If insufficient balance
                    else:
                        print(f"Transaction rejected for user {payer}.") # Message
                        # Reject transaction
                        response = {
                            "status": "Rejected",
                            "balance": users[payer]["balance"],
                        }
                        connectionSocket.send(json.dumps(response).encode())

            # Option 2: Fetch the list of transactions
            elif request == "GET_TRANSACTIONS":
                # Return the list of confirmed transactions for the user Payer or Payees
                if username in users and "txs" in users[username]:
                    txs = users[username]["txs"]
                else:
                    txs = []

                response = {
                    "status": "success",
                    "txs": txs,
                }
                print(f"Send the list of transactions to user {username}.") # Message
                connectionSocket.send(json.dumps(response).encode())

            # Option 3: Fetch X's balance
            elif request == "GET_X_BALANCE":
                # Get X current balance
                x_balance = users["X"]["balance"]

                response = {
                    "status": "success",
                    "balance": x_balance,
                }
                print(f"Send X's balance to user {username}.") # Message
                connectionSocket.send(json.dumps(response).encode())

            else:
                response = {
                    "status": "Error",
                    "message": "Invalid request"
                }
                print(f"Unable to send the list of transactions and X's balance to user {username}.")
                connectionSocket.send(json.dumps(response).encode())

    else:
        print(f"Authentication failed for user {username}.") # Message
        response = {
            "status": "Authentication failed",
        }
        connectionSocket.send(json.dumps(response).encode())

    connectionSocket.close()

while True:
    connectionSocket, addr = serverSocket.accept()
    clientThread = threading.Thread(target=handleClient, args=(connectionSocket, addr))
    clientThread.start()






