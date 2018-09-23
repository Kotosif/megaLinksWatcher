import re
import urllib.request
import urllib.parse
import json


def readLinkFromFile(filename):
    # Assumes the link is the first line of the file
    try:
        linkFile = open(filename, "r")
        link = linkFile.readline()
        if link == "":
            return None
        else:
            return link
    except (IOError, FileExistsError, FileNotFoundError):
        return None


def extractURLDetails(link):
    regex = re.compile("/(.)/thread/(.*)$")
    match = regex.search(link)
    if match is None:
        raise LookupError(
            "Could not find a regex match. Is the URL you gave formatted correctly?"
        )
    board = match.group(1)
    threadNumber = match.group(2)
    return (board, threadNumber)


def getThreadPostsInJSONFormat(link):
    board, threadNumber = extractURLDetails(link)
    try:
        if "archived.moe" in link:
            print("Archive link given")
            print("Sending HTTP request to get thread in HTML format...")
            req = urllib.request.Request(
                link,
                None,
                headers={
                    'User-Agent':
                    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7',
                    'Accept':
                    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                })
            response = urllib.request.urlopen(req)
            return [response.read().decode('utf-8')]
        else:
            apiurl = "http://a.4cdn.org/%s/thread/%s.json" % (board,
                                                              threadNumber)
            print("Sending HTTP request to get thread in JSON format...")
            response = urllib.request.urlopen(apiurl)
            jsonResponse = json.loads(response.read().decode('utf-8'))
            posts = jsonResponse["posts"]
            return posts
    except urllib.error.HTTPError as httpError:
        print(httpError.headers)
        print(httpError)
        exit(-1)


def findAllMegaLinks(posts, responseType):
    # posts - a list of the posts as a json object returned from the 4chan API
    regex = re.compile("(https://mega\.nz/#.?![\w!_-]+)( |<|$)")
    megaLinks = []
    matches = []
    print("Finding all mega links in thread...")
    for post in posts:
        if responseType == "json":
            comment = post["com"]
            matches = regex.findall(comment)
        elif responseType == "html":
            matches = regex.findall(post)
        for matchedLink, _extras in matches:
            if not matchedLink in megaLinks:
                megaLinks.append(matchedLink)
    return megaLinks


# Main Function
if __name__ == "__main__":
    # Config init
    linkFilename = "url.txt"

    # Main program execution
    print("This is an application for watching Mega.nz links on 4chan threads")
    print(
        "By default, this application will look for a %s file to obtain the link of the thread to watch"
        % linkFilename)
    print("Now looking for %s file..." % linkFilename)
    link = readLinkFromFile(linkFilename)
    if link is None:
        print("Could not find %s file. Please input the URL manually:" %
              linkFilename)
        while (link is None or link == ""):
            link = input()
            if (link is None or link == ""):
                print("Please enter a URL")
    responseType = ""
    if "archived.moe" in link:
        responseType = "html"
    else:
        responseType = "json"
    posts = getThreadPostsInJSONFormat(link)
    megaLinks = findAllMegaLinks(posts, responseType)
    print(megaLinks)
