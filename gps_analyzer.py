import json
import folium
from urllib.parse import urlparse, parse_qs

class gps_analysis:
    def gps_map():
    # Load the coordinates in WGS84 from the JSON file
        gps_list = []
        test=  []
        count = 0
        with open('gps_list.json', 'r') as f:
            data = json.load(f)
            for url in data:
                gps_list.append(url)
                query = urlparse(url).query
                params = parse_qs(query)
                count+=1
                if 'q' in params:
                    lat, lon = params['q'][0].split(',')
                    coord = {lat +',' + lon}
                    test.append(coord)
        #print(count)
        with open('GPS_ONLY_COORDS.json', "w") as f:
                    f.write(json.dumps(test, default=str, indent=4))

        with open('GPS_ONLY_COORDS.json', 'r') as f:
            data = json.load(f)

        # Create a list of coordinates
        coordinates_list = []

        for i in range(len(data)):
            coord_str = data[i].strip('{}').replace("'", "")
            lat, lon= coord_str.strip('{}').split(',')
            coordinates = [float(lat),float(lon)]
            coordinates_list.append(coordinates) # add each coordinate to the list
            
        # Create map centered on the first coordinate
        map = folium.Map(location=coordinates_list[0], zoom_start=12)

        # Add pins for coordinates
        for i in range(len(coordinates_list)):
            folium.Marker(location=coordinates_list[i]).add_to(map)

        # Save map in HTML
        map.save('gps_map.html')


        return ("map saved")