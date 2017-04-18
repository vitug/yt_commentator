# coding: utf-8

import time
from splinter import Browser
from stem import Signal
from stem.control import Controller
from IPython.display import clear_output
from fake_useragent import UserAgent
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import json
import datetime
import tinydb
import io
import regex

import common

class Youtube:
    def __init__(self):
        self.log = common.Logger()
        self.settings = common.Settings()
        self.comment_generator = common.CommentGenerator() # генератор комментариев
        self.browser = Browser('chrome')
        self.subscriptions = [] # наши подписки 
        self.comments = common.Comments2() # база данных комментариев
        common.Subscription.url_list = [] # массив наших подписок
        self.sleep_time_after_visit = 5
        self.our_channel_url = u'https://www.youtube.com/channel/'.format(self.settings.get_parameter('address')) # наш канал
        self.max_subscribers_amount = 1000 # подписываемся если количество подписчиком меньше этого числа
        with open('channels.txt', 'r') as f: # файл каналов с которых берем спосок каналов для подписки
            buffer = f.read()
            self.channels_list = buffer.split()
            self.channels_list = filter(bool, self.channels_list)
            self.channels_list = filter(lambda x: not x[0] == '#', self.channels_list)
            #self.channels_list = [x for x in self.channels_list if not x[0] == '#']
        self.all_channel_mode = True
        self.re_is_cyrillic = regex.compile('[\p{IsCyrillic}]', regex.UNICODE)  
        self.comment_not_russian = 'not russian title!'
        self.comment_errors_counter = 0
        
    def login(self):
        browser = self.browser
        browser.visit('https://accounts.google.com')
        browser.fill('Email', self.settings.get_parameter('login'))
        button = browser.find_by_id('next')
        button.click()
        browser.fill('Passwd', self.settings.get_parameter('password'))
        button = browser.find_by_id('signIn')
        button.click()
        self.log.info('login ok')
        time.sleep(self.sleep_time_after_visit)
        
    def get_subscriptions(self):        
        self.browser.visit('https://www.youtube.com/subscription_manager')
        time.sleep(self.sleep_time_after_visit)
        del self.subscriptions[:]
        links = self.browser.find_link_by_partial_href('/channel/')
        for link in links:
            #if link.visible:
            link_url = link['href']
            if not link_url in common.Subscription.url_list and not self.our_channel_url in link_url:
                self.subscriptions.append(common.Subscription(link_url, link.value))
                #print link.value
            #link.click()
        #self.subscriptions.reverse()
        return links
    
    def get_user_subscribers(self, user_url):
        if self.all_channel_mode:
            user_url = user_url.url
        self.browser.visit(user_url + '/channels')
        time.sleep(self.sleep_time_after_visit)
        self.log.info('open user {}'.format(user_url))
        links = self.browser.find_link_by_partial_href('/channel/')
        user_subs = []
        for link in links:
            #if link.visible:
                #print link.find_by_id('href').first
            if link['dir'] == 'ltr' and 'yt-ui-ellipsis' in link['class']:
                #print link.value#, link['href'], link['class']
                subs_url = link['href']
                if not subs_url == self.our_channel_url:
                    user_subs.append(subs_url)
        return user_subs
    
    def get_subscribers_amount(self):
        #elements = self.browser.find_by_xpath('//*[@id="c4-primary-header-contents"]/div/div/div[2]/div/span[2]/span[1]')
        #elements = self.browser.find_by_xpath('//*[@id="c4-primary-header-contents"]/div/div/div[2]/div/span/span[1]')
        #//*[@id="watch7-subscription-container"]/span/span[2]
        elements = self.browser.find_by_id('c4-primary-header-contents')
        spans = elements.find_by_tag('span')
        amount = 0
        for span in spans:
            if span['class'] == 'yt-subscription-button-subscriber-count-branded-horizontal subscribed yt-uix-tooltip':
                amount_str = span['title'].replace(unichr(160),'')
                #print map(ord, list(amount_str))
                amount = int(amount_str)
        return amount
    
    def open_user_page(self, user_url):
        self.browser.visit(user_url)
        time.sleep(self.sleep_time_after_visit) 
        subs = self.get_subscribers_amount() 
        return subs
    
    def open_user_videos_page(self, user_url):
        links = self.browser.find_link_by_partial_href('/videos')
        for link in links:
            if link.visible:
                self.log.info('open videos list {}'.format(link['href']))
                link.click()                
                break
        time.sleep(self.sleep_time_after_visit)
            
    def open_last_user_video(self, user_url, not_commented = True):
        self.open_user_videos_page(user_url)               
        links = self.browser.find_link_by_partial_href('watch?')
        url_found = False
        for link in links:
            #if link.visible:
            #print link.find_by_id('href').first
            #if link['dir'] == 'ltr' and 'yt-ui-ellipsis' in link['class']:
            url = link['href']
            #print link.value, url, link['class']
            if 'yt-uix-sessionlink' in link['class'] and not self.comments.is_video_commented(url):
                self.log.info('open video {}'.format(url))
                #link.click()
                self.browser.visit(url)
                url_found = True
                break
        if not url_found:
            return ''
        else:
            time.sleep(self.sleep_time_after_visit) 
            return url
     
    def find_user_of_current_video(self):
        path = '//*[@id="watch7-user-header"]/a'
        elements = self.browser.find_by_xpath(path)
        return elements.first['href']
    
    def press_like(self):        
        path_notlike = '//*[@id="watch8-sentiment-actions"]/span/span[2]/button'
        path_like = '//*[@id="watch8-sentiment-actions"]/span/span[1]/button'
        elements = self.browser.find_by_xpath(path_like)
        b = elements.first
        #print b['title']
        if b.visible:
            b.click()

    def press_subscribe(self):        
        path = '//*[@id="watch7-subscription-container"]/span/button[1]'
        elements = self.browser.find_by_xpath(path)
        b = elements.first
        already_subscribed = False
        if b['data-is-subscribed']:
            #print 'already subscribed!'
            already_subscribed = True
        else:
            if b.visible:
                b.click()            
        return already_subscribed
            
    #//*[@id="watch7-subscription-container"]/span/span[1]
    #//*[@id="c4-primary-header-contents"]/div/div/div[2]/div/span[2]/span[1]
    def have_it_cyrillic_letters(self, buffer):
        return not len(regex.findall(self.re_is_cyrillic, buffer)) == 0
    
    def comment_on_video(self):
        url = self.browser.driver.current_url
        if not 'watch?' in url:
            self.log.error('not video page!')
            return ''
            #raise Exception('not video page!')
        user = self.find_user_of_current_video()
        self.subscriptions.insert(0, common.Subscription(user, '')) #добавляем пользователя в подписки           
        if self.comments.is_user_commented(user):
            print 'user already commented {}'.format(user)
        if self.comments.is_video_commented(url):
            self.log.error('video already commented!')
            return ''
        #print self.get_subscribers_amount()        
        #проверяем есть ли в названии русские буквы
        title = self.browser.title
        if not self.have_it_cyrillic_letters(title):
            msg = self.comment_not_russian
            self.log.error(msg)
            return msg
        time.sleep(5)
        #raise Exception('like')
        self.browser.driver.execute_script("window.scrollTo(0, 350)")
        time.sleep(10)
        #browser.find_by_tag('html').first.type(Keys.PAGE_DOWN)

        elements_mode = 0 # разные типы комментариев и кнопок
        elements = self.browser.find_by_id('yt-comments-sb-standin')
        if len(elements) == 0:
            # комментарии отключены
            elements = self.browser.find_by_xpath('//*[@id="comment-section-renderer"]/div[1]/div[2]')
            if len(elements) == 0:
                msg = 'Cannot find field for comment!'
                self.log.error(msg)
                raise Exception(msg)
                #return ''
            elements_mode = 1
        if elements.first.visible:
            elements.first.click()
        else:
            raise Exception('Comment element not visible!')
        time.sleep(3)
        print 'elements mode', elements_mode

        #пишем комментарий
        if elements_mode == 0:
            elements = self.browser.find_by_xpath('//*[@id="yt-comments-sb-container"]/div[2]/div[1]/div[1]')
        else:
            elements = self.browser.find_by_xpath('//*[@id="comment-simplebox"]/div[1]')
        if len(elements) == 0:
            raise Exception('Comment element not found!')
            return ''
        elements.first.click()
        comment_text = self.comment_generator.get_comment()
        try:
            elements.first.fill(comment_text)
        except:
            msg = 'Error when fill comment!'
            self.log.error(msg)
            self.comment_errors_counter += 1
            if self.comment_errors_counter > 5:
                raise Exception(msg)
            return ''
        #keys = elements.first.type(comment_text, slowly=True) перестало работать, выдает исключение в цикле
        #for key in keys:
        #    pass

        # нажимаем кнопку
        if elements_mode == 0:
           elements = self.browser.find_by_xpath('//*[@id="yt-comments-sb-container"]/div[2]/div[1]/div[3]/button[2]')
        else:
            elements = self.browser.find_by_xpath('//*[@id="comment-simplebox"]/div[3]/button[2]')
        if len(elements) == 0:
            raise Exception('Cannot find send comment button!')
        elements.first.click()
        time.sleep(3)
        #print elements.first.text  
        #self.comments.add(url)
        self.log.info(u'comment video {}'.format(comment_text))

        #подписка
        subscribed_before = self.press_subscribe()
        if subscribed_before:
            # были подписаны ранее
            self.log.error('already subscribed!')
            #return ''
        time.sleep(3)
        # нажимаем лайк
        self.press_like()

        return comment_text
    
    def get_channel_list(self):
        if not self.all_channel_mode:
            channel_list = self.channels_list        
        else:
            channel_list = self.subscriptions
        return channel_list
#subs_cache = []