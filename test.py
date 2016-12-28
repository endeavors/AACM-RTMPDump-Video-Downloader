import subprocess,sys
def concatVideoFiles(out_filename, tf_input):
  try:
    args_list = ['ffmpeg', '-f', 'concat', '-i', 'bqpflwxkjj.txt', '-c', 'copy', '2-13-2012.flv']
    subprocess.check_call(args_list)
  except subprocess.CalledProcessError,e:
    print str(e)
    sys.stdout.write("Failed to concatenate video files: {0}\n".format(out_filename))
    sys.stdout.write("\tHere are the temp files:\n")
    tf_input.seek(0)
    for line in tf_input:
      filename = line.split()[-1].strip()
      sys.stdout.write("\t\t{0}\n".format(filename))
      sys.stdout.flush()

#tf_input = open('/var/folders/51/tz6__2k53bv99kjtxbby9j6h0000gn/T/tmpk_hm5D.txt')
concatVideoFiles("2-13-2012.flv",None)
