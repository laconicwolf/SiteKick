# SiteKick.py
SiteKick.py is a tools designed to pull some basic information from a website. It was specifically developed to scan environments with thousands of hosts that may be running hundreds or thousands of web services listening on standard or non-standard web ports. The tool takes a URL or a file containing URLs (http(s)://ipaddr:port) as input, and will send a web request (via Python requests) to each URL and will record the URL it was redirected to (if redirected), the website Title (if <title></title> tags are present), and Server type (if a server header is present). While pulling information from the site, if the title tag is not present, sitekick will use Selenium and PhantomJS to launch a silent browser and browse to the site, as occasionally titles are generated only when JavaScript is detected.  The captured information (URL, redirect, title, server) is printed to the terminal and optionally a CSV file. 

## Dependencies for sitekick.py
This script requires a few non-standard libraries (requests, selenium), which should all be available via pip. PhantomJS is also required, and can be downloaded either via a package manager or from http://phantomjs.org/download.html.

## Usage for sitekick.py
```
optional arguments:

  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -p, --print_all       display scan information to the screen
  -snt, --screenshot_no_title
                        Takes a screenshot if no title is found.
  -pr PROXY, --proxy PROXY
                        specify a proxy to use (-pr 127.0.0.1:8080)
  -csv [CSV], --csv [CSV]
                        specify the name of a csv file to write to. If the
                        file already exists it will be appended
  -uf URL_FILE, --url_file URL_FILE
                        specify a file containing urls formatted
                        http(s)://addr:port.
  -t [THREADS], --threads [THREADS]
                        specify number of threads (default=1)
```
                        

### Scan a list of URLs and output to a CSV file
`python3 sitekick.py -uf urls.txt -csv sitekick_scan.csv`

### Scan a list of URLs thorgh a proxy and print the output to the terminal
`python3 sitekick.py -uf urls.txt -p sitekick_scan.csv -pr 127.0.0.1:8080`
