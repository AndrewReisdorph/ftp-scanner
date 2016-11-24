
from selenium import webdriver
from urllib import quote

from guessit import guessit
from lxml import html

class VideoInfoFinder(object):

    def __init__(self):
        self.driver = webdriver.PhantomJS(r'../resources/phantomjs.exe')

    def get_imbd_data(self, imdb_url):
        imdb_data = {}
        video_name = None
        video_year = None
        video_rating = None
        video_duration = None
        video_imdb_rating = None
        video_genre_list = []
        self.driver.get(imdb_url)
        tree = html.fromstring(self.driver.page_source)
        title_bar_wrapper_elems = tree.xpath("//*[@class='title_bar_wrapper']")
        if title_bar_wrapper_elems != []:
            info = title_bar_wrapper_elems[0]
            video_name = info.find("div[@class='titleBar']/div/h1").text.encode('ascii', 'ignore')
            video_year_elem = info.find("div[@class='titleBar']/div/h1/span")
            if video_year_elem is not None:
                video_year = video_year_elem.text_content().replace('(', '').replace(')', '')

            subtext = info.find("div[@class='titleBar']/div/div[@class='subtext']")
            if subtext is not None:
                content_rating_elem = subtext.find("meta[@itemprop='contentRating']")
                if content_rating_elem is not None:
                    video_rating = content_rating_elem.get('content')
                time_elem = subtext.find("time")
                if time_elem is not None:
                    video_duration = time_elem.text.strip()
                a_elem_list = subtext.xpath("a")
                for a_elem in a_elem_list:
                    if r'/genre/' in a_elem.get('href'):
                        video_genre_list.append(a_elem.text_content())
            rating_divs = tree.xpath("//div[@class='imdbRating']")
            if rating_divs is not None and rating_divs != []:
                rating_div = rating_divs[0]
                rating_span = rating_div.find("div/strong/span[@itemprop='ratingValue']")
                if rating_span is not None:
                    video_imdb_rating = rating_span.text

            imdb_data['name'] = video_name
            imdb_data['year'] = video_year
            imdb_data['rating'] = video_rating
            imdb_data['duration'] = video_duration
            imdb_data['genre'] = video_genre_list
            imdb_data['imdb_rating'] = video_imdb_rating

        return imdb_data

    def get_duckduckgo_links(self, search_term):
        search_url = 'https://duckduckgo.com/?q={}{}'.format(quote(search_term + ' imdb'), '&ia=web')
        print 'url:', search_url
        self.driver.get(search_url)
        page_source = self.driver.page_source
        tree = html.fromstring(page_source)
        links = tree.xpath("//div[@class='cw']/div[@id='links_wrapper']/div[@id='links']")[0].getchildren()

        return links

    def get_video_info(self, video_title, alternate_name=None):
        video_info = {}

        # Search with file name, if no results are found then search parent folder name
        imdb_link = None
        for search_name in [video_title, alternate_name]:
            if search_name is not None:
                guessit_info = guessit(search_name)
                search_term = search_name.replace(guessit_info.get('release_group',''),'')
                search_term = search_term.replace(guessit_info.get('video_codec',''),'')
                search_term = search_term.replace('DVDRip','').replace('DVDrip','')

                links = self.get_duckduckgo_links(search_term)
                for link in links:
                    a_tag = link.find("*//a")
                    if a_tag is not None:
                        link_url = a_tag.get('href')
                        if 'www.imdb.com' in link_url and '/name/' not in link_url:
                            imdb_link = link_url
                            break
                else:
                    print 'No imdb links found for:{} - {} - {}'.format(search_name,guessit_info,guessit(search_name))
                if imdb_link:
                    break

        if imdb_link is not None:
            print '\t', imdb_link
            imdb_data = self.get_imbd_data(imdb_link)
            video_info.update(imdb_data)
            video_info.update(guessit_info)

            if video_info.has_key('rating') and video_info['rating'] and 'TV-' not in video_info['rating']:
                for key in ['episode_title','episode', 'season']:
                    try:
                        video_info.pop(key)
                    except KeyError:
                        pass

        else:
            print '\tNo imdb link found'

        if video_info.has_key('format') and not video_info.has_key('screen_size'):
            if video_info['format'] == 'DVD':
                video_info['screen_size'] = '480p'

        return video_info


if __name__ == '__main__':

    finder = VideoInfoFinder()
    print finder.get_video_info('28.Weeks.Later.2007.DVDRip.XviD-LPD')