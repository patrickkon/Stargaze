import os
import sys
sys.path.append("utils")
from measure_traffic import get_all_node_interface_usage, get_interval_all_node_interface_usage, exec_sh_command

SATS_TOPO_WITH_INTERFACE_FILE = "gen_cluster_data/topo_with_interface_file.txt"
statistics_pod_list = ["get-statistics-9cgdk", "get-statistics-9gs88", "get-statistics-fdd5l", "get-statistics-mzv7p", "get-statistics-shvbw", "get-statistics-xk96p"] # includes pods in all nodes except for k8s master node
TRAIN_FASHION_MNIST_JOB_YAML_FILE = "kubernetes/job-example-7.yaml"
JOB_NAME = "ray-test-job-7" # Note: this is obtained within TRAIN_FASHION_MNIST_JOB_YAML_FILE

# Before job starts:
node_interface_usage_old = get_all_node_interface_usage(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE)

# Execute job:
exec_job_cmd = ['kubectl', '-n', 'ray', 'apply', '-f', TRAIN_FASHION_MNIST_JOB_YAML_FILE]
o = exec_sh_command(exec_job_cmd)
print(o)

# Wait for job to complete (indefinite time):
# kubectl wait --for=condition=complete job/ray-test-job-2
wait_complete_cmd = ['kubectl', '-n', 'ray', 'wait', '--for=condition=complete', 'job/{}'.format(JOB_NAME), '--timeout=-1s'] # negative timeout waits for 1 week. 
o = exec_sh_command(wait_complete_cmd) # Currently, this will block until complete
print(o)

# After job completes:
node_interface_usage_new = get_all_node_interface_usage(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE)

# Total usage:
node_interface_usage_interval, agg_total_traffic = get_interval_all_node_interface_usage(node_interface_usage_old, node_interface_usage_new)
print("node_interface_usage_interval: ", node_interface_usage_interval)
print("Aggregate network traffic during interval: {}".format(agg_total_traffic))

# Log other metrics (obtained from log of the job):
# get_pod_of_job_cmd = ["kubectl", "get", "pods", "-n", "ray", "|", "grep", JOB_NAME, "|", "cut", "-d' '", "-f1"]
# pod = exec_sh_command(get_pod_of_job_cmd)
get_pod_of_job_cmd = ["kubectl", "get", "pods", "-n", "ray"]
get_pod_2 = ["grep", JOB_NAME]
get_pod_3 = ('cut', '-d', ' ', '-f', '1')

import subprocess
ps = subprocess.Popen(get_pod_of_job_cmd, stdout=subprocess.PIPE)
ps = subprocess.Popen(get_pod_2, stdout=subprocess.PIPE, stdin=ps.stdout)
output = subprocess.check_output(get_pod_3, stdin=ps.stdout)
pod_name = output.decode('ascii').split('\n')[0]

get_logs_cmd = ['kubectl', '-n', 'ray', 'logs', pod_name]
get_logs_2 = ['tail', '-n', '100'] # only 15 lines necessary for this job
ps = subprocess.Popen(get_logs_cmd, stdout=subprocess.PIPE)
output = subprocess.check_output(get_logs_2, stdin=ps.stdout)
print(output.decode('ascii'))

# Delete job:
delete_job_cmd = ['kubectl', '-n', 'ray', 'delete', 'job', JOB_NAME]
o = exec_sh_command(delete_job_cmd)
print(o)


# At time: Tue Apr 12 15:34:10 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 164748013251, bytes_in: 164923607002
# At time: Tue Apr 12 15:34:11 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1799838925, bytes_in: 11571708
# At time: Tue Apr 12 15:34:11 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 160397711503, bytes_in: 152419738073
# At time: Tue Apr 12 15:34:11 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1816101864, bytes_in: 181162471
# At time: Tue Apr 12 15:34:12 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 141792322984, bytes_in: 139295119049
# At time: Tue Apr 12 15:34:12 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1862641300, bytes_in: 20422391
# At time: Tue Apr 12 15:34:12 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 1220013691, bytes_in: 3019265359
# At time: Tue Apr 12 15:34:13 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1988697905, bytes_in: 11953789
# At time: Tue Apr 12 15:34:13 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 76476723, bytes_in: 20725597
# At time: Tue Apr 12 15:34:13 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 457226067, bytes_in: 3860241
# At time: Tue Apr 12 15:34:13 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 81309834, bytes_in: 21947726
# At time: Tue Apr 12 15:34:14 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 646473299, bytes_in: 6503198
# job.batch/ray-test-job-7 created

# job.batch/ray-test-job-7 condition met

# At time: Tue Apr 12 15:35:49 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 164750955463, bytes_in: 164929534646
# At time: Tue Apr 12 15:35:50 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1799853345, bytes_in: 11580762
# At time: Tue Apr 12 15:35:50 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 160418590792, bytes_in: 152429934148
# At time: Tue Apr 12 15:35:51 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1816154148, bytes_in: 181560908
# At time: Tue Apr 12 15:35:51 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 141797068338, bytes_in: 139300645922
# At time: Tue Apr 12 15:35:51 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1862704996, bytes_in: 20482573
# At time: Tue Apr 12 15:35:52 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 1220883726, bytes_in: 3020256535
# At time: Tue Apr 12 15:35:52 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1988793212, bytes_in: 12040439
# At time: Tue Apr 12 15:35:52 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 76530275, bytes_in: 20739578
# At time: Tue Apr 12 15:35:52 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 457240407, bytes_in: 3868647
# At time: Tue Apr 12 15:35:53 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 81362629, bytes_in: 21960647
# At time: Tue Apr 12 15:35:53 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 646487465, bytes_in: 6511496
# node: n0, int: eth1, total_bytes_out: 22.447296142578125, total_bytes_in: 45.224334716796875
# node: n0, int: eth0, total_bytes_out: 0.110015869140625, total_bytes_in: 0.0690765380859375
# node: n1, int: eth1, total_bytes_out: 159.29633331298828, total_bytes_in: 77.78987884521484
# node: n1, int: eth0, total_bytes_out: 0.398895263671875, total_bytes_in: 3.0398330688476562
# node: n2, int: eth1, total_bytes_out: 36.20417785644531, total_bytes_in: 42.16669464111328
# node: n2, int: eth0, total_bytes_out: 0.4859619140625, total_bytes_in: 0.4591522216796875
# node: n3, int: eth1, total_bytes_out: 6.637840270996094, total_bytes_in: 7.56207275390625
# node: n3, int: eth0, total_bytes_out: 0.7271347045898438, total_bytes_in: 0.6610870361328125
# node: g0, int: eth1, total_bytes_out: 0.4085693359375, total_bytes_in: 0.10666656494140625
# node: g0, int: eth0, total_bytes_out: 0.109405517578125, total_bytes_in: 0.0641326904296875
# node: g1, int: eth1, total_bytes_out: 0.40279388427734375, total_bytes_in: 0.09857940673828125
# node: g1, int: eth0, total_bytes_out: 0.1080780029296875, total_bytes_in: 0.0633087158203125
# [['n0', 'eth1', 22.447296142578125, 45.224334716796875], ['n0', 'eth0', 0.110015869140625, 0.0690765380859375], ['n1', 'eth1', 159.29633331298828, 77.78987884521484], ['n1', 'eth0', 0.398895263671875, 3.0398330688476562], ['n2', 'eth1', 36.20417785644531, 42.16669464111328], ['n2', 'eth0', 0.4859619140625, 0.4591522216796875], ['n3', 'eth1', 6.637840270996094, 7.56207275390625], ['n3', 'eth0', 0.7271347045898438, 0.6610870361328125], ['g0', 'eth1', 0.4085693359375, 0.10666656494140625], ['g0', 'eth0', 0.109405517578125, 0.0641326904296875], ['g1', 'eth1', 0.40279388427734375, 0.09857940673828125], ['g1', 'eth0', 0.1080780029296875, 0.0633087158203125]]
# (run pid=1110) ray.tune.error.TuneError: Trial train_01b19_00013: Checkpoint path /home/ray/ray_results/hyperband_test/train_01b19_00013_13_height=85.382_2022-04-12_13-35-33/checkpoint_000096/ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=1110) 2022-04-12 13:35:42,978  ERROR trial_runner.py:1068 -- Trial train_01b19_00013: Error handling checkpoint /home/ray/ray_results/hyperband_test/train_01b19_00013_13_height=85.382_2022-04-12_13-35-33/checkpoint_000099/
# (run pid=1110) Traceback (most recent call last):
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=1110)     checkpoint=trial.saving_to)
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=1110)     callback.on_checkpoint(**info)
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=1110)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=1110)     CLOUD_CHECKPOINTING_URL))
# (run pid=1110) ray.tune.error.TuneError: Trial train_01b19_00013: Checkpoint path /home/ray/ray_results/hyperband_test/train_01b19_00013_13_height=85.382_2022-04-12_13-35-33/checkpoint_000099/ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=1110) 2022-04-12 13:35:42,987  ERROR trial_runner.py:1068 -- Trial train_01b19_00013: Error handling checkpoint /home/ray/ray_results/hyperband_test/train_01b19_00013_13_height=85.382_2022-04-12_13-35-33/checkpoint_000099/
# (run pid=1110) Traceback (most recent call last):
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=1110)     checkpoint=trial.saving_to)
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=1110)     callback.on_checkpoint(**info)
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=1110)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=1110)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=1110)     CLOUD_CHECKPOINTING_URL))
# (run pid=1110) ray.tune.error.TuneError: Trial train_01b19_00013: Checkpoint path /home/ray/ray_results/hyperband_test/train_01b19_00013_13_height=85.382_2022-04-12_13-35-33/checkpoint_000099/ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=1110) 2022-04-12 13:35:43,292  INFO tune.py:639 -- Total run time: 50.66 seconds (49.58 seconds for the tuning loop).
# (run pid=1110) Result for train_01b19_00013:
# (run pid=1110)   date: 2022-04-12_13-35-42
# (run pid=1110)   done: false
# (run pid=1110)   episode_reward_mean: 85.38203544751333
# (run pid=1110)   experiment_id: 15423b123d004725add35d47eeab5f67
# (run pid=1110)   hostname: example-cluster-ray-worker-type-b6pjn
# (run pid=1110)   iterations_since_restore: 1
# (run pid=1110)   node_ip: 10.244.1.2
# (run pid=1110)   pid: 555
# (run pid=1110)   should_checkpoint: true
# (run pid=1110)   time_since_restore: 0.001363992691040039
# (run pid=1110)   time_this_iter_s: 0.001363992691040039
# (run pid=1110)   time_total_s: 0.7295985221862793
# (run pid=1110)   timestamp: 1649795742
# (run pid=1110)   timesteps_since_restore: 0
# (run pid=1110)   training_iteration: 67
# (run pid=1110)   trial_id: 01b19_00013
# (run pid=1110)   
# (run pid=1110) Result for train_01b19_00013:
# (run pid=1110)   date: 2022-04-12_13-35-42
# (run pid=1110)   done: true
# (run pid=1110)   episode_reward_mean: 85.38203544751333
# (run pid=1110)   experiment_id: 15423b123d004725add35d47eeab5f67
# (run pid=1110)   experiment_tag: 13_height=85.382
# (run pid=1110)   hostname: example-cluster-ray-worker-type-b6pjn
# (run pid=1110)   iterations_since_restore: 37
# (run pid=1110)   node_ip: 10.244.1.2
# (run pid=1110)   pid: 555
# (run pid=1110)   should_checkpoint: true
# (run pid=1110)   time_since_restore: 0.5935587882995605
# (run pid=1110)   time_this_iter_s: 0.004901885986328125
# (run pid=1110)   time_total_s: 1.3217933177947998
# (run pid=1110)   timestamp: 1649795742
# (run pid=1110)   timesteps_since_restore: 0
# (run pid=1110)   training_iteration: 103
# (run pid=1110)   trial_id: 01b19_00013
# (run pid=1110)   
# (run pid=1110) == Status ==
# (run pid=1110) Current time: 2022-04-12 13:35:43 (running for 00:00:49.69)
# (run pid=1110) Memory usage on this node: 1.7/5.5 GiB
# (run pid=1110) Using HyperBand: num_stopped=9 total_brackets=3
# (run pid=1110) Round #0:
# (run pid=1110)   Bracket(Max Size (n)=6, Milestone (r)=200, completed=100.0%): {TERMINATED: 6} 
# (run pid=1110)   Bracket(Max Size (n)=3, Milestone (r)=134, completed=100.0%): {TERMINATED: 9} 
# (run pid=1110)   Bracket(Max Size (n)=2, Milestone (r)=134, completed=100.0%): {TERMINATED: 5} 
# (run pid=1110) Resources requested: 0/4 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.27 GiB objects
# (run pid=1110) Current best trial: 01b19_00004 with episode_reward_mean=96.61909520288499 and parameters={'height': 96.61909520288499}
# (run pid=1110) Result logdir: /home/ray/ray_results/hyperband_test
# (run pid=1110) Number of trials: 20/20 (20 TERMINATED)
# (run pid=1110) +-------------------+------------+-----------------+----------+--------+------------------+----------+
# (run pid=1110) | Trial name        | status     | loc             |   height |   iter |   total time (s) |   reward |
# (run pid=1110) |-------------------+------------+-----------------+----------+--------+------------------+----------|
# (run pid=1110) | train_01b19_00000 | TERMINATED | 10.244.1.2:284  | 26.5902  |    100 |         3.60537  | 26.5902  |
# (run pid=1110) | train_01b19_00001 | TERMINATED | 10.244.3.3:249  |  4.45709 |    100 |         3.03082  |  4.45709 |
# (run pid=1110) | train_01b19_00002 | TERMINATED | 10.244.3.3:370  | 23.1491  |    100 |         1.89154  | 23.1491  |
# (run pid=1110) | train_01b19_00003 | TERMINATED | 10.244.1.2:435  | 61.6994  |    100 |         0.966615 | 61.6994  |
# (run pid=1110) | train_01b19_00004 | TERMINATED | 10.244.1.2:495  | 96.6191  |    100 |         2.20449  | 96.6191  |
# (run pid=1110) | train_01b19_00005 | TERMINATED | 10.244.2.3:2006 | 51.3377  |    100 |         1.60141  | 51.3377  |
# (run pid=1110) | train_01b19_00006 | TERMINATED | 10.244.2.3:1172 | 45.3268  |     66 |         1.72505  | 45.3268  |
# (run pid=1110) | train_01b19_00007 | TERMINATED | 10.244.1.2:345  | 38.9037  |     66 |         1.18639  | 38.9037  |
# (run pid=1110) | train_01b19_00008 | TERMINATED | 10.244.3.3:340  | 47.6638  |     66 |         1.21673  | 47.6638  |
# (run pid=1110) | train_01b19_00009 | TERMINATED | 10.244.1.2:405  | 41.9459  |     66 |         0.694421 | 41.9459  |
# (run pid=1110) | train_01b19_00010 | TERMINATED | 10.244.3.3:520  | 81.7988  |    103 |         2.47748  | 81.7988  |
# (run pid=1110) | train_01b19_00011 | TERMINATED | 10.244.4.2:256  | 64.5442  |    103 |         1.73402  | 64.5442  |
# (run pid=1110) | train_01b19_00012 | TERMINATED | 10.244.3.3:490  | 21.1017  |     66 |         1.20901  | 21.1017  |
# (run pid=1110) | train_01b19_00013 | TERMINATED | 10.244.1.2:555  | 85.382   |    103 |         1.32179  | 85.382   |
# (run pid=1110) | train_01b19_00014 | TERMINATED | 10.244.1.2:525  |  6.69292 |     66 |         0.587401 |  6.69292 |
# (run pid=1110) | train_01b19_00015 | TERMINATED | 10.244.2.3:1879 | 83.1114  |    103 |         1.51895  | 83.1114  |
# (run pid=1110) | train_01b19_00016 | TERMINATED | 10.244.1.2:375  | 37.8307  |     66 |         1.28094  | 37.8307  |
# (run pid=1110) | train_01b19_00017 | TERMINATED | 10.244.2.3:1763 |  5.47316 |     66 |         0.574806 |  5.47316 |
# (run pid=1110) | train_01b19_00018 | TERMINATED | 10.244.1.2:465  | 86.7766  |    103 |         1.19055  | 86.7766  |
# (run pid=1110) | train_01b19_00019 | TERMINATED | 10.244.2.3:1481 | 72.2706  |     66 |         0.790227 | 72.2706  |
# (run pid=1110) +-------------------+------------+-----------------+----------+--------+------------------+----------+
# (run pid=1110) 
# (run pid=1110) 
# Best hyperparameters found were:  {'height': 96.61909520288499}

# job.batch "ray-test-job-7" deleted