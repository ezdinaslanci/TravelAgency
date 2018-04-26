import socket, time, json


class CustomerInterface:

    def __init__(self):

        # data holders
        self.arrivalDate = self.departureDate = self.preferredHotel = self.preferredAirline = self.latestMessageFromTA = self.jsonMessage = ""
        self.numOfTravellers = 0

        # establish connection to travel agency
        self.socketToTravelAgency = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_HOST = socket.gethostname()
        self.TCP_PORT = 9999
        self.socketToTravelAgency.connect((self.TCP_HOST, self.TCP_PORT))

        self.getDetails()
        self.sendMessage(self.jsonMessage.encode("ascii"))
        self.receiveMessage()
        print(self.latestMessageFromTA)

    def getDetails(self):

        # get current date
        currentDate = time.strptime(time.strftime("%d.%m.%Y"), "%d.%m.%Y")

        # get arrival date and check if it is valid
        self.arrivalDate = input("Enter arrival date (dd.mm.YYYY): ")
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

        # get number of travellers and check if it is valid
        self.numOfTravellers = input("Enter number of travellers: ")
        while not isPositiveInteger(self.numOfTravellers):
            self.numOfTravellers = input("Invalid number! Enter number of travellers: ")

        # generate JSON message
        self.jsonMessage = json.dumps({"arrivalDate": str(self.arrivalDate), "departureDate": str(self.departureDate), "preferredHotel": str(self.preferredHotel), "preferredAirline": str(self.preferredAirline), "numOfTravellers": self.numOfTravellers})

    def sendMessage(self, message):
        self.socketToTravelAgency.send(message)

    def receiveMessage(self):
        self.latestMessageFromTA = self.socketToTravelAgency.recv(1024).decode('ascii')

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
    while True:
        customerInterface = CustomerInterface()

if __name__ == "__main__":
    main()