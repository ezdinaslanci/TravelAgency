import socket, json, itertools


class TravelAgency:

    def __init__(self):
        self.hotelPortDict = {"Hotel Discovery": 9000, "Hotel Endurance": 9001, "Hotel Daedalus": 9002, "Hotel Prometheus": 9003, "Hotel Serenity": 9004}
        self.airlinePortDict = {"Turkish Airlines": 9020, "Pegasus Airlines": 9021, "Ascendant Airlines": 9022, "Enterprise Airlines": 9023}
        self.arrivalDate = self.departureDate = self.preferredHotel = self.preferredAirline = ""
        self.numOfTravelers = 0
        self.proposedHotelList = []
        self.proposedAirlineList = []
        self.listenToCustomer()

    def clearStateInformation(self):
        self.arrivalDate = self.departureDate = self.preferredHotel = self.preferredAirline = ""
        self.numOfTravelers = 0
        self.proposedHotelList = []
        self.proposedAirlineList = []

    def listenToCustomer(self):

        # create a socket object
        customerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # get local machine name & port
        host = socket.gethostname()
        port = 8010

        # bind connection
        while True:
            try:
                print("Launching Travel Agency on {}:{}".format(host, port))
                customerSocket.bind((host, port))
                break
            except:
                pass
            print("Warning: Could not acquire port {}!".format(port))
            port += 1
        print("Travel Agency is online on {}:{}, waiting for a connection...\n".format(host, port))

        # queue up to 5 requests
        customerSocket.listen(5)

        # waiting for connections
        while True:

            # wait for a connection
            clientSocket, address = customerSocket.accept()

            # reset to defaults
            self.clearStateInformation()

            # got a customer!
            print("\nGot a customer from %s" % str(address))
            messageFromCustomerRaw = clientSocket.recv(200).decode('ascii')
            self.decodeMessageFromCI(messageFromCustomerRaw)

            # unknown hotel
            while self.preferredHotel not in self.hotelPortDict:
                clientSocket.send("[20]+{}".format(self.preferredHotel).encode('ascii'))
                messageFromCustomerRaw = clientSocket.recv(200).decode('ascii')
                self.decodeMessageFromCI(messageFromCustomerRaw)

            # unknown airline
            while self.preferredAirline not in self.airlinePortDict:
                clientSocket.send("[21]+{}".format(self.preferredAirline).encode('ascii'))
                messageFromCustomerRaw = clientSocket.recv(200).decode('ascii')
                self.decodeMessageFromCI(messageFromCustomerRaw)

            # contact to preferred airline & hotel, get response
            responseFromHotel = self.contactToHotel(self.preferredHotel, "check", self.arrivalDate, self.departureDate, self.numOfTravelers)
            responseFromAirline = self.contactToAirline(self.preferredAirline, "check", self.arrivalDate, self.departureDate, self.numOfTravelers)

            # decode response to JSON
            responseFromHotelJSON = json.loads(responseFromHotel)
            responseFromAirlineJSON = json.loads(responseFromAirline)

            # preferred hotel and airline are available
            if responseFromHotelJSON["ifAvailable"] and responseFromAirlineJSON["ifAvailable"]:
                clientSocket.send("[1]".encode('ascii'))
                reserveOrNot = clientSocket.recv(200).decode('ascii')
                if reserveOrNot == "yes":
                    responseFromHotel = self.contactToHotel(self.preferredHotel, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                    responseFromAirline = self.contactToAirline(self.preferredAirline, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                    if json.loads(responseFromHotel)["status"] == "reserved" and json.loads(responseFromAirline)["status"] == "reserved":
                        clientSocket.send("[8]+{}+{}".format(self.preferredHotel, self.preferredAirline).encode('ascii'))
                    else:
                        clientSocket.send("[30]".encode('ascii'))

            # preferred hotel is not available, preferred airline is available
            elif not responseFromHotelJSON["ifAvailable"] and responseFromAirlineJSON["ifAvailable"]:
                alternativeHotels = self.findAvailableHotels()
                if len(alternativeHotels) == 0:
                    clientSocket.send("[5]".encode('ascii'))
                else:
                    ifCustomerAccepts = False
                    for alternativeHotel in alternativeHotels:
                        clientSocket.send("[2]+{}".format(alternativeHotel).encode('ascii'))
                        reserveOrNot = clientSocket.recv(200).decode('ascii')
                        if reserveOrNot == "yes":
                            responseFromHotel = self.contactToHotel(alternativeHotel, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                            responseFromAirline = self.contactToAirline(self.preferredAirline, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                            if json.loads(responseFromHotel)["status"] == "reserved" and json.loads(responseFromAirline)["status"] == "reserved":
                                clientSocket.send("[8]+{}+{}".format(alternativeHotel, self.preferredAirline).encode('ascii'))
                            else:
                                clientSocket.send("[30]".encode('ascii'))
                            ifCustomerAccepts = True
                            break
                    if not ifCustomerAccepts:
                        clientSocket.send("[5]".encode('ascii'))

            # preferred hotel is available, preferred airline is not available
            elif responseFromHotelJSON["ifAvailable"] and not responseFromAirlineJSON["ifAvailable"]:
                alternativeAirlines = self.findAvailableAirlines()
                if len(alternativeAirlines) == 0:
                    clientSocket.send("[6]".encode('ascii'))
                else:
                    ifCustomerAccepts = False
                    for alternativeAirline in alternativeAirlines:
                        clientSocket.send("[3]+{}".format(alternativeAirline).encode('ascii'))
                        reserveOrNot = clientSocket.recv(200).decode('ascii')
                        if reserveOrNot == "yes":
                            responseFromHotel = self.contactToHotel(self.preferredHotel, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                            responseFromAirline = self.contactToAirline(alternativeAirline, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                            if json.loads(responseFromHotel)["status"] == "reserved" and json.loads(responseFromAirline)["status"] == "reserved":
                                clientSocket.send("[8]+{}+{}".format(self.preferredHotel, alternativeAirline).encode('ascii'))
                            else:
                                clientSocket.send("[30]".encode('ascii'))
                            ifCustomerAccepts = True
                            break
                    if not ifCustomerAccepts:
                        clientSocket.send("[6]".encode('ascii'))

            # preferred hotel and preferred airline are not available
            elif not responseFromHotelJSON["ifAvailable"] and not responseFromAirlineJSON["ifAvailable"]:
                alternativeHotels = self.findAvailableHotels()
                alternativeAirlines = self.findAvailableAirlines()
                if len(alternativeHotels) == 0 and len(alternativeAirlines) == 0:
                    clientSocket.send("[7]".encode('ascii'))
                elif len(alternativeHotels) == 0 and len(alternativeAirlines) > 0:
                    clientSocket.send("[5]".encode('ascii'))
                elif len(alternativeHotels) > 0 and len(alternativeAirlines) == 0:
                    clientSocket.send("[6]".encode('ascii'))
                elif len(alternativeHotels) > 0 and len(alternativeAirlines) > 0:
                    ifCustomerAccepts = False
                    alternatives = list(itertools.product(*[alternativeHotels, alternativeAirlines]))
                    for alternative in alternatives:
                        alternativeHotel = alternative[0]
                        alternativeAirline = alternative[1]
                        clientSocket.send("[4]+{}+{}".format(alternativeHotel, alternativeAirline).encode('ascii'))
                        reserveOrNot = clientSocket.recv(200).decode('ascii')
                        if reserveOrNot == "yes":
                            responseFromHotel = self.contactToHotel(alternativeHotel, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                            responseFromAirline = self.contactToAirline(alternativeAirline, "reserve", self.arrivalDate, self.departureDate, self.numOfTravelers)
                            if json.loads(responseFromHotel)["status"] == "reserved" and json.loads(responseFromAirline)["status"] == "reserved":
                                clientSocket.send("[8]+{}+{}".format(alternativeHotel, alternativeAirline).encode('ascii'))
                            else:
                                clientSocket.send("[30]".encode('ascii'))
                            ifCustomerAccepts = True
                            break
                    if not ifCustomerAccepts:
                        clientSocket.send("[7]".encode('ascii'))
                else:
                    clientSocket.send("[UNK]".encode('ascii'))

    def decodeMessageFromCI(self, messageFromCustomerRaw):
        messageFromCustomerJSON = json.loads(messageFromCustomerRaw)
        self.arrivalDate = messageFromCustomerJSON["arrivalDate"]
        self.departureDate = messageFromCustomerJSON["departureDate"]
        self.preferredHotel = messageFromCustomerJSON["preferredHotel"]
        self.preferredAirline = messageFromCustomerJSON["preferredAirline"]
        self.numOfTravelers = messageFromCustomerJSON["numOfTravelers"]
        print("Arrival Date: {}\nDeparture Date: {}\nPreferred Hotel: {}\nPreferred Airline: {}\nNumber of Travelers: {}".format(self.arrivalDate, self.departureDate, self.preferredHotel, self.preferredAirline, self.numOfTravelers))


    def contactToHotel(self, hotelName, requestType, arrivalDate, departureDate, numOfTravelers):
        hotelPort = self.hotelPortDict[hotelName]
        hotelHost = socket.gethostname()
        request = "GET /?type={}&arrivalDate={}&departureDate={}&numOfTravelers={} HTTP/1.1\nHost: {}\nUser-Agent:Mozilla 5.0\n\n".format(requestType, arrivalDate, departureDate, numOfTravelers, hotelHost)
        hotelSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hotelSocket.connect((hotelHost, hotelPort))
        hotelSocket.send(request.encode("ascii"))
        response = hotelSocket.recv(200).decode("ascii")
        responseSplitted = response.split("\n\n")
        responseContent = responseSplitted[1]
        print("{} responded: {}".format(hotelName, responseContent))
        return responseContent

    def contactToAirline(self, airlineName, requestType, arrivalDate, departureDate, numOfTravelers):
        airlinePort = self.airlinePortDict[airlineName]
        airlineHost = socket.gethostname()
        request = "GET /?type={}&arrivalDate={}&departureDate={}&numOfTravelers={} HTTP/1.1\nHost: {}\nUser-Agent:Mozilla 5.0\n\n".format(requestType, arrivalDate, departureDate, numOfTravelers, airlineHost)
        airlineSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        airlineSocket.connect((airlineHost, airlinePort))
        airlineSocket.send(request.encode("ascii"))
        response = airlineSocket.recv(200).decode("ascii")
        responseSplitted = response.split("\n\n")
        responseContent = responseSplitted[1]
        print("{} responded: {}".format(airlineName, responseContent))
        return responseContent

    def findAvailableHotels(self):
        availableHotels = []
        for hotelName, hotelPort in self.hotelPortDict.items():
            responseFromHotel = self.contactToHotel(hotelName, "check", self.arrivalDate, self.departureDate, self.numOfTravelers)
            responseFromHotelJSON = json.loads(responseFromHotel)
            if responseFromHotelJSON["ifAvailable"]:
                availableHotels.append(hotelName)
        return availableHotels

    def findAvailableAirlines(self):
        availableAirlines = []
        for airlineName, airlinePort in self.airlinePortDict.items():
            responseFromAirline = self.contactToAirline(airlineName, "check", self.arrivalDate, self.departureDate, self.numOfTravelers)
            responseFromAirlineJSON = json.loads(responseFromAirline)
            if responseFromAirlineJSON["ifAvailable"] and airlineName not in self.proposedAirlineList:
                availableAirlines.append(airlineName)
        return availableAirlines

def main():
    ta = TravelAgency()

if __name__ == "__main__":
    main()