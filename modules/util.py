from signal import SIGINT
from datetime import date, datetime
from commands import getoutput
from subprocess import Popen
import config
import os, socket, fcntl, struct

#
# Class houses utility functions
#

isDebug = False
DEBUG_LOG = 'zarp_debug.log'

# zarp version
def version():
	return "0.04B"

# zarp header
def header():
	print '\t\033[32m ____   __   ____  ____'
	print '\t(__  ) / _\ (  _ \(  _ \''
	print '\t / _/ /    \ )   / ) __/'
	print '\t(____)\_/\_/(__\_)(__)\033[0m'
	print "\t    [\033[33mVersion %s\033[0m]\t\t\t"%(version())
	if isDebug:
		print '\t      \033[34m[DEBUGGING]\033[0m'

#
# Print the passed error message in red formatted text!
#
def Error(msg):
	print '\033[31m[-] %s\033[0m'%(msg)
	if isDebug:
		debug(msg)	

#
# Print a warning/message in yellow formatted text!
#
def Msg(msg):
	print '\033[33m[!] %s\033[0m'%(msg)

# if debugging, write to dbg file
def debug(msg):
	if isDebug and not os.path.islink(DEBUG_LOG):
		with open(DEBUG_LOG, 'a+') as f:
			f.write(format('[%s %s] %s\n'%(date.today().isoformat(), datetime.now().strftime("%I:%M%p"), msg)))

# return the next IP address following the given IP address.
# It needs to be converted to an integer, then add 1, then converted back to an IP address
def next_ip(ip):
	ip2int = lambda ipstr: struct.unpack('!I', socket.inet_aton(ipstr))[0]
	int2ip = lambda n: socket.inet_ntoa(struct.pack('!I', n))
	return int2ip(ip2int(ip) + 1)

# Check if a given IP address is lies within the given netmask
# TRUE if 'ip' falls within 'mask'
# FALSE otherwise
def is_in_subnet(ip, mask):
	ipaddr = int(''.join([ '%02x' % int(x) for x in ip.split('.')]), 16)
	netstr,bits = net.split('/')
	netaddr = int(''.join([ '%02x' % int(x) for x in netstr.split('.')]), 16)
	mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
	return (ipaddr & mask) == (netaddr & mask)	

# verify if an app is installed (and pathed) properly 
def check_program(prog):
	tmp = init_app('which {0}'.format(prog), True)
	if len(tmp) > len(prog) and '/' in tmp:
		return True
	else:
		return False

# initialize an application 
# PROG is the full command with args
# OUTPUT true if output should be returned
#		 false if output should be dumped to null.  This will
#		 return a process handle and is meant for initializing 
#		 background processes.  Use wisely.
def init_app(prog, output):
	# dump output to null
	if not output:
		try:
			null = open(os.devnull, 'w')
			proc = Popen(prog, stdout=null, stderr=null)
		except Exception,j:
			Error("Error initializing app: %s"%j)
			return False
		return proc
	# just grab output
	else:
		return getoutput(prog)

#
# kill an application
#
def kill_app(proc):
	try:
		os.kill(proc.pid, SIGINT)
	except Exception, j:
		Error("Error killing app: %s"%(j))
		return False
	return True

#
# Try and automatically detect which adapter is in monitor mode
# NONE if there are none
#
def get_monitor_adapter():
	tmp = init_app('iwconfig', True)
	iface = None
	for line in tmp.split('\n'):	
		if line.startswith(' '):
			continue	
		elif len(line.split(' ')[0]) > 1:
			if 'Mode:Monitor' in line:
				return line.split(' ')[0]
	return None

#
# Enable monitor mode on the wireless adapter
#
def enable_monitor():
	tmp = init_app('iwconfig', True)
	iface = None
	for line in tmp.split('\n'):
		if line.startswith('wlan'):
			try:
				iface = line.split(' ')[0]
				tmp = getoutput('airmon-ng start {0}'.format(iface))
				debug("started \'%s\' in monitor mode"%iface)
			except Exception, j:
				Error("Error enabling monitor mode: %s"%j)
			break
	return get_monitor_adapter()

#
# Kill the monitoring adapter
#
def disable_monitor():
	try:
		adapt = get_monitor_adapter()
		if not adapt is None:
			tmp = getoutput('airmon-ng stop %s'%adapt)
			debug('killed monitor adapter %s'%adapt)
	except Exception, j:
		Error('error killing monitor adapter:%s'%j)

#
# Verify that the given interface exists
# TRUE if the adapter exists
# FALSE if it was not found
#
def verify_iface(iface):
	try:
		tmp = init_app('ifconfig', True)
		if not iface in tmp:
			return False
		return True
	except Exception, j:
		return False

#
# check if a local file exists
# TRUE if it does, FALSE otherwise
#
def does_file_exist(fle):
	try:
		with open(fle) as f: pass
	except IOError:
		return False
	return True

#
# get the main adapters IP
# ADAPTER is the local interface adapter to grab it from
#
def get_local_ip(adapter):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(
			s.fileno(),
			0x8915,
			struct.pack('256s', adapter[:15])
		)[20:24])

#
# Helper for the interface.
# arr is a list of items for display
#
def print_menu(arr):
	i = 0
	while i < len(arr):
		# if there are more than 6 items in the list, add another column
		if len(arr) > 6 and i < len(arr)-1:
			print '\t[%d] %s \t [%d] %s'%(i+1,arr[i],i+2,arr[i+1])
			i += 2
		else:
			print '\t[%d] %s'%(i+1,arr[i])
			i += 1
	print '\n0) Back'
	try:
		choice = raw_input('> ')
		if 'info' in choice:
			Error('\'info\' not implemented yet.')
			#stream.view_info(choice.split(' ')[1])	
			choice = -1
		elif 'set' in choice:
			opts = choice.split(' ')
			if opts[1] is None or opts[2] is None:
				return
			print '[!] Setting \033[33m%s\033[0m -> \033[32m%s\033[0m..'%(opts[1], opts[2])
			config.set(opts[1], opts[2])
			choice = -1
		elif 'opts' in choice:
			config.dump()
			choice = -1
		elif 'quit' in choice:
			# hard quit
			os._exit(1)
		else:
			choice = int(choice)
	except Exception:
		os.system('clear')
		choice = -1
	return choice
