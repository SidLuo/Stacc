import os
from mapbox import Geocoder

geocoder = Geocoder(access_token='pk.eyJ1IjoiZmZmeDAiLCJhIjoiY2psbGtsa21nMHlneDNwcW4wbzg3bDd5eiJ9.Q3ZS5kabj_xO1KVifuuQJQ')

response = geocoder.forward(
	"26 Henley Rd, Homebush west",
	lon = 151,
	lat = -33,
	country = ['au', 'nz']
	)
first = response.geojson()['features'][0]
print (first['place_name'])

for coord in first['geometry']['coordinates']:
	print (coord)

#coord = ([round(coord, 8) for coord in first['geometry']
#['coordinates']])

#print(coord)

