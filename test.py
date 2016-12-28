import subprocess,sys,os
def concatVideoFiles(out_filename,tf_input):
  try:
    print os.path.basename(tf_input.name)
    args_list = ['ffmpeg', '-f', 'concat', '-i']
    end = ['-c', 'copy', '2-13-2012.flv']
    print args_list + [os.path.basename(tf_input.name)] + end
    subprocess.check_call(args_list + [tf_input.name] + end)
  except subprocess.CalledProcessError,e:
    print str(e)
    sys.stdout.write("Failed to concatenate video files: {0}\n".format(out_filename))
    sys.stdout.write("\tHere are the temp files:\n")

tf_input = open('./pyscbvknao.txt','r')
concatVideoFiles("2-13-2012.flv",tf_input)
