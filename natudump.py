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
        
        if any(c not in '?+=0123456789' for c in captcha) or '=' not in captcha:
            print(captcha)
            assert False

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
    parser.add_argument('--jo-search', default  = 'https://www.legifrance.gouv.fr/jorf/jo/{year}?page={page}&pageSize=100', help = 'https://www.legifrance.gouv.fr/jorf/jo/2022/08/31/0201?datePubli=31%2F08%2F2022&nature=DECRET')
    parser.add_argument('--jo-download', default= 'https://www.legifrance.gouv.fr/download/secure/file/{token}')
    parser.add_argument('--years', default = [2016, 2017, 2018, 2019, 2020, 2021], type = int, nargs = '+')
    parser.add_argument('--output-directory', '-o', default = 'jo')
    parser.add_argument('--output-directory-prefix', default = 'C:\\Users\\vadim\\natudump\\')
    parser.add_argument('--chromedriver', default = '/usr/bin/chromedriver')
    parser.add_argument('--timeout', type = float, default = 10.0)
    parser.add_argument('--timeout-big', type = float, default = 30.0)
    parser.add_argument('--page-max', type = int, default = 10)

    args = parser.parse_args()

    os.makedirs(args.output_directory, exist_ok = True)
    
    chrome_prefs = {
        'download.default_directory': args.output_directory_prefix + args.output_directory,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True,
    }
    chrome_options = selenium.webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', chrome_prefs)
    chrome_options.headless = True
    chrome_service = selenium.webdriver.chrome.service.Service(executable_path = args.chromedriver)

    #driver.request_interceptor = driver.response_interceptor = (lambda request, response: print(request.url, request.headers, response.headers))
    
    for year in args.years:
        page = 1
        while True:
            try:
                driver = selenium.webdriver.Chrome(options = chrome_options, service = chrome_service)
                wait = selenium.webdriver.support.ui.WebDriverWait(driver, args.timeout)
                
                url = args.jo_search.format(year = year, page = page)
                
                driver.get(url)
                wait.until(selenium.webdriver.support.expected_conditions.url_to_be(url))

                jolinks = driver.find_elements('partial link text' , 'nominatives')

                print('Page', page, 'found', len(jolinks), 'links')
                
                for jolink in jolinks:
                    joid = jolink.get_attribute('data-textid')
                    if any(('joe_' + joid[-4:] + joid[2:4] + joid[:2]) in fname for fname in os.listdir(args.output_directory)):
                        print('Page', page, 'Skipping', joid)
                        continue

                    print('Page', page, 'Processing', joid)
                    
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
                    print('Page', page, 'OK', joid)
                    time.sleep(args.timeout)

                driver.quit()
                page += 1
                print('Page', page, 'increased')
                if len(jolinks) == 0 or page == args.page_max:
                    break

            
            except Exception as e:
                print(e)
                print('Page', page, 'big timeout')
                driver.quit()
                time.sleep(args.timeout_big)