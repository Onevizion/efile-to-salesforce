from onevizion import LogLevel, ModuleLog
import requests
from urllib.parse import urlencode, quote_plus, unquote
import json
import base64
import os
import onevizion

class Module:

	def __init__(self, ov_module_log: ModuleLog, settings_data: dict):
		self._module_log = ov_module_log
		self._settings = settings_data
		
	def start(self):
		self._module_log.add(LogLevel.INFO, 'Module is started')
		self.run_module(self._settings)
		self._module_log.add(LogLevel.INFO, 'Module is finished')

	def get_token(self, settings, token):
		if len(token)>0:
			return token
		
		url = settings['tokenUrl']

		x = settings['tokenParams']

		payload = urlencode(x, quote_via=quote_plus)

		url = f"{url}?{payload}"
		payload = {}
		print(url)

		headers = {
			'Content-Type': 'application/x-www-form-urlencoded',
			'Cookie': 'fpc=Ah06aNUJE5RCi-WhB2t-v6T0d1WAAQAAANehc98OAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
			}

		response = requests.request(settings['tokenPost'], url, headers=headers, data=payload)

		jresponce = response.json()

		print(jresponce)
		token = jresponce['access_token']

		print(token)
		return token

	def send_file(self, settings, token, filename, parentid, url):
		#url = settings['file_url']

		payload={}
		#files=[
		#	('file',('TestFile.txt',open(filename,'rb'),'text/plain'))
		#	]
		
		with open(filename, "rb") as f:
			encoded_string = base64.b64encode(f.read())
		encoded_stringutf8 = encoded_string.decode('utf-8')

		payload = {"ParentId": parentid, "Name": unquote(filename), "Body": encoded_stringutf8}
		payload = json.dumps(payload, default=repr)

		headers = {
		'Content-Type': 'application/json',
		'Authorization': f'Bearer {token}',
		'Cookie': 'BrowserId=LDjmwP51Ee-KgnMZL5HXXQ; CookieConsentPolicy=0:1; LSKey-c$CookieConsentPolicy=0:1; BrowserId=rpkvMGgSEfCq3S1nsRSUQQ; CookieConsentPolicy=0:1; LSKey-c$CookieConsentPolicy=0:1'
		}

		try:
			response = requests.request("POST", url, headers=headers, data=payload)
		except requests.exceptions.RequestException as e:
			print(e)  # should rarely occur and should be re-tried
			return False
		print(response.text)
		print(response.status_code)
		return response.status_code==201


	def run_module(self, settings):
		#
		None
		print('kilroy is here')
		token = ""

		for rec in settings["fields"]:
			req = onevizion.Trackor(rec['trackortype'], settings['ovUrl'], settings['ovAccessKey'], settings['ovSecretKey'], isTokenAuth=True)
			req2 = onevizion.Trackor(rec['trackortype'], settings['ovUrl'], settings['ovAccessKey'], settings['ovSecretKey'], isTokenAuth=True)

			#req.read(search=rec["search"],fields= ["TRACKOR_KEY","PR_SRQ_ID"])
			req.read(filterOptions=rec["filter"],fields= ["TRACKOR_KEY","RFP_TRACKER.RFP_SF_OPP_ID"])

			print(req.jsonData)
			print(req.errors)
			for r in req.jsonData:
				token = self.get_token(settings=self._settings, token=token)
				print(r['TRACKOR_KEY'])
				#try:
				filename=req2.GetFile(r['TRACKOR_ID'],rec['efilefield'])
				if len(req2.errors)>0:
					print(f"did not process request {r['TRACKOR_KEY']} {rec['efilefield']}")
					os.remove(filename)
				else:
					print(r)
					if self.send_file(settings, token, filename, r['RFP_Tracker.RFP_SF_OPP_ID'], rec['efileURL']):
						req2.update(trackorId=r['TRACKOR_ID'],fields={rec['trigger']:0})
						os.remove(filename)
						print(f"process request {r['TRACKOR_KEY']} {rec['efilefield']} {filename}")
					else:
						os.remove(filename)
						print(f"did not process request {r['TRACKOR_KEY']} {rec['efilefield']}")
