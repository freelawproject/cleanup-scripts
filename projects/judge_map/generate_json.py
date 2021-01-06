import pprint

template = {
  "type": "FeatureCollection",
  "features": [
    {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [-111.6782379150,39.32373809814] # Lat then Long
        }
    },
    {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [-74.00714111328,40.71455001831]
        }
    }]}

feat = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [-111.6782379150,39.32373809814] # Lat then Long
        }
    }

with open("locations_with_long_lat.txt", "r") as f: #technically lat than long
    locations = f.readlines()

spots = []
for location in locations:
    feat = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [-111.6782379150, 39.32373809814]  # Lat then Long
        }
    }
    try:
        row = location.split("\t")
        # # print(row)
        # feat["geometry"]['coordinates'] = [row[-1].strip(), row[-2].strip()]
        # # int(row[-1].strip())
        float(row[-1].strip())
        # place = feat["geometry"]['coordinates']
        # # print(feat)
        # spots.append(feat)
        # # print(feat)
        # template['features'] = spots

        spots.append({"longitude": row[-1].strip(), "latitude": row[-2].strip()})

    except Exception as e:
        # print(str(e))
        pass

pprint.pprint(spots)

# with open("")
