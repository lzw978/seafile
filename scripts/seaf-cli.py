#!/usr/bin/env python

'''
If you want to use this program to start ccnet or seafile, please make
sure that the config file has been initialized before using it.  If the
config file has not been created, you need to run the following command
to create it:
    seaf-cli.py -c <config-dir> -o init

After that you can use this program to start ccnet or seafile.  The
commands are as below:
 - start a ccnet daemon:
    seaf-cli.py -c <config-dir> -o start-ccnet

 - start a seafile daemon:
    seaf-cli.py -c <config-dir> [-w <worktree>] -o start-seafile

 - start seafile-apple:
    seaf-cli.py -c <config-dir> -o start

When ccnet and seafile daemon are running, this program can clone, sync,
and remove a repo:
 - clone a repo:
    seaf-cli.py -c <config-dir> -r <repo-id> -u <url> [-w <worktree>] -o clone

 - sync a repo:
    seaf-cli.py -c <config-dir> -r <repo-id> -o sync

 - remove a repo:
    seaf-cli.py -c <config-dir> -r <repo-id> -o remove
'''

import os
import sys
import getopt

import simplejson as json

import ccnet
import seafile

sys.path.append('/usr/local/lib/seafile/web')
sys.path.append('../web')

DEFAULT_CONFIG_FILE = '~/.ccnet'


def usage():
	print "usage: %s" % sys.argv[0]
	print "\t--config, -c config_file\tindicate config file path"
	print "\t--help, -h\t\t\tprint help information"
	print "\t--operation, -o OP [OPTIONS]\tdo some operations"
	print "\t--repo, -r repo_id\t\tindicate repo id"
	print "\t--token, -t token\t\tindicate token"
	print "\t--url, -u seahub url\t\tindicate seahub url"
	print "\t--worktree, -w worktre\t\tindicate seafile worktree"
	print "\t--version, -v\t\t\tprint version"


def print_version():
	print "%s: 1.4.0" % sys.argv[0]


def init_config(config):

	#initialize ccnet and seafile config file
	if os.path.exists(config):
		print "%s has existed" % config
		sys.exit(0)

	config = os.path.abspath(config)

	# init ccnet config file
	name = raw_input("Enter username: ")
	cmd = "ccnet-init -c " + config + " -n " + name
	os.system(cmd)

	# init seafile.ini
	seafile_ini = config + "/seafile.ini"
	seafile_data = config + "/seafile-data"
	fp = open(seafile_ini, 'w')
	fp.write(seafile_data)
	fp.close();

	sys.exit(0)


def verify_config(config):

	if not os.path.exists(config) or not os.path.isdir(config):
		return False

	ccnet_conf = config + "/ccnet.conf"
	seafile_ini = config + "/seafile.ini"
	if not os.path.exists(ccnet_conf) or \
	   not os.path.exists(seafile_ini):
		return False

	return True


def start_ccnet(config):
	print "starting ccnet daemon ..."

	config = os.path.abspath(config)
	if not verify_config(config):
		print "Couldn't load config file"
		sys.exit(0)

	cmd = "ccnet --daemon -c " + config
	os.system(cmd)
	sys.exit(0)


def start_seafile(config, worktree):
	print "starting seafile daemon ..."

	config = os.path.abspath(config)
	if not verify_config(config):
		print "Couldn't load config file"
		sys.exit(0)

	cmd = "seaf-daemon --daemon -c " + config
	if worktree != None:
		cmd = cmd + " -w " + worktree
	os.system(cmd)
	sys.exit(0);


def start_all(config):
	print "starting seafile-applet ..."

	config = os.path.abspath(config)
	if not verify_config(config):
		print "Couldn't load config file"
		sys.exit(0)

	cmd = "seafile-applet -c " + config
	os.system(cmd)
	sys.exit(0)


def clone_repo(config, repoid, url, worktree):

	# we import seaserv until in this fucntion because CCNET_CONF_PATH
	# needs to be changed
	config = os.path.abspath(config)
	if not verify_config(config):
		print "Couldn't load config file"
		sys.exit(0)

	os.environ["CCNET_CONF_DIR"] = config
	from seaserv import CCNET_CONF_PATH
	from seaserv import seafile_rpc
	from seaserv import get_repos, get_repo, \
		get_default_seafile_worktree

	from pysearpc import SearpcError

	print "initialize connection..."
	pool = ccnet.ClientPool(CCNET_CONF_PATH)
	ccnet_rpc = ccnet.CcnetRpcClient(pool, req_pool=True)
	seafile_rpc = seafile.RpcClient(pool, req_pool=True)

	# input username and password
	import getpass
	username = raw_input("Enter username: ")
	password = getpass.getpass("Enter password for user %s " % username)

	# get token
	curl_cmd = "curl -d 'username=" + username + "&password=" + password + \
		   "' " + url + "/api2/auth-token/"
	token_json = os.popen(curl_cmd).read()
	tmp = json.loads(token_json)
	token = tmp['token']

	# get repo info
	curl_cmd = "curl -H 'Authorization: Token " + token + "' -H 'Accept: " + \
		"application/json; indent=4' " + url + "/api2/repos/" + \
		repoid + "/download-info/"

	print "get repo info...."
	repo_info = os.popen(curl_cmd).read()
	tmp = json.loads(repo_info)
	encrypted = tmp['encrypted']
	clone_token = tmp['token']
	relay_id = tmp['relay_id']
	relay_addr = tmp['relay_addr']
	relay_port = tmp['relay_port']
	email = tmp['email']
	repo_name = tmp['repo_name']

	repo_passwd = None;
	if encrypted != '':
		repo_passwd = getpass.getpass("Enter password for encrypted library: ")

	print "start to clone..."
	seafile_rpc.clone(repoid, relay_id, repo_name.encode('utf-8'),
			  worktree.encode('utf-8'), clone_token, repo_passwd,
			  encrypted, relay_addr, relay_port, email)


def sync_repo(config, repoid):

	config = os.path.abspath(config)
	if not verify_config(config):
		print "Couldn't load config file"
		sys.exit(0)

	os.environ["CCNET_CONF_DIR"] = config
	from seaserv import CCNET_CONF_PATH
	from seaserv import seafile_rpc
	from seaserv import get_repos, get_repo, \
		get_default_seafile_worktree

	from pysearpc import SearpcError

	print "initialize connection..."
	pool = ccnet.ClientPool(CCNET_CONF_PATH)
	ccnet_rpc = ccnet.CcnetRpcClient(pool, req_pool=True)
	seafile_rpc = seafile.RpcClient(pool, req_pool=True)

	seafile_rpc.sync(repoid, None)


def remove_repo(config, repoid):

	config = os.path.abspath(config)
	if not verify_config(config):
		print "Couldn't load config file"
		sys.exit(0)

	os.environ["CCNET_CONF_DIR"] = config
	from seaserv import CCNET_CONF_PATH
	from seaserv import seafile_rpc
	from seaserv import get_repos, get_repo, \
		get_default_seafile_worktree

	from pysearpc import SearpcError

	print "initialize connection..."
	pool = ccnet.ClientPool(CCNET_CONF_PATH)
	ccnet_rpc = ccnet.CcnetRpcClient(pool, req_pool=True)
	seafile_rpc = seafile.RpcClient(pool, req_pool=True)

	seafile_rpc.remove_repo(repoid)


def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "c:ho:r:u:w:v", \
			["config=", "help", "operation", "repo", \
			 "url", "worktree", "version"])
	except getopt.GetoptError as err:
		print str(err)
		usage()
		sys.exit(-1)

	config_file = DEFAULT_CONFIG_FILE
	op = None
	worktree = None
	version = 0
	help = 0
	for o, a in opts:
		if o == '-v' or o == '--version':
			version = 1
		elif o == '-h' or o == '--help':
			help = 1
		elif o == '-c' or o == '--config':
			config_file = a
		elif o == '-o' or o == '--operation':
			op = a
		elif o == '-r' or o == '--repo':
			repoid = a
		elif o == '-u' or o == '--url':
			url = a
		elif o == '-w' or o == '--worktree':
			worktree = a
		else:
			assert False, "unhandled option"

	if help == 1:
		usage()
		sys.exit(0)

	if version == 1:
		print_version()
		sys.exit(0)

	if op == "init":
		init_config(config_file)
	elif op == "start":
		start_all(config_file)
	elif op == "start-ccnet":
		start_ccnet(config_file)
	elif op == "start-seafile":
		start_seafile(config_file, worktree)
	elif op == "clone":
		clone_repo(config_file, repoid, url, worktree)
	elif op == "sync":
		sync_repo(config_file, repoid)
	elif op == "remove":
		remove_repo(config_file, repoid)
	else:
		assert False, "unknown operation"


if __name__ == "__main__":
	main()
