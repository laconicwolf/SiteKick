# SiteKick.py and Invoke-SiteKick.ps1
SiteKick.py and Invoke-SiteKick.ps1 are tools designed to pull some basic information from a website. They were specifically developed to scan environments with thousands of hosts that may be running hundreds or thousands of web services listening on standard or non-standard web ports. The tools take a URL or a file containing URLs (http(s)://ipaddr:port) as input, and will send a web request (via Python requests or Invoke-WebRequests) to each URL and will record the URL it was redirected to (if redirected), the website Title (if <title></title> tags are present), and Server type (if a server header is present). The tools are slightly different, with the Python script being more full featured. This repository also contains web_addr_generator.py which is a script used to generate URLs for your environment that can be used in sitekick.py or Invoke-SiteKick. Usage instructions for web_addr_generator.py follows the intructions for sitekick.py and Invoke-SiteKick.

## sitekick.py
While pulling information from the site, if the title tag is not present, sitekick will use Selenium and PhantomJS to launch a silent browser and browse to the site, as occasionally titles are generated only when JavaScript is detected. This provides more thorough title detection when compared to Invoke-SiteKick. The captured information (URL, redirect, title, server) is either output to the terminal or a CSV file (or both). Additionally, sitekick.py can perform dirbusting if specified, and the directories will either be defined within the script, or a local file containing directories can be specified.

## Dependencies for sitekick.py
This script requires many non-standard libraries, which should all be available via pip. PhantomJS is also required, and can be downloaded either via a package manager or from http://phantomjs.org/download.html.

## Usage for sitekick.py
```
optional arguments:

  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -p, --print_all       display scan information to the screen
  -snt, --screenshot_no_title
                        Takes a screenshot if no title is found
  -d [{common,file}], --dirbust [{common,file}]
                        Attempts to dirbust common or file-specified
                        directories
  -df DIRBUST_FILE, --dirbust_file DIRBUST_FILE
                        Specify text file containing directories to test, one
                        directory per line.
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

### Scan a list of URLs and perform dirbusting of a few directories, printing to the terminal and a CSV file
> Directories defined in the directories() function within the script

`python3 sitekick.py -uf urls.txt -d common -p -csv sitekick_scan.csv`

### Scan a list of URLs and perform dirbusting of a directories specified in a local file, printing to the terminal
`python3 sitekick.py -uf urls.txt -d file -df directories.txt -p`

## Invoke-SiteKick
The main differences between this script and the Python version is that this script does not perform dirbusting and does not spawn a browser if the title cannot be found. I had played around with using a silent IE COM object to browse for title information, but this resulted in a perormance reduction that wasn't worth it. This script also does not provide a CSV output option, however it is compatible with the cmdlet Export-Csv. For usage, import the Invoke-SiteKick.ps1 script and run: 
`Get-Help Invoke-SiteKick` 

## Usage for web_addr_generator.py

### Generate a list of URLs for a specific network range
> Will generate URLs for 10.1.1.0/24 range. Each host will have ~45 URLs (1 for each common web port). Example:

```
python3 web_addr_generator.py -r 10.1.1.0/24
http://10.1.1.1:80
http://10.1.1.1:280
http://10.1.1.1:81
http://10.1.1.1:591
http://10.1.1.1:593
http://10.1.1.1:2080
http://10.1.1.1:2480
...
```

### Generate a list of URLs for a hosts specified in a local file
`python3 web_addr_generator.py -i hosts.txt`
