#!/bin/bash
/usr/bin/kinit -kt /home/bjxubaochuan/tools/hadoop-current/datacenter.keytab datacenter/dev@HADOOP.HZ.NETEASE.COM
cd /home/bjxubaochuan/doc2video_crontab
hadoop=/home/bjxubaochuan/tools/hadoop-current/bin/hadoop
jarpath=/home/bjxubaochuan/tools/hadoop-current/share/hadoop/tools/lib/hadoop-streaming-2.5.2.jar
output=/user/datacenter/xubaochuan/doc_video_base_new/index_
current=`date +%s`
timestamp=`expr $current / 100 \* 100`
output_dir=${output}${timestamp}
output_file=${output_dir}"/index_data"
output_tag=${output_dir}"/_SUCCESS"
result_file=log/result_${timestamp}
python knn.py > $result_file
filename=`tail -1 $result_file`
$hadoop fs -mkdir $output_dir
$hadoop fs -put $filename $output_file
if test $? -eq 0
then
  $hadoop fs -touchz $output_tag
  echo 'success' >> $result_file
else
  $hadoop fs -rmr $output_dir
  echo 'error' >> $result_file
fi
