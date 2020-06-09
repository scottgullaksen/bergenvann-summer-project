import requests

url = 'https://veret.gfi.uib.no/ws/download/'
payload = {'s': '1', 'format': 'csv', 'fromDate': '2016-01-01', 'toDate': '2016-12-31', 'params[]': 'TA'}

r = requests.post(url, payload)
rText = r.content.decode()
with open("florida_results2016.csv", "w", encoding='utf-8') as f:
	f.write(rText)


urlSedalen = 'https://www.bergensveret.no/ws/download/?fromDate=2019-01-01&toDate=2019-12-31&action=period_query&s=40&params%5B%5D=TA&params%5B%5D=PR&params%5B%5D=FF&params%5B%5D=DD&params%5B%5D=UU&params%5B%5D=QSI_010&format=csv&downloadData=S%C3%B8k'
rSedalen = requests.get(urlSedalen)
rTextSedalen = rSedalen.content.decode()
with open("sedalen_results.csv", "w", encoding= 'utf-8') as f:
	f.write(rTextSedalen)
