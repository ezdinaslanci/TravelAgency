import socket, json

class TravelAgency:
    def __init__(self):
        print("Travel Agency is running...")
        self.hotelPortDict = {"Hotel Black Star": 8080, "Hotel Dark Side": 8081}
        self.airlinePortDict = {"THY": 8082, "Pegasus": 8083}
        self.listenToCustomer()

    def listenToCustomer(self):

        # create a socket object
        customerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # get local machine name & port
        host = socket.gethostname()
        port = 9999

        # bind to the port
        customerSocket.bind((host, port))

        # queue up to 5 requests
        customerSocket.listen(5)

        # waiting for connections
        while True:

            # wait for a connection
            clientSocket, address = customerSocket.accept()

            # got a customer!
            print("\nGot a customer from %s" % str(address))
            messageFromCustomerRaw = clientSocket.recv(1024).decode('ascii')
            messageFromCustomerJSON = json.loads(messageFromCustomerRaw)
            print("\tArrival Date: {}\n\tDeparture Date: {}\n\tPreferred Hotel: {}\n\tPreferred Airline: {}\n\tNumber of Travellers: {}".format(messageFromCustomerJSON["arrivalDate"], messageFromCustomerJSON["departureDate"], messageFromCustomerJSON["preferredHotel"], messageFromCustomerJSON["preferredAirline"], messageFromCustomerJSON["numOfTravellers"]))

            # determine which hotel to contact
            if messageFromCustomerJSON["preferredHotel"] in self.hotelPortDict:
                hotelToContact = messageFromCustomerJSON["preferredHotel"]
            else:
                hotelToContact = list(self.hotelPortDict.keys())[0]

            if messageFromCustomerJSON["preferredAirline"] in self.airlinePortDict:
                airlineToContact = messageFromCustomerJSON["preferredAirline"]
            else:
                airlineToContact = list(self.airlinePortDict.keys())[0]

            # contact to determined hotel & get response
            responseFromHotel = self.contactToHotel(hotelToContact, "check", messageFromCustomerJSON["arrivalDate"], messageFromCustomerJSON["departureDate"], messageFromCustomerJSON["numOfTravellers"])
            responseFromAirline = self.contactToAirline(airlineToContact, "check", messageFromCustomerJSON["arrivalDate"], messageFromCustomerJSON["departureDate"], messageFromCustomerJSON["numOfTravellers"])

            # see the response (debug)
            print("\t{} responded: {}".format(hotelToContact, responseFromHotel))
            print("\t{} responded: {}".format(airlineToContact, responseFromAirline))

            # decode response to JSON
            responseFromHotelJSON = json.loads(responseFromHotel)
            responseFromAirlineJSON = json.loads(responseFromAirline)

            # if the hotel has available room or not
            if responseFromHotelJSON["ifAvailable"]:
                clientSocket.send("There are available rooms!".encode('ascii'))
            else:
                clientSocket.send("Sorry no available rooms.".encode('ascii'))

            # if the airline has available
            if responseFromAirlineJSON["ifAvailable"]:
                clientSocket.send("There are available flight!".encode('ascii'))
            else:
                clientSocket.send("Sorry no available flight.".encode('ascii'))

            # close connection
            clientSocket.close()

    def contactToHotel(self, hotelName, requestType, arrivalDate, departureDate, numOfTravellers):
        hotelPort = self.hotelPortDict[hotelName]
        hotelHost = socket.gethostname()
        request = "GET /?type={}&arrivalDate={}&departureDate={}&numOfTravellers={} HTTP/1.1\nHost: {}\nUser-Agent:Mozilla 5.0\n\n".format(requestType, arrivalDate, departureDate, numOfTravellers, hotelHost)
        hotelSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hotelSocket.connect((hotelHost, hotelPort))
        hotelSocket.send(request.encode("ascii"))
        response = hotelSocket.recv(1024).decode("ascii")
        responseSplitted = response.split("\n\n")
        responseContent = responseSplitted[1]
        return responseContent

    def contactToAirline(self, airlineName, requestType, arrivalDate, departureDate, numOfTravellers):
        airlinePort = self.airlinePortDict[airlineName]
        airlineHost = socket.gethostname()
        request = "GET /?type={}&arrivalDate={}&departureDate={}&numOfTravellers={} HTTP/1.1\nHost: {}\nUser-Agent:Mozilla 5.0\n\n".format(requestType, arrivalDate, departureDate, numOfTravellers, airlineHost)
        airlineSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        airlineSocket.connect((airlineHost, airlinePort))
        airlineSocket.send(request.encode("ascii"))
        response = airlineSocket.recv(1024).decode("ascii")
        responseSplitted = response.split("\n\n")
        responseContent = responseSplitted[1]
        return responseContent
def main():
    ta = TravelAgency()

if __name__ == "__main__":
    main()