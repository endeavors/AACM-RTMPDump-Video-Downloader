from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread
import subprocess,os,sys,re,json,glob,shutil


class ThreadWorker(Thread):
	def __init__(self,queue):
		Thread.__init__(self)
		self.queue = queue

	def run(self):
		while self.queue.qsize() != 0:
			download, args = self.queue.get() 
			download(self.getRTMPAddress(args[0]), args[1], args[2])
			self.queue.task_done()

	def getRTMPAddress(self,rec_id):
		return "{0}{1}{2}".format("rtmp://streams2.webconferencingonline.com/aacm4/",
			rec_id, "/FCAVPresence.vidConf1_mc.av.1")

class Downloader:
	def __init__(self,dir_path):
		self.arg_list = ["rtmpdump", "-q"]
		self.counter = 0
		self.totalfiles = 0
		self.queue = Queue()
		self.dir_path = dir_path
		self.numthreads = 8

		self.setTotalNumFiles()
		self.queueUp()
		#self.launchThreads()
		self.queue.join()
		self.mergeAllDirs()

	#generator
	def walkRootDir(self):
		for dirname in os.listdir(self.dir_path):
			#skip hidden files
			if not dirname[0].isalnum():
				continue

			to_dir_path = os.path.join(self.dir_path,dirname)
			for filename in os.listdir(to_dir_path):
				file_path = os.path.join(to_dir_path,filename)
				file_prefix,ext = os.path.splitext(filename)

				if os.path.isdir(file_path) or ext.strip() != ".html":
					continue
				with open(file_path,'r') as html_file:
					soup = BeautifulSoup(html_file.read(), "html.parser")
					flash_pattern = re.compile(r'var\s*flashvars\s*\=\s*(((.|\n))+?\})\;')
					flashvars = soup.find("script",text=flash_pattern)
					if flashvars:
						matching_id = flash_pattern.search(flashvars.text)
						if matching_id:
							stripped = re.search(r's:\s*(\"\d+\")\s*\,',matching_id.group(1))
							if stripped:
								rec_id = stripped.group(1).replace('"',"")
								yield (rec_id, file_prefix, dirname)
							else:
								print "FILE INVALID: " + filename
								self.totalfiles -= 1
						else:
							print "FILE INVALID: " + filename
							self.totalfiles -= 1
					else:
						print "FILE INVALID: " + filename
						self.totalfiles -= 1

	def download(self,address,out_filename,dirname):
		out_filename = out_filename + ".flv"
		try:
			subprocess.check_call(self.arg_list + ["-r", address] + ["-o", out_filename])
			self.counter += 1
			sys.stdout.write("Downloaded {0}  -> {1}/{2}\n".format(out_filename,self.counter,
			self.totalfiles))
			sys.stdout.flush()
		except subprocess.CalledProcessError,e:
			sys.stdout.write("UNABLE TO DOWNLOAD: {0}\n".format(out_filename))
			sys.stdout.flush()
		else:
			#put the file into the right directory
			cwd = os.getcwd()
			curr_path = os.path.join(cwd,dirname)
			if not os.path.exists(curr_path):
				os.makedirs(curr_path)
			
			shutil.move(os.path.join(cwd, out_filename), os.path.join(curr_path,
				out_filename))


	def setTotalNumFiles(self):
		for d in glob.glob(os.path.join(self.dir_path,"*")):
			for df in glob.glob(os.path.join(d,"*")): 
				if os.path.isfile(df) and df.endswith(".html"):
					self.totalfiles += 1

	def mergeAllDirs(self):
		out_dir = "Tabla Videos"
		cwd = os.getcwd()
		if not os.path.exists(os.path.join(cwd,out_dir)):
			os.makedirs(out_dir)

		for dir_name in next(os.walk(cwd))[1]:
			if re.match(r"\d{4}",dir_name):
				src = os.path.join(cwd,dir_name)
				dest = os.path.join(cwd, out_dir)
				destdir = os.path.join(dest,dir_name)
				if os.path.exists(destdir):
					shutil.rmtree(destdir)
				shutil.move(src,dest)

	def launchThreads(self):
		#create 10 threads
		for i in range(self.numthreads):
			t_worker = ThreadWorker(self.queue)
			t_worker.daemon = True
			t_worker.start()

	def queueUp(self):
		for download_args in self.walkRootDir():
			print download_args
			self.queue.put((self.download,download_args))		



root_dir = raw_input("Enter folder name where the videos are stored: ")
root_path = os.path.expanduser("~/")
dir_path = os.path.join(root_path, root_dir)
if os.path.isdir(dir_path):
	downloader = Downloader(dir_path)
else:
	sys.exit("Exiting: Not a directory")


	
	












