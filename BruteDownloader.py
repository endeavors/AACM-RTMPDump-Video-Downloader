from queue import Queue
from threading import Thread
import subprocess,os,sys


class ThreadWorker(Thread):
	def __init__(self,queue):
		Thread.__init__(self)
		self.queue = queue

	def run(self):
		while self.queue.qsize() != 0:
			download, args_list = self.queue.get() 
			address = self.getRTMPAddress(args_list[0],args_list[1])
			download(address, args_list[2])
			self.queue.task_done()

	def getRTMPAddress(self,rec_id,user):
		return "{0}{1}/{2}{3}".format("rtmp://streams2.webconferencingonline.com/",user,
			rec_id, "/FCAVPresence.vidConf1_mc.av.1")

class BruteDownloader:
	def __init__(self,in_filepath):
		self.arg_list = ["rtmpdump", "-q"]
		self.counter = 0
		self.totalfiles = 0
		self.queue = Queue()
		self.numthreads = 10

		self.queueUp(in_filepath)
		self.launchThreads()
		self.queue.join()

	def download(self,address,out_filename):
		try:
			subprocess.check_call(self.arg_list + ["-r", address] + ["-o", out_filename])
			self.counter += 1
			sys.stdout.write("Downloaded {0}  -> {1}/{2}\n".format(out_filename,self.counter,
			self.totalfiles))
			sys.stdout.flush()
		except subprocess.CalledProcessError,e:
			sys.stdout.write("UNABLE TO DOWNLOAD: {0}\n".format(out_filename))
			sys.stdout.flush()

	def launchThreads(self):
		for i in range(self.numthreads):
			t_worker = ThreadWorker(self.queue)
			t_worker.daemon = True
			t_worker.start()

	def queueUp(self,filepath):
		with open(filepath,"r") as in_file:
			for line in in_file:
				self.totalfiles += 1
				args_list = map(lambda x: x.strip(),line.split())
				self.queue.put((self.download,args_list))		


filepath = raw_input("Enter Input File: ")
downloader = BruteDownloader(filepath.strip())


