#HooptySearch

Hoopty Search is a tools to grab RSS car and truck data from Craigslist and then re-displays the data in a more attractive format.  First it will organize all the results by year of the car, then price and if possible it will try and scrape out the mileage of the cars.  It attempts to make a note about kilometers vs miles if possible.


The tools section contains a dynamically generated bit of html and the tool to generate it, the scrape_cities.py tool will grab all the cities from the main page of CL so the dropdown menu is populated with up to date cities.


You can see a live version at http://hooptysearch.com/

#Dependencies
python-feedparser

python-lxml