# https://chromedriver.chromium.org/downloads
# https://www.smashingmagazine.com/2021/12/headers-https-requests-ui-automation-testing/
# https://pypi.org/project/selenium-wire/

import os
import time
import argparse
import urllib.request
import html.parser

import selenium.webdriver
import selenium.webdriver.support.ui 
import selenium.webdriver.support.expected_conditions

class JoCaptcha(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.captcha = ''

    def handle_starttag(self, tag, attrs):
        if (tag == 'div' and any(k == 'class' and v == 'lf-captcha-sum' for k, v in attrs)) or (tag == 'input' and '<' in self.captcha and '</' not in self.captcha):
            self.captcha += f'<{tag}>'
    
    def handle_data(self, data):
        if '<' in self.captcha and '</' not in self.captcha:
            self.captcha += data
            
    def handle_endtag(self, tag):
        if tag == 'div' and '</' not in self.captcha:
            self.captcha += f'</{tag}>'

    def solve(self, replace = {' ' : '', '<div>' : '', '</div>' : '', '<input>' : '?', 'onze' : 11, 'douze' : 12, 'treize' : 13, 'quatorze' : 14, 'quinze' : 15, 'seize' : 16, 'dix-sept' : 17, 'dix-huit' : 18, 'dix-neuf' : 19, 'vingt' : 20, 'un' : 1, 'deux' : 2, 'trois' : 3, 'quatre' : 4, 'cinq' : 5, 'six' : 6, 'sept' : 7, 'huit' : 8, 'neuf' : 9, 'dix' : 10}):
        captcha = self.captcha
        for k, v in replace.items():
            captcha = captcha.replace(k, str(v))
        
        assert all(c in '?+=0123456789' for c in captcha) and '=' in captcha, captcha

        ab, c = captcha.split('=')
        a, b = ab.split('+')
        if a == '?':
            return int(c) - int(b)
        if b == '?':
            return int(c) - int(a)
        assert c == '?'
        return int(a) + int(b)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--jo-search', default  = 'https://www.legifrance.gouv.fr/jorf/jo/{year}?page={page}&pageSize=100')
    parser.add_argument('--jo-download', default= 'https://www.legifrance.gouv.fr/download/secure/file/{token}')
    parser.add_argument('--years', default = [2016, 2017, 2018, 2019, 2020, 2021], type = int, nargs = '+')
    parser.add_argument('--output-directory', '-o', default = 'jo')
    parser.add_argument('--output-directory-prefix', default = '')
    parser.add_argument('--chromedriver', default = '/usr/bin/chromedriver')
    parser.add_argument('--timeout', type = float, default = 10.0)
    parser.add_argument('--timeout-big', type = float, default = 30.0)
    parser.add_argument('--headmore', action = 'store_true')
    parser.add_argument('--debug', default = 'debug.html')

    args = parser.parse_args()
    print(args)

    os.makedirs(args.output_directory, exist_ok = True)
    
    chrome_prefs = {
        'download.default_directory': args.output_directory_prefix + args.output_directory,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True,
    }
    chrome_options = selenium.webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', chrome_prefs)
    if not args.headmore:
        chrome_options.add_argument('--headless')
    chrome_service = selenium.webdriver.chrome.service.Service(executable_path = args.chromedriver)

    #driver.request_interceptor = driver.response_interceptor = (lambda request, response: print(request.url, request.headers, response.headers))
    
    find_artefacts = lambda joid, temp: [fname for fname in os.listdir(args.output_directory) for prefix in ['joe_' + joid[-4:] + joid[2:4] + joid[:2], joid.rstrip('pdf')] if prefix in fname and ('.crdownload' in fname) == temp]

    for year in args.years:
        page = 1
        while True:
            driver = None
            try:
                driver = selenium.webdriver.Chrome(options = chrome_options, service = chrome_service)
                wait = selenium.webdriver.support.ui.WebDriverWait(driver, args.timeout)
                
                url = args.jo_search.format(year = year, page = page)
                
                driver.get(url)
                page_source = driver.page_source
                wait.until(selenium.webdriver.support.expected_conditions.url_to_be(url))

                jolinks = driver.find_elements('partial link text' , 'nominatives') + driver.find_elements('partial link text', 'version papier numérisée')

                print('Page', page, 'found', len(jolinks), 'links', url)
                
                breakpoint()
                for i, jolink in enumerate(jolinks):
                    joid = jolink.get_attribute('data-textid')
                    
                    res_files = find_artefacts(joid, temp = False)
                    if res_files:
                        print('Page', page, 'Skipping', joid)
                        continue

                    for fname in find_artefacts(joid, temp = True):
                        print('Temp file exists, deleting', joid, fname)
                        os.remove(os.path.join(args.output_directory, fname))

                    print('Page', page, 'Processing', joid, i, '/', len(jolinks))
                    
                    jolink.click()
                    wait.until(selenium.webdriver.support.expected_conditions.presence_of_element_located(('css selector', '.lf-captcha-line')))

                    captcha = driver.find_element('css selector', '.lf-captcha-line')
                    
                    jo_captcha_parser = JoCaptcha()
                    jo_captcha_parser.feed(captcha.get_attribute('innerHTML'))
                    captcha_solution = jo_captcha_parser.solve()

                    captcha.find_element('css selector', '.lf-captcha-input').send_keys(str(captcha_solution))
                    captcha.find_element('css selector', '.captcha-submit').click()
                    
                    wait.until(selenium.webdriver.support.expected_conditions.presence_of_element_located(('css selector', '.secure-content a')))
                    token = driver.find_element('css selector', '.secure-content a').get_attribute('href').split('token=')[-1]

                    url = args.jo_download.format(token = token)
                    driver.get(url)
                    
                    time.sleep(args.timeout)
                    while find_artefacts(joid, temp = True):
                        print('Download in progress, temp file exists, sleeping')
                        time.sleep(args.timeout)
                    assert find_artefacts(joid, temp = False), 'Must have final downloaded file'  
                    print('Page', page, 'OK', joid, 'PDF:', url)

                driver.quit()
                page += 1
                print('Page', page, 'increased')
                if len(jolinks) == 0:
                    if args.debug:
                        print('Debug', args.debug)
                        with open(args.debug, 'w') as f:
                            f.write(page_source)
                    break

            
            except Exception as e:
                print(e)
                print('Page', page, 'big timeout')
                if driver is not None:
                    driver.quit()
                time.sleep(args.timeout_big)
