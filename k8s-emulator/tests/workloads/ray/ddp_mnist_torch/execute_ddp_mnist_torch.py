import os
import sys
sys.path.append("utils")
from measure_traffic import get_all_node_interface_usage, get_interval_all_node_interface_usage, exec_sh_command

SATS_TOPO_WITH_INTERFACE_FILE = "gen_cluster_data/topo_with_interface_file.txt"
statistics_pod_list = ["get-statistics-8m89j", "get-statistics-9jlgq", "get-statistics-cjjlj", "get-statistics-zkgnc"] # includes pods in all nodes except for k8s master node
TRAIN_FASHION_MNIST_JOB_YAML_FILE = "kubernetes/job-example-8.yaml"
JOB_NAME = "ray-test-job-8" # Note: this is obtained within TRAIN_FASHION_MNIST_JOB_YAML_FILE

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



# num_worker = 2, num_sample = 2
# At time: Wed Apr 13 01:10:49 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165241995886, bytes_in: 165480390829
# At time: Wed Apr 13 01:10:49 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1801100235, bytes_in: 11875189
# At time: Wed Apr 13 01:10:50 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 166505108559, bytes_in: 154791616588
# At time: Wed Apr 13 01:10:50 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1827692849, bytes_in: 289149333
# At time: Wed Apr 13 01:10:50 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 142556727620, bytes_in: 141079937608
# At time: Wed Apr 13 01:10:51 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1878652495, bytes_in: 34618657
# At time: Wed Apr 13 01:10:51 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 1843846975, bytes_in: 4307966758
# At time: Wed Apr 13 01:10:51 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1990045235, bytes_in: 12339915
# At time: Wed Apr 13 01:10:52 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 93172516, bytes_in: 25241149
# At time: Wed Apr 13 01:10:52 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 458325923, bytes_in: 4011303
# At time: Wed Apr 13 01:10:52 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 104844022, bytes_in: 27351805
# At time: Wed Apr 13 01:10:52 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 647746899, bytes_in: 7026760
# job.batch/ray-test-job-8 created

# job.batch/ray-test-job-8 condition met

# At time: Wed Apr 13 01:12:05 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165299567922, bytes_in: 165483293103
# At time: Wed Apr 13 01:12:06 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1801114247, bytes_in: 11884135
# At time: Wed Apr 13 01:12:06 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 166631924918, bytes_in: 155020952732
# At time: Wed Apr 13 01:12:06 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1827706715, bytes_in: 289158500
# At time: Wed Apr 13 01:12:07 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 142614692447, bytes_in: 141138550100
# At time: Wed Apr 13 01:12:07 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1878743616, bytes_in: 34771428
# At time: Wed Apr 13 01:12:07 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 1957100200, bytes_in: 4366865961
# At time: Wed Apr 13 01:12:08 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1990061035, bytes_in: 12350399
# At time: Wed Apr 13 01:12:08 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 93208734, bytes_in: 25251739
# At time: Wed Apr 13 01:12:08 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 458339465, bytes_in: 4019601
# At time: Wed Apr 13 01:12:08 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 105296543, bytes_in: 27500761
# At time: Wed Apr 13 01:12:09 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 647777535, bytes_in: 7052193
# node: n0, int: eth1, total_bytes_out: 439.2397766113281, total_bytes_in: 22.142593383789062
# node: n0, int: eth0, total_bytes_out: 0.106903076171875, total_bytes_in: 0.0682525634765625
# node: n1, int: eth1, total_bytes_out: 967.5320358276367, total_bytes_in: 1749.6959228515625
# node: n1, int: eth0, total_bytes_out: 0.1057891845703125, total_bytes_in: 0.06993865966796875
# node: n2, int: eth1, total_bytes_out: 442.23653411865234, total_bytes_in: 447.1778259277344
# node: n2, int: eth0, total_bytes_out: 0.6951980590820312, total_bytes_in: 1.1655502319335938
# node: n3, int: eth1, total_bytes_out: 864.0535354614258, total_bytes_in: 449.3652572631836
# node: n3, int: eth0, total_bytes_out: 0.12054443359375, total_bytes_in: 0.079986572265625
# node: g0, int: eth1, total_bytes_out: 0.2763214111328125, total_bytes_in: 0.0807952880859375
# node: g0, int: eth0, total_bytes_out: 0.1033172607421875, total_bytes_in: 0.0633087158203125
# node: g1, int: eth1, total_bytes_out: 3.4524612426757812, total_bytes_in: 1.136444091796875
# node: g1, int: eth0, total_bytes_out: 0.233734130859375, total_bytes_in: 0.19403839111328125
# [['n0', 'eth1', 439.2397766113281, 22.142593383789062], ['n0', 'eth0', 0.106903076171875, 0.0682525634765625], ['n1', 'eth1', 967.5320358276367, 1749.6959228515625], ['n1', 'eth0', 0.1057891845703125, 0.06993865966796875], ['n2', 'eth1', 442.23653411865234, 447.1778259277344], ['n2', 'eth0', 0.6951980590820312, 1.1655502319335938], ['n3', 'eth1', 864.0535354614258, 449.3652572631836], ['n3', 'eth0', 0.12054443359375, 0.079986572265625], ['g0', 'eth1', 0.2763214111328125, 0.0807952880859375], ['g0', 'eth0', 0.1033172607421875, 0.0633087158203125], ['g1', 'eth1', 3.4524612426757812, 1.136444091796875], ['g1', 'eth0', 0.233734130859375, 0.19403839111328125]]
# (run pid=597) | WrappedDistributedTorchTrainable_962dd_00000 | RUNNING  | 10.244.2.7:730  | 0.64375 |      1 |         0.308777 |
# (run pid=597) | WrappedDistributedTorchTrainable_962dd_00001 | RUNNING  | 10.244.4.2:2201 |         |        |                  |
# (run pid=597) +----------------------------------------------+----------+-----------------+---------+--------+------------------+
# (run pid=597) 
# (run pid=597) 
# (run pid=597) Result for WrappedDistributedTorchTrainable_962dd_00001:
# (run pid=597)   date: 2022-04-12_23-12-00
# (run pid=597)   done: false
# (run pid=597)   experiment_id: 801d92a5aa014cbaaa46f2c5581712c6
# (run pid=597)   hostname: example-cluster-ray-worker-type-7xzdn
# (run pid=597)   iterations_since_restore: 1
# (run pid=597)   mean_accuracy: 0.63125
# (run pid=597)   node_ip: 10.244.4.2
# (run pid=597)   pid: 2201
# (run pid=597)   should_checkpoint: true
# (run pid=597)   time_since_restore: 0.333662748336792
# (run pid=597)   time_this_iter_s: 0.333662748336792
# (run pid=597)   time_total_s: 0.333662748336792
# (run pid=597)   timestamp: 1649830320
# (run pid=597)   timesteps_since_restore: 0
# (run pid=597)   training_iteration: 1
# (run pid=597)   trial_id: 962dd_00001
# (run pid=597)   
# (run pid=597) Result for WrappedDistributedTorchTrainable_962dd_00000:
# (run pid=597)   date: 2022-04-12_23-12-01
# (run pid=597)   done: true
# (run pid=597)   experiment_id: 7b1f036d73af471b9b6c1fc370cfc78e
# (run pid=597)   experiment_tag: '0'
# (run pid=597)   hostname: example-cluster-ray-head-type-m8wxn
# (run pid=597)   iterations_since_restore: 5
# (run pid=597)   mean_accuracy: 0.803125
# (run pid=597)   node_ip: 10.244.2.7
# (run pid=597)   pid: 730
# (run pid=597)   time_since_restore: 8.883832693099976
# (run pid=597)   time_this_iter_s: 0.36764049530029297
# (run pid=597)   time_total_s: 8.883832693099976
# (run pid=597)   timestamp: 1649830321
# (run pid=597)   timesteps_since_restore: 0
# (run pid=597)   training_iteration: 5
# (run pid=597)   trial_id: 962dd_00000
# (run pid=597)   
# (run pid=597) Result for WrappedDistributedTorchTrainable_962dd_00001:
# (run pid=597)   date: 2022-04-12_23-12-02
# (run pid=597)   done: true
# (run pid=597)   experiment_id: 801d92a5aa014cbaaa46f2c5581712c6
# (run pid=597)   experiment_tag: '1'
# (run pid=597)   hostname: example-cluster-ray-worker-type-7xzdn
# (run pid=597)   iterations_since_restore: 5
# (run pid=597)   mean_accuracy: 0.828125
# (run pid=597)   node_ip: 10.244.4.2
# (run pid=597)   pid: 2201
# (run pid=597)   time_since_restore: 1.7340326309204102
# (run pid=597)   time_this_iter_s: 0.37912893295288086
# (run pid=597)   time_total_s: 1.7340326309204102
# (run pid=597)   timestamp: 1649830322
# (run pid=597)   timesteps_since_restore: 0
# (run pid=597)   training_iteration: 5
# (run pid=597)   trial_id: 962dd_00001
# (run pid=597)   
# (run pid=597) == Status ==
# (run pid=597) Current time: 2022-04-12 23:12:02 (running for 00:00:20.47)
# (run pid=597) Memory usage on this node: 2.6/5.5 GiB
# (run pid=597) Using FIFO scheduling algorithm.
# (run pid=597) Resources requested: 0/4 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.24 GiB objects
# (run pid=597) Current best trial: 962dd_00001 with mean_accuracy=0.828125 and parameters={}
# (run pid=597) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-12_23-11-41
# (run pid=597) Number of trials: 2/2 (2 TERMINATED)
# (run pid=597) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=597) | Trial name                                   | status     | loc             |      acc |   iter |   total time (s) |
# (run pid=597) |----------------------------------------------+------------+-----------------+----------+--------+------------------|
# (run pid=597) | WrappedDistributedTorchTrainable_962dd_00000 | TERMINATED | 10.244.2.7:730  | 0.803125 |      5 |          8.88383 |
# (run pid=597) | WrappedDistributedTorchTrainable_962dd_00001 | TERMINATED | 10.244.4.2:2201 | 0.828125 |      5 |          1.73403 |
# (run pid=597) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=597) 
# (run pid=597) 
# (run pid=597) 2022-04-12 23:12:00,750   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_962dd_00001: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-12_23-11-41/WrappedDistributedTorchTrainable_962dd_00001_1_2022-04-12_23-11-52/checkpoint_000001/./
# (run pid=597) Traceback (most recent call last):
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=597)     checkpoint=trial.saving_to)
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=597)     callback.on_checkpoint(**info)
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=597)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=597)     CLOUD_CHECKPOINTING_URL))
# (run pid=597) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_962dd_00001: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-12_23-11-41/WrappedDistributedTorchTrainable_962dd_00001_1_2022-04-12_23-11-52/checkpoint_000001/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=597) 2022-04-12 23:12:01,822   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_962dd_00001: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-12_23-11-41/WrappedDistributedTorchTrainable_962dd_00001_1_2022-04-12_23-11-52/checkpoint_000004/./
# (run pid=597) Traceback (most recent call last):
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=597)     checkpoint=trial.saving_to)
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=597)     callback.on_checkpoint(**info)
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=597)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=597)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=597)     CLOUD_CHECKPOINTING_URL))
# (run pid=597) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_962dd_00001: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-12_23-11-41/WrappedDistributedTorchTrainable_962dd_00001_1_2022-04-12_23-11-52/checkpoint_000004/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=597) 2022-04-12 23:12:02,281   INFO tune.py:639 -- Total run time: 21.99 seconds (20.47 seconds for the tuning loop).
# Best hyperparameters found were:  {}
# Job completion time: 29.78162073699059

# job.batch "ray-test-job-8" deleted




# num_workers = 1, num_samples=2
# At time: Wed Apr 13 10:55:22 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165657534230, bytes_in: 165754852347
# At time: Wed Apr 13 10:55:22 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1802307818, bytes_in: 12125676
# At time: Wed Apr 13 10:55:22 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 171831651429, bytes_in: 157034108695
# At time: Wed Apr 13 10:55:23 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1830563145, bytes_in: 302538436
# At time: Wed Apr 13 10:55:23 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 143034914676, bytes_in: 142441733064
# At time: Wed Apr 13 10:55:23 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1880517572, bytes_in: 35797756
# At time: Wed Apr 13 10:55:24 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 2706090081, bytes_in: 5533132359
# At time: Wed Apr 13 10:55:24 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991208581, bytes_in: 12545462
# At time: Wed Apr 13 10:55:24 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 110191756, bytes_in: 29874129
# At time: Wed Apr 13 10:55:25 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459387899, bytes_in: 4127248
# At time: Wed Apr 13 10:55:25 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 124218739, bytes_in: 32500553
# At time: Wed Apr 13 10:55:25 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 648875465, bytes_in: 7204503
# job.batch/ray-test-job-8 created

# job.batch/ray-test-job-8 condition met

# At time: Wed Apr 13 10:56:30 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165769856802, bytes_in: 165812826176
# At time: Wed Apr 13 10:56:30 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1802321284, bytes_in: 12134204
# At time: Wed Apr 13 10:56:30 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 172008140405, bytes_in: 157259969189
# At time: Wed Apr 13 10:56:31 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1830606029, bytes_in: 302804585
# At time: Wed Apr 13 10:56:31 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 143035144107, bytes_in: 142497352753
# At time: Wed Apr 13 10:56:31 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1880580505, bytes_in: 35857540
# At time: Wed Apr 13 10:56:32 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 2818489317, bytes_in: 5591210694
# At time: Wed Apr 13 10:56:32 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991222179, bytes_in: 12554558
# At time: Wed Apr 13 10:56:32 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 110221231, bytes_in: 29882932
# At time: Wed Apr 13 10:56:33 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459401233, bytes_in: 4135547
# At time: Wed Apr 13 10:56:33 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 124251175, bytes_in: 32510104
# At time: Wed Apr 13 10:56:33 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 648888799, bytes_in: 7212736
# node: n0, int: eth1, total_bytes_out: 856.9532165527344, total_bytes_in: 442.30521392822266
# node: n0, int: eth0, total_bytes_out: 0.1027374267578125, total_bytes_in: 0.0650634765625
# node: n1, int: eth1, total_bytes_out: 1346.5040283203125, total_bytes_in: 1723.1788177490234
# node: n1, int: eth0, total_bytes_out: 0.327178955078125, total_bytes_in: 2.0305557250976562
# node: n2, int: eth1, total_bytes_out: 1.7504196166992188, total_bytes_in: 424.3445510864258
# node: n2, int: eth0, total_bytes_out: 0.48014068603515625, total_bytes_in: 0.45611572265625
# node: n3, int: eth1, total_bytes_out: 857.5381164550781, total_bytes_in: 443.10253143310547
# node: n3, int: eth0, total_bytes_out: 0.1037445068359375, total_bytes_in: 0.06939697265625
# node: g0, int: eth1, total_bytes_out: 0.22487640380859375, total_bytes_in: 0.06716156005859375
# node: g0, int: eth0, total_bytes_out: 0.1017303466796875, total_bytes_in: 0.06331634521484375
# node: g1, int: eth1, total_bytes_out: 0.247467041015625, total_bytes_in: 0.07286834716796875
# node: g1, int: eth0, total_bytes_out: 0.1017303466796875, total_bytes_in: 0.06281280517578125
# [['n0', 'eth1', 856.9532165527344, 442.30521392822266], ['n0', 'eth0', 0.1027374267578125, 0.0650634765625], ['n1', 'eth1', 1346.5040283203125, 1723.1788177490234], ['n1', 'eth0', 0.327178955078125, 2.0305557250976562], ['n2', 'eth1', 1.7504196166992188, 424.3445510864258], ['n2', 'eth0', 0.48014068603515625, 0.45611572265625], ['n3', 'eth1', 857.5381164550781, 443.10253143310547], ['n3', 'eth0', 0.1037445068359375, 0.06939697265625], ['g0', 'eth1', 0.22487640380859375, 0.06716156005859375], ['g0', 'eth0', 0.1017303466796875, 0.06331634521484375], ['g1', 'eth1', 0.247467041015625, 0.07286834716796875], ['g1', 'eth0', 0.1017303466796875, 0.06281280517578125]]
# (run pid=596)   
# (run pid=596) Result for WrappedDistributedTorchTrainable_39e68_00000:
# (run pid=596)   date: 2022-04-13_08-56-23
# (run pid=596)   done: true
# (run pid=596)   experiment_id: eadadcc32b42489992fb0cae1173ded4
# (run pid=596)   experiment_tag: '0'
# (run pid=596)   hostname: example-cluster-ray-worker-type-7xzdn
# (run pid=596)   iterations_since_restore: 5
# (run pid=596)   mean_accuracy: 0.803125
# (run pid=596)   node_ip: 10.244.4.2
# (run pid=596)   pid: 3496
# (run pid=596)   time_since_restore: 6.855214595794678
# (run pid=596)   time_this_iter_s: 0.2614405155181885
# (run pid=596)   time_total_s: 6.855214595794678
# (run pid=596)   timestamp: 1649865383
# (run pid=596)   timesteps_since_restore: 0
# (run pid=596)   training_iteration: 5
# (run pid=596)   trial_id: 39e68_00000
# (run pid=596)   
# (run pid=596) Result for WrappedDistributedTorchTrainable_39e68_00001:
# (run pid=596)   date: 2022-04-13_08-56-23
# (run pid=596)   done: true
# (run pid=596)   experiment_id: 6ed550d18ff24810a6ad82e74536e1be
# (run pid=596)   experiment_tag: '1'
# (run pid=596)   hostname: example-cluster-ray-worker-type-h9z85
# (run pid=596)   iterations_since_restore: 5
# (run pid=596)   mean_accuracy: 0.865625
# (run pid=596)   node_ip: 10.244.1.2
# (run pid=596)   pid: 1222
# (run pid=596)   time_since_restore: 1.312525987625122
# (run pid=596)   time_this_iter_s: 0.2901747226715088
# (run pid=596)   time_total_s: 1.312525987625122
# (run pid=596)   timestamp: 1649865383
# (run pid=596)   timesteps_since_restore: 0
# (run pid=596)   training_iteration: 5
# (run pid=596)   trial_id: 39e68_00001
# (run pid=596)   
# (run pid=596) == Status ==
# (run pid=596) Current time: 2022-04-13 08:56:23 (running for 00:00:18.31)
# (run pid=596) Memory usage on this node: 2.4/5.5 GiB
# (run pid=596) Using FIFO scheduling algorithm.
# (run pid=596) Resources requested: 0/3 CPUs, 0/0 GPUs, 0.0/4.2 GiB heap, 0.0/1.67 GiB objects
# (run pid=596) Current best trial: 39e68_00001 with mean_accuracy=0.865625 and parameters={}
# (run pid=596) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05
# (run pid=596) Number of trials: 2/2 (2 TERMINATED)
# (run pid=596) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=596) | Trial name                                   | status     | loc             |      acc |   iter |   total time (s) |
# (run pid=596) |----------------------------------------------+------------+-----------------+----------+--------+------------------|
# (run pid=596) | WrappedDistributedTorchTrainable_39e68_00000 | TERMINATED | 10.244.4.2:3496 | 0.803125 |      5 |          6.85521 |
# (run pid=596) | WrappedDistributedTorchTrainable_39e68_00001 | TERMINATED | 10.244.1.2:1222 | 0.865625 |      5 |          1.31253 |
# (run pid=596) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=596) 
# (run pid=596) 
# Best hyperparameters found were:  {}
# Job completion time: 27.77852009498747
# (run pid=596) 2022-04-13 08:56:22,602   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_39e68_00000: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00000_0_2022-04-13_08-56-07/checkpoint_000001/./
# (run pid=596) Traceback (most recent call last):
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=596)     checkpoint=trial.saving_to)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=596)     callback.on_checkpoint(**info)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=596)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=596)     CLOUD_CHECKPOINTING_URL))
# (run pid=596) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_39e68_00000: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00000_0_2022-04-13_08-56-07/checkpoint_000001/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=596) 2022-04-13 08:56:22,840   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_39e68_00001: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00001_1_2022-04-13_08-56-16/checkpoint_000001/./
# (run pid=596) Traceback (most recent call last):
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=596)     checkpoint=trial.saving_to)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=596)     callback.on_checkpoint(**info)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=596)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=596)     CLOUD_CHECKPOINTING_URL))
# (run pid=596) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_39e68_00001: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00001_1_2022-04-13_08-56-16/checkpoint_000001/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=596) 2022-04-13 08:56:23,402   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_39e68_00000: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00000_0_2022-04-13_08-56-07/checkpoint_000004/./
# (run pid=596) Traceback (most recent call last):
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=596)     checkpoint=trial.saving_to)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=596)     callback.on_checkpoint(**info)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=596)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=596)     CLOUD_CHECKPOINTING_URL))
# (run pid=596) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_39e68_00000: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00000_0_2022-04-13_08-56-07/checkpoint_000004/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=596) 2022-04-13 08:56:23,618   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_39e68_00001: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00001_1_2022-04-13_08-56-16/checkpoint_000004/./
# (run pid=596) Traceback (most recent call last):
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=596)     checkpoint=trial.saving_to)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=596)     callback.on_checkpoint(**info)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=596)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=596)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=596)     CLOUD_CHECKPOINTING_URL))
# (run pid=596) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_39e68_00001: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_08-56-05/WrappedDistributedTorchTrainable_39e68_00001_1_2022-04-13_08-56-16/checkpoint_000004/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=596) 2022-04-13 08:56:24,020   INFO tune.py:639 -- Total run time: 19.84 seconds (18.31 seconds for the tuning loop).

# job.batch "ray-test-job-8" deleted




# Num workers = 1, num_samples = 3. This normally does not work due to memory overload I think, but here it worked because: (1) 3rd ray worker was already deployed due to a failed previous job.  (2) the ray head was recreated due to failed previous job, and had only ~300MB of memory used before the job started. 
# At time: Wed Apr 13 11:15:25 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165839853768, bytes_in: 165855144081
# At time: Wed Apr 13 11:15:26 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1802430294, bytes_in: 12197069
# At time: Wed Apr 13 11:15:26 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 172393447795, bytes_in: 157528474025
# At time: Wed Apr 13 11:15:26 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1831134289, bytes_in: 305929000
# At time: Wed Apr 13 11:15:27 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 143037442693, bytes_in: 142610386913
# At time: Wed Apr 13 11:15:27 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1881340335, bytes_in: 36647274
# At time: Wed Apr 13 11:15:27 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 3000024394, bytes_in: 5745147844
# At time: Wed Apr 13 11:15:28 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991331123, bytes_in: 12615393
# At time: Wed Apr 13 11:15:28 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 110782831, bytes_in: 30039516
# At time: Wed Apr 13 11:15:28 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459490275, bytes_in: 4178716
# At time: Wed Apr 13 11:15:28 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 125684180, bytes_in: 32741198
# At time: Wed Apr 13 11:15:29 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 648992059, bytes_in: 7270007
# job.batch/ray-test-job-8 created

# job.batch/ray-test-job-8 condition met

# At time: Wed Apr 13 11:16:42 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165896950054, bytes_in: 165913183741
# At time: Wed Apr 13 11:16:43 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1802444284, bytes_in: 12206173
# At time: Wed Apr 13 11:16:43 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 172631213706, bytes_in: 157812871705
# At time: Wed Apr 13 11:16:43 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1831176213, bytes_in: 306307854
# At time: Wed Apr 13 11:16:44 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 143094759315, bytes_in: 142668751849
# At time: Wed Apr 13 11:16:44 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1881410938, bytes_in: 36713096
# At time: Wed Apr 13 11:16:44 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 3168593372, bytes_in: 5859223498
# At time: Wed Apr 13 11:16:45 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991345275, bytes_in: 12624629
# At time: Wed Apr 13 11:16:45 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 110818543, bytes_in: 30050589
# At time: Wed Apr 13 11:16:45 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459503869, bytes_in: 4186949
# At time: Wed Apr 13 11:16:46 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 125719153, bytes_in: 32752503
# At time: Wed Apr 13 11:16:46 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 649006027, bytes_in: 7278732
# node: n0, int: eth1, total_bytes_out: 435.61009216308594, total_bytes_in: 442.8074645996094
# node: n0, int: eth0, total_bytes_out: 0.1067352294921875, total_bytes_in: 0.0694580078125
# node: n1, int: eth1, total_bytes_out: 1814.0099411010742, total_bytes_in: 2169.7821044921875
# node: n1, int: eth0, total_bytes_out: 0.319854736328125, total_bytes_in: 2.8904266357421875
# node: n2, int: eth1, total_bytes_out: 437.29112243652344, total_bytes_in: 445.28912353515625
# node: n2, int: eth0, total_bytes_out: 0.5386581420898438, total_bytes_in: 0.5021820068359375
# node: n3, int: eth1, total_bytes_out: 1286.0792388916016, total_bytes_in: 870.3281707763672
# node: n3, int: eth0, total_bytes_out: 0.10797119140625, total_bytes_in: 0.070465087890625
# node: g0, int: eth1, total_bytes_out: 0.2724609375, total_bytes_in: 0.08448028564453125
# node: g0, int: eth0, total_bytes_out: 0.1037139892578125, total_bytes_in: 0.06281280517578125
# node: g1, int: eth1, total_bytes_out: 0.26682281494140625, total_bytes_in: 0.08625030517578125
# node: g1, int: eth0, total_bytes_out: 0.1065673828125, total_bytes_in: 0.06656646728515625
# [['n0', 'eth1', 435.61009216308594, 442.8074645996094], ['n0', 'eth0', 0.1067352294921875, 0.0694580078125], ['n1', 'eth1', 1814.0099411010742, 2169.7821044921875], ['n1', 'eth0', 0.319854736328125, 2.8904266357421875], ['n2', 'eth1', 437.29112243652344, 445.28912353515625], ['n2', 'eth0', 0.5386581420898438, 0.5021820068359375], ['n3', 'eth1', 1286.0792388916016, 870.3281707763672], ['n3', 'eth0', 0.10797119140625, 0.070465087890625], ['g0', 'eth1', 0.2724609375, 0.08448028564453125], ['g0', 'eth0', 0.1037139892578125, 0.06281280517578125], ['g1', 'eth1', 0.26682281494140625, 0.08625030517578125], ['g1', 'eth0', 0.1065673828125, 0.06656646728515625]]
# (run pid=592)   experiment_id: 1be579c51aca490f9620509f5a1cdf84
# (run pid=592)   hostname: example-cluster-ray-worker-type-7xzdn
# (run pid=592)   iterations_since_restore: 1
# (run pid=592)   mean_accuracy: 0.459375
# (run pid=592)   node_ip: 10.244.4.2
# (run pid=592)   pid: 3904
# (run pid=592)   should_checkpoint: true
# (run pid=592)   time_since_restore: 0.27378225326538086
# (run pid=592)   time_this_iter_s: 0.27378225326538086
# (run pid=592)   time_total_s: 0.27378225326538086
# (run pid=592)   timestamp: 1649866597
# (run pid=592)   timesteps_since_restore: 0
# (run pid=592)   training_iteration: 1
# (run pid=592)   trial_id: 0c92a_00002
# (run pid=592)   
# (run pid=592) Result for WrappedDistributedTorchTrainable_0c92a_00000:
# (run pid=592)   date: 2022-04-13_09-16-38
# (run pid=592)   done: true
# (run pid=592)   experiment_id: fb91ec9bc31a4a3dadd3b1aa058e7981
# (run pid=592)   experiment_tag: '0'
# (run pid=592)   hostname: example-cluster-ray-worker-type-7xzdn
# (run pid=592)   iterations_since_restore: 5
# (run pid=592)   mean_accuracy: 0.809375
# (run pid=592)   node_ip: 10.244.4.2
# (run pid=592)   pid: 3871
# (run pid=592)   time_since_restore: 9.398651361465454
# (run pid=592)   time_this_iter_s: 0.25548505783081055
# (run pid=592)   time_total_s: 9.398651361465454
# (run pid=592)   timestamp: 1649866598
# (run pid=592)   timesteps_since_restore: 0
# (run pid=592)   training_iteration: 5
# (run pid=592)   trial_id: 0c92a_00000
# (run pid=592)   
# (run pid=592) 2022-04-13 09:16:38,486   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_0c92a_00002: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-16-17/WrappedDistributedTorchTrainable_0c92a_00002_2_2022-04-13_09-16-29/checkpoint_000004/./
# (run pid=592) Traceback (most recent call last):
# (run pid=592)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=592)     checkpoint=trial.saving_to)
# (run pid=592)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=592)     callback.on_checkpoint(**info)
# (run pid=592)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=592)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=592)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=592)     CLOUD_CHECKPOINTING_URL))
# (run pid=592) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_0c92a_00002: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-16-17/WrappedDistributedTorchTrainable_0c92a_00002_2_2022-04-13_09-16-29/checkpoint_000004/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=592) 2022-04-13 09:16:38,904   INFO tune.py:639 -- Total run time: 22.23 seconds (20.75 seconds for the tuning loop).
# (run pid=592) Result for WrappedDistributedTorchTrainable_0c92a_00001:
# (run pid=592)   date: 2022-04-13_09-16-38
# (run pid=592)   done: true
# (run pid=592)   experiment_id: 0c6a5730353149e68d21c20f2dee686c
# (run pid=592)   experiment_tag: '1'
# (run pid=592)   hostname: example-cluster-ray-worker-type-h9z85
# (run pid=592)   iterations_since_restore: 5
# (run pid=592)   mean_accuracy: 0.84375
# (run pid=592)   node_ip: 10.244.1.2
# (run pid=592)   pid: 1534
# (run pid=592)   time_since_restore: 1.5961322784423828
# (run pid=592)   time_this_iter_s: 0.3466618061065674
# (run pid=592)   time_total_s: 1.5961322784423828
# (run pid=592)   timestamp: 1649866598
# (run pid=592)   timesteps_since_restore: 0
# (run pid=592)   training_iteration: 5
# (run pid=592)   trial_id: 0c92a_00001
# (run pid=592)   
# (run pid=592) Result for WrappedDistributedTorchTrainable_0c92a_00002:
# (run pid=592)   date: 2022-04-13_09-16-38
# (run pid=592)   done: true
# (run pid=592)   experiment_id: 1be579c51aca490f9620509f5a1cdf84
# (run pid=592)   experiment_tag: '2'
# (run pid=592)   hostname: example-cluster-ray-worker-type-7xzdn
# (run pid=592)   iterations_since_restore: 5
# (run pid=592)   mean_accuracy: 0.834375
# (run pid=592)   node_ip: 10.244.4.2
# (run pid=592)   pid: 3904
# (run pid=592)   time_since_restore: 1.461684226989746
# (run pid=592)   time_this_iter_s: 0.3200368881225586
# (run pid=592)   time_total_s: 1.461684226989746
# (run pid=592)   timestamp: 1649866598
# (run pid=592)   timesteps_since_restore: 0
# (run pid=592)   training_iteration: 5
# (run pid=592)   trial_id: 0c92a_00002
# (run pid=592)   
# (run pid=592) == Status ==
# (run pid=592) Current time: 2022-04-13 09:16:38 (running for 00:00:20.76)
# (run pid=592) Memory usage on this node: 2.5/5.5 GiB
# (run pid=592) Using FIFO scheduling algorithm.
# (run pid=592) Resources requested: 0/4 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.23 GiB objects
# (run pid=592) Current best trial: 0c92a_00001 with mean_accuracy=0.84375 and parameters={}
# (run pid=592) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-16-17
# (run pid=592) Number of trials: 3/3 (3 TERMINATED)
# (run pid=592) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=592) | Trial name                                   | status     | loc             |      acc |   iter |   total time (s) |
# (run pid=592) |----------------------------------------------+------------+-----------------+----------+--------+------------------|
# (run pid=592) | WrappedDistributedTorchTrainable_0c92a_00000 | TERMINATED | 10.244.4.2:3871 | 0.809375 |      5 |          9.39865 |
# (run pid=592) | WrappedDistributedTorchTrainable_0c92a_00001 | TERMINATED | 10.244.1.2:1534 | 0.84375  |      5 |          1.59613 |
# (run pid=592) | WrappedDistributedTorchTrainable_0c92a_00002 | TERMINATED | 10.244.4.2:3904 | 0.834375 |      5 |          1.46168 |
# (run pid=592) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=592) 
# (run pid=592) 
# Best hyperparameters found were:  {}
# Job completion time: 30.265338185010478

# job.batch "ray-test-job-8" deleted




# num_worker = 1, num_Samples = 5, head node mem limit: 6gb.
# At time: Wed Apr 13 11:29:50 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165900118169, bytes_in: 165919949344
# At time: Wed Apr 13 11:29:51 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1802489356, bytes_in: 12224325
# At time: Wed Apr 13 11:29:51 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 172783257458, bytes_in: 157841897017
# At time: Wed Apr 13 11:29:51 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1831594170, bytes_in: 308358741
# At time: Wed Apr 13 11:29:52 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 143103257505, bytes_in: 142746145272
# At time: Wed Apr 13 11:29:52 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1881577233, bytes_in: 36882077
# At time: Wed Apr 13 11:29:52 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 3176924791, bytes_in: 5881323063
# At time: Wed Apr 13 11:29:53 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991409627, bytes_in: 12657718
# At time: Wed Apr 13 11:29:53 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 111208864, bytes_in: 30158790
# At time: Wed Apr 13 11:29:53 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459548155, bytes_in: 4204279
# At time: Wed Apr 13 11:29:54 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 126659468, bytes_in: 32898534
# At time: Wed Apr 13 11:29:54 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 649083619, bytes_in: 7322176
# job.batch/ray-test-job-8 created

# job.batch/ray-test-job-8 condition met

# At time: Wed Apr 13 11:31:44 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 165956264435, bytes_in: 165976111267
# At time: Wed Apr 13 11:31:44 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1802590269, bytes_in: 12316668
# At time: Wed Apr 13 11:31:45 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 173080928713, bytes_in: 158238676423
# At time: Wed Apr 13 11:31:45 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1831646104, bytes_in: 308808678
# At time: Wed Apr 13 11:31:45 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 143328598113, bytes_in: 142973650594
# At time: Wed Apr 13 11:31:46 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1881642186, bytes_in: 36943567
# At time: Wed Apr 13 11:31:46 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 3290311292, bytes_in: 5885785471
# At time: Wed Apr 13 11:31:46 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991424289, bytes_in: 12666572
# At time: Wed Apr 13 11:31:47 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 111267116, bytes_in: 30174473
# At time: Wed Apr 13 11:31:47 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459562977, bytes_in: 4212842
# At time: Wed Apr 13 11:31:47 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 126717628, bytes_in: 32914841
# At time: Wed Apr 13 11:31:47 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 649098323, bytes_in: 7330649
# node: n0, int: eth1, total_bytes_out: 428.3620147705078, total_bytes_in: 428.4814682006836
# node: n0, int: eth0, total_bytes_out: 0.7699050903320312, total_bytes_in: 0.7045211791992188
# node: n1, int: eth1, total_bytes_out: 2271.051445007324, total_bytes_in: 3027.1866302490234
# node: n1, int: eth0, total_bytes_out: 0.3962249755859375, total_bytes_in: 3.4327468872070312
# node: n2, int: eth1, total_bytes_out: 1719.21240234375, total_bytes_in: 1735.7278594970703
# node: n2, int: eth0, total_bytes_out: 0.49555206298828125, total_bytes_in: 0.4691314697265625
# node: n3, int: eth1, total_bytes_out: 865.0703506469727, total_bytes_in: 34.04547119140625
# node: n3, int: eth0, total_bytes_out: 0.1118621826171875, total_bytes_in: 0.0675506591796875
# node: g0, int: eth1, total_bytes_out: 0.444427490234375, total_bytes_in: 0.11965179443359375
# node: g0, int: eth0, total_bytes_out: 0.1130828857421875, total_bytes_in: 0.06533050537109375
# node: g1, int: eth1, total_bytes_out: 0.4437255859375, total_bytes_in: 0.12441253662109375
# node: g1, int: eth0, total_bytes_out: 0.1121826171875, total_bytes_in: 0.06464385986328125
# [['n0', 'eth1', 428.3620147705078, 428.4814682006836], ['n0', 'eth0', 0.7699050903320312, 0.7045211791992188], ['n1', 'eth1', 2271.051445007324, 3027.1866302490234], ['n1', 'eth0', 0.3962249755859375, 3.4327468872070312], ['n2', 'eth1', 1719.21240234375, 1735.7278594970703], ['n2', 'eth0', 0.49555206298828125, 0.4691314697265625], ['n3', 'eth1', 865.0703506469727, 34.04547119140625], ['n3', 'eth0', 0.1118621826171875, 0.0675506591796875], ['g0', 'eth1', 0.444427490234375, 0.11965179443359375], ['g0', 'eth0', 0.1130828857421875, 0.06533050537109375], ['g1', 'eth1', 0.4437255859375, 0.12441253662109375], ['g1', 'eth0', 0.1121826171875, 0.06464385986328125]]
# (run pid=354)     checkpoint=trial.saving_to)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=354)     callback.on_checkpoint(**info)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=354)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=354)     CLOUD_CHECKPOINTING_URL))
# (run pid=354) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_0d414_00003: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38/WrappedDistributedTorchTrainable_0d414_00003_3_2022-04-13_09-31-05/checkpoint_000001/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=354) 2022-04-13 09:31:39,480   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_0d414_00004: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38/WrappedDistributedTorchTrainable_0d414_00004_4_2022-04-13_09-31-29/checkpoint_000001/./
# (run pid=354) Traceback (most recent call last):
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=354)     checkpoint=trial.saving_to)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=354)     callback.on_checkpoint(**info)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=354)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=354)     CLOUD_CHECKPOINTING_URL))
# (run pid=354) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_0d414_00004: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38/WrappedDistributedTorchTrainable_0d414_00004_4_2022-04-13_09-31-29/checkpoint_000001/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=354) 2022-04-13 09:31:40,015   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_0d414_00003: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38/WrappedDistributedTorchTrainable_0d414_00003_3_2022-04-13_09-31-05/checkpoint_000004/./
# (run pid=354) Traceback (most recent call last):
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=354)     checkpoint=trial.saving_to)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=354)     callback.on_checkpoint(**info)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=354)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=354)     CLOUD_CHECKPOINTING_URL))
# (run pid=354) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_0d414_00003: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38/WrappedDistributedTorchTrainable_0d414_00003_3_2022-04-13_09-31-05/checkpoint_000004/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=354) 2022-04-13 09:31:40,372   ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_0d414_00004: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38/WrappedDistributedTorchTrainable_0d414_00004_4_2022-04-13_09-31-29/checkpoint_000004/./
# (run pid=354) Traceback (most recent call last):
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=354)     checkpoint=trial.saving_to)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=354)     callback.on_checkpoint(**info)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=354)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=354)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=354)     CLOUD_CHECKPOINTING_URL))
# (run pid=354) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_0d414_00004: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38/WrappedDistributedTorchTrainable_0d414_00004_4_2022-04-13_09-31-29/checkpoint_000004/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=354)   
# (run pid=354) Result for WrappedDistributedTorchTrainable_0d414_00003:
# (run pid=354)   date: 2022-04-13_09-31-40
# (run pid=354)   done: true
# (run pid=354)   experiment_id: c6225286b2a7431c83f7c52ce293a775
# (run pid=354)   experiment_tag: '3'
# (run pid=354)   hostname: example-cluster-ray-worker-type-f849v
# (run pid=354)   iterations_since_restore: 5
# (run pid=354)   mean_accuracy: 0.7875
# (run pid=354)   node_ip: 10.244.1.2
# (run pid=354)   pid: 192
# (run pid=354)   time_since_restore: 5.2483179569244385
# (run pid=354)   time_this_iter_s: 0.23736882209777832
# (run pid=354)   time_total_s: 5.2483179569244385
# (run pid=354)   timestamp: 1649867500
# (run pid=354)   timesteps_since_restore: 0
# (run pid=354)   training_iteration: 5
# (run pid=354)   trial_id: 0d414_00003
# (run pid=354)   
# (run pid=354) Result for WrappedDistributedTorchTrainable_0d414_00004:
# (run pid=354)   date: 2022-04-13_09-31-40
# (run pid=354)   done: true
# (run pid=354)   experiment_id: 255cf0b892af4eb8b49ff38191e83462
# (run pid=354)   experiment_tag: '4'
# (run pid=354)   hostname: example-cluster-ray-worker-type-b92ld
# (run pid=354)   iterations_since_restore: 5
# (run pid=354)   mean_accuracy: 0.74375
# (run pid=354)   node_ip: 10.244.3.3
# (run pid=354)   pid: 709
# (run pid=354)   time_since_restore: 1.4759573936462402
# (run pid=354)   time_this_iter_s: 0.2947056293487549
# (run pid=354)   time_total_s: 1.4759573936462402
# (run pid=354)   timestamp: 1649867500
# (run pid=354)   timesteps_since_restore: 0
# (run pid=354)   training_iteration: 5
# (run pid=354)   trial_id: 0d414_00004
# (run pid=354)   
# (run pid=354) == Status ==
# (run pid=354) Current time: 2022-04-13 09:31:40 (running for 00:01:02.47)
# (run pid=354) Memory usage on this node: 3.2/5.5 GiB
# (run pid=354) Using FIFO scheduling algorithm.
# (run pid=354) Resources requested: 0/4 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.86 GiB objects
# (run pid=354) Current best trial: 0d414_00002 with mean_accuracy=0.85 and parameters={}
# (run pid=354) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_09-30-38
# (run pid=354) Number of trials: 5/5 (5 TERMINATED)
# (run pid=354) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=354) | Trial name                                   | status     | loc             |      acc |   iter |   total time (s) |
# (run pid=354) |----------------------------------------------+------------+-----------------+----------+--------+------------------|
# (run pid=354) | WrappedDistributedTorchTrainable_0d414_00000 | TERMINATED | 10.244.3.3:603  | 0.784375 |      5 |         28.6913  |
# (run pid=354) | WrappedDistributedTorchTrainable_0d414_00001 | TERMINATED | 10.244.2.14:754 | 0.846875 |      5 |         24.9582  |
# (run pid=354) | WrappedDistributedTorchTrainable_0d414_00002 | TERMINATED | 10.244.3.3:674  | 0.85     |      5 |         14.467   |
# (run pid=354) | WrappedDistributedTorchTrainable_0d414_00003 | TERMINATED | 10.244.1.2:192  | 0.7875   |      5 |          5.24832 |
# (run pid=354) | WrappedDistributedTorchTrainable_0d414_00004 | TERMINATED | 10.244.3.3:709  | 0.74375  |      5 |          1.47596 |
# (run pid=354) +----------------------------------------------+------------+-----------------+----------+--------+------------------+
# (run pid=354) 
# (run pid=354) 
# Best hyperparameters found were:  {}
# Job completion time: 71.83180273498874
# (run pid=354) 2022-04-13 09:31:40,779   INFO tune.py:639 -- Total run time: 63.95 seconds (62.46 seconds for the tuning loop).

# job.batch "ray-test-job-8" deleted




# num_workers = 2, num_samples = 2, final working version. Using FashionMNIST dataset and getting best batch_size as the hyperparameter
# At time: Wed Apr 13 19:34:21 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 2272413932, bytes_in: 2645014651
# At time: Wed Apr 13 19:34:22 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1765887399, bytes_in: 11758557
# At time: Wed Apr 13 19:34:22 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 14335634798, bytes_in: 13707331335
# At time: Wed Apr 13 19:34:22 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1768556523, bytes_in: 26481033
# At time: Wed Apr 13 19:34:23 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 1889799286, bytes_in: 1095842343
# At time: Wed Apr 13 19:34:23 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1766869611, bytes_in: 13323363
# At time: Wed Apr 13 19:34:23 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 12052386771, bytes_in: 12848404637
# At time: Wed Apr 13 19:34:24 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1765490999, bytes_in: 10892415
# At time: Wed Apr 13 19:34:24 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 2515081, bytes_in: 684380
# At time: Wed Apr 13 19:34:24 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270186437, bytes_in: 3182100
# At time: Wed Apr 13 19:34:24 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 2525353, bytes_in: 688721
# At time: Wed Apr 13 19:34:25 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270081563, bytes_in: 3028619
# job.batch/ray-test-job-8 created

# job.batch/ray-test-job-8 condition met

# At time: Wed Apr 13 19:35:42 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 2385848340, bytes_in: 2648927622
# At time: Wed Apr 13 19:35:43 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1765902615, bytes_in: 11769369
# At time: Wed Apr 13 19:35:43 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 14460727356, bytes_in: 13934730860
# At time: Wed Apr 13 19:35:43 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1768598169, bytes_in: 26824598
# At time: Wed Apr 13 19:35:44 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 2003219643, bytes_in: 1211149098
# At time: Wed Apr 13 19:35:44 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1766933906, bytes_in: 13385263
# At time: Wed Apr 13 19:35:44 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 12052482350, bytes_in: 12848426165
# At time: Wed Apr 13 19:35:45 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1765583952, bytes_in: 10976546
# At time: Wed Apr 13 19:35:45 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 2551667, bytes_in: 693930
# At time: Wed Apr 13 19:35:45 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270200309, bytes_in: 3190701
# At time: Wed Apr 13 19:35:45 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 2560719, bytes_in: 699603
# At time: Wed Apr 13 19:35:46 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270095917, bytes_in: 3037556
# node: n0, int: eth1, total_bytes_out: 865.4358520507812, total_bytes_in: 29.853599548339844
# node: n0, int: eth0, total_bytes_out: 0.1160888671875, total_bytes_in: 0.082489013671875
# node: n1, int: eth1, total_bytes_out: 954.3804779052734, total_bytes_in: 1734.9206924438477
# node: n1, int: eth0, total_bytes_out: 0.3177337646484375, total_bytes_in: 2.6211929321289062
# node: n2, int: eth1, total_bytes_out: 865.3286514282227, total_bytes_in: 879.7207260131836
# node: n2, int: eth0, total_bytes_out: 0.49053192138671875, total_bytes_in: 0.472259521484375
# node: n3, int: eth1, total_bytes_out: 0.7292098999023438, total_bytes_in: 0.16424560546875
# node: n3, int: eth0, total_bytes_out: 0.7091751098632812, total_bytes_in: 0.6418685913085938
# node: g0, int: eth1, total_bytes_out: 0.2791290283203125, total_bytes_in: 0.0728607177734375
# node: g0, int: eth0, total_bytes_out: 0.1058349609375, total_bytes_in: 0.06562042236328125
# node: g1, int: eth1, total_bytes_out: 0.2698211669921875, total_bytes_in: 0.0830230712890625
# node: g1, int: eth0, total_bytes_out: 0.1095123291015625, total_bytes_in: 0.06818389892578125
# [['n0', 'eth1', 865.4358520507812, 29.853599548339844], ['n0', 'eth0', 0.1160888671875, 0.082489013671875], ['n1', 'eth1', 954.3804779052734, 1734.9206924438477], ['n1', 'eth0', 0.3177337646484375, 2.6211929321289062], ['n2', 'eth1', 865.3286514282227, 879.7207260131836], ['n2', 'eth0', 0.49053192138671875, 0.472259521484375], ['n3', 'eth1', 0.7292098999023438, 0.16424560546875], ['n3', 'eth0', 0.7091751098632812, 0.6418685913085938], ['g0', 'eth1', 0.2791290283203125, 0.0728607177734375], ['g0', 'eth0', 0.1058349609375, 0.06562042236328125], ['g1', 'eth1', 0.2698211669921875, 0.0830230712890625], ['g1', 'eth0', 0.1095123291015625, 0.06818389892578125]]
# (run pid=9896) |----------------------------------------------+------------+----------------+--------------+----------+--------+------------------|
# (run pid=9896) | WrappedDistributedTorchTrainable_bcc5d_00001 | PENDING    |                |           64 |          |        |                  |
# (run pid=9896) | WrappedDistributedTorchTrainable_bcc5d_00000 | TERMINATED | 10.244.3.3:251 |           16 | 0.640625 |      5 |          4.81081 |
# (run pid=9896) +----------------------------------------------+------------+----------------+--------------+----------+--------+------------------+
# (run pid=9896) 
# (run pid=9896) 
# (run pid=9896) 2022-04-13 17:35:20,938  ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_bcc5d_00000: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_17-35-08/WrappedDistributedTorchTrainable_bcc5d_00000_0_batch_size=16_2022-04-13_17-35-11/checkpoint_000001/./
# (run pid=9896) Traceback (most recent call last):
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=9896)     checkpoint=trial.saving_to)
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=9896)     callback.on_checkpoint(**info)
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=9896)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=9896)     CLOUD_CHECKPOINTING_URL))
# (run pid=9896) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_bcc5d_00000: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_17-35-08/WrappedDistributedTorchTrainable_bcc5d_00000_0_batch_size=16_2022-04-13_17-35-11/checkpoint_000001/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# (run pid=9896) 2022-04-13 17:35:24,073  ERROR trial_runner.py:1068 -- Trial WrappedDistributedTorchTrainable_bcc5d_00000: Error handling checkpoint /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_17-35-08/WrappedDistributedTorchTrainable_bcc5d_00000_0_batch_size=16_2022-04-13_17-35-11/checkpoint_000004/./
# (run pid=9896) Traceback (most recent call last):
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/trial_runner.py", line 1062, in _process_trial_save
# (run pid=9896)     checkpoint=trial.saving_to)
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/callback.py", line 259, in on_checkpoint
# (run pid=9896)     callback.on_checkpoint(**info)
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 546, in on_checkpoint
# (run pid=9896)     self._sync_trial_checkpoint(trial, checkpoint)
# (run pid=9896)   File "/home/ray/anaconda3/lib/python3.7/site-packages/ray/tune/syncer.py", line 521, in _sync_trial_checkpoint
# (run pid=9896)     CLOUD_CHECKPOINTING_URL))
# (run pid=9896) ray.tune.error.TuneError: Trial WrappedDistributedTorchTrainable_bcc5d_00000: Checkpoint path /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_17-35-08/WrappedDistributedTorchTrainable_bcc5d_00000_0_batch_size=16_2022-04-13_17-35-11/checkpoint_000004/./ not found after successful sync down. Are you running on a Kubernetes or managed cluster? rsync will not function due to a lack of SSH functionality. You'll need to use cloud-checkpointing if that's the case, see instructions here: https://docs.ray.io/en/master/tune/user-guide.html#using-cloud-storage .
# Warning: The actor ImplicitFunc is very large (52 MiB). Check that its definition is not implicitly capturing a large array or other object in scope. Tip: use ray.put() to put large objects in the Ray object store.
# (run pid=9896) 2022-04-13 17:35:39,080  INFO tune.py:639 -- Total run time: 31.49 seconds (30.04 seconds for the tuning loop).
# (run pid=9896) == Status ==
# (run pid=9896) Current time: 2022-04-13 17:35:37 (running for 00:00:28.45)
# (run pid=9896) Memory usage on this node: 3.0/5.5 GiB
# (run pid=9896) Using FIFO scheduling algorithm.
# (run pid=9896) Resources requested: 2.0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=9896) Current best trial: bcc5d_00000 with mean_accuracy=0.640625 and parameters={'batch_size': 16}
# (run pid=9896) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_17-35-08
# (run pid=9896) Number of trials: 2/2 (1 RUNNING, 1 TERMINATED)
# (run pid=9896) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=9896) | Trial name                                   | status     | loc              |   batch_size |      acc |   iter |   total time (s) |
# (run pid=9896) |----------------------------------------------+------------+------------------+--------------+----------+--------+------------------|
# (run pid=9896) | WrappedDistributedTorchTrainable_bcc5d_00001 | RUNNING    | 10.244.2.4:10277 |           64 |          |        |                  |
# (run pid=9896) | WrappedDistributedTorchTrainable_bcc5d_00000 | TERMINATED | 10.244.3.3:251   |           16 | 0.640625 |      5 |          4.81081 |
# (run pid=9896) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=9896) 
# (run pid=9896) 
# (run pid=9896) Result for WrappedDistributedTorchTrainable_bcc5d_00001:
# (run pid=9896)   date: 2022-04-13_17-35-37
# (run pid=9896)   done: false
# (run pid=9896)   experiment_id: 68c8b0cfffa740e1b85414161c7edcca
# (run pid=9896)   hostname: example-cluster-ray-head-type-twp5n
# (run pid=9896)   iterations_since_restore: 1
# (run pid=9896)   mean_accuracy: 0.540625
# (run pid=9896)   node_ip: 10.244.2.4
# (run pid=9896)   pid: 10277
# (run pid=9896)   should_checkpoint: true
# (run pid=9896)   time_since_restore: 0.30310606956481934
# (run pid=9896)   time_this_iter_s: 0.30310606956481934
# (run pid=9896)   time_total_s: 0.30310606956481934
# (run pid=9896)   timestamp: 1649896537
# (run pid=9896)   timesteps_since_restore: 0
# (run pid=9896)   training_iteration: 1
# (run pid=9896)   trial_id: bcc5d_00001
# (run pid=9896)   
# (run pid=9896) Result for WrappedDistributedTorchTrainable_bcc5d_00001:
# (run pid=9896)   date: 2022-04-13_17-35-38
# (run pid=9896)   done: true
# (run pid=9896)   experiment_id: 68c8b0cfffa740e1b85414161c7edcca
# (run pid=9896)   experiment_tag: 1_batch_size=64
# (run pid=9896)   hostname: example-cluster-ray-head-type-twp5n
# (run pid=9896)   iterations_since_restore: 5
# (run pid=9896)   mean_accuracy: 0.684375
# (run pid=9896)   node_ip: 10.244.2.4
# (run pid=9896)   pid: 10277
# (run pid=9896)   time_since_restore: 1.5542378425598145
# (run pid=9896)   time_this_iter_s: 0.30683016777038574
# (run pid=9896)   time_total_s: 1.5542378425598145
# (run pid=9896)   timestamp: 1649896538
# (run pid=9896)   timesteps_since_restore: 0
# (run pid=9896)   training_iteration: 5
# (run pid=9896)   trial_id: bcc5d_00001
# (run pid=9896)   
# (run pid=9896) == Status ==
# (run pid=9896) Current time: 2022-04-13 17:35:38 (running for 00:00:30.05)
# (run pid=9896) Memory usage on this node: 3.0/5.5 GiB
# (run pid=9896) Using FIFO scheduling algorithm.
# (run pid=9896) Resources requested: 0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=9896) Current best trial: bcc5d_00001 with mean_accuracy=0.684375 and parameters={'batch_size': 64}
# (run pid=9896) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_17-35-08
# (run pid=9896) Number of trials: 2/2 (2 TERMINATED)
# (run pid=9896) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=9896) | Trial name                                   | status     | loc              |   batch_size |      acc |   iter |   total time (s) |
# (run pid=9896) |----------------------------------------------+------------+------------------+--------------+----------+--------+------------------|
# (run pid=9896) | WrappedDistributedTorchTrainable_bcc5d_00000 | TERMINATED | 10.244.3.3:251   |           16 | 0.640625 |      5 |          4.81081 |
# (run pid=9896) | WrappedDistributedTorchTrainable_bcc5d_00001 | TERMINATED | 10.244.2.4:10277 |           64 | 0.684375 |      5 |          1.55424 |
# (run pid=9896) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=9896) 
# (run pid=9896) 
# Best hyperparameters found were:  {'batch_size': 64}
# Job completion time: 39.377536617999795

# job.batch "ray-test-job-8" deleted




# same as above
# At time: Wed Apr 13 20:27:15 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 2430987752, bytes_in: 2775182958
# At time: Wed Apr 13 20:27:15 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1766014179, bytes_in: 11795221
# At time: Wed Apr 13 20:27:15 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 14974947268, bytes_in: 14076943537
# At time: Wed Apr 13 20:27:16 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1769684901, bytes_in: 37674781
# At time: Wed Apr 13 20:27:16 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 2016541268, bytes_in: 1289245422
# At time: Wed Apr 13 20:27:16 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1767273992, bytes_in: 14405165
# At time: Wed Apr 13 20:27:17 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 12091039789, bytes_in: 12930937350
# At time: Wed Apr 13 20:27:17 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1765695984, bytes_in: 11003404
# At time: Wed Apr 13 20:27:17 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 4037536, bytes_in: 1095290
# At time: Wed Apr 13 20:27:17 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270309947, bytes_in: 3213887
# At time: Wed Apr 13 20:27:18 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 4052256, bytes_in: 1100457
# At time: Wed Apr 13 20:27:18 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270217939, bytes_in: 3072250
# job.batch/ray-test-job-8 created

# job.batch/ray-test-job-8 condition met

# At time: Wed Apr 13 20:28:37 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 2488401786, bytes_in: 2779098682
# At time: Wed Apr 13 20:28:38 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1766028117, bytes_in: 11804075
# At time: Wed Apr 13 20:28:38 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 15044367325, bytes_in: 14248850749
# At time: Wed Apr 13 20:28:38 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1769726095, bytes_in: 37970104
# At time: Wed Apr 13 20:28:39 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 2130494233, bytes_in: 1349111841
# At time: Wed Apr 13 20:28:39 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1767338237, bytes_in: 14466771
# At time: Wed Apr 13 20:28:39 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 12091173241, bytes_in: 12930986234
# At time: Wed Apr 13 20:28:40 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1765790077, bytes_in: 11089927
# At time: Wed Apr 13 20:28:40 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 4074536, bytes_in: 1105162
# At time: Wed Apr 13 20:28:40 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270323753, bytes_in: 3222357
# At time: Wed Apr 13 20:28:40 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 4090699, bytes_in: 1111504
# At time: Wed Apr 13 20:28:41 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270231887, bytes_in: 3080744
# node: n0, int: eth1, total_bytes_out: 438.03431701660156, total_bytes_in: 29.874603271484375
# node: n0, int: eth0, total_bytes_out: 0.1063385009765625, total_bytes_in: 0.0675506591796875
# node: n1, int: eth1, total_bytes_out: 529.6330032348633, total_bytes_in: 1311.5479431152344
# node: n1, int: eth0, total_bytes_out: 0.3142852783203125, total_bytes_in: 2.2531356811523438
# node: n2, int: eth1, total_bytes_out: 869.3921279907227, total_bytes_in: 456.7445297241211
# node: n2, int: eth0, total_bytes_out: 0.49015045166015625, total_bytes_in: 0.4700164794921875
# node: n3, int: eth1, total_bytes_out: 1.018157958984375, total_bytes_in: 0.372955322265625
# node: n3, int: eth0, total_bytes_out: 0.7178726196289062, total_bytes_in: 0.6601181030273438
# node: g0, int: eth1, total_bytes_out: 0.28228759765625, total_bytes_in: 0.0753173828125
# node: g0, int: eth0, total_bytes_out: 0.1053314208984375, total_bytes_in: 0.0646209716796875
# node: g1, int: eth1, total_bytes_out: 0.29329681396484375, total_bytes_in: 0.08428192138671875
# node: g1, int: eth0, total_bytes_out: 0.106414794921875, total_bytes_in: 0.0648040771484375
# [['n0', 'eth1', 438.03431701660156, 29.874603271484375], ['n0', 'eth0', 0.1063385009765625, 0.0675506591796875], ['n1', 'eth1', 529.6330032348633, 1311.5479431152344], ['n1', 'eth0', 0.3142852783203125, 2.2531356811523438], ['n2', 'eth1', 869.3921279907227, 456.7445297241211], ['n2', 'eth0', 0.49015045166015625, 0.4700164794921875], ['n3', 'eth1', 1.018157958984375, 0.372955322265625], ['n3', 'eth0', 0.7178726196289062, 0.6601181030273438], ['g0', 'eth1', 0.28228759765625, 0.0753173828125], ['g0', 'eth0', 0.1053314208984375, 0.0646209716796875], ['g1', 'eth1', 0.29329681396484375, 0.08428192138671875], ['g1', 'eth0', 0.106414794921875, 0.0648040771484375]]
# (run pid=14476) Using FIFO scheduling algorithm.
# (run pid=14476) Resources requested: 0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=14476) Current best trial: 208bf_00000 with mean_accuracy=0.696875 and parameters={'batch_size': 16}
# (run pid=14476) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-28-02
# (run pid=14476) Number of trials: 2/2 (1 PENDING, 1 TERMINATED)
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) | Trial name                                   | status     | loc              |   batch_size |      acc |   iter |   total time (s) |
# (run pid=14476) |----------------------------------------------+------------+------------------+--------------+----------+--------+------------------|
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00001 | PENDING    |                  |           16 |          |        |                  |
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00000 | TERMINATED | 10.244.2.4:14669 |           16 | 0.696875 |      5 |          5.09685 |
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) 
# (run pid=14476) 
# (run pid=14476) == Status ==
# (run pid=14476) Current time: 2022-04-13 18:28:33 (running for 00:00:30.19)
# (run pid=14476) Memory usage on this node: 3.3/5.5 GiB
# (run pid=14476) Using FIFO scheduling algorithm.
# (run pid=14476) Resources requested: 2.0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=14476) Current best trial: 208bf_00000 with mean_accuracy=0.696875 and parameters={'batch_size': 16}
# (run pid=14476) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-28-02
# (run pid=14476) Number of trials: 2/2 (1 RUNNING, 1 TERMINATED)
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) | Trial name                                   | status     | loc              |   batch_size |      acc |   iter |   total time (s) |
# (run pid=14476) |----------------------------------------------+------------+------------------+--------------+----------+--------+------------------|
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00001 | RUNNING    | 10.244.2.4:14905 |           16 |          |        |                  |
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00000 | TERMINATED | 10.244.2.4:14669 |           16 | 0.696875 |      5 |          5.09685 |
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) 
# (run pid=14476) 
# (run pid=14476) 2022-04-13 18:28:34,751 INFO tune.py:639 -- Total run time: 33.44 seconds (31.80 seconds for the tuning loop).
# (run pid=14476) Result for WrappedDistributedTorchTrainable_208bf_00001:
# (run pid=14476)   date: 2022-04-13_18-28-33
# (run pid=14476)   done: false
# (run pid=14476)   experiment_id: 497df660f1e44ef1888f97a2d775bc71
# (run pid=14476)   hostname: example-cluster-ray-head-type-twp5n
# (run pid=14476)   iterations_since_restore: 1
# (run pid=14476)   mean_accuracy: 0.528125
# (run pid=14476)   node_ip: 10.244.2.4
# (run pid=14476)   pid: 14905
# (run pid=14476)   should_checkpoint: true
# (run pid=14476)   time_since_restore: 0.3015730381011963
# (run pid=14476)   time_this_iter_s: 0.3015730381011963
# (run pid=14476)   time_total_s: 0.3015730381011963
# (run pid=14476)   timestamp: 1649899713
# (run pid=14476)   timesteps_since_restore: 0
# (run pid=14476)   training_iteration: 1
# (run pid=14476)   trial_id: 208bf_00001
# (run pid=14476)   
# (run pid=14476) == Status ==
# (run pid=14476) Current time: 2022-04-13 18:28:33 (running for 00:00:30.54)
# (run pid=14476) Memory usage on this node: 3.0/5.5 GiB
# (run pid=14476) Using FIFO scheduling algorithm.
# (run pid=14476) Resources requested: 2.0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=14476) Current best trial: 208bf_00000 with mean_accuracy=0.696875 and parameters={'batch_size': 16}
# (run pid=14476) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-28-02
# (run pid=14476) Number of trials: 2/2 (1 RUNNING, 1 TERMINATED)
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) | Trial name                                   | status     | loc              |   batch_size |      acc |   iter |   total time (s) |
# (run pid=14476) |----------------------------------------------+------------+------------------+--------------+----------+--------+------------------|
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00001 | RUNNING    | 10.244.2.4:14905 |           16 | 0.528125 |      1 |         0.301573 |
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00000 | TERMINATED | 10.244.2.4:14669 |           16 | 0.696875 |      5 |         5.09685  |
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) 
# (run pid=14476) 
# (run pid=14476) Result for WrappedDistributedTorchTrainable_208bf_00001:
# (run pid=14476)   date: 2022-04-13_18-28-34
# (run pid=14476)   done: true
# (run pid=14476)   experiment_id: 497df660f1e44ef1888f97a2d775bc71
# (run pid=14476)   experiment_tag: 1_batch_size=16
# (run pid=14476)   hostname: example-cluster-ray-head-type-twp5n
# (run pid=14476)   iterations_since_restore: 5
# (run pid=14476)   mean_accuracy: 0.703125
# (run pid=14476)   node_ip: 10.244.2.4
# (run pid=14476)   pid: 14905
# (run pid=14476)   time_since_restore: 1.5922462940216064
# (run pid=14476)   time_this_iter_s: 0.3197779655456543
# (run pid=14476)   time_total_s: 1.5922462940216064
# (run pid=14476)   timestamp: 1649899714
# (run pid=14476)   timesteps_since_restore: 0
# (run pid=14476)   training_iteration: 5
# (run pid=14476)   trial_id: 208bf_00001
# (run pid=14476)   
# (run pid=14476) == Status ==
# (run pid=14476) Current time: 2022-04-13 18:28:34 (running for 00:00:31.80)
# (run pid=14476) Memory usage on this node: 3.1/5.5 GiB
# (run pid=14476) Using FIFO scheduling algorithm.
# (run pid=14476) Resources requested: 0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=14476) Current best trial: 208bf_00001 with mean_accuracy=0.703125 and parameters={'batch_size': 16}
# (run pid=14476) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-28-02
# (run pid=14476) Number of trials: 2/2 (2 TERMINATED)
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) | Trial name                                   | status     | loc              |   batch_size |      acc |   iter |   total time (s) |
# (run pid=14476) |----------------------------------------------+------------+------------------+--------------+----------+--------+------------------|
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00000 | TERMINATED | 10.244.2.4:14669 |           16 | 0.696875 |      5 |          5.09685 |
# (run pid=14476) | WrappedDistributedTorchTrainable_208bf_00001 | TERMINATED | 10.244.2.4:14905 |           16 | 0.703125 |      5 |          1.59225 |
# (run pid=14476) +----------------------------------------------+------------+------------------+--------------+----------+--------+------------------+
# (run pid=14476) 
# (run pid=14476) 
# Best hyperparameters found were:  {'batch_size': 16}
# Job completion time: 41.3549968490006

# job.batch "ray-test-job-8" deleted




# same as above
# At time: Wed Apr 13 20:49:34 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 2502094459, bytes_in: 2803122864
# At time: Wed Apr 13 20:49:35 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1766170008, bytes_in: 11904488
# At time: Wed Apr 13 20:49:35 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 15300869419, bytes_in: 14316644717
# At time: Wed Apr 13 20:49:35 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1770251347, bytes_in: 42982619
# At time: Wed Apr 13 20:49:36 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 2152570749, bytes_in: 1459345955
# At time: Wed Apr 13 20:49:36 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1767485900, bytes_in: 15007835
# At time: Wed Apr 13 20:49:36 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 12103931772, bytes_in: 12956116539
# At time: Wed Apr 13 20:49:37 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1765848293, bytes_in: 11109511
# At time: Wed Apr 13 20:49:37 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 4688507, bytes_in: 1271432
# At time: Wed Apr 13 20:49:37 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270381441, bytes_in: 3241223
# At time: Wed Apr 13 20:49:38 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 4698401, bytes_in: 1278533
# At time: Wed Apr 13 20:49:38 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270293225, bytes_in: 3102820
# job.batch/ray-test-job-8 created

# job.batch/ray-test-job-8 condition met

# At time: Wed Apr 13 20:50:59 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 2615592994, bytes_in: 2807165057
# At time: Wed Apr 13 20:50:59 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1766184370, bytes_in: 11914132
# At time: Wed Apr 13 20:50:59 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 15370737469, bytes_in: 14488485435
# At time: Wed Apr 13 20:51:00 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1770292101, bytes_in: 43314150
# At time: Wed Apr 13 20:51:00 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 2210300357, bytes_in: 1519141307
# At time: Wed Apr 13 20:51:01 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1767549863, bytes_in: 15068601
# At time: Wed Apr 13 20:51:01 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 12104081465, bytes_in: 12956183332
# At time: Wed Apr 13 20:51:01 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1765943337, bytes_in: 11196480
# At time: Wed Apr 13 20:51:02 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 4733439, bytes_in: 1282882
# At time: Wed Apr 13 20:51:02 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270395299, bytes_in: 3249849
# At time: Wed Apr 13 20:51:02 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 4745126, bytes_in: 1288936
# At time: Wed Apr 13 20:51:02 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270307329, bytes_in: 3111470
# node: n0, int: eth1, total_bytes_out: 865.9251022338867, total_bytes_in: 30.83948516845703
# node: n0, int: eth0, total_bytes_out: 0.1095733642578125, total_bytes_in: 0.073577880859375
# node: n1, int: eth1, total_bytes_out: 533.0509185791016, total_bytes_in: 1311.0406341552734
# node: n1, int: eth0, total_bytes_out: 0.3109283447265625, total_bytes_in: 2.5293807983398438
# node: n2, int: eth1, total_bytes_out: 440.44195556640625, total_bytes_in: 456.20233154296875
# node: n2, int: eth0, total_bytes_out: 0.48799896240234375, total_bytes_in: 0.4636077880859375
# node: n3, int: eth1, total_bytes_out: 1.1420669555664062, total_bytes_in: 0.5095901489257812
# node: n3, int: eth0, total_bytes_out: 0.725128173828125, total_bytes_in: 0.6635208129882812
# node: g0, int: eth1, total_bytes_out: 0.342803955078125, total_bytes_in: 0.0873565673828125
# node: g0, int: eth0, total_bytes_out: 0.1057281494140625, total_bytes_in: 0.0658111572265625
# node: g1, int: eth1, total_bytes_out: 0.35648345947265625, total_bytes_in: 0.07936859130859375
# node: g1, int: eth0, total_bytes_out: 0.10760498046875, total_bytes_in: 0.0659942626953125
# [['n0', 'eth1', 865.9251022338867, 30.83948516845703], ['n0', 'eth0', 0.1095733642578125, 0.073577880859375], ['n1', 'eth1', 533.0509185791016, 1311.0406341552734], ['n1', 'eth0', 0.3109283447265625, 2.5293807983398438], ['n2', 'eth1', 440.44195556640625, 456.20233154296875], ['n2', 'eth0', 0.48799896240234375, 0.4636077880859375], ['n3', 'eth1', 1.1420669555664062, 0.5095901489257812], ['n3', 'eth0', 0.725128173828125, 0.6635208129882812], ['g0', 'eth1', 0.342803955078125, 0.0873565673828125], ['g0', 'eth0', 0.1057281494140625, 0.0658111572265625], ['g1', 'eth1', 0.35648345947265625, 0.07936859130859375], ['g1', 'eth0', 0.10760498046875, 0.0659942626953125]]
# (run pid=20346) Resources requested: 0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=20346) Current best trial: 3efc3_00000 with mean_accuracy=0.7375 and parameters={'batch_size': 64}
# (run pid=20346) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-50-22
# (run pid=20346) Number of trials: 2/2 (1 PENDING, 1 TERMINATED)
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) | Trial name                                   | status     | loc              |   batch_size |    acc |   iter |   total time (s) |
# (run pid=20346) |----------------------------------------------+------------+------------------+--------------+--------+--------+------------------|
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00001 | PENDING    |                  |           16 |        |        |                  |
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00000 | TERMINATED | 10.244.2.4:20540 |           64 | 0.7375 |      5 |          5.06059 |
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) 
# (run pid=20346) 
# (run pid=20346) == Status ==
# (run pid=20346) Current time: 2022-04-13 18:50:47 (running for 00:00:24.71)
# (run pid=20346) Memory usage on this node: 2.9/5.5 GiB
# (run pid=20346) Using FIFO scheduling algorithm.
# (run pid=20346) Resources requested: 0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=20346) Current best trial: 3efc3_00000 with mean_accuracy=0.7375 and parameters={'batch_size': 64}
# (run pid=20346) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-50-22
# (run pid=20346) Number of trials: 2/2 (1 PENDING, 1 TERMINATED)
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) | Trial name                                   | status     | loc              |   batch_size |    acc |   iter |   total time (s) |
# (run pid=20346) |----------------------------------------------+------------+------------------+--------------+--------+--------+------------------|
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00001 | PENDING    |                  |           16 |        |        |                  |
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00000 | TERMINATED | 10.244.2.4:20540 |           64 | 0.7375 |      5 |          5.06059 |
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) 
# (run pid=20346) 
# Warning: The actor ImplicitFunc is very large (52 MiB). Check that its definition is not implicitly capturing a large array or other object in scope. Tip: use ray.put() to put large objects in the Ray object store.
# (run pid=20346) == Status ==
# (run pid=20346) Current time: 2022-04-13 18:50:53 (running for 00:00:30.98)
# (run pid=20346) Memory usage on this node: 3.1/5.5 GiB
# (run pid=20346) Using FIFO scheduling algorithm.
# (run pid=20346) Resources requested: 2.0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=20346) Current best trial: 3efc3_00000 with mean_accuracy=0.7375 and parameters={'batch_size': 64}
# (run pid=20346) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-50-22
# (run pid=20346) Number of trials: 2/2 (1 RUNNING, 1 TERMINATED)
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) | Trial name                                   | status     | loc              |   batch_size |    acc |   iter |   total time (s) |
# (run pid=20346) |----------------------------------------------+------------+------------------+--------------+--------+--------+------------------|
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00001 | RUNNING    | 10.244.2.4:20781 |           16 |        |        |                  |
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00000 | TERMINATED | 10.244.2.4:20540 |           64 | 0.7375 |      5 |          5.06059 |
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) 
# (run pid=20346) 
# (run pid=20346) Result for WrappedDistributedTorchTrainable_3efc3_00001:
# (run pid=20346)   date: 2022-04-13_18-50-53
# (run pid=20346)   done: false
# (run pid=20346)   experiment_id: 20399c32b7644d9b946bbc8673cbb58e
# (run pid=20346)   hostname: example-cluster-ray-head-type-twp5n
# (run pid=20346)   iterations_since_restore: 1
# (run pid=20346)   mean_accuracy: 0.38125
# (run pid=20346)   node_ip: 10.244.2.4
# (run pid=20346)   pid: 20781
# (run pid=20346)   should_checkpoint: true
# (run pid=20346)   time_since_restore: 0.3338639736175537
# (run pid=20346)   time_this_iter_s: 0.3338639736175537
# (run pid=20346)   time_total_s: 0.3338639736175537
# (run pid=20346)   timestamp: 1649901053
# (run pid=20346)   timesteps_since_restore: 0
# (run pid=20346)   training_iteration: 1
# (run pid=20346)   trial_id: 3efc3_00001
# (run pid=20346)   
# (run pid=20346) Result for WrappedDistributedTorchTrainable_3efc3_00001:
# (run pid=20346)   date: 2022-04-13_18-50-55
# (run pid=20346)   done: true
# (run pid=20346)   experiment_id: 20399c32b7644d9b946bbc8673cbb58e
# (run pid=20346)   experiment_tag: 1_batch_size=16
# (run pid=20346)   hostname: example-cluster-ray-head-type-twp5n
# (run pid=20346)   iterations_since_restore: 5
# (run pid=20346)   mean_accuracy: 0.725
# (run pid=20346)   node_ip: 10.244.2.4
# (run pid=20346)   pid: 20781
# (run pid=20346)   time_since_restore: 1.6736342906951904
# (run pid=20346)   time_this_iter_s: 0.3308839797973633
# (run pid=20346)   time_total_s: 1.6736342906951904
# (run pid=20346)   timestamp: 1649901055
# (run pid=20346)   timesteps_since_restore: 0
# (run pid=20346)   training_iteration: 5
# (run pid=20346)   trial_id: 3efc3_00001
# (run pid=20346)   
# (run pid=20346) == Status ==
# (run pid=20346) Current time: 2022-04-13 18:50:55 (running for 00:00:32.69)
# (run pid=20346) Memory usage on this node: 3.1/5.5 GiB
# (run pid=20346) Using FIFO scheduling algorithm.
# (run pid=20346) Resources requested: 0/3 CPUs, 0/0 GPUs, 0.0/5.6 GiB heap, 0.0/2.26 GiB objects
# (run pid=20346) Current best trial: 3efc3_00000 with mean_accuracy=0.7375 and parameters={'batch_size': 64}
# (run pid=20346) Result logdir: /home/ray/ray_results/WrappedDistributedTorchTrainable_2022-04-13_18-50-22
# (run pid=20346) Number of trials: 2/2 (2 TERMINATED)
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) | Trial name                                   | status     | loc              |   batch_size |    acc |   iter |   total time (s) |
# (run pid=20346) |----------------------------------------------+------------+------------------+--------------+--------+--------+------------------|
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00000 | TERMINATED | 10.244.2.4:20540 |           64 | 0.7375 |      5 |          5.06059 |
# (run pid=20346) | WrappedDistributedTorchTrainable_3efc3_00001 | TERMINATED | 10.244.2.4:20781 |           16 | 0.725  |      5 |          1.67363 |
# (run pid=20346) +----------------------------------------------+------------+------------------+--------------+--------+--------+------------------+
# (run pid=20346) 
# (run pid=20346) 
# Best hyperparameters found were:  {'batch_size': 64}
# Job completion time: 42.15458594499978
# (run pid=20346) 2022-04-13 18:50:55,176 INFO tune.py:639 -- Total run time: 34.09 seconds (32.69 seconds for the tuning loop).

# job.batch "ray-test-job-8" deleted