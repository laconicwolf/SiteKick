#!/usr/bin/env python


__author__ = 'Jake Miller (@LaconicWolf)'
__date__ = '20180425'
__version__ = '0.02'
__description__ = '''A multi-threaded web scanner that pulls title and server information'''


import sys
import argparse
import re
import os
import time
import random
import threading
import csv

# Fixes Python3 to Python2 backwards compatability
try:
    import queue
except ImportError:
    import Queue as queue
try:
    from urlparse import urlparse
except ModuleNotFoundError:
    from urllib.parse import urlparse

# Third party modules
try:
    import paramiko
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


def banner():
    """Returns ascii art sourced from: http://patorjk.com/software/taag/"""
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
    """Returns a randomly chosen User-Agent string."""
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


def parse_to_html(data):
    """Writes output to an HTML file"""
    #url, title, server, redir_url, screenshot
    file_name = "sitekick_results.html"
    new_data = [line for line in data if line[-1]]
    fh = open(file_name, 'a')
    for line in new_data:
        url = '<td><a href="{}">{}</a></td>'.format(line[0], line[0])
        screenshot = '<td><img src="screenshots/{}" style="width:420px;height:300px;"></td>'.format(line[4])
        fh.write("<table><tr>\n{}\n{}\n</tr></table>\n".format(url, screenshot))


def parse_to_csv(data, csv_name=None):
    """Takes a list of lists and outputs to a csv file."""
    csv_name = 'results.csv' if not csv_name else csv_name
    if not os.path.isfile(csv_name):
        if sys.version.startswith('3'):
            csv_file = open(csv_name, 'w', newline='')
        else:
            csv_file = open(csv_name, 'wb')
        csv_writer = csv.writer(csv_file)
        top_row = ['URL', 'Title', 'Server', 'Redirect URL', 'Screenshot', 'HTTP Creds', 'SSH Creds', 'Notes']
        csv_writer.writerow(top_row)
        print('\n[+] The file {} does not exist. New file created!\n'.format(csv_name))
    else:
        try:
            if sys.version.startswith('3'):
                csv_file = open(csv_name, 'a', newline='')
            else:
                csv_file = open(csv_name, 'ab')
        except PermissionError:
            print("\n[-] Permission denied to open the file {}. Check if the file is open and try again.\n".format(csv_name))
            exit()
        csv_writer = csv.writer(csv_file)
        print('\n[+]  {} exists. Appending to file!\n'.format(csv_name))
    for line in data:
        csv_writer.writerow(line)
    csv_file.close()


def normalize_urls(urls):
    """Accepts a list of urls and formats them so they will be accepted.
    Returns a new list of the processed urls.
    """
    urlList = []
    httpPortList = ['80', '280', '81', '591', '593', '2080', '2480', '3080', 
                  '4080', '4567', '5080', '5104', '5800', '6080',
                  '7001', '7080', '7777', '8000', '8008', '8042', '8080',
                  '8081', '8082', '8088', '8180', '8222', '8280', '8281',
                  '8530', '8887', '9000', '9080', '9090', '16080']                    
    httpsPortList = ['832', '981', '1311', '7002', '7021', '7023', '7025',
                   '7777', '8333', '8531', '8888']
    for url in urls:
        if '*.' in url:
            url.replace('*.', '')
        if not url.startswith('http'):
            if ':' in url:
                port = url.split(':')[-1]
                if port in httpPortList:
                    urlList.append('http://' + url)
                elif port in httpsPortList or port.endswith('43'):
                    urlList.append('https://' + url)
                else:
                    url = url.strip()
                    url = url.strip('/')
                    urlList.append('http://' + url + ':80')
                    urlList.append('https://' + url + ':443')
                    continue
            else:
                    url = url.strip()
                    url = url.strip('/')
                    urlList.append('http://' + url + ':80')
                    urlList.append('https://' + url + ':443')
                    continue
        if len(url.split(':')) != 3:
            if url[0:5] != 'https':    
                url = url.strip()
                url = url.strip('/')
                urlList.append(url + ':80')
                continue
            elif url[0:5] == 'https':
                url = url.strip()
                url = url.strip('/')
                urlList.append(url + ':443')
                continue
        url = url.strip()
        url = url.strip('/')
        urlList.append(url)
    return urlList


def make_request(url):
    """Builds a requests object, makes a request, and returns 
    a response object.
    """
    s = requests.Session()
    user_agent = get_random_useragent()
    s.headers['User-Agent'] = user_agent
    if args.proxy:
        s.proxies['http'] = args.proxy
        s.proxies['https'] = args.proxy
    resp = s.get(url, verify=False, timeout=int(args.timeout))
    return resp


def check_site_title(resp_obj, url):
    """Parses the title from a response object. If the title returns empty,
    a silent selenium browser is used to gather the title.
    """
    title = re.findall(r'<title.*?>(.+?)</title>',resp_obj.text, re.IGNORECASE)
    screen_shot_name = ""
    if title == []:
        if args.verbose:
            print("[*] Browsing to the url with PhantomJS")
        try:
            desired_capabilities = DesiredCapabilities.PHANTOMJS.copy()
            desired_capabilities['phantomjs.page.customHeaders.User-Agent'] = get_random_useragent()
            desired_capabilities['phantomjs.page.settings.resourceTimeout'] = '10000'
            browser = webdriver.PhantomJS(desired_capabilities=desired_capabilities, service_args=['--ignore-ssl-errors=true'])
        except:
            # If PhantomJS is not installed, a blank title will be returned
            if args.verbose:
                print("[-] An error occurred with PhantomJS")
            title = ""
            return title, screen_shot_name
        try:
            browser.get(url)
        except:
            return title, screen_shot_name
        WebDriverWait(browser, 2)
        title = browser.title
        if args.screenshot_no_title and title == '':
            if not os.path.exists('screenshots'):
                os.mkdir('screenshots')
            screen_shot_name = url.split('//')[1].split(':')[0].replace('.', '-') + '_' + url.split('//')[1].split(':')[1].strip('/') + '.png'
            browser.save_screenshot('screenshots' + os.sep + screen_shot_name)
        browser.close()
    else: 
        title = title[0]
    return title, screen_shot_name


def ssh_connect(hostname, username, password, port=22):
    """Attempts to connect to a specified host with specified credentials."""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(hostname=hostname,
                           port=port,
                           username=username,
                           password=password)
        if args.verbose:
            with lock:
                print('Authentication successful on {}:{} with {} : {}'.format(
                    hostname, str(port), username, password))
        return "Success - {}:{}".format(username, password)
    except paramiko.ssh_exception.NoValidConnectionsError:
        if args.verbose:
            with lock:
                print('[-] Unable to connect via SSH to {}:{}'.format(
                    hostname, port))
        return "Connect Error"
    except paramiko.ssh_exception.AuthenticationException:
        if args.verbose:
            with lock:
                print('[-] Authentication failed on {}:{} with {} : {}'.format(
                    hostname, port, username, password))
        return "Failure - {}:{}".format(username, password)
    except Exception as e:
        if args.verbose:
            with lock:
                print('[-] An unknown error occurred on {}:{} with {} : {}\nError: {}'.format(
                    hostname, port, username, password, e))
        return "Unknown Error", e


def map_title_to_ssh_creds(url, title, server):
    """Maps title and/or url path and/or server to default SSH credentials"""
    title = title.lower()
    title_mappings = {
        'stealthwatch management console': {'sysadmin': 'lan1cope'} 
    }
    if title in title_mappings.keys():
        ssh_creds = title_mappings.get(title)
    else:
        ssh_creds = ''
    return ssh_creds


def site_login(url, creds):
    """Attempts to login to a specified host with specified credentials and parameters.
    Currently not implemented, and will just return the creds.
    """
    return creds


def map_site_data_to_web_creds(url, title, server):
    """Maps titles and/or url path and/or server to default web credentials"""
    title = title.lower()
    title_mappings = {
        'polycom - configuration utility': [
            {'user':'123'},
            {'polycom': '456'}
        ]
    }
    if title in title_mappings.keys():
        creds = title_mappings.get(title)
    else:
        creds = ''
    return creds


def scanner_controller(url):
    """Controls most of the logic for the script. Accepts a URL and calls 
    various functions to make requests and prints output to the terminal.
    Returns nothing, but adds data to the data variable, which will be used 
    to print to a csv file. 
    """
    global data
    request_data = []
    screenshot = ""
    try:
        resp = make_request(url)
    except Exception as e:
        if args.verbose:
            with print_lock:
                print('[-] Unable to connect to site: {}'.format(url))
                print('[*] {}'.format(e))
        return
    if 'WWW-Authenticate' in resp.headers:
        auth_type = resp.headers['WWW-Authenticate']
        title = "Requires {} authentication".format(auth_type)
    elif not 'WWW-Authenticate' in resp.headers:
        title, screenshot = check_site_title(resp, url)
    else:
        title = 'Unable to determine title'
    
    # Checks the site's server, redirect url, and default creds.
    server = resp.headers['Server'] if 'Server' in resp.headers else ""
    redir_url = resp.url if resp.url.strip('/') != url.strip('/') else ""
    http_def_creds = map_site_data_to_web_creds(redir_url, title, server)
    ssh_def_creds = map_title_to_ssh_creds(redir_url, title, server)

    if args.check_creds:

        # Attempts to login via HTTP wwith default credentials
        if http_def_creds:
            http_creds_data = site_login(url, http_def_creds)
        else:
            http_creds_data = ''

        # Attempts to login via SSH wwith default credentials
        if ssh_def_creds:
            parsed_url = urlparse(url)
            ssh_host = parsed_url.netloc.split(':')[0]
            ssh_user = list(ssh_def_creds.keys())[0]
            ssh_pass = list(ssh_def_creds.values())[0]
            ssh_creds_data = ssh_connect(ssh_host, ssh_user, ssh_pass)
        else:
            ssh_creds_data = ''
    else:
        http_creds_data = http_def_creds
        ssh_creds_data = ssh_def_creds

    # Populate the data variable for display and output
    request_data.extend((url, title, server, redir_url, screenshot, http_creds_data, ssh_creds_data))
    data.append(request_data)

    # Format the title and server for displaying
    printable_title = title[:24] + "..." if len(title) > 24 else title
    printable_server = server[:14] + "..." if len(title) > 14 else server
    if str(printable_title) == '[]':
        printable_title = ''
    if str(printable_server) == '[]':
        printable_server = ''

    if args.check_creds:
        with print_lock:
            print('{:30}{:30}{:30}{:30}'.format(str(url), str(printable_title), str(http_creds_data), str(ssh_creds_data)))
    else:
        with print_lock:
            print('{:30}{:30}{:20}{:30}'.format(str(url), str(printable_title), str(printable_server), str(redir_url)))


def process_queue():
    """Processes the url queue and calls the scanner controller function"""
    while True:
        current_url = url_queue.get()
        scanner_controller(current_url)
        url_queue.task_done()


def main():
    """Normalizes the URLs and starts multithreading"""
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
    if args.screenshot_no_title:
        parse_to_html(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true")
    parser.add_argument("-snt", "--screenshot_no_title",
                        help="Takes a screenshot if no title is found",
                        action="store_true")
    parser.add_argument("-pr", "--proxy", 
                        help="Specify a proxy to use (-p 127.0.0.1:8080)")
    parser.add_argument("-csv", "--csv",
                        nargs='?',
                        const='results.csv',
                        default='results.csv',
                        help="specify the name of a csv file to write to. If the file already exists it will be appended")
    parser.add_argument("-uf", "--url_file",
                        help="specify a file containing urls formatted http(s)://addr:port.")
    parser.add_argument("-u", "--url",
                        help="specify a single url formatted http(s)://addr:port.")
    parser.add_argument("-cc", "--check_creds",
                        help="Attempts to login with default credentials if identified",
                        action="store_true")
    parser.add_argument("-t", "--threads",
                        nargs="?",
                        type=int,
                        const=30,
                        default=30,
                        help="Specify number of threads (default=30)")
    parser.add_argument("-to", "--timeout",
                        nargs="?", 
                        type=int, 
                        default=10, 
                        help="Specify number of seconds until a connection timeout (default=10)")
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
    url_queue = queue.Queue()
    print(banner())
    print('By: {}'.format(__author__))
    print(__description__)

    if len(urls) == 1:
        print('\n[*] Loaded {} URL...\n'.format(len(urls)))
    else:
        print('\n[*] Loaded {} URLs...\n'.format(len(urls)))
    time.sleep(3)
    if args.check_creds:
        print('{:30}{:30}{:30}{:30}'.format("URL", "Title", "Web Creds", "SSH Creds"))
    else:
        print('{:30}{:30}{:20}{:30}'.format("URL", "Title", "Server", "Redirect URL"))

    print_lock = threading.Lock()
    url_queue = queue.Queue()

    # Global variable where all data will be stored
    # The scanner_controller function appends data here
    data = []

    main()
