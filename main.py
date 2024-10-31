#import folium
import requests
#пример первой координаты 15.458470,47.064970
#Пример второй координаты 15.476760,47.071100
coord1 = input()
coord2 = input()
url = f'http://router.project-osrm.org/route/v1/driving/{coord1};{coord2}'
response = requests.get(url)
#print(response.text)
data = response.json()
geom = data['routes'][0]['geometry']
dist = data['routes'][0]['distance']
print(geom)
print(dist)