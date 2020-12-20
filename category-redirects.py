import pywikibot
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
	for ns in range(-2, 15):
		PARAMS = {
		"action": "query",
		"generator": "allredirects",
		"arnamespace": ns,
		"format": "json"
		}

		session = requests.Session()
		request = session.get(url=URL, params=PARAMS, verify=False)
		json = request.json()

		output = set()

		for page in json["query"]["pages"]:
			output.add(json["query"]["pages"][page]["title"])

		try:
			continueValue = json["continue"]["garcontinue"]
		except:
			continueValue = ''

		while continueValue:
			PARAMS = {
			"action": "query",
			"generator": "allredirects",
			"arnamespace": ns,
			"format": "json",
			"garcontinue": continueValue
			}

			request = session.get(url=URL, params=PARAMS, verify=False)
			json = request.json()

			for page in json["query"]["pages"]:
				output.add(json["query"]["pages"][page]["title"])

			try:
				continueValue = json["continue"]["garcontinue"]
			except:
				continueValue = ''
	PARAMS = {
	"action": "query",
	"list": "categorymembers",
	"cmtitle": "Category:Redirects",
	"cmnamespace": "*",
	"format": "json"
	}

	request = session.get(url=URL, params=PARAMS, verify=False)
	json = request.json()

	remove = set()
	for page in json["query"]["categorymembers"]:
		remove.add(page["title"])

	try:
		continueValue = json["continue"]["cmcontinue"]
	except:
		continueValue = ''

	while continueValue:
		PARAMS = {
		"action": "query",
		"list": "categorymembers",
		"cmtitle": "Category:Redirects",
		"cmnamespace": "*",
		"format": "json",
		"cmcontinue": continueValue
		}

		request = session.get(url=URL, params=PARAMS, verify=False)
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
		page.save("Add to %s" % (category))	

if __name__ == '__main__':
	for title in getRedirects(getURL()):
		addToCategory(title, "Redirects")
