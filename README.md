# fei_webscraper
A simple web scraper to quickly download all relevant horse-event data from the fei website. It only supports the eventing and dressure categories, but can be easily extended to cover all other categories. 

### Example
Prepare an Excel file with the following row called `example.xlsx`

```
Place 	    Country	Start	  End	    Classes
Vilamoura	POR	    10/1/18	10/7/18	CSI1*, CSI3*, CSIYH1*
```

and in a python file

```
from fei_webscraper.eventing import PaardenDatabase, ProcessExcel, DatabaseToExcel

input_file = 'example.xlsx'
output_file = 'ResultsEventing.xlsx'

db = PaardenDatabase()
ProcessExcel(input_file, output_file, db)
db.DatabaseToExcel(output_file)
```

excecuting this script will enter the search query into the fei search-engine and go through all events, sub/side events on each day and dump all gathered data into a new excel sheet called `ResultsEventing.xlsx`.

### Installation
Run `pip install .` inside the fei_webscraper folder to build and install this package. The webscraper relies on having a chromedriver that connects the Chrome webbrowser with the Selenium package. This chromedriver should be placed in the same directory as the above example python script.
