import scrapy
from lxml import etree
import re
import os
import hashlib
from pprint import pprint
from CachedPageFinder.items import CachedpagefinderItem

class CachedPageCrawler(scrapy.Spider):
    name = 'cpc'
    cachedServerDomain = 'https://web.archive.org'
    girlspicMain = 'http://plus.girlspic.jp'
    html_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'htmls')
    unhandle_links = []
    prepare_Links = []
    done_links = []
    #allowed_domains = ['www.google.com']

    start_urls = [
        cachedServerDomain+'/web/*/'+girlspicMain+'/*'
    ]

    def ignore(self, url):
        if re.search('http://plus.girlspic.jp/(\d+)/images', url) != None or \
           re.search('http://plus.girlspic.jp/image/(\d+)/(\d+)', url) != None or \
           re.search('http://plus.girlspic.jp/(\d+)/favoriteImages', url) != None:
            return False
        elif re.search('http://plus.girlspic.jp/plusUsers/(\d+)', url) != None :
            # Not so much info here.
            return True
        elif re.search('http://plus.girlspic.jp/(\d+)/(followers|following)', url) != None:
            # Cached Page server doesn't have so much this case and
            # most these case have favorite or images page).
            # So we don't care here.
            return True
        elif re.search('http://plus.girlspic.jp/(.)*(search|login)', url) != None:
            # Unfortunately we can't handle this case with server alive.
            return True
        else:
            return True


    def extract_img_url(self, url):
        if re.search('http(s)*://(.)*.(jpg|png)', url) != None:
            return re.search('http(s)*://(.)*.(jpg|png)', url).group(0), True
        elif re.search('http(s)*://(.)*\?', url) != None:
            temp = re.search('http(s)*://(.)*\?', url).group(0)
            return temp[:-1], False
        else:
            return url, False

    def parse_personal_page(self, response):
        url = re.search('https://web.archive.org/web/(\d)+/http://plus.girlspic.jp/(\d+)/images', response.url).group(0).split('/')
        user_id = url[-2]
        timestamp = url[4]

        html = etree.HTML(response.body)

        # version 1
        result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/div[2]/h1')
        if len(result) > 0:
            item = CachedpagefinderItem()
            item['personal'] = {}
            item['personal']['record'] = []
            item['image_urls'] = []
            info = {}

            info['Timestamp'] = timestamp
            info['Id'] = user_id
            info['Name'] = result[0].text
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/div[2]/p/img')
            info['FaceUrl'], download = self.extract_img_url(result[0].attrib['src'])
            if download == True:
                item['image_urls'].append(info['FaceUrl'])
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/p/span')
            if len(result) > 0:
                _Category = result[0].text
            else:
                _Category = None
            if _Category != None:
                info['Category'] = _Category
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/div[2]/div/dl/dd/span')
            if len(result) == 4:
                info['LoveCnt'] = result[0].text
                info['FollowCnt'] = result[2].text
                info['FollowedCnt'] = result[3].text
            elif len(result) == 3:
                info['LoveCnt'] = result[0].text
                info['FollowCnt'] = result[1].text
                info['FollowedCnt'] = result[2].text
            else:
                raise

            result = html.xpath('//*[@id="girlspic"]/div[3]/div[3]/div[1]/p')
            if len(result) > 0:
                info['Detail'] = ' '.join(result[0].itertext())

            result = html.xpath('//*[@id="girlspic"]/div[3]/div[3]/div[3]/ul/li')
            if len(result) > 0:
                info['Img'] = []

            for elt in result:
                if len(elt.xpath('./div[1]/p/a')) > 0:
                    temp = {}
                    url = re.search('http://plus.girlspic.jp/image/(\d+)/(\d+)', elt.xpath('./div[1]/p/a')[0].attrib['href']).group(0).split('/')
                    temp['Id'] = url[-1]
                    if _Category != None:
                        temp['Category'] = _Category
                    temp['Url'], download = self.extract_img_url(elt.xpath('./div[1]/p/a/img')[0].attrib['src'])
                    if download == True:
                        item['image_urls'].append(temp['Url'])
                    temp['LoveCnt'] = elt.xpath('./div[2]/p[1]/span')[0].text
                    temp['Time'] = elt.xpath('./div[2]/p[2]/text()')[0]
                    info['Img'].append(temp)

            item['personal']['record'].append(info)
            yield item

        # version 2
        result = html.xpath('//*[@id="wrapper"]/section[2]/section[2]/div/h2')
        if len(result) > 0:
            item = CachedpagefinderItem()
            item['personal'] = {}
            item['personal']['record'] = []
            item['image_urls'] = []
            info = {}

            info['Timestamp'] = timestamp
            info['Id'] = user_id
            info['Name'] = result[0].text
            result = html.xpath('//*[@id="wrapper"]/section[2]/section[1]/div/img')
            info['FaceUrl'], download = self.extract_img_url(result[0].attrib['data-original'])
            if download == True:
                item['image_urls'].append(info['FaceUrl'])
            result = html.xpath('//*[@id="wrapper"]/section[2]/section[2]/section/div[2]/a/text()')
            info['Category'] = ''.join(result).replace('\n','')
            _Category = info['Category']
            result = html.xpath('//*[@id="wrapper"]/section[2]/section[2]/section/div[1]/p[2]/text()')
            info['LoveCnt'] = result[0]
            result = html.xpath('//*[@id="wrapper"]/section[2]/section[2]/ul/li[2]/a/p[1]')
            info['FollowCnt'] = result[0].text
            result = html.xpath('//*[@id="wrapper"]/section[2]/section[2]/ul/li[3]/a/p[1]')
            info['FollowedCnt'] = result[0].text

            result = html.xpath('//*[@id="myPhotoAll"]/ul/li/div')
            if len(result) > 0:
                info['Img'] = []

            for elt in result:
                temp = {}
                url = re.search('http://plus.girlspic.jp/image/(\d+)/(\d+)', elt.xpath('./a')[0].attrib['href']).group(0).split('/')
                temp['Id'] = url[-1]
                temp['Category'] = _Category
                temp['Url'], download = self.extract_img_url(elt.xpath('./a/img')[0].attrib['data-original'])
                if download == True:
                    item['image_urls'].append(temp['Url'])
                temp['LoveCnt'] = elt.xpath('./div/div/p')[0].text
                temp['Time'] = elt.xpath('./p')[0].text
                info['Img'].append(temp)

            item['personal']['record'].append(info)

            # others
            result = html.xpath('//*[@id="wrapper"]/section[5]/ul/li/div')
            for elt in result:
                info = {}
                url = re.search('http://plus.girlspic.jp/image/(\d+)/(\d+)', elt.xpath('./a')[0].attrib['href']).group(0).split('/')
                info['Id'] = url[-2]
                info['Img'] = []
                temp = {}
                temp['Id'] = url[-1]
                temp['Category'] = _Category
                temp['Url'], download = self.extract_img_url(elt.xpath('./a/img')[0].attrib['data-original'])
                if download == True:
                    item['image_urls'].append(temp['Url'])
                temp['LoveCnt'] = elt.xpath('./div/div/p')[0].text
                info['Img'].append(temp)
                item['personal']['record'].append(info)
            yield item
        self.done_links.append(response.url)


    def parse_image_page(self, response):
        url = re.search('https://web.archive.org/web/(\d)+/http://plus.girlspic.jp/image/(\d+)/(\d+)', response.url).group(0).split('/')
        user_id = url[-2]
        timestamp = url[4]

        html = etree.HTML(response.body)

        result = html.xpath('//*[@id="girlspic"]/div[3]/div[1]/div/div[2]/div[1]/div/div/p[1]/a')
        if len(result) > 0:
            item = CachedpagefinderItem()
            item['personal'] = {}
            item['personal']['record'] = []
            item['image_urls'] = []
            info = {}

            info['Timestamp'] = timestamp
            info['Id'] = user_id
            info['Name'] = result[0].text
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[1]/div/div[2]/div[1]/div/p/a/img')
            info['FaceUrl'], download = self.extract_img_url(result[0].attrib['src'])
            if download == True:
                item['image_urls'].append(info['FaceUrl'])
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[1]/div/div[2]/div[1]/div/div/p[2]/text()')
            if len(result) == 0:
                result = html.xpath('//*[@id="slider"]/div/div/div[2]/div[1]/dl/dd/ul/li/a/text()')
            _Category = result[0]
            info['Category'] = _Category
            info['Img'] = []
            temp = {}
            temp['Id'] = url[-1]
            result = html.xpath('//*[@id="slider"]/div/div/div[2]/div[1]/dl/dd/ul/li/a')
            temp['Category'] = _Category
            result = html.xpath('//*[@id="slider"]/div/div/div[1]/ul/li/div/p/img')
            temp['Url'], download = self.extract_img_url(result[0].attrib['src'])
            if download == True:
                item['image_urls'].append(temp['Url'])
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[1]/div/div[2]/div[2]/div[1]/p')
            if len(result) > 0:
                temp['Detail'] = ' '.join(result[0].itertext())
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[1]/div/div[2]/div[2]/div[1]/ul/li/a/text()')
            temp['Tag'] = result
            result = html.xpath('//*[@id="slider"]/div/div/div[2]/div[2]/div/div/p')
            temp['LoveCnt'] = result[0].text
            result = html.xpath('//*[@id="slider"]/div/div/div[2]/div[1]/p/text()')
            temp['Time'] = result[0]
            info['Img'].append(temp)
            item['personal']['record'].append(info)
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[1]/div/div[2]/div/ul/li')
            for elt in result:
                if len(elt.xpath('./div[1]/p/a')) > 0:
                    info = {}
                    url = re.search('http://plus.girlspic.jp/image/(\d+)/(\d+)', elt.xpath('./div[1]/p/a')[0].attrib['href']).group(0).split('/')
                    info['Id'] = url[-2]
                    info['Img'] = []
                    temp = {}
                    temp['Id'] = url[-1]
                    temp['Category'] = _Category
                    temp['Url'], download = self.extract_img_url(elt.xpath('./div[1]/p/a/img')[0].attrib['src'])
                    if download == True:
                        item['image_urls'].append(temp['Url'])
                    temp['Time'] = elt.xpath('./div[3]/p/text()')[0]
                    info['Img'].append(temp)
                    item['personal']['record'].append(info)
            yield item
        self.done_links.append(response.url)


    def parse_favorite_page(self, response):
        url = re.search('https://web.archive.org/web/(\d)+/http://plus.girlspic.jp/(\d+)/favoriteImages', response.url).group(0).split('/')
        user_id = url[-2]
        timestamp = url[4]

        html = etree.HTML(response.body)

        result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/div[2]/h1')
        if len(result) > 0:
            item = CachedpagefinderItem()
            item['personal'] = {}
            item['personal']['record'] = []
            item['image_urls'] = []
            info = {}

            info['Timestamp'] = timestamp
            info['Id'] = user_id
            info['Name'] = result[0].text
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/div[2]/p/img')
            info['FaceUrl'], download = self.extract_img_url(result[0].attrib['src'])
            if download == True:
                item['image_urls'].append(info['FaceUrl'])
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/p/span')
            if len(result) > 0:
                _Category = result[0].text
            else:
                _Category = None
            if _Category != None:
                info['Category'] = _Category
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[2]/div[2]/div/dl/dd/span')
            if len(result) == 4:
                info['LoveCnt'] = result[0].text
                info['FollowCnt'] = result[2].text
                info['FollowedCnt'] = result[3].text
            elif len(result) == 3:
                info['LoveCnt'] = result[0].text
                info['FollowCnt'] = result[1].text
                info['FollowedCnt'] = result[2].text
            else:
                raise
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[3]/div[1]/p')
            if len(result) > 0:
                info['Detail'] = ' '.join(result[0].itertext())
            item['personal']['record'].append(info)
            result = html.xpath('//*[@id="girlspic"]/div[3]/div[3]/div[3]/ul/li')
            for elt in result:
                info = {}
                url = re.search('http://plus.girlspic.jp/image/(\d+)/(\d+)', elt.xpath('./div[1]/a')[0].attrib['href']).group(0)
                info['Id'] = url.split('/')[-2]
                info['Img'] = []
                temp = {}
                temp['Id'] = url.split('/')[-1]
                if _Category != None:
                    temp['Category'] = _Category
                temp['Url'], download = self.extract_img_url(elt.xpath('./div[1]/p/a/img')[0].attrib['src'])
                if download == True:
                    item['image_urls'].append(temp['Url'])
                temp['LoveCnt'] = elt.xpath('./div[2]/p[1]/span')[0].text
                temp['Time'] = elt.xpath('div[2]/p[2]/text()')[0]
                info['Img'].append(temp)
                item['personal']['record'].append(info)
            yield item
        self.done_links.append(response.url)

    def parse_link(self, response):
        # it means cached server error
        if len(response.xpath('//*[@id="error"]')) != 0 :
            self.done_links.append(response.url+' @ErrorPage')
            return

        # backup html to local
        '''
        if re.search('^file', response.url) == None :
            md5_url = hashlib.md5(response.url)
            html_fname = os.path.join(self.html_path, md5_url.hexdigest()+'.html')
            if os.path.exists(self.html_path) != True:
                try:
                    os.makedirs(self.html_path)
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            file = open(html_fname, 'w')
            file.write(response.body)
            file.close
        '''

        if re.search('http://plus.girlspic.jp/(\d+)/images', response.url) != None:
            return self.parse_personal_page(response)
        elif re.search('http://plus.girlspic.jp/image/(\d+)/(\d+)', response.url) != None:
            return self.parse_image_page(response)
        elif re.search('http://plus.girlspic.jp/(\d+)/favoriteImages', response.url) != None:
            return self.parse_favorite_page(response)

        self.done_links.append(response.url+' @UnhandleCase')
        return


    def spreadLink(self, response):
        html = etree.HTML(response.body)
        search_result = html.xpath('//div[@class="pop"]/ul/li/a')
        for elt in search_result:
            url = self.cachedServerDomain + elt.attrib['href']
            md5_url = hashlib.md5(url)
            html_fname = os.path.join(self.html_path, md5_url.hexdigest()+'.html')

            self.prepare_Links.append(url)
            if os.path.exists(html_fname) == True:
                yield scrapy.Request('file:////'+html_fname, self.parse_link)
            else:
                yield scrapy.Request(url, self.parse_link)


    def parse(self, response):
        '''
        html = etree.HTML(response.body)
        search_result = html.xpath('//*[@id="resultsUrl"]/tbody/tr')
        for elt in search_result:
            url = elt.findall('./td[1]/a')[0].text

            if self.ignore(url) == False:
                yield scrapy.Request(self.cachedServerDomain+'/web/*/'+url, self.spreadLink)
            else:
                self.unhandle_links.append(self.cachedServerDomain+'/web/2/'+url)
        '''
        # test spread code

        table =[
            self.cachedServerDomain+'/web/*/'+'http://plus.girlspic.jp/1247/images',
            self.cachedServerDomain+'/web/*/'+'http://plus.girlspic.jp/111842/images',
            self.cachedServerDomain+'/web/*/'+'http://plus.girlspic.jp/image/100100/572913',
            self.cachedServerDomain+'/web/*/'+'http://plus.girlspic.jp/100100/favoriteImages',
            self.cachedServerDomain+'/web/*/'+'http://plus.girlspic.jp/107601/images', #fail link
            self.cachedServerDomain+'/web/*/'+'http://plus.girlspic.jp/162115/images', #fail link
            self.cachedServerDomain+'/web/*/'+'http://plus.girlspic.jp/image/435676/2105021',
        ]

        #yield scrapy.Request(table[0], self.spreadLink) #2
        #yield scrapy.Request(table[1], self.spreadLink) #7
        #yield scrapy.Request(table[2], self.spreadLink) #5
        #yield scrapy.Request(table[3], self.spreadLink) #20
        yield scrapy.Request(table[6], self.spreadLink)

        '''
        table = []
        file = open('Log/FailLink.txt', 'r')
        for line in file:
            table.append(line)
        file.close()
        for item in table:
            url = item.strip()
            yield scrapy.Request(url, self.parse_link)
        '''