import socket, time, json
from collections import OrderedDict
from threading import Thread


class Airline(Thread):

    def __init__(self, port, airlineName):
        Thread.__init__(self)
        self.socketToTravelAgency = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_HOST = socket.gethostname()
        self.TCP_PORT = port
        self.airlineName = airlineName
        self.airlineNameDBDict = {"THY": "airlineDBs/THY_db.json", "Pegasus": "airlineDBs/Pegasus_db.json"}
        self.activateServer()

    def activateServer(self):
        while True:
            try:
                print("Launching HTTP server for {} on {}:{}".format(self.airlineName, self.TCP_HOST, self.TCP_PORT))
                self.socketToTravelAgency.bind((self.TCP_HOST, self.TCP_PORT))
                break

            except:
                pass

            print("Warning: Could not acquire port {}!".format(self.TCP_PORT))
            self.TCP_PORT += 1

        print("{} is online on {}:{}, waiting for a connection...\n".format(self.airlineName, self.TCP_HOST, self.TCP_PORT))
        Thread(target = self.waitForConnection).start()

        # self.waitForConnection()

    def shutDownServer(self):
        try:
            print("\nShutting down the server...")
            self.socketToTravelAgency.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            print("Warning: could not shut down the socket. Maybe it was already closed?", e)

    def generateHeaders(self, code):
        if code == 200:
            header = "HTTP/1.1 200 OK\n"
        elif code == 404:
            header = "HTTP/1.1 404 Not Found\n"
        else:
            header = "Unknown code!"

        # write further headers
        current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += "Date: " + current_date + "\n"
        header += "Server: Python-HTTP-Server for Hotels\n\n"

        return header

    def waitForConnection(self):
        while True:
            self.socketToTravelAgency.listen(3) # maximum number of queued connections

            clientSocket, address = self.socketToTravelAgency.accept()
            print("\n{} got a request from {}".format(self.airlineName, address))

            # receive and decode data
            data = clientSocket.recv(1024)
            string = bytes.decode(data)

            # get request method
            requestMethod = string.split(' ')[0]

            # dictionary that will store the query
            queryDict = {}

            if requestMethod == "GET":
                if string.split(' ')[1] == "/favicon.ico":
                    pass
                else:
                    queryFromTA = string.split(" ")[1].split("?")[1].split("&")
                    for item in queryFromTA:
                        queryDict[item.split("=")[0]] = item.split("=")[1]

                    print(queryDict)

                if not ("arrivalDate" in queryDict and isDateValid(queryDict["arrivalDate"])):
                    responseContent = b"Invalid arrival date!"
                elif not ("departureDate" in queryDict and isDateValid(queryDict["departureDate"])):
                    responseContent = b"Invalid departure date!"
                elif queryDict["type"] not in ("check", "reserve"):
                    responseContent = b"Invalid request type!"
                else:
                    currentDate = time.strptime(time.strftime("%d.%m.%Y"), "%d.%m.%Y")
                    arrivalDate = time.strptime(queryDict["arrivalDate"], "%d.%m.%Y")
                    departureDate = time.strptime(queryDict["departureDate"], "%d.%m.%Y")
                    if arrivalDate < currentDate or departureDate < arrivalDate:
                        responseContent = b"Time travelling is not invented yet!"
                    else:
                        responseContent = str(self.checkIfDateAvailable(self.airlineName, queryDict["type"], queryDict["arrivalDate"], queryDict["departureDate"], queryDict["numOfTravellers"])).encode("ascii")

                responseHeaders = self.generateHeaders(200)
                server_response =  responseHeaders.encode()
                server_response +=  responseContent
                clientSocket.send(server_response)
                clientSocket.close()

            else:
                print("Unknown HTTP request method: ", requestMethod)

    def checkIfDateAvailable(self, airlineName, requestType, arrivalDate, departureDate, numOfTravellers):
        airlineDB = self.airlineNameDBDict[airlineName]
        arrivalDate = time.strptime(arrivalDate, "%d.%m.%Y")
        departureDate = time.strptime(departureDate, "%d.%m.%Y")
        numOfTravellers = int(numOfTravellers)

        try:
            with open(airlineDB) as airlineDBFile:
                jsonDB = json.load(airlineDBFile)
        except:
            print("No DB found.")
            return

        numOfSeat = jsonDB["numOfSeat"]
        seats = jsonDB["seats"]
        availableSeats = []

        # find available rooms for requested time period
        for seatNumber in range(numOfSeat):
            seat = seats[seatNumber]
            reservedDates = seat["reservedDates"]
            ifSeatAvailable = True
            for reservedDateNumber in range(len(reservedDates)):
                reservedDate = reservedDates[reservedDateNumber]
                seatArrivalDate = time.strptime(reservedDate["arrivalDate"], "%d.%m.%Y")
                seatDepartureDate = time.strptime(reservedDate["departureDate"], "%d.%m.%Y")
                if seatArrivalDate < arrivalDate < seatDepartureDate or seatArrivalDate < departureDate < seatDepartureDate or arrivalDate < seatArrivalDate < departureDate or arrivalDate < seatDepartureDate < departureDate:
                    ifSeatAvailable = False
                    break
            if ifSeatAvailable:
                availableSeats.append(seat["seatID"])

        ifAirlineAvaible = numOfTravellers <= len(availableSeats)

        if ifAirlineAvaible and requestType == "reserve":
            for travellerNum in range(numOfTravellers):
                reservedDate = {"arrivalDate": time.strftime("%d.%m.%Y", arrivalDate), "departureDate": time.strftime("%d.%m.%Y", departureDate)}
                reservedDate = OrderedDict(sorted(reservedDate.items(), key=lambda t: t[0]))
                jsonDB["seat"][availableSeats[travellerNum] - 1]["reservedDates"].append(reservedDate)
            with open(airlineDB, "w") as airlineDBFile:
                json.dump(jsonDB, airlineDBFile, sort_keys = False)

        response = json.dumps({"ifAvailable": ifAirlineAvaible, "availableSeats": availableSeats, "status": "not reserved"}, sort_keys = False)
        return response

def isDateValid(strDate):
    try:
        validDate = time.strptime(strDate, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def main():
    airline1 = Airline(8082, "THY")
    airline2 = Airline(8083, "Pegasus")

if __name__ == "__main__":
    main()
