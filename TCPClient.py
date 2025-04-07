from socket import *
import json

serverName = 'localhost'
serverPort = 12000

while True:
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))

    # Obtain the user information
    username = input("Enter username: ")
    password = input("Enter password: ")

    # Send information to the server
    information = f"{username},{password}"
    clientSocket.send(information.encode())

    # Receive authentication response
    response = clientSocket.recv(1024).decode()

    # Parse JSON response
    responseJson = json.loads(response)

    # Check if authentication is successful
    if responseJson["status"] == "Authenticated":
        # If yes, display the response and menu option
        userBalance = float(responseJson['balance'])
        userTxs = responseJson['txs']
        print(f"Authenticated. Your balance is {userBalance} BTC.")

        # Menu loop
        while True:
            print("\nMenu:")
            print("(1) Make a transaction")
            print("(2) Fetch the list of transactions from the server and display it.")
            print("(3) Fetch the X's balance from the server and display it.")
            print("(4) Quit the program.")

            choice = input("Enter your choice (1-4): ").strip()

            # Make a transaction
            if choice == "1":
                # Send the request to the server
                clientSocket.send("MAKE_TRANSACTION".encode())
                # Find the max TX ID where the user is the Payer
                payerTxs = [tx for tx in userTxs if tx["payer"] == username]
                if payerTxs:
                    maxTxsID = max(int(tx["id"]) for tx in payerTxs) + 1
                else:
                    maxTxsID = 100 if username == "A" else 200 if username == "B" else 300 if username == "C" else 400

                # Request transaction details
                amount = float(input("How much do you transfer? "))

                # 10% fee of each transaction made
                fee = amount * 0.1 # Apply the 10% fee
                netAmount = amount - fee # Minus fee from transferring amount

                # Choose Payee1
                payee_options = [p for p in ["A", "B", "C", "D"] if p != username]
                print(f"Who will be Payee1? Options: {', '.join(payee_options)}")
                payee1 = input("Enter Payee1: ").strip().upper()
                while payee1 not in payee_options:
                    print(f"Invalid option. Please try again.")
                    payee1 = input("Enter Payee1: ").strip().upper()

                # Amount of Payee1
                amount1 = float(input(f"How much will {payee1} receive? (<= {netAmount} BTC): "))
                while amount1 > netAmount:
                    print(f"{payee1} cannot receive more than {netAmount} BTC. Please input a smaller amount.")
                    amount1 = float(input(f"Enter a valid amount for {payee1}: "))

                # If Payee1 takes full transferring amount, skip Payee2
                if netAmount == amount1:
                    payee2, amount2 = "None", 0.0
                    print(f"Skip. Payee2 is not needed.")
                else:
                    # Payee2 takes remaining amount
                    other_payees_options = [p for p in payee_options if p != payee1]
                    print(f"Who will be Payee2? Options: {', '.join(other_payees_options)}")
                    payee2 = input("Enter Payee2: ").strip().upper()
                    while payee2 not in other_payees_options:
                        print("Invalid option. Please try again.")
                        payee2 = input("Enter Payee2: ").strip().upper()
                    # Amount of Payee2
                    amount2 = round(netAmount - amount1, 2)  # Transferring amount minus 10% minus amount of Payee1
                    print(f"{payee2} will receive {amount2:.2f} BTC.")

                # Create transaction
                transaction = {
                    "id": str(maxTxsID),
                    "payer": username,
                    "PayerAmount": amount,
                    "payee1": payee1,
                    "Amount1": amount1,
                    "payee2": payee2,
                    "Amount2": amount2,
                    "status": "temporary",
                }

                # Send transaction to the sever
                clientSocket.send(json.dumps(transaction).encode())

                # Receive the response from the server
                response = clientSocket.recv(1024).decode()
                responseJson = json.loads(response)

                # If balance is sufficient, respond TX confirmed
                if responseJson["status"] == "Confirmed":
                    # Update user balance and confirm the transaction
                    userBalance = float(responseJson["balance"])

                    # Update the transaction status to confirmed
                    for tx in userTxs:
                        if tx["id"] == transaction["id"]:
                            tx["status"] = "confirmed"
                            break

                    # Display TX is confirmed and update user's current balance
                    print(f"Transaction confirmed. Your new balance is {userBalance} BTC.")

                # If balance insufficient, respond TX rejected
                elif responseJson["status"] == "Rejected":
                    # Update user balance from server response
                    userBalance = float(responseJson["balance"])

                    # Display TX is rejected and sends user's current balance
                    print(f"Transaction rejected. Your current balance is {userBalance} BTC.")

                    # Delete TX from its list
                    userTxs[:] = [tx for tx in userTxs if tx["id"] != transaction["id"]]

            # Fetch the list of transactions from the server and display it
            elif choice == "2":
                # Send the request to the server
                clientSocket.send("GET_TRANSACTIONS".encode())

                response = clientSocket.recv(1024).decode()
                responseJson = json.loads(response)

                # Display the txs in a table format
                if responseJson["status"] == "success":
                    print("\nYour Transaction History")
                    print("-" * 90)
                    print(f"{'TX ID':<10} {'Payer':<10} {'PayerAmount':<15} {'Payee1':<10} {'Amount1':<10} {'Payee2':<10} {'Amount2':<10} {'Status':<10}")
                    print("-" * 90)

                    # Display the confirmed transactions
                    if "txs" in responseJson:
                        confirmedTxs = responseJson["txs"]
                        if confirmedTxs:
                            for tx in confirmedTxs:
                                print(f"{tx['id']:<10} {tx['payer']:<10} {tx['PayerAmount']:<15} {tx['payee1']:<10} {tx['Amount1']:<10} {tx['payee2']:<10} {tx['Amount2']:<10} {tx['status']:<10}")
                        else:
                            print("No confirmed transactions found.")

            # Fetch X's balance (the fees) and display it
            elif choice == "3":
                # Send request to the server
                clientSocket.send("GET_X_BALANCE".encode())

                response = clientSocket.recv(1024).decode()
                responseJson = json.loads(response)

                # Display the X balance in a table format
                if responseJson["status"] == "success":
                    print("\nYour Bitcoin System X Balance")
                    print("-" * 40)
                    print(f"{'Account':<15}{'Balance':<15}")
                    print("-" * 40)
                    print(f"{'X':<15}{responseJson['balance']:<15}")
                    print("-" * 40)
                else:
                    print("X's balance cannot be reached.")

            # Quit the program
            elif choice == "4":
                print("Thank you for using this program. Goodbye.")
                clientSocket.close()
                exit()

            else:
                print("Invalid choice. Please enter a valid option.")

    else:
        print("Authentication failed.")

        # Display a menu with options to the user
        print("\nMenu:")
        print("(1) Enter the username and password again.")
        print("(2) Quit the program.")

        # Prompt the user for their choice
        choice = input("Enter your choice (1/2): ").strip()

        if choice == "2":
            print("Thank you for using this program. Goodbye.")
            break
        elif choice == "1":
            print("Please input your username and password again.")
            continue

    clientSocket.close()
