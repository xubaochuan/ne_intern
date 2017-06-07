mkdir log
mkdir log/online
mkdir log/offline
mkdir temp
mkdir video
nohup python index.py > log/online/e.txt & 2>&1
nohup python lib_video.py > log/offline/e.txt & 2>&1
