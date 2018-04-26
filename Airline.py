import socket, time, json
from threading import Thread


class Airline(Thread):

    def __init__(self, port, airlineName, numOfSeats, resetDB):

        # thread super-constructor
        Thread.__init__(self)

        # connection stuff
        self.socketToTravelAgency = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_HOST = socket.gethostname()
        self.TCP_PORT = port

        # airline's properties
        self.airlineName = airlineName

        # obtaining DB
        self.dbName = "airlineDBs/" + self.airlineName.lower().replace(" ", "_") + "_db.json"
        if resetDB:
            generateEmptyDB(self.airlineName, self.dbName, numOfSeats)

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
                        responseContent = str(self.queryDB(queryDict["type"], queryDict["arrivalDate"], queryDict["departureDate"], queryDict["numOfTravelers"])).encode("ascii")

                responseHeaders = self.generateHeaders(200)
                server_response =  responseHeaders.encode()
                server_response +=  responseContent
                clientSocket.send(server_response)
                clientSocket.close()

            else:
                print("Unknown HTTP request method: ", requestMethod)

    def queryDB(self, requestType, arrivalDate, departureDate, numOfTravelers):
        arrivalDate = time.strptime(arrivalDate, "%d.%m.%Y")
        departureDate = time.strptime(departureDate, "%d.%m.%Y")
        numOfTravelers = int(numOfTravelers)

        try:
            with open(self.dbName) as airlineDBFile:
                jsonDB = json.load(airlineDBFile)
        except:
            print("No DB found.")
            return

        numOfSeats = jsonDB["numOfSeats"]
        seats = jsonDB["seats"]
        availableSeatsArrival = []
        availableSeatsDeparture = []

        # find available seats for requested dates
        for seatNumber in range(numOfSeats):
            seat = seats[seatNumber]
            reservedDates = seat["reservedDates"]
            ifSeatAvailableArrival = ifSeatAvailableDeparture = True

            for reservedDateNumber in range(len(reservedDates)):
                reservedDate = time.strptime(reservedDates[reservedDateNumber]["date"], "%d.%m.%Y")
                if arrivalDate == reservedDate:
                    ifSeatAvailableArrival = False
                    break
            if ifSeatAvailableArrival:
                availableSeatsArrival.append(seat["seatID"])

            for reservedDateNumber in range(len(reservedDates)):
                reservedDate = time.strptime(reservedDates[reservedDateNumber]["date"], "%d.%m.%Y")
                if departureDate == reservedDate:
                    ifSeatAvailableDeparture = False
                    break
            if ifSeatAvailableDeparture:
                availableSeatsDeparture.append(seat["seatID"])


        # if airline is available for requested dates
        ifAirlineAvailable = numOfTravelers <= min(len(availableSeatsArrival), len(availableSeatsDeparture))

        # write reserved days to database
        if ifAirlineAvailable and requestType == "reserve":
            reservedSeatsArrival = []
            reservedSeatsDeparture = []
            for travelerNum in range(numOfTravelers):
                reservedDate1 = {"date": time.strftime("%d.%m.%Y", arrivalDate)}
                reservedDate2 = {"date": time.strftime("%d.%m.%Y", departureDate)}
                jsonDB["seats"][availableSeatsArrival[travelerNum] - 1]["reservedDates"].append(reservedDate1)
                jsonDB["seats"][availableSeatsDeparture[travelerNum] - 1]["reservedDates"].append(reservedDate2)
                reservedSeatsArrival.append(jsonDB["seats"][availableSeatsArrival[travelerNum] - 1]["seatID"])
                reservedSeatsDeparture.append(jsonDB["seats"][availableSeatsDeparture[travelerNum] - 1]["seatID"])
            try:
                with open(self.dbName, "w") as airlineDBFile:
                    json.dump(jsonDB, airlineDBFile, indent = 4, sort_keys = True)
            except:
                print("No DB found.")
                return
            response = json.dumps({"ifAvailable": ifAirlineAvailable, "reservedSeats": (reservedSeatsArrival, reservedSeatsDeparture), "status": "reserved"}, sort_keys = False)
        else:
            response = json.dumps({"ifAvailable": ifAirlineAvailable, "availableSeats": (availableSeatsArrival, availableSeatsDeparture), "status": "not reserved"}, sort_keys = False)
        return response

def isDateValid(strDate):
    try:
        validDate = time.strptime(strDate, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def generateEmptyDB(airlineName, dbName, numOfSeats):
    jsonDB = {'airlineName': airlineName, 'numOfSeats': numOfSeats, 'seats': []}
    for num in range(numOfSeats):
        seat = {'seatID': num + 1, 'reservedDates': []}
        jsonDB['seats'].append(seat)
    with open(dbName, "w") as airlineDBFile:
        json.dump(jsonDB, airlineDBFile, indent = 4, sort_keys = True)


def main():
    airline0 = Airline(9020, "Turkish Airlines", 4, True)
    airline1 = Airline(9021, "Pegasus Airlines", 5, True)
    airline2 = Airline(9022, "Ascendant Airlines", 3, True)
    airline3 = Airline(9023, "Enterprise Airlines", 6, True)

if __name__ == "__main__":
    main()
