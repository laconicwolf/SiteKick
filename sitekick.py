import sys
if not sys.version.startswith('3'):
    print('\n[-] This script will not work with Python2. Please use Python3. Quitting!')
    exit()
try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    from selenium import webdriver
    from selenium.webdriver import DesiredCapabilities
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError as error:
    missing_module = str(error).split(' ')[-1]
    print('\n[-] This script requires several modules that you may not have.')
    print('[*] Missing module: {}'.format(missing_module))
    print('[*] Try running "pip install {}", or do an Internet search for installation instructions.'.format(missing_module.strip("'")))
    exit()
import argparse
import re
import os
import time
import random
import threading
import csv
from queue import Queue


__author__ = 'Jake Miller (@LaconicWolf)'
__date__ = '20180425'
__version__ = '0.01'
__description__ = '''A multi-threaded web scanner that pulls title and server information'''


def banner():
    ''' Returns ascii art sourced from: http://patorjk.com/software/taag/
    '''
    ascii_art = '''
  _________.__  __          ____  __.__        __    
 /   _____/|__|/  |_  ____ |    |/ _|__| ____ |  | __
 \\_____  \\ |  \\   __\\/ __ \\|      < |  |/ ___\\|  |/ /
 /        \\|  ||  | \\  ___/|    |  \\|  \\  \\___|    < 
/_______  /|__||__|  \\___  >____|__ \\__|\\___  >__|_ \\
        \\/               \\/        \\/       \\/     \\/
'''
    return ascii_art


def get_random_useragent():
    ''' Returns a randomly chosen User-Agent string.
    '''
    win_edge = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
    win_firefox = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/43.0'
    win_chrome = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
    lin_firefox = 'Mozilla/5.0 (X11; Linux i686; rv:30.0) Gecko/20100101 Firefox/42.0'
    mac_chrome = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.38 Safari/537.36'
    ie = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)'
    ua_dict = {
        1: win_edge,
        2: win_firefox,
        3: win_chrome,
        4: lin_firefox,
        5: mac_chrome,
        6: ie
    }
    rand_num = random.randrange(1, (len(ua_dict) + 1))
    return ua_dict[rand_num]


def parse_to_csv(data, csv_name=None):
    ''' Takes a list of lists and outputs to a csv file.
    '''
    csv_name = 'results.csv' if not csv_name else csv_name
    if not os.path.isfile(csv_name):
        csv_file = open(csv_name, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        top_row = ['URL', 'Title', 'Server', 'Redirect URL', 'Notes']
        csv_writer.writerow(top_row)
        print('\n[+] The file {} does not exist. New file created!\n'.format(csv_name))
    else:
        try:
            csv_file = open(csv_name, 'a', newline='')
        except PermissionError:
            print("\n[-] Permission denied to open the file {}. Check if the file is open and try again.\n".format(csv_name))
            exit()
        csv_writer = csv.writer(csv_file)
        print('\n[+]  {} exists. Appending to file!\n'.format(csv_name))
    for line in data:
        csv_writer.writerow(line)
    csv_file.close()


def normalize_urls(urls):
    ''' Accepts a list of urls and formats them so they will be accepted.
    Returns a new list of the processed urls.
    '''
    url_list = []
    http_port_list = ['80', '280', '81', '591', '593', '2080', '2480', '3080', 
                  '4080', '4567', '5080', '5104', '5800', '6080',
                  '7001', '7080', '7777', '8000', '8008', '8042', '8080',
                  '8081', '8082', '8088', '8180', '8222', '8280', '8281',
                  '8530', '8887', '9000', '9080', '9090', '16080']                    
    https_port_list = ['832', '981', '1311', '7002', '7021', '7023', '7025',
                   '7777', '8333', '8531', '8888']
    for url in urls:
        if '*.' in url:
            url.replace('*.', '')
        if not url.startswith('http'):
            if ':' in url:
                port = url.split(':')[-1]
                if port in http_port_list:
                    url_list.append('http://' + url)
                elif port in https_port_list or port.endswith('43'):
                    url_list.append('https://' + url)
                else:
                    url = url.strip()
                    url = url.strip('/') + '/'
                    url_list.append('http://' + url)
                    url_list.append('https://' + url)
                    continue
            else:
                    url = url.strip()
                    url = url.strip('/') + '/'
                    url_list.append('http://' + url)
                    url_list.append('https://' + url)
                    continue
        url = url.strip()
        url = url.strip('/') + '/'
        url_list.append(url)
    return url_list


def make_request(url):
    ''' Builds a requests object, makes a request, and returns 
    a response object.
    '''
    s = requests.Session()
    user_agent = get_random_useragent()
    s.headers['User-Agent'] = user_agent
    if args.proxy:
        s.proxies['http'] = args.proxy
        s.proxies['https'] = args.proxy
    resp = s.get(url, verify=False, timeout=int(args.timeout))
    return resp


def check_site_title(resp_obj, url):
    ''' Parses the title from a response object. If the title returns empty,
    a silent selenium browser is used to gather the title.
    '''
    title = re.findall(r'<title.*?>(.+?)</title>',resp_obj.text, re.IGNORECASE)
    if title == []:
        if args.verbose:
            print("[*] Browsing to the url with PhantomJS")
        try:
            desired_capabilities = DesiredCapabilities.PHANTOMJS.copy()
            desired_capabilities['phantomjs.page.customHeaders.User-Agent'] = get_random_useragent()
            browser = webdriver.PhantomJS(desired_capabilities=desired_capabilities)
        except:
            # If PhantomJS is not installed, a blank title will be returned
            if args.verbose:
                print("[-] An error occurred with PhantomJS")
            title = ""
            return title
        browser.get(url)
        WebDriverWait(browser, 2)
        title = browser.title
        if args.screenshot_no_title and title == '':
            screen_shot_name = url.split('//')[1].split(':')[0]
            browser.save_screenshot(screen_shot_name + '.png')
        browser.close()
    else: 
        title = title[0]
    return title


def scanner_controller(url):
    ''' Controls most of the logic for the script. Accepts a URL and calls 
    various functions to make requests and prints output to the terminal.
    Returns nothing, but adds data to the data variable, which can be used 
    to print to a file. 
    '''
    global data
    request_data = []
    try:
        resp = make_request(url)
    except Exception as e:
        if args.verbose:
            with print_lock:
                print('[-] Unable to connect to site: {}'.format(url))
                print('[*] {}'.format(e))
        return
    if 'WWW-Authenticate' in resp.headers:
        auth_type = resp_obj.headers['WWW-Authenticate']
        title = "Requires {} authentication".format(auth_type)
    elif not 'WWW-Authenticate' in resp.headers:
        title = check_site_title(resp, url)
    else:
        title = 'Unable to determine title'
    
    # checks the site's server and redirect url.
    server = resp.headers['Server'] if 'Server' in resp.headers else ""
    redir_url = resp.url if resp.url.strip('/') != url.strip('/') else ""

    request_data.extend((url, title, server, redir_url))
    data.append(request_data)

    printable_title = title[:29] + "..." if len(title) > 29 else title
    with print_lock:
        print('{:35}{:35}{:20}{:35}'.format(url, printable_title, server, redir_url))


def process_queue():
    ''' processes the url queue and calls the scanner controller function
    '''
    while True:
        current_url = url_queue.get()
        scanner_controller(current_url)
        url_queue.task_done()


def main():
    ''' Normalizes the URLs and starts multithreading
    '''
    processed_urls = normalize_urls(urls)
    
    for i in range(args.threads):
        t = threading.Thread(target=process_queue)
        t.daemon = True
        t.start()

    for current_url in processed_urls:
        url_queue.put(current_url)

    url_queue.join()

    if args.csv:
        parse_to_csv(data, csv_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-snt", "--screenshot_no_title", help="Takes a screenshot if no title is found", action="store_true")
    parser.add_argument("-pr", "--proxy", help="Specify a proxy to use (-p 127.0.0.1:8080)")
    parser.add_argument("-csv", "--csv", nargs='?', const='results.csv', help="specify the name of a csv file to write to. If the file already exists it will be appended")
    parser.add_argument("-uf", "--url_file", help="specify a file containing urls formatted http(s)://addr:port.")
    parser.add_argument("-u", "--url", help="specify a single url formatted http(s)://addr:port.")
    parser.add_argument("-t", "--threads", nargs="?", type=int, default=5, help="Specify number of threads (default=5)")
    parser.add_argument("-to", "--timeout", nargs="?", type=int, default=10, help="Specify number of seconds until a connection timeout (default=10)")
    args = parser.parse_args()

    if not args.url and not args.url_file:
        parser.print_help()
        print("\n[-] Please specify a URL (-u) or an input file containing URLs (-uf).\n")
        exit()

    if args.url and args.url_file:
        parser.print_help()
        print("\n[-] Please specify a URL (-u) or an input file containing URLs (-uf). Not both\n")
        exit()

    if args.url_file:
        urlfile = args.url_file
        if not os.path.exists(urlfile):
            print("\n[-] The file cannot be found or you do not have permission to open the file. Please check the path and try again\n")
            exit()
        urls = open(urlfile).read().splitlines()

    if args.url:
        urls = [args.url]
        
    csv_name = args.csv

    # suppress SSL warnings in the terminal
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    
    # initiates the queue
    url_queue = Queue()
    print(banner())
    print('By: {}'.format(__author__))
    print(__description__)

    if len(urls) == 1:
        print('\n[*] Loaded {} URL...\n'.format(len(urls)))
    else:
        print('\n[*] Loaded {} URLs...\n'.format(len(urls)))
    time.sleep(3)
    print('{:35}{:35}{:20}{:35}'.format("URL", "Title", "Server", "Redirect URL"))

    print_lock = threading.Lock()
    url_queue = Queue()

    # Global variable where all data will be stored
    # The scanner_controller function appends data here
    data = []

    main()
