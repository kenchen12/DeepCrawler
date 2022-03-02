from requests import Request, Session
import cx_Oracle
import re
import sys
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
pages = {}
def get_tor_links(text):
    links = re.findall(r"[a-zA-Z0-9]{56}\.onion", text)
    return links

def process_links(links):
    if len(links) == 1:
        return
    aux = {}
    new_links = {}
    for link in links:
    #TODO Save referer
        count = aux.get(link, 0)
        aux[link] = count + 1
    for key in aux:
        count = pages.get(key, 0)
        if count == 0:
            new_links[key] = 0
    return new_links
def request(url, method = "GET", data= "", headers={}, proxies = {}):
    if (url == None or url == ""):
        print("invalid url")
        return
    s = Session()
    req = Request(method, "http://"+url, data=data, headers=headers)
    req = req.prepare()
    try: 
        res = s.send(req, proxies=proxies)
    except:
        return "<title> unreachable </title>"
    return str(res.content)

def get_title(html):
    title = re.search(r"<title>.*</title>", html)
    if title == None:
        return ""
    title = title[0][7:-8]

    return title

def save_page_visit(url, title, source, links):
    cursor = connection.cursor()
    cursor.executemany("update pages_list set visited = :1 where url = :2", [(1 ,url)])
    cursor.executemany("insert into pages (url, title, source) values (:1, :2, :3)", [(url, title, source)])
    new_pages = []
    if links != None:
        for link in links:
            new_pages.append((link, depth + 1, 0))
            pages[link] = 1
        cursor.executemany("insert into pages_list (url, depth, visited) values (:1, :2, :3)", new_pages)
    connection.commit()  
def crawl():
    n_pages = len(pages)
    i = 0
    while i < n_pages:
        page = list(pages)[i]
        print("visiting " + page)
        response = request(page, headers=tor_headers, proxies=tor_proxy)
        title = get_title(response)[:1024]
        links = get_tor_links(response)
        new_links = process_links(links)
        save_page_visit(page, title, response, new_links)
        n_new_links = 0; 
        if new_links == None:
            n_new_links = 0
        else:
            n_new_links = len(new_links)
        print("visited " + page + " found " + str(n_new_links) +'\n')
        n_pages = len(pages)
        i = i + 1
        print("progress " + str(i/len(pages)) + '\n')

def get_pages():
    cursor = connection.cursor()
    for row in cursor.execute("select distinct url from APP.PAGES_LIST"):
        pages[row[0]] = 0


crawl()
