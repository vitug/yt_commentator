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
import logging

class Logger():
    def __init__(self):
        self.file_name = 'youtube.log'
        logging.basicConfig(level=logging.DEBUG)
        #logging.basicConfig(filename=self.file_name, filemode='a', level=logging.DEBUG)
        
        self.logger = logging.getLogger('youtube')
        self.close()
        self.logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(self.file_name, mode = 'a')
        fh.setLevel(logging.DEBUG)
        self.file_handler = fh

        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        #ch.setLevel(logging.DEBUG)

        # add the handlers to the logger
        self.logger.addHandler(fh)
        #self.logger.addHandler(ch)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #formatter = logging.Formatter('%(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # now if you use logger it will not log to console.
        #self.logger.propagate = False
        # logging.basicConfig(filename=self.file_name, filemode='w', level=logging.DEBUG)
    def info(self, msg):
        self.logger.info(msg)
        #logging.info(msg)

    def error(self, msg):
        self.logger.error(msg)
        #logging.error(msg)
        
    def close(self):
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)  
            
class Subscription:
    url_list = []
    def __init__(self, url, name = ''):
        self.name = name
        self.url = url
        if not url in Subscription.url_list:
            Subscription.url_list.append(url)
            
class Settings:
    def __init__(self):
        base = {}
        self.filename = 'settings.json'
        try:
            with open(self.filename, mode='r') as f:
                base = json.load(f)
                self.db = base['settings']
        except:
            self.db = [dict(address='', login='', password='')]
            self.save()
            #raise Exception('Fill {}!'.format(self.filename))
            
    def save(self):
        with open(self.filename, 'w') as f: 
            base = dict(settings=self.db)
            json.dump(base,f,indent=2)  
            
    def get_parameter(self, name):
        return self.db[0][name]
            
        
class Comments:
    def __init__(self):
        # dict()
        self.date_format = '%Y-%m-%d %H:%M:%S,%f'
        base = {}
        try:
            with open('comments.json', mode='r') as f:
                base = json.load(f)
                self.dates = base['dates']
                self.users = base['users']
                self.videos = base['videos']
                self.comments = base['comments']
        except:
            self.dates = []
            self.users = []
            self.videos = []
            self.comments = []
            
    def save(self):
        with open('comments.json', 'w') as f: 
            base = dict(dates=self.dates, users=self.users, videos=self.videos, comments=self.comments)
            json.dump(base,f,indent=2)
            
    def add(self, user, video, comment = ''):
        if not user in self.users or not video in self.videos or not comment in self.comments:
            self.dates.append(datetime.datetime.now().strftime(self.date_format))
            self.users.append(user)
            self.videos.append(video)
            self.comments.append(comment)
        else:
            raise Exception('duplicate!')
            
    def is_video_commented(self, video):
        return video in self.videos

class Comments2:
    def __init__(self):
        # dict()
        self.date_format = '%Y-%m-%d %H:%M:%S,%f'
        self.file_name = 'comments.json'
        self.db_all = tinydb.TinyDB(self.file_name)
        self.db = self.db_all.table('comments')
        self.users_db = self.db_all.table('users')
        self.query = tinydb.Query()
            
    def close(self):
        self.db_all.close()
 
    def add_user(self, user, subs_amount):
        query = self.query
        result = self.users_db.search((query.user == user))
        if len(result) == 0:
            date = datetime.datetime.now()
            self.users_db.insert(dict(date = date, user = user, subscribers = subs_amount))
            
    def add(self, user, video, comment = ''):
        query = self.query
        result = self.db.search((query.user == user) & (query.video == video) & (query.comment == comment))
        if len(result) == 0:
            date = datetime.datetime.now()
            self.db.insert(dict(date = date, user = user, video = video, comment = comment))
        else:
            print result
            raise Exception('duplicate!')
     
    def video_comments(self, video):
        result = self.db.search(self.query.video == video)
        return result
    
    def user_comments(self, user):
        result = self.db.search(self.query.user == user)
        return result   
    
    def is_user_commented(self, user):
        result = self.user_comments(user)
        #print result
        return not len(result) == 0    
    
    def is_video_commented(self, video):
        result = self.video_comments(video)
        #print result
        return not len(result) == 0
    
    def indent(self):
        with open(self.file_name, mode='r') as f:
            base = json.load(f) 
        with open(self.file_name, 'w') as f: 
            json.dump(base,f,indent=2)                
            
class CommentGenerator:
    index = 0
    def __init__(self):        
        with io.open('comments_list.txt', mode='r', encoding = 'utf8') as f:
            buffer = f.read()
            #buffer = buffer.decode('utf8').encode('cp1251')
            self.comments = buffer.splitlines()
            self.comments = filter(bool, self.comments)
            map(unicode.strip, self.comments)
            
    def get_comment(self):
        #i = np.random.randint(len(self.comments))
        i = CommentGenerator.index
        CommentGenerator.index += 1
        if CommentGenerator.index == len(self.comments):
            CommentGenerator.index =0
        new = self.comments[i]
        if not new:
            raise 'empty!'
        return new