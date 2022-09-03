import os
import sys
sys.path.append("utils")
from measure_traffic import get_all_node_interface_usage, get_interval_all_node_interface_usage, exec_sh_command

SATS_TOPO_WITH_INTERFACE_FILE = "gen_cluster_data/topo_with_interface_file.txt"
statistics_pod_list = ["get-statistics-2blj9", "get-statistics-4v4bp", "get-statistics-jd9f8", "get-statistics-kkmkk", "get-statistics-nsv4c", "get-statistics-tj5n8", "get-statistics-2v9pl"] # includes pods in all nodes except for k8s master node
TRAIN_FASHION_MNIST_JOB_YAML_FILE = "kubernetes/job-example-9.yaml"
JOB_NAME = "ray-test-job-9" # Note: this is obtained within TRAIN_FASHION_MNIST_JOB_YAML_FILE

# Before job starts:
node_interface_usage_old = get_all_node_interface_usage(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE)
get_pod_info_cmd = ['kubectl', '-n', 'ray', 'get', 'pods', '-o', 'wide']
o = exec_sh_command(get_pod_info_cmd)
print(o)
get_pod_info_cmd = ['kubectl', 'get', 'pods', '-o', 'wide']
o = exec_sh_command(get_pod_info_cmd)
print(o)

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
# get_logs_2 = ['tail', '-n', '100'] # only 15 lines necessary for this job
o = exec_sh_command(get_logs_cmd)
print(o)

# Delete job:
delete_job_cmd = ['kubectl', '-n', 'ray', 'delete', 'job', JOB_NAME]
o = exec_sh_command(delete_job_cmd)
print(o)





# num_partitions = 50, max 6GB head node. Unfortunately too much output this run so did not see everything:
# Reduce Progress.:   2%|▏         | 1/50 [02:16<00:05,  9.17it/s]
# Reduce Progress.:   6%|▌         | 3/50 [02:17<00:03, 14.53it/s]
# Reduce Progress.:   8%|▊         | 4/50 [02:18<00:17,  2.57it/s]
# Reduce Progress.:  10%|█         | 5/50 [02:19<00:28,  1.58it/s]
# Reduce Progress.:  12%|█▏        | 6/50 [02:19<00:20,  2.15it/s]
# Reduce Progress.:  14%|█▍        | 7/50 [02:19<00:15,  2.82it/s]
# Reduce Progress.:  16%|█▌        | 8/50 [02:20<00:20,  2.07it/s]
# Reduce Progress.:  18%|█▊        | 9/50 [02:21<00:26,  1.56it/s]
# Reduce Progress.:  20%|██        | 10/50 [02:23<00:46,  1.16s/it]
# Reduce Progress.:  22%|██▏       | 11/50 [02:24<00:42,  1.08s/it]
# Reduce Progress.:  24%|██▍       | 12/50 [02:24<00:29,  1.27it/s]
# Reduce Progress.:  26%|██▌       | 13/50 [02:25<00:27,  1.35it/s]
# Reduce Progress.:  28%|██▊       | 14/50 [02:25<00:23,  1.54it/s]
# Reduce Progress.:  30%|███       | 15/50 [02:26<00:21,  1.62it/s]
# Reduce Progress.:  32%|███▏      | 16/50 [02:26<00:17,  2.00it/s]
# Reduce Progress.:  34%|███▍      | 17/50 [02:26<00:13,  2.41it/s]
# Reduce Progress.:  38%|███▊      | 19/50 [02:27<00:15,  1.94it/s]
# Reduce Progress.:  40%|████      | 20/50 [02:28<00:14,  2.13it/s]
# Reduce Progress.:  42%|████▏     | 21/50 [02:28<00:11,  2.47it/s]
# Reduce Progress.:  44%|████▍     | 22/50 [02:29<00:15,  1.84it/s]
# Reduce Progress.:  48%|████▊     | 24/50 [02:30<00:15,  1.65it/s]
# Reduce Progress.:  50%|█████     | 25/50 [02:31<00:13,  1.82it/s]
# Reduce Progress.:  52%|█████▏    | 26/50 [02:31<00:10,  2.29it/s]
# Reduce Progress.:  54%|█████▍    | 27/50 [02:32<00:13,  1.71it/s]
# Reduce Progress.:  56%|█████▌    | 28/50 [02:33<00:14,  1.51it/s]
# Reduce Progress.:  58%|█████▊    | 29/50 [02:33<00:11,  1.75it/s]
# Reduce Progress.:  60%|██████    | 30/50 [02:37<00:29,  1.47s/it]
# Reduce Progress.:  62%|██████▏   | 31/50 [02:37<00:20,  1.07s/it]
# Reduce Progress.:  66%|██████▌   | 33/50 [02:37<00:10,  1.64it/s]
# Reduce Progress.:  68%|██████▊   | 34/50 [02:38<00:12,  1.32it/s]
# Reduce Progress.:  70%|███████   | 35/50 [02:38<00:08,  1.70it/s]
# Reduce Progress.:  72%|███████▏  | 36/50 [02:38<00:06,  2.18it/s]
# Reduce Progress.:  74%|███████▍  | 37/50 [02:39<00:08,  1.47it/s]
# Reduce Progress.:  76%|███████▌  | 38/50 [02:40<00:06,  1.93it/s]
# Reduce Progress.:  78%|███████▊  | 39/50 [02:40<00:06,  1.68it/s]
# Reduce Progress.:  80%|████████  | 40/50 [02:40<00:04,  2.20it/s]
# Reduce Progress.:  82%|████████▏ | 41/50 [02:41<00:04,  2.04it/s]
# Reduce Progress.:  84%|████████▍ | 42/50 [02:43<00:07,  1.14it/s]
# Reduce Progress.:  86%|████████▌ | 43/50 [02:43<00:04,  1.47it/s]
# Reduce Progress.:  88%|████████▊ | 44/50 [02:43<00:03,  1.84it/s]
# Reduce Progress.:  90%|█████████ | 45/50 [02:43<00:02,  2.24it/s]
# Reduce Progress.:  92%|█████████▏| 46/50 [02:45<00:02,  1.62it/s]
# Reduce Progress.:  94%|█████████▍| 47/50 [02:45<00:01,  1.88it/s]
# Reduce Progress.:  96%|█████████▌| 48/50 [02:45<00:00,  2.46it/s]
# Reduce Progress.:  98%|█████████▊| 49/50 [02:45<00:00,  2.39it/s]
# Map Progress.: 100%|██████████| 50/50 [02:46<00:00,  3.33s/it]/s]
# Shuffled 9536 MiB in 167.28865766525269 seconds
# Job completion time: 171.55905112597975

# Reduce Progress.: 100%|██████████| 50/50 [02:46<00:00,  3.33s/it]

# job.batch "ray-test-job-9" deleted





# num_partitions = 50, max 6GB head node.
# At time: Wed Apr 13 14:12:04 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 178134443067, bytes_in: 180182878152
# At time: Wed Apr 13 14:12:05 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1802993069, bytes_in: 12435306
# At time: Wed Apr 13 14:12:05 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 189068480022, bytes_in: 172175805312
# At time: Wed Apr 13 14:12:06 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1834872751, bytes_in: 339408231
# At time: Wed Apr 13 14:12:06 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 145569193538, bytes_in: 143774762101
# At time: Wed Apr 13 14:12:06 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1882999015, bytes_in: 38327956
# At time: Wed Apr 13 14:12:07 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 5535778409, bytes_in: 9027102405
# At time: Wed Apr 13 14:12:07 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991914970, bytes_in: 12869983
# At time: Wed Apr 13 14:12:07 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 115970728, bytes_in: 31483647
# At time: Wed Apr 13 14:12:07 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459965175, bytes_in: 4324394
# At time: Wed Apr 13 14:12:08 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 132332549, bytes_in: 34319582
# At time: Wed Apr 13 14:12:08 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 649531209, bytes_in: 7466353
# job.batch/ray-test-job-9 created

# job.batch/ray-test-job-9 condition met

# At time: Wed Apr 13 14:15:52 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth1, bytes_out: 180067683548, bytes_in: 182121681154
# At time: Wed Apr 13 14:15:53 CDT 2022, node: n0, stats_pod: get-statistics-shvbw, int: eth0, bytes_out: 1803011728, bytes_in: 12445152
# At time: Wed Apr 13 14:15:53 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth1, bytes_out: 191305226083, bytes_in: 174992911545
# At time: Wed Apr 13 14:15:54 CDT 2022, node: n1, stats_pod: get-statistics-xk96p, int: eth0, bytes_out: 1834970909, bytes_in: 341622325
# At time: Wed Apr 13 14:15:54 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth1, bytes_out: 145570598274, bytes_in: 143777150262
# At time: Wed Apr 13 14:15:54 CDT 2022, node: n2, stats_pod: get-statistics-mzv7p, int: eth0, bytes_out: 1883142897, bytes_in: 38464009
# At time: Wed Apr 13 14:15:55 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth1, bytes_out: 7825704635, bytes_in: 10722278887
# At time: Wed Apr 13 14:15:55 CDT 2022, node: n3, stats_pod: get-statistics-fdd5l, int: eth0, bytes_out: 1991933394, bytes_in: 12879944
# At time: Wed Apr 13 14:15:55 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth1, bytes_out: 116086108, bytes_in: 31515433
# At time: Wed Apr 13 14:15:56 CDT 2022, node: g0, stats_pod: get-statistics-9gs88, int: eth0, bytes_out: 459982843, bytes_in: 4332867
# At time: Wed Apr 13 14:15:56 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth1, bytes_out: 132671298, bytes_in: 34366133
# At time: Wed Apr 13 14:15:56 CDT 2022, node: g1, stats_pod: get-statistics-9cgdk, int: eth0, bytes_out: 649550239, bytes_in: 7476402
# node: n0, int: eth1, total_bytes_out: 14749.45435333252, total_bytes_in: 14791.893020629883
# node: n0, int: eth0, total_bytes_out: 0.14235687255859375, total_bytes_in: 0.0751190185546875
# node: n1, int: eth1, total_bytes_out: 17065.01816558838, total_bytes_in: 21492.81488800049
# node: n1, int: eth0, total_bytes_out: 0.7488861083984375, total_bytes_in: 16.892196655273438
# node: n2, int: eth1, total_bytes_out: 10.71728515625, total_bytes_in: 18.22022247314453
# node: n2, int: eth0, total_bytes_out: 1.0977325439453125, total_bytes_in: 1.0380020141601562
# node: n3, int: eth1, total_bytes_out: 17470.75062561035, total_bytes_in: 12933.170181274414
# node: n3, int: eth0, total_bytes_out: 0.14056396484375, total_bytes_in: 0.07599639892578125
# node: g0, int: eth1, total_bytes_out: 0.880279541015625, total_bytes_in: 0.2425079345703125
# node: g0, int: eth0, total_bytes_out: 0.134796142578125, total_bytes_in: 0.06464385986328125
# node: g1, int: eth1, total_bytes_out: 2.5844497680664062, total_bytes_in: 0.35515594482421875
# node: g1, int: eth0, total_bytes_out: 0.1451873779296875, total_bytes_in: 0.07666778564453125
# [['n0', 'eth1', 14749.45435333252, 14791.893020629883], ['n0', 'eth0', 0.14235687255859375, 0.0751190185546875], ['n1', 'eth1', 17065.01816558838, 21492.81488800049], ['n1', 'eth0', 0.7488861083984375, 16.892196655273438], ['n2', 'eth1', 10.71728515625, 18.22022247314453], ['n2', 'eth0', 1.0977325439453125, 1.0380020141601562], ['n3', 'eth1', 17470.75062561035, 12933.170181274414], ['n3', 'eth0', 0.14056396484375, 0.07599639892578125], ['g0', 'eth1', 0.880279541015625, 0.2425079345703125], ['g0', 'eth0', 0.134796142578125, 0.06464385986328125], ['g1', 'eth1', 2.5844497680664062, 0.35515594482421875], ['g1', 'eth0', 0.1451873779296875, 0.07666778564453125]]
# WARNING: 6 PYTHON worker processes have been started on node: 76d9d81add3aeed59a14162f2ca6acf51382a6d451f60a52ec0dbe22 with address: 10.244.2.14. This could be a result of using a large number of actors, or due to tasks blocked in ray.get() calls (see https://github.com/ray-project/ray/issues/3644 for some discussion of workarounds).
# WARNING: 4 PYTHON worker processes have been started on node: 5fa1ebc5804814e42ac551f37e146df8b27202101fadcc4172f17230 with address: 10.244.4.2. This could be a result of using a large number of actors, or due to tasks blocked in ray.get() calls (see https://github.com/ray-project/ray/issues/3644 for some discussion of workarounds).
# WARNING: 6 PYTHON worker processes have been started on node: ed339848b0f7cd61abb74fe30be0c6bfbf31682eacb0e7be6bb03425 with address: 10.244.1.2. This could be a result of using a large number of actors, or due to tasks blocked in ray.get() calls (see https://github.com/ray-project/ray/issues/3644 for some discussion of workarounds).
# Connecting to a existing cluster...

#   0%|          | 0/50 [00:00<?, ?it/s]
# Map Progress.:   0%|          | 0/50 [00:00<?, ?it/s]

#   0%|          | 0/50 [00:00<?, ?it/s]                  WARNING: 5 PYTHON worker processes have been started on node: 5fa1ebc5804814e42ac551f37e146df8b27202101fadcc4172f17230 with address: 10.244.4.2. This could be a result of using a large number of actors, or due to tasks blocked in ray.get() calls (see https://github.com/ray-project/ray/issues/3644 for some discussion of workarounds).

# Map Progress.:   4%|▍         | 2/50 [00:01<00:25,  1.91it/s]
# Map Progress.:   8%|▊         | 4/50 [00:01<00:11,  4.02it/s]
# Map Progress.:  12%|█▏        | 6/50 [00:01<00:09,  4.43it/s]
# Map Progress.:  14%|█▍        | 7/50 [00:02<00:20,  2.14it/s]
# Map Progress.:  18%|█▊        | 9/50 [00:03<00:20,  2.00it/s]
# Map Progress.:  20%|██        | 10/50 [00:04<00:20,  1.92it/s]
# Map Progress.:  22%|██▏       | 11/50 [00:04<00:19,  2.03it/s]
# Map Progress.:  26%|██▌       | 13/50 [00:05<00:15,  2.43it/s]
# Map Progress.:  28%|██▊       | 14/50 [00:05<00:12,  2.92it/s]
# Map Progress.:  30%|███       | 15/50 [00:06<00:13,  2.64it/s]
# Map Progress.:  32%|███▏      | 16/50 [00:06<00:11,  3.02it/s]
# Map Progress.:  38%|███▊      | 19/50 [00:06<00:08,  3.58it/s]
# Map Progress.:  40%|████      | 20/50 [00:07<00:11,  2.60it/s]
# Map Progress.:  44%|████▍     | 22/50 [00:08<00:09,  2.93it/s]
# Map Progress.:  46%|████▌     | 23/50 [00:08<00:07,  3.38it/s]
# Map Progress.:  48%|████▊     | 24/50 [00:09<00:09,  2.63it/s]
# Map Progress.:  50%|█████     | 25/50 [00:09<00:08,  2.95it/s]
# Map Progress.:  52%|█████▏    | 26/50 [00:09<00:09,  2.47it/s]
# Map Progress.:  54%|█████▍    | 27/50 [00:10<00:07,  2.90it/s]
# Map Progress.:  58%|█████▊    | 29/50 [00:10<00:07,  2.86it/s]
# Map Progress.:  60%|██████    | 30/50 [00:10<00:06,  3.22it/s]
# Map Progress.:  66%|██████▌   | 33/50 [00:11<00:04,  3.91it/s]
# Map Progress.:  70%|███████   | 35/50 [00:13<00:06,  2.39it/s]
# Map Progress.:  72%|███████▏  | 36/50 [00:13<00:05,  2.67it/s]
# Map Progress.:  74%|███████▍  | 37/50 [00:13<00:05,  2.26it/s]
# Map Progress.:  78%|███████▊  | 39/50 [00:14<00:04,  2.69it/s]
# Map Progress.:  80%|████████  | 40/50 [00:14<00:03,  3.16it/s]
# Map Progress.:  82%|████████▏ | 41/50 [00:15<00:03,  2.63it/s]
# Map Progress.:  84%|████████▍ | 42/50 [00:16<00:04,  1.87it/s]
# Map Progress.:  86%|████████▌ | 43/50 [00:16<00:03,  1.81it/s]
# Map Progress.:  88%|████████▊ | 44/50 [00:17<00:02,  2.08it/s]
# Map Progress.:  90%|█████████ | 45/50 [00:17<00:01,  2.65it/s]
# Map Progress.:  92%|█████████▏| 46/50 [00:17<00:01,  3.32it/s]
# Map Progress.:  94%|█████████▍| 47/50 [00:17<00:00,  3.41it/s]
# Map Progress.:  96%|█████████▌| 48/50 [00:17<00:00,  4.17it/s]
# Map Progress.:  98%|█████████▊| 49/50 [00:17<00:00,  4.27it/s]
# Map Progress.: 100%|██████████| 50/50 [00:17<00:00,  5.05it/s]

# Reduce Progress.:   2%|▏         | 1/50 [02:22<1:56:08, 142.22s/it]
# Reduce Progress.:   4%|▍         | 2/50 [02:22<46:54, 58.63s/it]   
# Reduce Progress.:   6%|▌         | 3/50 [02:22<24:59, 31.91s/it]
# Reduce Progress.:   8%|▊         | 4/50 [02:23<15:13, 19.85s/it]
# Reduce Progress.:  10%|█         | 5/50 [02:23<09:32, 12.73s/it]
# Reduce Progress.:  12%|█▏        | 6/50 [02:24<06:11,  8.44s/it]
# Reduce Progress.:  14%|█▍        | 7/50 [02:24<04:17,  5.98s/it]
# Reduce Progress.:  16%|█▌        | 8/50 [02:26<03:08,  4.48s/it]
# Reduce Progress.:  18%|█▊        | 9/50 [02:26<02:07,  3.12s/it]
# Reduce Progress.:  20%|██        | 10/50 [02:26<01:27,  2.19s/it]
# Reduce Progress.:  22%|██▏       | 11/50 [02:27<01:09,  1.79s/it]
# Reduce Progress.:  24%|██▍       | 12/50 [02:28<01:05,  1.71s/it]
# Reduce Progress.:  26%|██▌       | 13/50 [02:28<00:45,  1.23s/it]
# Reduce Progress.:  28%|██▊       | 14/50 [02:29<00:32,  1.12it/s]
# Reduce Progress.:  30%|███       | 15/50 [02:30<00:33,  1.05it/s]
# Reduce Progress.:  34%|███▍      | 17/50 [02:31<00:26,  1.24it/s]
# Reduce Progress.:  36%|███▌      | 18/50 [02:31<00:21,  1.51it/s]
# Reduce Progress.:  38%|███▊      | 19/50 [02:33<00:27,  1.11it/s]
# Reduce Progress.:  40%|████      | 20/50 [02:33<00:20,  1.46it/s]
# Reduce Progress.:  42%|████▏     | 21/50 [02:33<00:17,  1.62it/s]
# Reduce Progress.:  44%|████▍     | 22/50 [02:35<00:27,  1.03it/s]
# Reduce Progress.:  46%|████▌     | 23/50 [02:38<00:41,  1.53s/it]
# Reduce Progress.:  48%|████▊     | 24/50 [02:38<00:29,  1.12s/it]
# Reduce Progress.:  50%|█████     | 25/50 [02:38<00:21,  1.16it/s]
# Reduce Progress.:  52%|█████▏    | 26/50 [02:40<00:24,  1.01s/it]
# Reduce Progress.:  56%|█████▌    | 28/50 [02:40<00:12,  1.75it/s]
# Reduce Progress.:  58%|█████▊    | 29/50 [02:41<00:15,  1.36it/s]
# Reduce Progress.:  60%|██████    | 30/50 [02:43<00:20,  1.02s/it]WARNING: 7 PYTHON worker processes have been started on node: ed339848b0f7cd61abb74fe30be0c6bfbf31682eacb0e7be6bb03425 with address: 10.244.1.2. This could be a result of using a large number of actors, or due to tasks blocked in ray.get() calls (see https://github.com/ray-project/ray/issues/3644 for some discussion of workarounds).


# Reduce Progress.:  66%|██████▌   | 33/50 [02:46<00:17,  1.05s/it]
# Reduce Progress.:  68%|██████▊   | 34/50 [02:46<00:13,  1.23it/s]
# Reduce Progress.:  70%|███████   | 35/50 [02:47<00:15,  1.04s/it]
# Reduce Progress.:  72%|███████▏  | 36/50 [02:48<00:12,  1.14it/s]
# Reduce Progress.:  74%|███████▍  | 37/50 [02:48<00:10,  1.22it/s]
# Reduce Progress.:  76%|███████▌  | 38/50 [02:49<00:08,  1.45it/s]
# Reduce Progress.:  78%|███████▊  | 39/50 [02:50<00:09,  1.21it/s]
# Reduce Progress.:  80%|████████  | 40/50 [02:50<00:06,  1.53it/s]
# Reduce Progress.:  82%|████████▏ | 41/50 [02:50<00:04,  2.02it/s]
# Reduce Progress.:  84%|████████▍ | 42/50 [02:51<00:05,  1.46it/s]
# Reduce Progress.:  86%|████████▌ | 43/50 [02:52<00:04,  1.54it/s]
# Reduce Progress.:  88%|████████▊ | 44/50 [02:52<00:03,  1.92it/s]
# Reduce Progress.:  90%|█████████ | 45/50 [02:54<00:03,  1.36it/s]
# Reduce Progress.:  92%|█████████▏| 46/50 [02:54<00:02,  1.82it/s]
# Reduce Progress.:  94%|█████████▍| 47/50 [02:55<00:02,  1.39it/s]
# Reduce Progress.:  96%|█████████▌| 48/50 [02:55<00:01,  1.87it/s]
# Reduce Progress.:  98%|█████████▊| 49/50 [02:56<00:00,  1.28it/s]
# Map Progress.: 100%|██████████| 50/50 [02:57<00:00,  3.55s/it]/s]

# Reduce Progress.: 100%|██████████| 50/50 [02:57<00:00,  3.55s/it]
# Shuffled 9536 MiB in 178.09569120407104 seconds
# Job completion time: 182.63186893999227

# job.batch "ray-test-job-9" deleted




# Same as above:
# At time: Wed Apr 13 21:36:28 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 13422860769, bytes_in: 13211993851
# At time: Wed Apr 13 21:36:29 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1766581980, bytes_in: 12225071
# At time: Wed Apr 13 21:36:29 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 26734854622, bytes_in: 26234629479
# At time: Wed Apr 13 21:36:29 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1771283451, bytes_in: 53028849
# At time: Wed Apr 13 21:36:30 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 2897203271, bytes_in: 2241387379
# At time: Wed Apr 13 21:36:30 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1768572736, bytes_in: 16671069
# At time: Wed Apr 13 21:36:30 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 12417073143, bytes_in: 13078643861
# At time: Wed Apr 13 21:36:31 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1766405418, bytes_in: 11541505
# At time: Wed Apr 13 21:36:31 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 6065283, bytes_in: 1637496
# At time: Wed Apr 13 21:36:31 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270642823, bytes_in: 3378237
# At time: Wed Apr 13 21:36:31 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 6083148, bytes_in: 1648479
# At time: Wed Apr 13 21:36:32 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270557793, bytes_in: 3241850
# job.batch/ray-test-job-9 created

# job.batch/ray-test-job-9 condition met

# At time: Wed Apr 13 21:40:04 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth1, bytes_out: 15070912187, bytes_in: 14664170596
# At time: Wed Apr 13 21:40:05 CDT 2022, node: n0, stats_pod: get-statistics-t8l2g, int: eth0, bytes_out: 1766599798, bytes_in: 12234541
# At time: Wed Apr 13 21:40:05 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth1, bytes_out: 28681934684, bytes_in: 28970575138
# At time: Wed Apr 13 21:40:06 CDT 2022, node: n1, stats_pod: get-statistics-qgknz, int: eth0, bytes_out: 1771383329, bytes_in: 54906089
# At time: Wed Apr 13 21:40:06 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth1, bytes_out: 5044055149, bytes_in: 3985764291
# At time: Wed Apr 13 21:40:06 CDT 2022, node: n2, stats_pod: get-statistics-lb65j, int: eth0, bytes_out: 1768643903, bytes_in: 16740863
# At time: Wed Apr 13 21:40:07 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth1, bytes_out: 14065321358, bytes_in: 14529553078
# At time: Wed Apr 13 21:40:07 CDT 2022, node: n3, stats_pod: get-statistics-7blcx, int: eth0, bytes_out: 1766422732, bytes_in: 11551043
# At time: Wed Apr 13 21:40:07 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth1, bytes_out: 6164842, bytes_in: 1663130
# At time: Wed Apr 13 21:40:07 CDT 2022, node: g0, stats_pod: get-statistics-cpj2s, int: eth0, bytes_out: 270659939, bytes_in: 3386545
# At time: Wed Apr 13 21:40:08 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth1, bytes_out: 6180109, bytes_in: 1673873
# At time: Wed Apr 13 21:40:08 CDT 2022, node: g1, stats_pod: get-statistics-vd2cj, int: eth0, bytes_out: 270575503, bytes_in: 3250740
# node: n0, int: eth1, total_bytes_out: 12573.634475708008, total_bytes_in: 11079.229316711426
# node: n0, int: eth0, total_bytes_out: 0.1359405517578125, total_bytes_in: 0.0722503662109375
# node: n1, int: eth1, total_bytes_out: 14855.041976928711, total_bytes_in: 20873.608848571777
# node: n1, int: eth0, total_bytes_out: 0.7620086669921875, total_bytes_in: 14.32220458984375
# node: n2, int: eth1, total_bytes_out: 16379.179977416992, total_bytes_in: 13308.539672851562
# node: n2, int: eth0, total_bytes_out: 0.5429611206054688, total_bytes_in: 0.5324859619140625
# node: n3, int: eth1, total_bytes_out: 12575.135917663574, total_bytes_in: 11069.55884552002
# node: n3, int: eth0, total_bytes_out: 0.1320953369140625, total_bytes_in: 0.0727691650390625
# node: g0, int: eth1, total_bytes_out: 0.7595748901367188, total_bytes_in: 0.1955718994140625
# node: g0, int: eth0, total_bytes_out: 0.130584716796875, total_bytes_in: 0.063385009765625
# node: g1, int: eth1, total_bytes_out: 0.7397537231445312, total_bytes_in: 0.1937408447265625
# node: g1, int: eth0, total_bytes_out: 0.1351165771484375, total_bytes_in: 0.0678253173828125
# [['n0', 'eth1', 12573.634475708008, 11079.229316711426], ['n0', 'eth0', 0.1359405517578125, 0.0722503662109375], ['n1', 'eth1', 14855.041976928711, 20873.608848571777], ['n1', 'eth0', 0.7620086669921875, 14.32220458984375], ['n2', 'eth1', 16379.179977416992, 13308.539672851562], ['n2', 'eth0', 0.5429611206054688, 0.5324859619140625], ['n3', 'eth1', 12575.135917663574, 11069.55884552002], ['n3', 'eth0', 0.1320953369140625, 0.0727691650390625], ['g0', 'eth1', 0.7595748901367188, 0.1955718994140625], ['g0', 'eth0', 0.130584716796875, 0.063385009765625], ['g1', 'eth1', 0.7397537231445312, 0.1937408447265625], ['g1', 'eth0', 0.1351165771484375, 0.0678253173828125]]
# Connecting to a existing cluster...

#   0%|          | 0/50 [00:00<?, ?it/s]
# Map Progress.:   0%|          | 0/50 [00:00<?, ?it/s]

#   0%|          | 0/50 [00:00<?, ?it/s]
# Map Progress.:   2%|▏         | 1/50 [00:00<00:41,  1.19it/s]
# Map Progress.:   8%|▊         | 4/50 [00:00<00:08,  5.29it/s]
# Map Progress.:  12%|█▏        | 6/50 [00:01<00:09,  4.64it/s]
# Map Progress.:  16%|█▌        | 8/50 [00:02<00:11,  3.51it/s]
# Map Progress.:  20%|██        | 10/50 [00:02<00:09,  4.14it/s]
# Map Progress.:  22%|██▏       | 11/50 [00:02<00:08,  4.63it/s]
# Map Progress.:  24%|██▍       | 12/50 [00:02<00:08,  4.36it/s]
# Map Progress.:  26%|██▌       | 13/50 [00:03<00:13,  2.72it/s]
# Map Progress.:  30%|███       | 15/50 [00:04<00:11,  3.12it/s]
# Map Progress.:  34%|███▍      | 17/50 [00:04<00:09,  3.41it/s]
# Map Progress.:  36%|███▌      | 18/50 [00:05<00:09,  3.40it/s]
# Map Progress.:  38%|███▊      | 19/50 [00:05<00:09,  3.15it/s]
# Map Progress.:  40%|████      | 20/50 [00:05<00:07,  3.76it/s]
# Map Progress.:  42%|████▏     | 21/50 [00:05<00:08,  3.62it/s]
# Map Progress.:  44%|████▍     | 22/50 [00:06<00:07,  3.95it/s]
# Map Progress.:  46%|████▌     | 23/50 [00:06<00:06,  4.27it/s]
# Map Progress.:  48%|████▊     | 24/50 [00:06<00:05,  4.90it/s]
# Map Progress.:  50%|█████     | 25/50 [00:06<00:07,  3.16it/s]
# Map Progress.:  54%|█████▍    | 27/50 [00:07<00:07,  3.05it/s]
# Map Progress.:  56%|█████▌    | 28/50 [00:07<00:06,  3.64it/s]
# Map Progress.:  58%|█████▊    | 29/50 [00:08<00:06,  3.02it/s]
# Map Progress.:  62%|██████▏   | 31/50 [00:08<00:04,  4.66it/s]
# Map Progress.:  64%|██████▍   | 32/50 [00:08<00:03,  4.83it/s]
# Map Progress.:  72%|███████▏  | 36/50 [00:09<00:02,  4.91it/s]
# Map Progress.:  74%|███████▍  | 37/50 [00:10<00:03,  3.29it/s]
# Map Progress.:  78%|███████▊  | 39/50 [00:10<00:02,  3.67it/s]
# Map Progress.:  80%|████████  | 40/50 [00:10<00:02,  3.92it/s]
# Map Progress.:  82%|████████▏ | 41/50 [00:10<00:02,  4.44it/s]
# Map Progress.:  84%|████████▍ | 42/50 [00:11<00:02,  3.17it/s]
# Map Progress.:  86%|████████▌ | 43/50 [00:11<00:02,  2.76it/s]
# Map Progress.:  88%|████████▊ | 44/50 [00:12<00:02,  2.94it/s]
# Map Progress.:  90%|█████████ | 45/50 [00:12<00:01,  3.25it/s]
# Map Progress.:  92%|█████████▏| 46/50 [00:12<00:01,  3.03it/s]
# Map Progress.:  94%|█████████▍| 47/50 [00:13<00:00,  3.11it/s](raylet, ip=10.244.4.2) [2022-04-13 19:37:49,187 E 5523 5523] (raylet) worker_pool.cc:481: Some workers of the worker process(7570) have not registered within the timeout. The process is still alive, probably it's hanging during start.

# Map Progress.:  98%|█████████▊| 49/50 [02:01<00:24, 24.49s/it]
# Map Progress.: 100%|██████████| 50/50 [02:01<00:00, 18.56s/it]

# Reduce Progress.:   4%|▍         | 2/50 [02:18<55:15, 69.08s/it]
# Reduce Progress.:   6%|▌         | 3/50 [02:18<31:38, 40.39s/it]
# Reduce Progress.:   8%|▊         | 4/50 [02:18<19:26, 25.36s/it]
# Reduce Progress.:  10%|█         | 5/50 [02:19<12:41, 16.93s/it]
# Reduce Progress.:  12%|█▏        | 6/50 [02:20<08:36, 11.73s/it]
# Reduce Progress.:  14%|█▍        | 7/50 [02:20<05:43,  8.00s/it]
# Reduce Progress.:  16%|█▌        | 8/50 [02:21<03:51,  5.51s/it]
# Reduce Progress.:  18%|█▊        | 9/50 [02:21<02:37,  3.85s/it]
# Reduce Progress.:  20%|██        | 10/50 [02:29<03:23,  5.09s/it]
# Reduce Progress.:  22%|██▏       | 11/50 [02:29<02:20,  3.61s/it]
# Reduce Progress.:  24%|██▍       | 12/50 [02:29<01:39,  2.61s/it]
# Reduce Progress.:  26%|██▌       | 13/50 [02:29<01:08,  1.85s/it]
# Reduce Progress.:  28%|██▊       | 14/50 [02:32<01:19,  2.20s/it]
# Reduce Progress.:  30%|███       | 15/50 [02:33<00:58,  1.68s/it]
# Reduce Progress.:  32%|███▏      | 16/50 [02:33<00:41,  1.21s/it]
# Reduce Progress.:  34%|███▍      | 17/50 [02:33<00:30,  1.10it/s]
# Reduce Progress.:  36%|███▌      | 18/50 [02:34<00:26,  1.20it/s]
# Reduce Progress.:  38%|███▊      | 19/50 [02:34<00:22,  1.39it/s]
# Reduce Progress.:  40%|████      | 20/50 [02:35<00:23,  1.28it/s]
# Reduce Progress.:  42%|████▏     | 21/50 [02:35<00:17,  1.62it/s]
# Reduce Progress.:  44%|████▍     | 22/50 [02:35<00:13,  2.14it/s]
# Reduce Progress.:  46%|████▌     | 23/50 [02:36<00:10,  2.54it/s]
# Reduce Progress.:  48%|████▊     | 24/50 [02:36<00:12,  2.11it/s]
# Reduce Progress.:  52%|█████▏    | 26/50 [02:37<00:09,  2.62it/s]
# Reduce Progress.:  54%|█████▍    | 27/50 [02:39<00:16,  1.37it/s]
# Reduce Progress.:  56%|█████▌    | 28/50 [02:39<00:13,  1.67it/s]
# Reduce Progress.:  58%|█████▊    | 29/50 [02:39<00:10,  2.00it/s]
# Reduce Progress.:  60%|██████    | 30/50 [02:40<00:10,  1.94it/s]
# Reduce Progress.:  62%|██████▏   | 31/50 [02:40<00:09,  2.02it/s]
# Reduce Progress.:  64%|██████▍   | 32/50 [02:40<00:08,  2.24it/s]
# Reduce Progress.:  66%|██████▌   | 33/50 [02:41<00:05,  2.87it/s]
# Reduce Progress.:  68%|██████▊   | 34/50 [02:42<00:09,  1.73it/s]
# Reduce Progress.:  70%|███████   | 35/50 [02:42<00:07,  2.11it/s]
# Reduce Progress.:  72%|███████▏  | 36/50 [02:42<00:05,  2.74it/s]
# Reduce Progress.:  76%|███████▌  | 38/50 [02:43<00:05,  2.34it/s]
# Reduce Progress.:  78%|███████▊  | 39/50 [02:43<00:04,  2.65it/s]
# Reduce Progress.:  80%|████████  | 40/50 [02:45<00:06,  1.64it/s]
# Reduce Progress.:  84%|████████▍ | 42/50 [02:45<00:02,  2.68it/s]
# Reduce Progress.:  86%|████████▌ | 43/50 [02:45<00:02,  2.95it/s]
# Reduce Progress.:  90%|█████████ | 45/50 [02:46<00:02,  2.33it/s]
# Reduce Progress.:  94%|█████████▍| 47/50 [02:47<00:01,  1.94it/s]
# Reduce Progress.:  96%|█████████▌| 48/50 [02:47<00:00,  2.31it/s]
# Reduce Progress.:  98%|█████████▊| 49/50 [02:48<00:00,  1.88it/s]
# Map Progress.: 100%|██████████| 50/50 [02:49<00:00,  3.40s/it]/s]

# Reduce Progress.: 100%|██████████| 50/50 [02:49<00:00,  3.40s/it]
# Shuffled 9536 MiB in 170.475079536438 seconds
# Job completion time: 174.72176736799884

# job.batch "ray-test-job-9" deleted