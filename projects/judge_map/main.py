import requests
import urllib.parse

with open("locations.txt", "r") as f:
    locations = f.readlines()

for location in locations:

    row = location.split("\t")
    # try:
    #     print(row[1], "\t-\t", row[2])
    # except:
    #     pass

    # url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(f"{row[2]}") +'?format=json'
    #
    # response = requests.get(url).json()
    # print(response[0]["lat"])
    # print(response[0]["lon"])
    try:
        url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(
            f"{row[2]}") + '?format=json'

        response = requests.get(url).json()

        print(f"{location.strip()} \t {response[0]['lat']} \t {response[0]['lon']}")
    except:
        print(f"{location.strip()}")
