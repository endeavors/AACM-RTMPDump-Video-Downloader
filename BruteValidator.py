#validates which IDs are stored in the remote database
from Queue import Queue
import threading
import subprocess,re,fcntl,sys

class ThreadWorker(threading.Thread):
	def __init__(self,queue):
		threading.Thread.__init__(self)
		self.queue = queue

	def run(self):
		while self.queue.qsize() != 0:
			download, args = self.queue.get()
			download(args,self.getRTMPAddress(args[1],args[0]))
			self.queue.task_done()

	def getRTMPAddress(self,user,rec_id):
		return "{0}{1}/{2}{3}".format("rtmp://streams2.webconferencingonline.com/",user,
			rec_id, "/FCAVPresence.vidConf1_mc.av.1")

class BruteValidator:
	def __init__(self,filename=None):
		self.queue = Queue()
		self.arg_list = ["rtmpdump","-o", "/dev/null","--stop", "0.01","-r"]
		self.month_map = {
			"Jan":1,
			"Feb":2,
			"Mar":3,
			"Apr":4,
			"May":5,
			"Jun":6,
			"Jul":7,
			"Aug":8,
			"Sep":9,
			"Oct":10,
			"Nov":11,
			"Dec":12
		}
		self.numthreads = 10
		filename = "brute_nums.txt" if not filename else filename
		if not filename.endswith(".txt"):
			filename = filename + ".txt"
		self.outfile = open(filename,"a+")
		self.outfile.write("\n")
		self.outfile.flush()
		print "File opened"
		self.lock = threading.Lock()
		self.queueUp()
		self.launchThreads()
		self.queue.join()
		self.outfile.close()
		print "File closed"

	def writeToFile(self,filename,rec_id,user):
		self.lock.acquire()
		self.outfile.write("{0} {1} {2}\n".format(rec_id,user,filename))
		self.outfile.flush()
		self.lock.release()

	def download(self,args,address):
		out = None
		try:
			out = subprocess.check_output(self.arg_list+ [address],stderr= subprocess.STDOUT)
		except subprocess.CalledProcessError,e:
			out = e.output
		finally:
			date_m = re.search(r"creationdate\s*(.*)",out)
			if date_m:
				date_list = date_m.group(1).split()
				month = str(self.month_map[date_list[1].strip()])
				date = date_list[2].strip()
				date_sub_m = re.sub("[0]+","",date)
				year = date_list[-1].strip()
				filename = "{0}-{1}-{2}.flv".format(month,date,year)
				self.writeToFile(filename,args[0],args[1])
				sys.stdout.write("FOUND: {0} {1} {2}\n".format(args[0],args[1],filename))
				sys.stdout.flush()
			else:
				sys.stdout.write("invalid: " + args[0] + "\n")
				sys.stdout.flush()

	def launchThreads(self):
		for i in range(self.numthreads):
			t_worker = ThreadWorker(self.queue)
			t_worker.daemon = True
			t_worker.start()

	def queueUp(self):
		for i in xrange(314259,400000):
			for user in ["aacm20"]:
				self.queue.put((self.download,(str(i),user)))

filename = raw_input("Enter output file name: ")
brute = BruteValidator(filename.strip())
