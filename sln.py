import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from util import init_logging


class GScraper:

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get(url='http://www.google.com?hl=en')
        self.log = init_logging(__name__)

    def get_no_autocompletes(self, item, city):
        # check number of autocompletes for an item in the search bar
        # Return all autocompletes
        search = '"{}" "{}"'.format(item, city)
        field = self.driver.find_element_by_name('q')
        field.clear()
        field.send_keys(search)
        field.send_keys(Keys.ENTER)
        sleep(0.6)
        # ul = self.driver.find_element_by_class_name('erkvQe')
        # li_items = ul.find_elements_by_tag_name('span')
        # no_results = len(li_items)
        # Get the thing that sayws how many results
        results_info = self.driver.find_element_by_id('resultStats').text

        # Find no of google results
        expr = r"([0-9,]+)"
        no_results = re.findall(expr, results_info)
        if not no_results:
            return 0
        # if "No results found" return 0
        topstuff = self.driver.find_element_by_id('topstuff')
        if topstuff and 'No results found' in topstuff.text:
            return 0

        no_results = int(no_results[0].replace(',', ''))

        self.log.debug('{} results for search {}'.format(no_results, search))
        return no_results