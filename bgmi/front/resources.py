# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import datetime

from collections import defaultdict

from icalendar import Calendar, Event

from bgmi.config import SAVE_PATH, FRONT_STATIC_PATH
from bgmi.front.base import BaseHandler, COVER_URL

from bgmi.models import Download, Bangumi, Followed
from bgmi.utils import normalize_path


class BangumiHandler(BaseHandler):
    def get(self, _):
        if os.environ.get('DEV', False):
            with open(os.path.join(SAVE_PATH, _), 'rb') as f:
                self.write(f.read())
                self.finish()
        else:
            self.set_header('Content-Type', 'text/html')
            self.write('<h1>BGmi HTTP Service</h1>')
            self.write('<pre>Please modify your web server configure file\n'
                       'to server this path to \'%s\'.\n'
                       'e.g.\n\n'
                       '...\n'
                       'autoindex on;\n'
                       'location /bangumi {\n'
                       '    alias %s;\n'
                       '}\n'
                       '...\n</pre>' % (SAVE_PATH, SAVE_PATH)
                       )
            self.finish()


class ImageCSSHandler(BaseHandler):
    def get(self):
        data = Followed.get_all_followed(status=None, bangumi_status=None)
        data.extend(self.patch_list)
        for _ in data:
            _['cover'] = '{}/{}'.format(COVER_URL, normalize_path(_['cover']))

        self.set_header('Content-Type', 'text/css; charset=utf-8')
        self.render('templates/image.css', data=data)


class RssHandler(BaseHandler):
    def get(self):
        data = Download.get_all_downloads()
        self.set_header('Content-Type', 'text/xml')
        self.render('templates/download.xml', data=data)


class CalendarHandler(BaseHandler):
    def get(self):
        type_ = self.get_argument('type', 0)

        cal = Calendar()
        cal.add('prodid', '-//BGmi Followed Bangumi Calendar//bangumi.ricterz.me//')
        cal.add('version', '2.0')

        data = Followed.get_all_followed(order='followed.updated_time', desc=True)
        data.extend(self.patch_list)

        if type_ == 0:

            bangumi = defaultdict(list)
            [bangumi[Bangumi.week.index(i['update_time']) + 1].append(i['bangumi_name']) for i in data]

            weekday = datetime.datetime.now().weekday()
            for i, k in enumerate(range(weekday, weekday + 7)):
                if k % 7 in bangumi:
                    for v in bangumi[k % 7]:
                        event = Event()
                        event.add('summary', v)
                        event.add('dtstart', datetime.datetime.now().date() + datetime.timedelta(i - 1))
                        event.add('dtend', datetime.datetime.now().date() + datetime.timedelta(i - 1))
                        cal.add_component(event)
        else:
            data = [bangumi for bangumi in data if bangumi['status'] == 2]
            for bangumi in data:
                event = Event()
                event.add('summary', 'Updated: {}'.format(bangumi['bangumi_name']))
                event.add('dtstart', datetime.datetime.now().date())
                event.add('dtend', datetime.datetime.now().date())
                cal.add_component(event)

        cal.add('name', 'Bangumi Calendar')
        cal.add('X-WR-CALNAM', 'Bangumi Calendar')
        cal.add('description', 'Followed Bangumi Calendar')
        cal.add('X-WR-CALDESC', 'Followed Bangumi Calendar')

        self.write(cal.to_ical())
        self.finish()


class AdminHandler(BaseHandler):
    def get(self, _):
        if os.environ.get('DEV', False):
            with open(os.path.join(FRONT_STATIC_PATH, _), 'rb') as f:
                if _.endswith('css'):
                    self.add_header("content-type", "text/css; charset=UTF-8")
                self.write(f.read())
                self.finish()
        else:
            self.set_header('Content-Type', 'text/html')
            self.write('<h1>BGmi HTTP Service</h1>')
            self.write('<pre>Please modify your web server configure file\n'
                       'to server this path to \'%s\'.\n'
                       'e.g.\n\n'
                       '...\n'
                       'location /admin {\n'
                       '    alias %s;\n'
                       '}\n'
                       '...\n</pre>' % (FRONT_STATIC_PATH, FRONT_STATIC_PATH)
                       )
            self.finish()