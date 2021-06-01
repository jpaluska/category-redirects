import pywikibot
import requests
import json
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Number of pages to process per run
BATCH_SIZE = 5

#Name/path of file containing title of last processed page and namespace
FILE_NAME = "cat-redirects-last.txt"

def getURL():
	"""
	Gets the API URL of the wiki.

	Returns:
		URL (str): API url of the wiki
	"""

	site = pywikibot.getSite()
	URL = site.protocol() + "://" + site.hostname() + site.scriptpath() + "/api.php"
	return URL

def getRedirects(URL):
	"""
	Gets a list of all the pages containing redirects. Only returns redirects not already in Category:Redirects.

	Parameters:
		URL (str): the API URL of the wiki
	
	Returns:
		output (list): a list with titles of pages containing redirects
	"""

	if not os.path.isfile(FILE_NAME):
		last = ''
		ns = -2
	else:
		with open(FILE_NAME) as reader:
			last = reader.readline()
			ns = int(reader.readline())

	output = set()
	session = requests.Session()

	PARAMS = {
	"action": "query",
	"generator": "allredirects",
	"garnamespace": ns,
	"garlimit": BATCH_SIZE,
	"format": "json",
	"garcontinue": last
	}
	
	if not last or last == '\n':
		del PARAMS["garcontinue"]

	request = session.get(url=URL, params=PARAMS, verify=False)
	json = request.json()
	
	try:	
		for page in json["query"]["pages"]:
			try:
				output.add(json["query"]["pages"][page]["title"])
			except:
				break
	except:
		print("NOTHING IN NAMESPACE")		

	with open(FILE_NAME, "w+") as writer:
		try:	
			writer.write(json["continue"]["garcontinue"] + "\n" + str(ns))
		except:
			if ns < 15:
				ns += 1
			else:
				ns = -2
			writer.write('' + "\n" + str(ns))

	CATS_PARAMS = {
	"action": "query",
	"list": "categorymembers",
	"cmtitle": "Category:Redirects",
	"cmnamespace": "*",
	"format": "json"
	}

	request = session.get(url=URL, params=CATS_PARAMS, verify=False)
	json = request.json()

	remove = set()
	for page in json["query"]["categorymembers"]:
		remove.add(page["title"])

	try:
		continueValue = json["continue"]["cmcontinue"]
	except:
		continueValue = ''

	while continueValue:
		CATS_PARAMS = {
		"action": "query",
		"list": "categorymembers",
		"cmtitle": "Category:Redirects",
		"cmnamespace": "*",
		"format": "json",
		"cmcontinue": continueValue
		}

		request = session.get(url=URL, params=CATS_PARAMS, verify=False)
		json = request.json()

		for page in json["query"]["categorymembers"]:
			remove.add(page["title"])

		try:
			continueValue = json["continue"]["cmcontinue"]
		except:
			continueValue = ''
	
	return output.difference(remove)

def addToCategory(title, category):
	"""
	Adds a page to a category.

	Parameters:
		title (str): the title of the page to be added to a category
		category (str): the category to add the page to
	"""

	page = pywikibot.Page(pywikibot.Site(), title)
	text = page.text
	category = "[[Category:" + category + "]]" 

	if text.find(category) != -1:
		print("Page is already in %s! Skipping %s..." % (category, title))
	else:
		print("Page is not in %s! Adding %s..." % (category, title))
		page.text += category
		page.save("Add to ")	

if __name__ == '__main__':
	for title in getRedirects(getURL()):
		addToCategory(title, "Redirects")
