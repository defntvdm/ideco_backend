#!/usr/bin/env python3

from aiohttp import web
from asyncio import get_event_loop
from os import popen
from os.path import exists
import json

ACTIONS = ['start', 'stop', 'restart']
SERVICES = {}
FLAG = 0
HTML = '''
	<!DOCTYPE html>
	<html>
	<head>
		<meta charset="utf-8">
		<title>%s</title>
		<script type="text/javascript">
			function changeDaemon(service, action) {
				document.location.href = '/'+service+'/'+action+'/'+cbox.checked;
			}
			%sdocument.location.href = '/';
		</script>
		<style>
		td, tr, table {
			border: 1px solid black;
		}
		td {
			padding: 3px 10px;
		}
		.on {
			color: green;
		}
		.off {
			color: red;
		}
		</style>
	</head>
	<body>
		%s
	</body>
	</html>
'''

def main():
	data = popen('sudo service --status-all')
	line = data.readline()
	while line:
		SERVICES[line[8:-1]] = True if line[3] == '+' else False
		line = data.readline()
	loop = get_event_loop()
	app = web.Application(loop=loop)
	app.router.add_get('/', handler)
	app.router.add_get('/{service}/{action}/{flag}', changeDaemon)
	web.run_app(app, host='localhost', port=10000)

async def handler(request):
	html = HTML % ('Main', '//', await generate_table())
	resp = web.Response(
			text=html,
			content_type='text/html',
		)
	return resp

async def changeDaemon(request):
	global FLAG
	action = request.match_info['action']
	service = request.match_info['service']
	FLAG = 1 if request.match_info['flag'] == 'true' else 0
	if not (action in ACTIONS and service in SERVICES.keys()):
		return web.Response(
			text='Ну и зачем баловаться?',
			content_type='text/html'
		)
	popen('sudo service ' + service + ' ' + action)

	if action == 'start' or action == 'restart':
		SERVICES[service] = True
	else:
		SERVICES[service] = False
	html = HTML % ('', '', '')
	return web.Response(
			text=html,
			content_type='text/html'
		)

async def generate_table():
	table = ''
	services = list(SERVICES.keys())
	services.sort()
	table += '<table><input type="checkbox" id="cbox"%s>' % (' checked' if FLAG else '')
	for serv in services:
		table += '''<tr class="{1}">
					<td>{0}</td>
					<td>{1}</td>
					<td><button onclick="changeDaemon('{0}','start')"{2}>Start</button></td>
					<td><button onclick="changeDaemon('{0}','stop')"{3}>Stop</button></td>
					<td><button onclick="changeDaemon('{0}','restart')"{3}>Restart</button></td>
					</tr>'''.format(serv, 
									'on' if SERVICES[serv] else 'off', 
									' disabled' if SERVICES[serv] and FLAG else '', 
									' disabled' if not SERVICES[serv] and FLAG else '')
	return table + '</table>'

if __name__ == '__main__':
	if not exists('config.json'):
		FLAG = 0
	else:
		with open('config.json') as f:
			config = json.loads(f.read())
			FLAG = config['flag']
	main()
	with open('config.json', 'w') as f:
		f.write(json.dumps({'flag': FLAG}))
