from requests import Request, Session
import cx_Oracle
import re
import sys
import validators
#usage crawler.py username password database page
print(sys.argv)

connection = cx_Oracle.connect(user=sys.argv[1], password=sys.argv[2], dsn=sys.argv[3])
tor_headers = {\
    "User-Agent": "Mozilla\/6.0 (Windows NT 10.0; rv:91.0) Gecko\/20100101 Firefox\/91.0",\
    "Accept": "text\/html,application\/xhtml+xml,application\/xml;q=1.9,image/webp,*\/*;q=1.8",\
    "Sec-Fetch-Dest": "document",\
    "Sec-Fetch-Mode": "navigate",\
    "Sec-Fetch-Site": "cross-site",\
    "Sec-Fetch-User": "?1",\
    "Upgrade-Insecure-Requests": "1",\
    "Accept-Encoding": "gzip, deflate",\
    "Connection": "keep-alive"\
}
#socks5h = dns through socks5
tor_proxy = {\
    "http": "socks5h://127.0.0.1:9050",\
    "https": "socks5h://127.0.0.1:9050"\
}
pages = {"http://27m3p2uv7igmj6kvd4ql3cct5h3sdwrsajovkkndeufumzyfhlfev4qd.onion":0, "http://6nhmgdpnyoljh5uzr5kwlatx2u3diou4ldeommfxjz3wkhalzgjqxzqd.onion": 0, "http://2jwcnprqbugvyi6ok2h2h7u26qc6j5wxm7feh3znlh2qu3h6hjld4kyd.onion":0, "http://jgwe5cjqdbyvudjqskaajbfibfewew4pndx52dye7ug3mt3jimmktkid.onion":0}
depth = 0
def get_tor_links(text):
    if text == None:
        return None
    links = re.findall(r"[a-zA-Z0-9]{56}\.onion", text)
    links = ['http://' + link for link in links]
    return links
def get_internal_links(text):
    if text == None:
        return None
    links = re.findall(r"\"\/.*?\"", text)
    links = [link[1:-1] for link in links]
    return links
def process_links(links, internal_links, url):
    global pages
    cursor = connection.cursor()
    new_links = {}
    new_internal_links = {}
    if links != None:
        cursor = connection.cursor()
        aux = {}
        new_pages = []
        referer_list = []
        pages_list = []
        for link in links:
            count = aux.get(link, 0)
            aux[link] = count + 1
        for key in aux:
            count2 = pages.get(key)
            if count2 == None:
                new_pages.append((link, depth + 1, 0))
                new_links[key] = 0
                pages[key] = 0
                referer_list.append((link, url))
                pages_list.append((link, depth + 1, 0))
        cursor = connection.cursor()
        cursor.executemany("insert into pages_list (url, depth, visited) values (:1, :2, :3)", pages_list)
        connection.commit()
        cursor = connection.cursor()
        cursor.executemany("insert into pages_referer (url, referer) values (:1, :2)", referer_list)
        connection.commit()
        print("    "+str(len(new_links)) + " new links")
        print()
    if internal_links != None:
        aux = {}
        new_pages2 = []
        internal_links = [url+link for link in internal_links]
        for link in internal_links:
            if validators.url(link):
                count = aux.get(link, 0)
                aux[link] = count + 1
        referer_list = []
        pages_list = []
        for key in aux:
            count3 = pages.get(key)
            referer_list.append((link, url))
            
            if count3 == None:
                new_pages2.append((link, depth + 1, 0))
                new_internal_links[key] = 0
                pages_list.append((link, depth + 1, 0))
                pages[key] = 0
        cursor = connection.cursor()
        cursor.executemany("insert into pages_list (url, depth, visited) values (:1, :2, :3)", new_pages2)
        connection.commit()
        cursor = connection.cursor()
        cursor.executemany("insert into pages_referer (url, referer) values (:1, :2)", referer_list)
        connection.commit()
        print("    "+str(len(new_internal_links)) + " new internal links")
        print()
        
    return (new_links, new_internal_links)
def request(url, method = "GET", data= "", headers={}, proxies = {}):
    if not (validators.url(url)):
        print("invalid url")
        return
    s = Session()
    req = Request(method, url, data=data, headers=headers)
    req = req.prepare()
    try: 
        res = s.send(req, proxies=proxies)
    except:
        return "<title>unreachable</title>"
    return str(res.content)

def get_title(html):
    if html == None:
        return ""

    title = re.search(r"<title.*?>.*?</title>", html)
    if title == None:
        return ""
    title = title[0]
    
    return title

def save_page_visit(url, title, source):
    cursor = connection.cursor()
    cursor.executemany("update pages_list set visited = :1 where url = :2", [(1 ,url)])
    if len(url) > 71:
        s_source = None
    else:
        s_source = source
    cursor.executemany("insert into pages (url, title, source) values (:1, :2, :3)", [(url, title, s_source)])
    connection.commit()  
def crawl():
    n_pages = len(pages)
    i = 0
    while i < n_pages:
        page = list(pages)[i]
        if(len(page) > 1024):
            i = i+1
            continue
        if (page[0:7] != "http://" and page[0:8] != "https://"):
            page = "http://" + page
        if page[-1] == '/':
            page = page[0:-1]
        print("visiting " + page)
        response = request(page, headers=tor_headers, proxies=tor_proxy)
        
        title = get_title(response)[:1024]
        links = get_tor_links(response)
        
        internal_links = get_internal_links(response)
        (new_links, new_internal_links) = process_links(links, internal_links, page)
        save_page_visit(page, title, response)

        n_pages = len(pages)
        i = i + 1
        print("progress " + str(i/len(pages)) + '\n')

def get_pages():
    cursor = connection.cursor()
    for row in cursor.execute("select distinct url from APP.PAGES_LIST"):
        pages[row[0]] = 0


crawl()
