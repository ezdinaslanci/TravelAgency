import socket, time, json


class CustomerInterface:

    def __init__(self, port):

        # get port of TA
        self.TCP_PORT = port

        # data holders
        self.arrivalDate = self.departureDate = self.preferredHotel = self.preferredAirline = self.latestMessageFromTA = self.latestStatusCodeFromTA = self.reserveOrNot = self.jsonMessage = ""
        self.numOfTravelers = 0

        # establish connection to travel agency
        self.socketToTravelAgency = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_HOST = socket.gethostname()
        self.socketToTravelAgency.connect((self.TCP_HOST, self.TCP_PORT))

        # begin the procedure
        self.getDetails()
        self.sendMessage(self.jsonMessage.encode("ascii"))
        self.receiveMessage()

        # unknown preferred hotel
        while self.latestStatusCodeFromTA == "[20]":
            print("\nThere is no hotel in name \"{}\", please enter a new one.".format(self.preferredHotel))
            self.preferredHotel = input("Type your choice [HOTELNAME]: ")
            self.jsonMessage = json.dumps({"arrivalDate": str(self.arrivalDate), "departureDate": str(self.departureDate), "preferredHotel": str(self.preferredHotel), "preferredAirline": str(self.preferredAirline), "numOfTravelers": self.numOfTravelers})
            self.sendMessage(self.jsonMessage.encode("ascii"))
            self.receiveMessage()

        # unknown preferred airline
        while self.latestStatusCodeFromTA == "[21]":
            print("\nThere is no airline in name \"{}\", please enter a new one.".format(self.preferredAirline))
            self.preferredAirline = input("Type your choice [AIRLINE]: ")
            self.jsonMessage = json.dumps({"arrivalDate": str(self.arrivalDate), "departureDate": str(self.departureDate), "preferredHotel": str(self.preferredHotel), "preferredAirline": str(self.preferredAirline), "numOfTravelers": self.numOfTravelers})
            self.sendMessage(self.jsonMessage.encode("ascii"))
            self.receiveMessage()

        # preferred hotel and airline are available
        if self.latestMessageFromTA == "[1]":
            print("\nYay! {} and {} are available for dates {} and {} for {} people, would you like to reserve?".format(self.preferredHotel, self.preferredAirline, self.arrivalDate, self.departureDate, self.numOfTravelers))
            self.reserveOrNot = input("Type your choice [yes/no]: ")
            while self.reserveOrNot not in ("yes", "no"):
                self.reserveOrNot = input("Unknown choice, type your choice [yes/no]: ")
            if self.reserveOrNot == "yes":
                self.sendMessage(self.reserveOrNot.encode("ascii"))
                self.receiveMessage()
                if self.latestStatusCodeFromTA == "[8]":
                    reservedHotel = self.latestMessageFromTA.split("+")[1]
                    reservedAirline = self.latestMessageFromTA.split("+")[2]
                    print("\nSuccessfully reserved {} and {}.".format(reservedHotel, reservedAirline))
                else:
                    print("\nSomething went wrong. ERR:1")
            else:
                print("Goodbye!")

        # preferred hotel is not available, preferred airline is available
        elif self.latestStatusCodeFromTA == "[2]":
            alternativeHotel = self.latestMessageFromTA.split("+")[1]
            print("\nSorry! {} is not available between {} and {} for {} people, but {} is, would you like to reserve?".format(self.preferredHotel, self.arrivalDate, self.departureDate, self.numOfTravelers, alternativeHotel))
            self.reserveOrNot = input("Type your choice [yes/no]: ")
            while self.reserveOrNot not in ("yes", "no"):
                self.reserveOrNot = input("Unknown choice, type your choice [yes/no]: ")
            self.sendMessage(self.reserveOrNot.encode("ascii"))
            self.receiveMessage()
            while self.latestStatusCodeFromTA == "[2]":
                alternativeHotel = self.latestMessageFromTA.split("+")[1]
                print("\nWhat about {}?".format(alternativeHotel))
                self.reserveOrNot = input("Type your choice [yes/no]: ")
                while self.reserveOrNot not in ("yes", "no"):
                    self.reserveOrNot = input("Unknown choice, type your choice [yes/no]: ")
                self.sendMessage(self.reserveOrNot.encode("ascii"))
                self.receiveMessage()
            if self.latestStatusCodeFromTA == "[5]":
                print("\nSorry! There is no other alternative hotel.")
            elif self.latestStatusCodeFromTA == "[8]":
                reservedHotel = self.latestMessageFromTA.split("+")[1]
                reservedAirline = self.latestMessageFromTA.split("+")[2]
                print("\nSuccessfully reserved {} and {}.".format(reservedHotel, reservedAirline))
            else:
                print("\nSomething went wrong. ERR:2")

        # preferred hotel is available, preferred airline is not available
        elif self.latestStatusCodeFromTA == "[3]":
            alternativeAirline = self.latestMessageFromTA.split("+")[1]
            print("\nSorry! {} is not available for {} and {} for {} people, but {} is, would you like to reserve?".format(self.preferredAirline, self.arrivalDate, self.departureDate, self.numOfTravelers, alternativeAirline))
            self.reserveOrNot = input("Type your choice [yes/no]: ")
            while self.reserveOrNot not in ("yes", "no"):
                self.reserveOrNot = input("Unknown choice, type your choice [yes/no]: ")
            self.sendMessage(self.reserveOrNot.encode("ascii"))
            self.receiveMessage()
            while self.latestStatusCodeFromTA == "[3]":
                alternativeAirline = self.latestMessageFromTA.split("+")[1]
                print("\nWhat about {}?".format(alternativeAirline))
                self.reserveOrNot = input("Type your choice [yes/no]: ")
                while self.reserveOrNot not in ("yes", "no"):
                    self.reserveOrNot = input("Unknown choice, type your choice [yes/no]: ")
                self.sendMessage(self.reserveOrNot.encode("ascii"))
                self.receiveMessage()
            if self.latestStatusCodeFromTA == "[6]":
                print("\nSorry! There is no other alternative airline.")
            elif self.latestStatusCodeFromTA == "[8]":
                reservedHotel = self.latestMessageFromTA.split("+")[1]
                reservedAirline = self.latestMessageFromTA.split("+")[2]
                print("\nSuccessfully reserved {} and {}.".format(reservedHotel, reservedAirline))
            else:
                print("\nSomething went wrong. ERR:2")

        # preferred hotel and preferred airline are not available
        elif self.latestStatusCodeFromTA == "[4]":
            alternativeHotel = self.latestMessageFromTA.split("+")[1]
            alternativeAirline = self.latestMessageFromTA.split("+")[2]
            print("\nSorry! {} and {} are not available for {} and {} for {} people, but {} and {} are, would you like to reserve?".format(self.preferredHotel, self.preferredAirline, self.arrivalDate, self.departureDate, self.numOfTravelers, alternativeHotel, alternativeAirline))
            self.reserveOrNot = input("Type your choice [yes/no]: ")
            while self.reserveOrNot not in ("yes", "no"):
                self.reserveOrNot = input("Unknown choice, type your choice [yes/no]: ")
            self.sendMessage(self.reserveOrNot.encode("ascii"))
            self.receiveMessage()
            while self.latestStatusCodeFromTA == "[4]":
                alternativeHotel = self.latestMessageFromTA.split("+")[1]
                alternativeAirline = self.latestMessageFromTA.split("+")[2]
                print("\nWhat about {} and {}?".format(alternativeHotel, alternativeAirline))
                self.reserveOrNot = input("Type your choice [yes/no]: ")
                while self.reserveOrNot not in ("yes", "no"):
                    self.reserveOrNot = input("Unknown choice, type your choice [yes/no]: ")
                self.sendMessage(self.reserveOrNot.encode("ascii"))
                self.receiveMessage()
            if self.latestStatusCodeFromTA == "[5]":
                print("\nSorry! There is no other alternative hotel.")
            elif self.latestStatusCodeFromTA == "[6]":
                print("\nSorry! There is no other alternative airline.")
            elif self.latestStatusCodeFromTA == "[7]":
                print("\nSorry! There is no other alternative combination.")
            elif self.latestStatusCodeFromTA == "[8]":
                reservedHotel = self.latestMessageFromTA.split("+")[1]
                reservedAirline = self.latestMessageFromTA.split("+")[2]
                print("\nSuccessfully reserved {} and {}.".format(reservedHotel, reservedAirline))
            else:
                print("\nSomething went wrong. ERR:3")

        # no available hotel
        elif self.latestStatusCodeFromTA == "[5]":
            print("\nSorry! There is no available hotel between {} and {} for {} people.".format(self.arrivalDate, self.departureDate, self.numOfTravelers))

        # no available airline
        elif self.latestStatusCodeFromTA == "[6]":
            print("\nSorry! There is no available airline for {} and {} for {} people.".format(self.arrivalDate, self.departureDate, self.numOfTravelers))

        # no available hotel and airline
        elif self.latestStatusCodeFromTA == "[7]":
            print("\nSorry! There is no available hotel and airline for {} and {} for {} people.".format(self.arrivalDate, self.departureDate, self.numOfTravelers))

        self.socketToTravelAgency.close()

    def getDetails(self):

        # get current date
        currentDate = time.strptime(time.strftime("%d.%m.%Y"), "%d.%m.%Y")

        # get arrival date and check if it is valid
        self.arrivalDate = input("\nEnter arrival date (dd.mm.YYYY): ")
        while not isDateValid(self.arrivalDate) or time.strptime(self.arrivalDate, "%d.%m.%Y") < currentDate:
            self.arrivalDate = input("Invalid Date! Enter arrival date: ")

        # get departure date and check if it is valid
        self.departureDate = input("Enter departure date (dd.mm.YYYY): ")
        while not isDateValid(self.departureDate) or time.strptime(self.departureDate, "%d.%m.%Y") < time.strptime(self.arrivalDate, "%d.%m.%Y"):
            self.departureDate = input("Invalid Date! Enter departure date: ")

        # get preferred hotel
        self.preferredHotel = input("Enter preferred hotel: ")

        # get preferred airline
        self.preferredAirline = input("Enter preferred airline: ")

        # get number of travelers and check if it is valid
        self.numOfTravelers = input("Enter number of travelers: ")
        while not isPositiveInteger(self.numOfTravelers):
            self.numOfTravelers = input("Invalid number! Enter number of travelers: ")

        # generate JSON message
        self.jsonMessage = json.dumps({"arrivalDate": str(self.arrivalDate), "departureDate": str(self.departureDate), "preferredHotel": str(self.preferredHotel), "preferredAirline": str(self.preferredAirline), "numOfTravelers": self.numOfTravelers})

    def sendMessage(self, message):
        self.socketToTravelAgency.send(message)

    def receiveMessage(self):
        self.latestMessageFromTA = self.socketToTravelAgency.recv(50).decode('ascii')
        if self.latestMessageFromTA.count("+") >= 1 or len(self.latestMessageFromTA) == 3:
            self.latestStatusCodeFromTA = self.latestMessageFromTA.split("+")[0]
        else:
            self.latestStatusCodeFromTA = None

def isDateValid(strDate):
    try:
        validDate = time.strptime(strDate, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def isPositiveInteger(strInteger):
    try:
        posInt = int(strInteger)
    except ValueError:
        return False
    if posInt > 0:
        return True
    else:
        return False

def main():
    portOfTA = int(input("\nEnter port to TA: "))
    while True:
        ci = CustomerInterface(portOfTA)

if __name__ == "__main__":
    main()