from urllib import quote
import re
import datetime

from selenium import webdriver
from guessit import guessit
from lxml import html
from imdb import IMDb


class VideoInfoFinder(object):

    def __init__(self):
        self.driver = webdriver.PhantomJS(r'../resources/phantomjs.exe')
        self.imdb = IMDb()

    def get_imbd_data(self, imdb_url):
        imdb_data = {}
        video_id_regex = '\/title\/tt(?P<video_id>\d+)\/'
        match_obj = re.search(video_id_regex, imdb_url)
        if match_obj:
            video_id = match_obj.groupdict()['video_id']
            database_results = self.imdb.get_movie(video_id).data
            for key in ['director', 'genres', 'kind', 'mpaa', 'certificates', 'rating', 'runtimes', 'title', 'year']:
                if key in database_results:
                    if key == 'genres':
                        genres = ', '.join(database_results['genres'])
                        imdb_data['genres'] = genres
                    elif key == 'mpaa':
                        mpaa = database_results['mpaa']
                        rating = None
                        match_obj = re.search('Rated\s(?P<rating>G|PG|PG-13|R|NC-17)', mpaa)
                        if match_obj:
                            rating = match_obj.groupdict()['rating']
                        imdb_data['mpaa'] = rating
                    elif key == 'certificates':
                        if 'mpaa' in imdb_data and imdb_data['mpaa']:
                            pass
                        else:
                            for certificate in database_results['certificates']:
                                if 'USA' in certificate and 'TV' not in certificate:
                                    search_obj = re.search('USA:(?P<rating>G|PG|PG-13|R|NC-17)', certificate)
                                    if search_obj:
                                        imdb_data['mpaa'] = search_obj.groupdict()['rating']
                                        break
                    elif key == 'runtimes':
                        search_obj = re.search('(?P<minutes>\d+)', database_results['runtimes'][0])
                        if search_obj:
                            minutes_str = search_obj.groupdict()['minutes']
                            minutes = int(minutes_str)
                            minutes = str(datetime.timedelta(minutes=minutes))
                        else:
                            minutes = None
                        imdb_data['runtime'] = minutes
                    else:
                        imdb_data[key] = database_results[key]
                else:
                    imdb_data[key] = None

        return imdb_data

    def get_duckduckgo_links(self, search_term):
        urls = []
        search_term = quote(search_term + ' imdb')
        search_url = 'https://duckduckgo.com/?q={}&ia=web'.format(search_term)
        print 'url:', search_url
        self.driver.get(search_url)
        page_source = self.driver.page_source
        tree = html.fromstring(page_source)
        links = tree.xpath("//div[@class='cw']/div[@id='links_wrapper']/div[@id='links']")[0].getchildren()

        for link in links:
            a_tag = link.find("*//a")
            if a_tag is not None:
                link_url = a_tag.get('href')
                urls.append(link_url)

        return urls

    def get_video_info(self, video_title, alternate_name=None):
        video_info = {}

        # Search with file name, if no results are found then search parent folder name
        imdb_link = None
        for search_name in [video_title, alternate_name]:
            if search_name is not None:
                guessit_info = guessit(search_name)
                for guessit_data in ['release_group', 'video_codec', 'website']:
                    search_name = search_name.replace(guessit_info.get(guessit_data, ''), '')
                for term in ['dvdrip']:
                    pattern = re.compile(term, re.IGNORECASE)
                    search_name = pattern.sub('', search_name)
                search_name = search_name.replace('.', ' ')
                search_name = search_name.replace('-', ' ')


                links = self.get_duckduckgo_links(search_name)
                for link_url in links:
                    if 'www.imdb.com' in link_url and '/name/' not in link_url:
                        imdb_link = link_url
                        break
                else:
                    print 'No imdb links found for:{} - {} - {}'.format(search_name, guessit_info, guessit(search_name))
                if imdb_link:
                    break

        if imdb_link is not None:
            print '\t', imdb_link
            video_info.update(guessit_info)
            imdb_data = self.get_imbd_data(imdb_link)
            video_info.update(imdb_data)

            # If the video is a movie, remove any show specific attributes that guessit might have detected
            if video_info.get('kind', None) == 'movie':
                for key in ['episode_title', 'episode', 'season']:
                    if key in video_info:
                        video_info.pop(key)

        else:
            print '\tNo imdb link found'

        if 'format' in video_info and 'screen_size' not in video_info:
            if video_info['format'] == 'DVD':
                video_info['screen_size'] = '480p'

        return video_info


if __name__ == '__main__':
    finder = VideoInfoFinder()
    print finder.get_video_info('28.Weeks.Later.2007.DVDRip.XviD-LPD')
