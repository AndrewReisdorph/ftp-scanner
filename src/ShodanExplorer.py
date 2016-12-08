import requests
from lxml import html

USER_AGENT = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/' \
             r'537.36'


class ShodanExplorer(object):

    def __init__(self):
        self.session = requests.session()
        self.search_url = r'https://www.shodan.io/search'
        self.header = {'User-Agent': USER_AGENT}
        self.init_cookies()
        self.org_list = ['Comcast Cable', 'AT&T', 'Time Warner Cable', 'CenturyLink', 'Charter', 'Verizon', 'Cox',
                         'Optimum', 'Frontier', 'Suddenlink', 'Earthlink', 'Windstream', 'Cable One', 'NetZero', 'Juno',
                         'AOL', 'MSN', 'Mediacom']

    def init_cookies(self):
        self.session.get(r'https://account.shodan.io/login')

    def login(self):
        data = {'username': 'meltztest',
                'password': 'shodantest',
                'grant_type': 'password',
                'continue': r'https://account.shodan.io',
                'login_submit': 'Log in'}

        response = self.session.post(r'https://account.shodan.io/login', data=data, headers=self.header)

        if 'Account Overview' in response.text:
            return True

        return False

    def get_query_results(self, query):
        ip_list = []
        search_url = r'https://www.shodan.io/search'
        params = {'query': query,
                  'page': 1}
        for page_num in range(1, 6):
            params['page'] = page_num
            response = self.session.get(search_url, params=params, headers=self.header)
            tree = html.fromstring(response.content)
            page_ips = [div.text_content().strip() for div in tree.xpath(r'//div[@class="ip"]')]
            if not page_ips:
                break
            ip_list += page_ips

        return ip_list

if __name__ == '__main__':
    e = ShodanExplorer()
    login_status = e.login()
    print "Login: {}".format(login_status)

    if login_status:
        print e.get_query_results(r'ftp country:"US" port:"21" org:"Comcast Cable"')
