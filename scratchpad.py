import requests


link = 'https://instagram.flwo2-3.fna.fbcdn.net/v/t51.29350-15/450487750_467929272661589_8972365471726566768_n.jpg?se=7&stp=dst-jpg_e35&efg=eyJ2ZW5jb2RlX3RhZyI6ImltYWdlX3VybGdlbi4xNDQweDE4MDAuc2RyLmYyOTM1MCJ9&_nc_ht=instagram.flwo2-3.fna.fbcdn.net&_nc_cat=105&_nc_ohc=GLgXNqiyXN8Q7kNvgEWg8KU&edm=ABmJApABAAAA&ccb=7-5&ig_cache_key=MzQxMDUxMTU3NTE1OTEwMDI1MA%3D%3D.2-ccb7-5&oh=00_AYA1jILZGGnxbvzKQdDsQK4ifihiUZwutmiglmB8Ny4r1A&oe=669B5435&_nc_sid=b41fef'


response = requests.get(link)
print(response.content)

