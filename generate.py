from datetime import datetime
import glob
import json
import os
import sys
import re
import urllib
from jinja2 import Environment, PackageLoader

if sys.version_info.major < 3:
    exit("This code requires Python 3.\nThis is {}".format(sys.version))

def main():
    conferences, topics = read_files()
    #print(conferences)
    generate_pages(conferences, topics)

def read_files():
    conferences = []
    topics = {}

    for filename in glob.glob("data/*.txt"):
        print("Reading {}".format(filename))
        conf = {}
        try:
            this = {}
            nickname = os.path.basename(filename)
            nickname = nickname[0:-4]
            #print(nickname)
            this['nickname'] = nickname
            with open(filename, encoding="utf-8") as fh:
                for line in fh:
                    line = line.rstrip('\n')
                    if re.search(r'\A\s*#', line):
                        continue
                    if re.search(r'\A\s*\Z', line):
                        continue
                    k,v = re.split(r'\s*:\s*', line, maxsplit=1)
                    this[k] = v
            conferences.append(this)

            my_topics = []
            for t in re.split(r'\s*,\s*', this['topics']):
                p = topic2path(t)
                my_topics.append({
                    'name' : t,
                    'path' : p,
                })
                if p not in topics:
                    topics[p] = {
                        'name': t,
                        'events' : []
                    }
                topics[p]['events'].append(this)
            this['topics'] = my_topics
        except Exception as e:
            exit("ERROR: {} in file {}".format(e, filename))

    return sorted(conferences, key=lambda x: x['start_date']), topics

def generate_pages(conferences, topics):
    env = Environment(loader=PackageLoader('conf', 'templates'))
    if not os.path.exists('html/'):
        os.mkdir('html/')

    event_template = env.get_template('event.html')
    if not os.path.exists('html/e/'):
        os.mkdir('html/e/')
    for event in conferences:
        #print(event['nickname'])

        tweet_me = event['name']
        tweet_me += ' on ' + event['start_date']
        if event['twitter']:
            tweet_me += ' @' + event['twitter']
        tweet_me += " " + event['url']
        for t in event['topics']:
            tweet_me += ' #' + t['name']
        #tweet_me += ' via @szabgab'
        tweet_me += ' via http://conferences.szabgab.com/'

        event['tweet_me'] = urllib.parse.quote(tweet_me)
        try:
            with open('html/e/' + event['nickname'], 'w', encoding="utf-8") as fh:
                fh.write(event_template.render(
                    h1          = event['name'],
                    title       = event['name'],
                    event = event,
            ))
        except Exception as e:
            print("ERROR: {}".format(e))

    now = datetime.now().strftime('%Y-%m-%d')
    #print(now)
    future = list(filter(lambda x: x['start_date'] >= now, conferences))
    #print(future)
    main_template = env.get_template('index.html')
    with open('html/index.html', 'w', encoding="utf-8") as fh:
        fh.write(main_template.render(
            h1          = 'Tech related conferences',
            title       = 'Tech related conferences',
            conferences = future,
        ))

    with open('html/conferences', 'w', encoding="utf-8") as fh:
        fh.write(main_template.render(
            h1          = 'Tech related conferences',
            title       = 'Tech related conferences',
            conferences = conferences,
        ))

    cfp = list(filter(lambda x: 'cfp_date' in x and x['cfp_date'] >= now, conferences))
    cfp.sort(key=lambda x: x['cfp_date'])
    cfp_template = env.get_template('cfp.html')
    with open('html/cfp', 'w', encoding="utf-8") as fh:
        fh.write(cfp_template.render(
            h1          = 'Call for Papers',
            title       = 'Call of Papers',
            conferences = cfp,
        ))


    no_code = list(filter(lambda x: not x.get('code_of_conduct'), conferences))
    code_template = env.get_template('code-of-conduct.html')
    with open('html/code-of-conduct', 'w', encoding="utf-8") as fh:
        fh.write(code_template.render(
            h1          = 'Code of Conduct',
            title       = 'Code of Conduct (or lack of it)',
            conferences = no_code,
        ))

    topic_template = env.get_template('topic.html')
    if not os.path.exists('html/t/'):
        os.mkdir('html/t/')
    for t in topics.keys():
        with open('html/t/' + t, 'w', encoding="utf-8") as fh:
            fh.write(topic_template.render(
                h1          = topics[t]['name'],
                title       = topics[t]['name'],
                conferences = sorted(topics[t]['events'], key=lambda x: x['start_date']),
            ))

        


def topic2path(tag):
    return re.sub(r'[\W_]+', '-', tag.lower())

main()

# vim: expandtab
