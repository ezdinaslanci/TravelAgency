import socket, time, json
from collections import OrderedDict
from threading import Thread


class Hotel(Thread):

    def __init__(self, port, hotelName, numOfRooms, resetDB):

        # thread super-constructor
        Thread.__init__(self)

        # connection stuff
        self.socketToTravelAgency = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_HOST = socket.gethostname()
        self.TCP_PORT = port

        # hotel's properties
        self.hotelName = hotelName

        # obtaining DB
        self.dbName = "hotelDBs/" + self.hotelName.lower().replace(" ", "_") + "_db.json"
        if resetDB:
            generateEmptyDB(self.hotelName, self.dbName, numOfRooms)

        self.activateServer()

    def activateServer(self):
        while True:
            try:
                print("Launching HTTP server for {} on {}:{}".format(self.hotelName, self.TCP_HOST, self.TCP_PORT))
                self.socketToTravelAgency.bind((self.TCP_HOST, self.TCP_PORT))
                break

            except:
                pass

            print("Warning: Could not acquire port {}!".format(self.TCP_PORT))
            self.TCP_PORT += 1

        print("{} is online on {}:{}, waiting for a connection...\n".format(self.hotelName, self.TCP_HOST, self.TCP_PORT))
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
            print("\n{} got a request from {}".format(self.hotelName, address))

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
            with open(self.dbName) as hotelDBFile:
                jsonDB = json.load(hotelDBFile)
        except:
            print("No DB found.")
            return

        numOfRooms = jsonDB["numOfRooms"]
        rooms = jsonDB["rooms"]
        availableRooms = []

        # find available rooms for requested time period
        for roomNumber in range(numOfRooms):
            room = rooms[roomNumber]
            reservedDates = room["reservedDates"]
            ifRoomAvailable = True
            for reservedDateNumber in range(len(reservedDates)):
                reservedDate = reservedDates[reservedDateNumber]
                roomArrivalDate = time.strptime(reservedDate["arrivalDate"], "%d.%m.%Y")
                roomDepartureDate = time.strptime(reservedDate["departureDate"], "%d.%m.%Y")
                if roomArrivalDate <= arrivalDate <= roomDepartureDate or roomArrivalDate <= departureDate <= roomDepartureDate or arrivalDate <= roomArrivalDate <= departureDate or arrivalDate <= roomDepartureDate <= departureDate:
                    ifRoomAvailable = False
                    break
            if ifRoomAvailable:
                availableRooms.append(room["roomID"])

        ifHotelAvailable = numOfTravelers <= len(availableRooms)

        # write reserved days to database
        if ifHotelAvailable and requestType == "reserve":
            reservedRooms = []
            for travelerNum in range(numOfTravelers):
                reservedDate = {"arrivalDate": time.strftime("%d.%m.%Y", arrivalDate), "departureDate": time.strftime("%d.%m.%Y", departureDate)}
                reservedDate = OrderedDict(sorted(reservedDate.items(), key=lambda t: t[0]))
                jsonDB["rooms"][availableRooms[travelerNum] - 1]["reservedDates"].append(reservedDate)
                reservedRooms.append(jsonDB["rooms"][availableRooms[travelerNum] - 1]["roomID"])
            try:
                with open(self.dbName, "w") as hotelDBFile:
                    json.dump(jsonDB, hotelDBFile, indent = 4, sort_keys = True)
            except:
                print("No DB found.")
                return
            response = json.dumps({"ifAvailable": ifHotelAvailable, "reservedRooms": reservedRooms, "status": "reserved"}, sort_keys = False)
        else:
            response = json.dumps({"ifAvailable": ifHotelAvailable, "availableRooms": availableRooms, "status": "not reserved"}, sort_keys = False)

        # return response (thank you captain)
        return response

def isDateValid(strDate):
    try:
        validDate = time.strptime(strDate, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def generateEmptyDB(hotelName, dbName, numOfRooms):
    jsonDB = {'hotelName': hotelName, 'numOfRooms': numOfRooms, 'rooms': []}
    for num in range(numOfRooms):
        room = {'roomID': num + 1, 'reservedDates': []}
        jsonDB['rooms'].append(room)
    with open(dbName, "w") as hotelDBFile:
        json.dump(jsonDB, hotelDBFile, indent = 4, sort_keys = True)


def main():
    hotel0 = Hotel(9000, "Hotel Discovery", 4, True)
    hotel1 = Hotel(9001, "Hotel Endurance", 3, True)
    hotel2 = Hotel(9002, "Hotel Daedalus", 5, True)
    hotel3 = Hotel(9003, "Hotel Prometheus", 3, True)
    hotel4 = Hotel(9004, "Hotel Serenity", 3, True)

if __name__ == "__main__":
    main()
