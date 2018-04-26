import socket, time, json
from collections import OrderedDict
from threading import Thread


class Hotel(Thread):

    def __init__(self, port, hotelName):
        Thread.__init__(self)
        self.socketToTravelAgency = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_HOST = socket.gethostname()
        self.TCP_PORT = port
        self.hotelName = hotelName
        self.hotelNameDBDict = {"Hotel Black Star": "hotelDBs/hotel_black_star_db.json", "Hotel Dark Side": "hotelDBs/hotel_dark_side_db.json"}
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
                        responseContent = str(self.checkIfDateAvailable(self.hotelName, queryDict["type"], queryDict["arrivalDate"], queryDict["departureDate"], queryDict["numOfTravellers"])).encode("ascii")

                responseHeaders = self.generateHeaders(200)
                server_response =  responseHeaders.encode()
                server_response +=  responseContent
                clientSocket.send(server_response)
                clientSocket.close()

            else:
                print("Unknown HTTP request method: ", requestMethod)

    def checkIfDateAvailable(self, hotelName, requestType, arrivalDate, departureDate, numOfTravellers):
        hotelDB = self.hotelNameDBDict[hotelName]
        arrivalDate = time.strptime(arrivalDate, "%d.%m.%Y")
        departureDate = time.strptime(departureDate, "%d.%m.%Y")
        numOfTravellers = int(numOfTravellers)

        try:
            with open(hotelDB) as hotelDBFile:
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
                if roomArrivalDate < arrivalDate < roomDepartureDate or roomArrivalDate < departureDate < roomDepartureDate or arrivalDate < roomArrivalDate < departureDate or arrivalDate < roomDepartureDate < departureDate:
                    ifRoomAvailable = False
                    break
            if ifRoomAvailable:
                availableRooms.append(room["roomID"])

        ifHotelAvailable = numOfTravellers <= len(availableRooms)

        if ifHotelAvailable and requestType == "reserve":
            for travellerNum in range(numOfTravellers):
                reservedDate = {"arrivalDate": time.strftime("%d.%m.%Y", arrivalDate), "departureDate": time.strftime("%d.%m.%Y", departureDate)}
                reservedDate = OrderedDict(sorted(reservedDate.items(), key=lambda t: t[0]))
                jsonDB["rooms"][availableRooms[travellerNum] - 1]["reservedDates"].append(reservedDate)
            with open(hotelDB, "w") as hotelDBFile:
                json.dump(jsonDB, hotelDBFile, sort_keys = False)

        response = json.dumps({"ifAvailable": ifHotelAvailable, "availableRooms": availableRooms, "status": "not reserved"}, sort_keys = False)
        return response

def isDateValid(strDate):
    try:
        validDate = time.strptime(strDate, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def main():
    hotel1 = Hotel(8080, "Hotel Black Star")
    hotel2 = Hotel(8081, "Hotel Dark Side")

if __name__ == "__main__":
    main()
