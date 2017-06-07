#!/bin/bash
/usr/bin/kinit -kt /data/xubaochuan/tools/hadoop-current/datacenter.keytab datacenter/dev@HADOOP.HZ.NETEASE.COM
cd /data/xubaochuan/doc2video_crontab
hadoop=/data/xubaochuan/tools/hadoop-current/bin/hadoop
jarpath=/data/xubaochuan/tools/hadoop-current/share/hadoop/tools/lib/hadoop-streaming-2.5.2.jar
output=/user/datacenter/xubaochuan/doc_video_base/index_
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
else
  $hadoop fs -rmr $output_dir
fi
