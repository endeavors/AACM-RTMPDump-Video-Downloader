from queue import Queue
from threading import Thread
from random import choice
from string import ascii_lowercase
import subprocess,os,sys,re,shutil,tempfile

class ThreadWorker(Thread):
	def __init__(self,queue):
		Thread.__init__(self)
		self.queue = queue

	def run(self):
		while self.queue.qsize() != 0:
			download, (date,idlist) = self.queue.get()
			#RTMP address doesn't include ID iter value
			addr_list = map(lambda x: self.getRTMPAddress(x[0],x[1]) ,idlist)
			download(addr_list, date)
			self.queue.task_done()

	def getRTMPAddress(self,rec_id,uname):
		return "{0}{1}/{2}{3}".format("rtmp://streams2.webconferencingonline.com/",uname,
			rec_id, "/FCAVPresence.vidConf1_mc.av.")

class BruteDownloader:
	def __init__(self,in_filename,out_dirname):
		self.arg_list = ["rtmpdump"]
		self.counter = 0
		self.totalfiles = 0
		self.queue = Queue()
		self.numthreads = 1
		self.queueUp(in_filename)
		self.launchThreads()
		self.queue.join()
		self.mergeAllDirs(out_dirname)
		self.cleanup()

	def download(self,address_list,out_filename):
		tf_input = tempfile.NamedTemporaryFile(delete=False)
		tf_input_name = tf_input.name
		failDownload = False

		for address in address_list:
			iternum = self.getValidFileNum(address)
			for iditer in xrange(1,iternum+1):
				tmpaddress = address + str(iditer)
				try:
					vid_file = tempfile.NamedTemporaryFile(delete=False)
					subprocess.check_call(self.arg_list + ["-r", tmpaddress] + ["-o", vid_file.name])
					out_vid_name = vid_file.name + ".flv"

					tf_input.write("file {0}\n".format(out_vid_name))
					os.rename(vid_file.name,out_vid_name)
				except subprocess.CalledProcessError,e:
					sys.stdout.write("UNABLE TO DOWNLOAD: {0}\n".format(out_filename))
					sys.stdout.flush()
					failDownload = True
				finally:
					vid_file.close()

		tf_input.close()
		if not failDownload:
			self.concatVideoFiles(out_filename, tf_input_name)
			#put the file into the right directory
			date = self.extractDate(out_filename)
			if date:
				self.moveFiletoDir(out_filename,date)
				self.counter += 1
				sys.stdout.write("Downloaded {0}  -> {1}/{2}\n".format(out_filename,self.counter,
					self.totalfiles))
			else:
				sys.stdout.write("Couldn't find the right directory to place the video file!")
			sys.stdout.flush()


		#delete temp files
		with open(tf_input_name,'r') as tf_input:
			for line in tf_input:
				filename = line.split()[-1].strip()
				os.remove(filename)
		os.remove(tf_input_name)

	#We care about accuracy over time here
	def getValidFileNum(self,address):
		args_list = ["rtmpdump", "--stop", "0.01", "-o", "/dev/null"]
		iditer = 1
		out = None
		while True:
			temp_addr = address + str(iditer)
			try:
				out = subprocess.check_output(args_list + ["-r", temp_addr],
					stderr= subprocess.STDOUT)
			except subprocess.CalledProcessError,e:
				out = e.output
			finally:
				date_m = re.search(r"creationdate\s*(.*)",out)
				if not date_m: break
				else: iditer += 1
		return iditer - 1

	#ffmpeg doesn't like temp files
	def concatVideoFiles(self,out_filename, tf_input_name):
		tf_input = open(tf_input_name,'r')
		try:
			args_list = ["ffmpeg", "-f", "concat", "-safe","0","-i", tf_input_name,
				"-c", "copy", out_filename, "-loglevel", "quiet"]
			subprocess.check_call(args_list)
		except subprocess.CalledProcessError,e:
			sys.stdout.write("Failed to concatenate video files: {0}\n".format(out_filename))
			sys.stdout.write("\tHere are the temp files:\n")
			tf_input.seek(0)
			for line in tf_input:
				filename = line.split()[-1].strip()
				sys.stdout.write("\t\t{0}\n".format(filename))
				sys.stdout.flush()
		finally:
			tf_input.close()

	def moveFiletoDir(self,out_filename,dirname):
		#outfile must be in current working directory
		cwd = os.getcwd()
		curr_path = os.path.join(cwd,dirname)
		if not os.path.exists(curr_path):
			os.makedirs(curr_path)

		shutil.move(os.path.join(cwd, out_filename), os.path.join(curr_path,
			out_filename))

	def mergeAllDirs(self,out_dir):
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

	def cleanup(self):
		try:
			subprocess.check_call(["pkill","-9","rtmpdump"])
			subprocess.check_call(["pkill","-9","Python"])
			subprocess.check_call(["pkill","-9","ffmpeg"])
		except subprocess.CalledProcessError,e:
			pass

	def extractDate(self,out_filename):
		m = re.search(r".*\-(\d{4}).flv",out_filename)
		if m:
			return m.group(1).strip()
		return None

	def getRandomFileName(self):
		tmp_file = ''.join(choice(ascii_lowercase) for i in range(10))
		while os.path.exists(os.path.join(os.getcwd(),tmp_file)):
			tmp_file = ''.join(choice(ascii_lowercase) for i in range(10))
		return tmp_file

	def launchThreads(self):
		for i in range(self.numthreads):
			t_worker = ThreadWorker(self.queue)
			t_worker.daemon = True
			t_worker.start()

	def queueUp(self,filepath):
		dates_dict = {}
		with open(filepath,"r") as in_file:
			for line in in_file:
				try:
					args_list = map(lambda x: x.strip(),line.split())
					ID, uname, date = args_list[0], args_list[1], args_list[-1]
					if date in dates_dict:
						dates_dict[date].append([ID,uname])
					else:
						dates_dict[date] = [[ID,uname]]
				except:
					pass

		for kvtup in dates_dict.viewitems():
			self.queue.put((self.download,kvtup))
		self.totalfiles = len(dates_dict)

infilename = raw_input("Enter Input File Name: ")
outdirname = raw_input("Enter Output Directory Name: ")
downloader = BruteDownloader(infilename.strip(),outdirname.strip())
