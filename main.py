import csv
import json
import string
import requests
from requests.exceptions import ConnectionError
from requests.exceptions import TooManyRedirects
from requests.exceptions import Timeout
from requests.exceptions import HTTPError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from bs4 import BeautifulSoup
from tqdm import tqdm

urllist =  input("Please enter the csv file name from which to read URLs from: ")
fields = ['URL',  'Status', 'Division', 'Line of Business', 'COID', 'Name', 'Site Type']

with open(urllist, 'r+') as url_list:
    reader = csv.DictReader(url_list, fieldnames = fields)
    next(reader)
   rows = []
    progress = tqdm(reader)
    for row in progress:
        url = 'http://' + row['URL'] + '/'
        secure_url = "https://" + row['URL'] + '/'
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
            response = requests.get(url, headers=headers, timeout=5)
            data = response.text
            true_site = False
            
            #checking url for special instances
            if response.status_code == 200:
                if response.url == 'http://beta.ehc.com':
                    row['Status'] = 'beta.ehc.com - Page not found (404 error)'
                elif secure_url != response.url:
                    row['Status'] = 'Redirects to ' + response.url
                    true_site = True
                else:
                    row['Status'] = 'Working'
                    true_site = True

            #if a real real site, get data from script/json tag    
            if true_site == True:

                soup = BeautifulSoup(data, 'html.parser')

                scripts = soup.find_all('script')
                scriptsToString = str(scripts)

                if "COID" in scriptsToString:
                    body_tag = soup.find('body')
                    script_tag = body_tag.find('script').text
                    new_string = script_tag.replace('<script>', '').replace('window.dataLayer = window.dataLayer || [];', '').replace('dataLayer.push(', '').replace(');', '').replace('\'', '"').replace('</script>', '')
                    string_object = json.loads(new_string)

                    #grabbing specific values from script/json tag
                    division = string_object["Division"]
                    line = string_object["Line of Business"]
                    coid = string_object["Facility COID"]
                    name = string_object["Facility Name"]
                    site_type = string_object["Site Type"]

                    #setting and adding values to rows list
                    row['Division'] = division
                    row['Line of Business'] = line
                    row['COID'] = coid
                    row['Name'] = name
                    row['Site Type'] = site_type
                else:
                    row['Status'] = 'Redirects to ' + response.url + ' - not a HUT site'

        #catching exceptions        
        except ConnectionError as e:
            row['Status'] = "DNS failure or refused connection"
            
        except HTTPError as e:
            row['Status'] = "404 Client Error"
        except TooManyRedirects as e:
            row['Status'] = "Too many redirects"
        except Timeout as e:
            row['Status'] = "Request timeout"

        #adding row info to the new rows list    
        rows.append(row)

    #writting to the same csv file
    url_list.seek(0)
    writer = csv.DictWriter(url_list, delimiter=',', lineterminator='\n', fieldnames = fields)
    writer.writeheader()
    writer.writerows(rows)

print("\nDone gathering data!")
