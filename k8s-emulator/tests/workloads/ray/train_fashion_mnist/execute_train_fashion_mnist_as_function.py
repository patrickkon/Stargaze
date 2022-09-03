import os
import sys
sys.path.append("utils")
from measure_traffic import get_all_node_interface_usage, get_interval_all_node_interface_usage, exec_sh_command


def execute_train_fashion_mnist(statistics_pod_list):
    # Example: statistics_pod_list = ["get-statistics-nzh67", "get-statistics-r29sh", "get-statistics-tlmrc", "get-statistics-vnpkf"] # includes pods in all nodes except for k8s master node

    SATS_TOPO_WITH_INTERFACE_FILE = "gen_cluster_data/topo_with_interface_file.txt"
    TRAIN_FASHION_MNIST_JOB_YAML_FILE = "kubernetes/job-example-4.yaml"
    JOB_NAME = "ray-test-job-4" # Note: this is obtained within TRAIN_FASHION_MNIST_JOB_YAML_FILE

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
    get_logs_2 = ['tail', '-n', '100'] # only 15 lines necessary for this job
    ps = subprocess.Popen(get_logs_cmd, stdout=subprocess.PIPE)
    output = subprocess.check_output(get_logs_2, stdin=ps.stdout)
    print(output.decode('ascii'))

    # Delete job:
    delete_job_cmd = ['kubectl', '-n', 'ray', 'delete', 'job', JOB_NAME]
    o = exec_sh_command(delete_job_cmd)
    print(o)


# Example output:
# At time: Sat Apr  2 17:46:38 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 112636936705, bytes_in: 108824977219
# At time: Sat Apr  2 17:46:38 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 114244977104, bytes_in: 108050454576
# At time: Sat Apr  2 17:46:39 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 216998433053, bytes_in: 215149173461
# At time: Sat Apr  2 17:46:39 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 215152096693, bytes_in: 216995557661
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 17:48:58 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 122773626802, bytes_in: 118964408067
# At time: Sat Apr  2 17:48:59 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 124396754291, bytes_in: 118185716898
# At time: Sat Apr  2 17:48:59 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 227136401050, bytes_in: 225286186725
# At time: Sat Apr  2 17:48:59 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 225289114070, bytes_in: 227133479535
# node: n0, int: eth1, total_bytes_out: 77336.80799102783, total_bytes_in: 77357.71826171875
# node: n1, int: eth1, total_bytes_out: 77451.91335296631, total_bytes_in: 77325.91493225098
# node: n1, int: eth2, total_bytes_out: 77346.55759429932, total_bytes_in: 77339.27355957031
# node: n2, int: eth1, total_bytes_out: 77339.30493927002, total_bytes_in: 77346.20570373535
# [['n0', 'eth1', 77336.80799102783, 77357.71826171875], ['n1', 'eth1', 77451.91335296631, 77325.91493225098], ['n1', 'eth2', 77346.55759429932, 77339.27355957031], ['n2', 'eth1', 77339.30493927002, 77346.20570373535]]
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=991, ip=10.244.3.3) 2022-04-02 15:47:27,409        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=991, ip=10.244.3.3) 2022-04-02 15:47:27,410        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=1232, ip=10.244.1.2) 2022-04-02 15:47:27,411       INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=1232, ip=10.244.1.2) 2022-04-02 15:47:27,411       INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=1232, ip=10.244.1.2) Test Error: 
# (BaseWorkerMixin pid=1232, ip=10.244.1.2)  Accuracy: 41.0%, Avg loss: 1.920438 
# (BaseWorkerMixin pid=1232, ip=10.244.1.2) 
# Loss results: ([2.246521023428364, 2.1563210897384937, 2.0364806970972924, 1.9204383845541888], [22.20642654200492, 21.645052409003256, 22.336018724003225, 21.919916155995452])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.24505376360219, 2.1530710967483033, 2.031372543353184, 1.913638107336251]
# Epoch times for worker 1: [22.154020404996118, 21.578321556997253, 22.438462705002166, 21.846020849989145]
# Job completion time: 101.66028631699737
# Num_workers: 2

# job.batch "ray-test-job-2" deleted


# At time: Sat Apr  2 17:55:08 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 122791175316, bytes_in: 118975702584
# At time: Sat Apr  2 17:55:08 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 124438074244, bytes_in: 118199050185
# At time: Sat Apr  2 17:55:09 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 227149631511, bytes_in: 225300990797
# At time: Sat Apr  2 17:55:09 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 225303928477, bytes_in: 227146706706
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 17:57:16 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 132928258690, bytes_in: 129059507033
# At time: Sat Apr  2 17:57:17 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 134533594876, bytes_in: 128334635135
# At time: Sat Apr  2 17:57:17 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 227267076597, bytes_in: 225314710114
# At time: Sat Apr  2 17:57:17 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 225317723765, bytes_in: 227264150216
# node: n0, int: eth1, total_bytes_out: 77339.8084564209, total_bytes_in: 76933.32251739502
# node: n1, int: eth1, total_bytes_out: 77022.70989990234, total_bytes_in: 77328.3763885498
# node: n1, int: eth2, total_bytes_out: 896.0348968505859, total_bytes_in: 104.67008209228516
# node: n2, int: eth1, total_bytes_out: 105.24969482421875, total_bytes_in: 896.0228729248047
# [['n0', 'eth1', 77339.8084564209, 76933.32251739502], ['n1', 'eth1', 77022.70989990234, 77328.3763885498], ['n1', 'eth2', 896.0348968505859, 104.67008209228516], ['n2', 'eth1', 105.24969482421875, 896.0228729248047]]
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=1472, ip=10.244.1.2) 2022-04-02 15:55:52,949       INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=1472, ip=10.244.1.2) 2022-04-02 15:55:52,950       INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=213, ip=10.244.2.6) 2022-04-02 15:55:52,943        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=213, ip=10.244.2.6) 2022-04-02 15:55:52,944        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=1472, ip=10.244.1.2) Test Error: 
# (BaseWorkerMixin pid=1472, ip=10.244.1.2)  Accuracy: 50.1%, Avg loss: 1.810566 
# (BaseWorkerMixin pid=1472, ip=10.244.1.2) 
# Loss results: ([2.247746087942913, 2.16549563256039, 2.005769156346655, 1.810565626545317], [20.320532864992856, 19.83988592401147, 20.011629474000074, 19.860610864998307])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.2474558201565107, 2.1664788540761184, 2.014062717462042, 1.8277532325428762]
# Epoch times for worker 1: [20.28601399299805, 19.86782268701063, 19.99842738499865, 19.85431719200278]
# Job completion time: 93.15634196900646
# Num_workers: 2

# job.batch "ray-test-job-2" deleted


# At time: Sat Apr  2 18:02:06 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 132944820835, bytes_in: 129072849078
# At time: Sat Apr  2 18:02:06 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 134572687750, bytes_in: 128346881606
# At time: Sat Apr  2 18:02:07 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 237412374466, bytes_in: 235479589524
# At time: Sat Apr  2 18:02:07 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 235482536635, bytes_in: 237409437756
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 18:04:19 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 132952355022, bytes_in: 129079001794
# At time: Sat Apr  2 18:04:20 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 134591130535, bytes_in: 128352809921
# At time: Sat Apr  2 18:04:20 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 247554588957, bytes_in: 245568748163
# At time: Sat Apr  2 18:04:21 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 245571700333, bytes_in: 247551652528
# node: n0, int: eth1, total_bytes_out: 57.481285095214844, total_bytes_in: 46.941497802734375
# node: n1, int: eth1, total_bytes_out: 140.70728302001953, total_bytes_in: 45.229454040527344
# node: n1, int: eth2, total_bytes_out: 77378.9557723999, total_bytes_in: 76974.1717453003
# node: n2, int: eth1, total_bytes_out: 76974.21034240723, total_bytes_in: 77378.95791625977
# [['n0', 'eth1', 57.481285095214844, 46.941497802734375], ['n1', 'eth1', 140.70728302001953, 45.229454040527344], ['n1', 'eth2', 77378.9557723999, 76974.1717453003], ['n2', 'eth1', 76974.21034240723, 77378.95791625977]]
# (BaseWorkerMixin pid=1205) loss: 1.780868  [28800/30000]
# (BaseWorkerMixin pid=322, ip=10.244.2.6) loss: 1.843721  [28800/30000]
# (BaseWorkerMixin pid=322, ip=10.244.2.6) Test Error: 
# (BaseWorkerMixin pid=322, ip=10.244.2.6)  Accuracy: 36.5%, Avg loss: 1.927724 
# (BaseWorkerMixin pid=322, ip=10.244.2.6) 
# (BaseWorkerMixin pid=1205) Test Error: 
# (BaseWorkerMixin pid=1205)  Accuracy: 36.6%, Avg loss: 1.923623 
# (BaseWorkerMixin pid=1205) 
# Loss results: ([2.2523960611622806, 2.17372141825925, 2.054287427549909, 1.923623153358508], [20.447554375990876, 20.518504661988118, 20.547964269004297, 20.003932277002605])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.2522050605458057, 2.174455044375863, 2.0569870866787663, 1.9277238716745073]
# Epoch times for worker 1: [20.18777499200951, 20.560146734002046, 20.417078468002728, 20.14964151100139]
# Job completion time: 94.90623328999209
# Num_workers: 2

# job.batch "ray-test-job-2" deleted




# ray head in n0. When both ray worker nodes were heavily utilized:

# At time: Sat Apr  2 18:27:34 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 163591605300, bytes_in: 159640635775
# At time: Sat Apr  2 18:27:34 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 165270646830, bytes_in: 158974781589
# At time: Sat Apr  2 18:27:35 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 257915625439, bytes_in: 255781725057
# At time: Sat Apr  2 18:27:35 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 255784718159, bytes_in: 257912680536
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 18:29:37 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 163665545771, bytes_in: 159701025793
# At time: Sat Apr  2 18:29:37 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 165342296255, bytes_in: 159046983719
# At time: Sat Apr  2 18:29:38 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 268112552325, bytes_in: 265918166870
# At time: Sat Apr  2 18:29:38 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 265921159285, bytes_in: 268109615806
# node: n0, int: eth1, total_bytes_out: 564.1210250854492, total_bytes_in: 460.73927307128906
# node: n1, int: eth1, total_bytes_out: 546.641731262207, total_bytes_in: 550.8585357666016
# node: n1, int: eth2, total_bytes_out: 77796.37821960449, total_bytes_in: 77334.91373443604
# node: n2, int: eth1, total_bytes_out: 77334.90849304199, total_bytes_in: 77796.44218444824
# [['n0', 'eth1', 564.1210250854492, 460.73927307128906], ['n1', 'eth1', 546.641731262207, 550.8585357666016], ['n1', 'eth2', 77796.37821960449, 77334.91373443604], ['n2', 'eth1', 77334.90849304199, 77796.44218444824]]
# (BaseWorkerMixin pid=279, ip=10.244.3.3) 
# Loss results: ([2.2356620852354987, 2.1340971737150936, 1.9792661970588052, 1.8083633267955415], [17.471636346002924, 17.944672809011536, 17.905975745001342, 17.845705539002665])
# Num of epochs: 4
# Batch Size: 64
# (BaseWorkerMixin pid=748, ip=10.244.2.6) 2022-04-02 16:28:18,774        INFO torch.py:67 -- Setting up process group for: env:// [rank=1, world_size=2]
# /home/ray/anaconda3/lib/python3.7/site-packages/ray/util/client/worker.py:514: UserWarning: More than 10MB of messages have been created to schedule tasks on the server. This can be slow on Ray Client due to communication overhead over the network. If you're running many fine-grained tasks, consider running them inside a single remote function. See the section on "Too fine-grained tasks" in the Ray Design Patterns document for more details: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.f7ins22n6nyl. If your functions frequently use large objects, consider storing the objects remotely with ray.put. An example of this is shown in the "Closure capture of large / unserializable object" section of the Ray Design Patterns document, available here: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.1afmymq455wu
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=748, ip=10.244.2.6) 2022-04-02 16:28:22,895        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=748, ip=10.244.2.6) 2022-04-02 16:28:22,896        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=279, ip=10.244.3.3) 2022-04-02 16:28:22,896        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=279, ip=10.244.3.3) 2022-04-02 16:28:22,896        INFO torch.py:247 -- Wrapping provided model in DDP.
# Epoch times for worker 0: [2.241396629126968, 2.1472886671685867, 2.0032454805009685, 1.8422471383574661]
# Epoch times for worker 1: [17.42144037000253, 17.965844615988317, 17.8223035060073, 17.88869927500491]
# Job completion time: 84.52083581400802
# Num_workers: 2

# job.batch "ray-test-job-2" deleted

# Same as above: run 2. 
# At time: Sat Apr  2 18:30:58 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 163675955684, bytes_in: 159703217388
# At time: Sat Apr  2 18:30:59 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 165352549726, bytes_in: 159056954767
# At time: Sat Apr  2 18:30:59 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 268117223766, bytes_in: 265921621094
# At time: Sat Apr  2 18:30:59 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 265924614192, bytes_in: 268114236566
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 18:33:03 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 163749929286, bytes_in: 159763698140
# At time: Sat Apr  2 18:33:04 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 165422422567, bytes_in: 159129280123
# At time: Sat Apr  2 18:33:04 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 278255594803, bytes_in: 276057924910
# At time: Sat Apr  2 18:33:04 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 276060921791, bytes_in: 278252604296
# node: n0, int: eth1, total_bytes_out: 564.3737945556641, total_bytes_in: 461.4315185546875
# node: n1, int: eth1, total_bytes_out: 533.0874710083008, total_bytes_in: 551.7986755371094
# node: n1, int: eth2, total_bytes_out: 77349.63254547119, total_bytes_in: 77333.8609008789
# node: n2, int: eth1, total_bytes_out: 77333.88976287842, total_bytes_in: 77349.60731506348
# [['n0', 'eth1', 564.3737945556641, 461.4315185546875], ['n1', 'eth1', 533.0874710083008, 551.7986755371094], ['n1', 'eth2', 77349.63254547119, 77333.8609008789], ['n2', 'eth1', 77333.88976287842, 77349.60731506348]]
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=817, ip=10.244.2.6) 2022-04-02 16:31:47,834        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=817, ip=10.244.2.6) 2022-04-02 16:31:47,834        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=321, ip=10.244.3.3) 2022-04-02 16:31:47,837        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=321, ip=10.244.3.3) 2022-04-02 16:31:47,837        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=817, ip=10.244.2.6) Test Error: 
# (BaseWorkerMixin pid=817, ip=10.244.2.6)  Accuracy: 55.4%, Avg loss: 1.592509 
# (BaseWorkerMixin pid=817, ip=10.244.2.6) 
# Loss results: ([2.20903730696174, 2.0574667241163316, 1.8210527069249731, 1.5925086000163085], [18.038042347005103, 18.04349178400298, 17.793006987994886, 18.118684909000876])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.207212265889356, 2.055469888031103, 1.8201535993320928, 1.5921664792261305]
# Epoch times for worker 1: [17.99430934099655, 18.069873316999292, 17.859207116009202, 18.047570648006513]
# Job completion time: 86.34336417198938
# Num_workers: 2

# job.batch "ray-test-job-2" deleted

# same as above: run 3
# At time: Sat Apr  2 18:33:46 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 163756500888, bytes_in: 159764845947
# At time: Sat Apr  2 18:33:46 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 165426464894, bytes_in: 159134734179
# At time: Sat Apr  2 18:33:47 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 278258287480, bytes_in: 276058570492
# At time: Sat Apr  2 18:33:47 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 276061567326, bytes_in: 278255295356
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 18:35:50 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 163830367157, bytes_in: 159825270837
# At time: Sat Apr  2 18:35:50 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 165498114536, bytes_in: 159207002469
# At time: Sat Apr  2 18:35:51 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 288396740874, bytes_in: 286197434368
# At time: Sat Apr  2 18:35:51 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 286200434769, bytes_in: 288393745105
# node: n0, int: eth1, total_bytes_out: 563.5549087524414, total_bytes_in: 461.0053253173828
# node: n1, int: eth1, total_bytes_out: 546.6433868408203, total_bytes_in: 551.3632965087891
# node: n1, int: eth2, total_bytes_out: 77350.2608795166, total_bytes_in: 77353.39260864258
# node: n2, int: eth1, total_bytes_out: 77353.41982269287, total_bytes_in: 77350.23307037354
# [['n0', 'eth1', 563.5549087524414, 461.0053253173828], ['n1', 'eth1', 546.6433868408203, 551.3632965087891], ['n1', 'eth2', 77350.2608795166, 77353.39260864258], ['n2', 'eth1', 77353.41982269287, 77350.23307037354]]
# (BaseWorkerMixin pid=888, ip=10.244.2.6)  Accuracy: 56.8%, Avg loss: 1.488229 
# (BaseWorkerMixin pid=888, ip=10.244.2.6) 
# Loss results: ([2.1840387666301364, 1.9917613852555585, 1.7154526186596817, 1.4882291843936701], [17.716214428000967, 17.857971420002286, 17.92579594400013, 18.114342187996954])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.185927202747126, 1.9976103761393553, 1.7256842335318303, 1.4997560499580043]
# Epoch times for worker 1: [17.66722591299913, 17.872956949999207, 17.938433023999096, 18.08130565600004]
# Job completion time: 85.56045138899935
# Num_workers: 2
# /home/ray/anaconda3/lib/python3.7/site-packages/ray/util/client/worker.py:514: UserWarning: More than 10MB of messages have been created to schedule tasks on the server. This can be slow on Ray Client due to communication overhead over the network. If you're running many fine-grained tasks, consider running them inside a single remote function. See the section on "Too fine-grained tasks" in the Ray Design Patterns document for more details: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.f7ins22n6nyl. If your functions frequently use large objects, consider storing the objects remotely with ray.put. An example of this is shown in the "Closure capture of large / unserializable object" section of the Ray Design Patterns document, available here: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.1afmymq455wu
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=358, ip=10.244.3.3) 2022-04-02 16:34:35,414        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=358, ip=10.244.3.3) 2022-04-02 16:34:35,415        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=888, ip=10.244.2.6) 2022-04-02 16:34:35,407        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=888, ip=10.244.2.6) 2022-04-02 16:34:35,407        INFO torch.py:247 -- Wrapping provided model in DDP.

# job.batch "ray-test-job-2" deleted



# ray head in n1. both workers heavily utilized:
# At time: Sat Apr  2 18:46:47 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 174071943640, bytes_in: 169974754090
# At time: Sat Apr  2 18:46:47 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 175697252001, bytes_in: 169439295489
# At time: Sat Apr  2 18:46:47 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 298670344563, bytes_in: 296347035608
# At time: Sat Apr  2 18:46:48 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 296350058183, bytes_in: 298667332641
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 18:49:06 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 184213242698, bytes_in: 180056025329
# At time: Sat Apr  2 18:49:06 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 185793052088, bytes_in: 179579273301
# At time: Sat Apr  2 18:49:07 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 308867798477, bytes_in: 306484556399
# At time: Sat Apr  2 18:49:07 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 306487577979, bytes_in: 308864789921
# node: n0, int: eth1, total_bytes_out: 77371.97157287598, total_bytes_in: 76913.99565887451
# node: n1, int: eth1, total_bytes_out: 77024.84197235107, total_bytes_in: 77361.89126586914
# node: n1, int: eth2, total_bytes_out: 77800.39912414551, total_bytes_in: 77343.14568328857
# node: n2, int: eth1, total_bytes_out: 77343.13809204102, total_bytes_in: 77800.4248046875
# [['n0', 'eth1', 77371.97157287598, 76913.99565887451], ['n1', 'eth1', 77024.84197235107, 77361.89126586914], ['n1', 'eth2', 77800.39912414551, 77343.14568328857], ['n2', 'eth1', 77343.13809204102, 77800.4248046875]]
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=703, ip=10.244.3.3) 2022-04-02 16:47:35,241        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=703, ip=10.244.3.3) 2022-04-02 16:47:35,241        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=249, ip=10.244.1.2) 2022-04-02 16:47:35,245        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=249, ip=10.244.1.2) 2022-04-02 16:47:35,245        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=703, ip=10.244.3.3) Test Error: 
# (BaseWorkerMixin pid=703, ip=10.244.3.3)  Accuracy: 45.9%, Avg loss: 1.821543 
# (BaseWorkerMixin pid=703, ip=10.244.3.3) 
# Loss results: ([2.234462183751878, 2.136401164303919, 1.989122083232661, 1.8215425705454151], [21.553227028009132, 20.819620626003598, 20.761478231012006, 20.60682731299312])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.2337132138051805, 2.1343102774042992, 1.9862974965648286, 1.8186417742139975]
# Epoch times for worker 1: [21.533359312990797, 20.79541944200173, 20.830623155998182, 20.475052422989393]
# Job completion time: 97.04411566299677
# Num_workers: 2

# job.batch "ray-test-job-2" deleted


# ray head in n1. only 1 worker is heavily utilized:

# At time: Sat Apr  2 18:49:39 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 184215786324, bytes_in: 180057577283
# At time: Sat Apr  2 18:49:40 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 185797072336, bytes_in: 179580548686
# At time: Sat Apr  2 18:49:40 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 308869695987, bytes_in: 306485059269
# At time: Sat Apr  2 18:49:40 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 306488081131, bytes_in: 308866719645
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 18:51:53 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 194353560469, bytes_in: 190140267071
# At time: Sat Apr  2 18:51:53 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 195893731248, bytes_in: 189716899141
# At time: Sat Apr  2 18:51:54 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 309044679178, bytes_in: 306548128695
# At time: Sat Apr  2 18:51:54 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 306551160097, bytes_in: 309041660126
# node: n0, int: eth1, total_bytes_out: 77345.07862091064, total_bytes_in: 76924.81832885742
# node: n1, int: eth1, total_bytes_out: 77031.39428710938, total_bytes_in: 77334.21672821045
# node: n1, int: eth2, total_bytes_out: 1335.0158004760742, total_bytes_in: 481.18153381347656
# node: n2, int: eth1, total_bytes_out: 481.2543182373047, total_bytes_in: 1334.6899490356445
# [['n0', 'eth1', 77345.07862091064, 76924.81832885742], ['n1', 'eth1', 77031.39428710938, 77334.21672821045], ['n1', 'eth2', 1335.0158004760742, 481.18153381347656], ['n2', 'eth1', 481.2543182373047, 1334.6899490356445]]
# (BaseWorkerMixin pid=286, ip=10.244.1.2) loss: 1.907803  [28800/30000]
# (BaseWorkerMixin pid=1780) loss: 1.505204  [28800/30000]
# (BaseWorkerMixin pid=286, ip=10.244.1.2) Test Error: 
# (BaseWorkerMixin pid=286, ip=10.244.1.2)  Accuracy: 51.5%, Avg loss: 1.702378 
# (BaseWorkerMixin pid=286, ip=10.244.1.2) 
# (BaseWorkerMixin pid=1780) Test Error: 
# (BaseWorkerMixin pid=1780)  Accuracy: 49.2%, Avg loss: 1.742027 
# (BaseWorkerMixin pid=1780) 
# Loss results: ([2.2165038752707704, 2.084118993418991, 1.8894091085263878, 1.7023779662551395], [20.45703534600034, 20.602901653997833, 20.658770535999793, 20.74732769599359])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.222562392046497, 2.099304616830911, 1.9175466906492877, 1.7420270792238273]
# Epoch times for worker 1: [20.51925984400441, 20.585436112000025, 20.56746116100112, 20.9017761189898]
# Job completion time: 94.39224042699789
# Num_workers: 2

# job.batch "ray-test-job-2" deleted.


# same as above (node placement and utilization of workers), except that tc is activated and set at values of t=0: 
# At time: Sat Apr  2 19:07:27 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 214668571156, bytes_in: 210332684783
# At time: Sat Apr  2 19:07:28 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 216167898072, bytes_in: 210020947365
# At time: Sat Apr  2 19:07:28 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 319345176684, bytes_in: 316708567025
# At time: Sat Apr  2 19:07:28 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 316711617300, bytes_in: 319342132584
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 19:11:47 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 224815849169, bytes_in: 220419105761
# At time: Sat Apr  2 19:11:47 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 226274242050, bytes_in: 220164802480
# At time: Sat Apr  2 19:11:47 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 319416065530, bytes_in: 316716383439
# At time: Sat Apr  2 19:11:48 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 316719440160, bytes_in: 319413013809
# node: n0, int: eth1, total_bytes_out: 77417.58737945557, total_bytes_in: 76953.28504943848
# node: n1, int: eth1, total_bytes_out: 77105.28547668457, total_bytes_in: 77391.47274017334
# node: n1, int: eth2, total_bytes_out: 540.8389739990234, total_bytes_in: 59.63450622558594
# node: n2, int: eth1, total_bytes_out: 59.683685302734375, total_bytes_in: 540.7808303833008
# [['n0', 'eth1', 77417.58737945557, 76953.28504943848], ['n1', 'eth1', 77105.28547668457, 77391.47274017334], ['n1', 'eth2', 540.8389739990234, 59.63450622558594], ['n2', 'eth1', 59.683685302734375, 540.7808303833008]]
# (BaseWorkerMixin pid=398, ip=10.244.1.2) loss: 1.578661  [28800/30000]
# (BaseWorkerMixin pid=2900) loss: 1.833458  [28800/30000]
# (BaseWorkerMixin pid=398, ip=10.244.1.2) Test Error: 
# (BaseWorkerMixin pid=398, ip=10.244.1.2)  Accuracy: 55.4%, Avg loss: 1.707042 
# (BaseWorkerMixin pid=398, ip=10.244.1.2) 
# (BaseWorkerMixin pid=2900) Test Error: 
# (BaseWorkerMixin pid=2900)  Accuracy: 57.3%, Avg loss: 1.674298 
# (BaseWorkerMixin pid=2900) 
# Loss results: ([2.205472085126646, 2.0602016509718197, 1.8598615963747547, 1.67429827884504], [50.165089536996675, 57.95042992000526, 50.23512587399455, 51.5312385080033])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.211123600127591, 2.0740184966166306, 1.8840991926800674, 1.7070420152822119]
# Epoch times for worker 1: [50.097735739007476, 57.9737054080033, 50.241856060005375, 51.41506819501228]
# Job completion time: 224.48833766099415
# Num_workers: 2

# job.batch "ray-test-job-2" deleted


# same as above, except with varying tc. Now roughly t=0.
# At time: Sat Apr  2 20:45:13 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 225105527833, bytes_in: 220669784552
# At time: Sat Apr  2 20:45:13 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 227002308447, bytes_in: 220379525663
# At time: Sat Apr  2 20:45:13 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 319743079226, bytes_in: 316891389891
# At time: Sat Apr  2 20:45:14 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 316894594944, bytes_in: 319739891652
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 20:48:22 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 225172216463, bytes_in: 220790198455
# At time: Sat Apr  2 20:48:22 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 227138029382, bytes_in: 220443617973
# At time: Sat Apr  2 20:48:22 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 329884686022, bytes_in: 327030185367
# At time: Sat Apr  2 20:48:23 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 327033392756, bytes_in: 329881483341
# node: n0, int: eth1, total_bytes_out: 508.7938690185547, total_bytes_in: 918.685173034668
# node: n1, int: eth1, total_bytes_out: 1035.4685592651367, total_bytes_in: 488.9855194091797
# node: n1, int: eth2, total_bytes_out: 77374.31942749023, total_bytes_in: 77352.87075805664
# node: n2, int: eth1, total_bytes_out: 77352.88858032227, total_bytes_in: 77374.20417022705
# [['n0', 'eth1', 508.7938690185547, 918.685173034668], ['n1', 'eth1', 1035.4685592651367, 488.9855194091797], ['n1', 'eth2', 77374.31942749023, 77352.87075805664], ['n2', 'eth1', 77352.88858032227, 77374.20417022705]]
# (BaseWorkerMixin pid=3414)  Accuracy: 35.6%, Avg loss: 1.912981 
# (BaseWorkerMixin pid=3414) 
# Loss results: ([2.2399790287017822, 2.1545080652662145, 2.040004754522044, 1.9129809862489153], [27.759860987003776, 27.046822506003082, 38.6322758919996, 39.03094358899398])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.2423273681835005, 2.1615641018387617, 2.053455903271961, 1.929959108875056]
# Epoch times for worker 1: [27.61340598699462, 27.09005790199444, 38.67611910200503, 39.062054043009994]
# Job completion time: 149.43445996299852
# Num_workers: 2
# /home/ray/anaconda3/lib/python3.7/site-packages/ray/util/client/worker.py:514: UserWarning: More than 10MB of messages have been created to schedule tasks on the server. This can be slow on Ray Client due to communication overhead over the network. If you're running many fine-grained tasks, consider running them inside a single remote function. See the section on "Too fine-grained tasks" in the Ray Design Patterns document for more details: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.f7ins22n6nyl. If your functions frequently use large objects, consider storing the objects remotely with ray.put. An example of this is shown in the "Closure capture of large / unserializable object" section of the Ray Design Patterns document, available here: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.1afmymq455wu
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=878, ip=10.244.3.3) 2022-04-02 18:46:05,319      INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=878, ip=10.244.3.3) 2022-04-02 18:46:05,319      INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=3414) 2022-04-02 18:46:05,312      INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=3414) 2022-04-02 18:46:05,312      INFO torch.py:247 -- Wrapping provided model in DDP.

# job.batch "ray-test-job-2" deleted


# same as above, except with varying tc. Now roughly t=3 mins 40 secs.
# At time: Sat Apr  2 20:48:39 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 225172887187, bytes_in: 220791017130
# At time: Sat Apr  2 20:48:39 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 227140060320, bytes_in: 220444414447
# At time: Sat Apr  2 20:48:40 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 329885827250, bytes_in: 327030442988
# At time: Sat Apr  2 20:48:40 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 327033651260, bytes_in: 329882624153
# job.batch/ray-test-job-2 created

# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 20:54:18 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 235324275576, bytes_in: 230941905374
# At time: Sat Apr  2 20:54:18 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 237320301350, bytes_in: 230590134947
# At time: Sat Apr  2 20:54:18 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 340037697015, bytes_in: 337177515073
# At time: Sat Apr  2 20:54:19 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 337180737822, bytes_in: 340034485716
# node: n0, int: eth1, total_bytes_out: 77448.94705963135, total_bytes_in: 77445.13125610352
# node: n1, int: eth1, total_bytes_out: 77669.07524108887, total_bytes_in: 77405.70449829102
# node: n1, int: eth2, total_bytes_out: 77452.61966705322, total_bytes_in: 77416.01627349854
# node: n2, int: eth1, total_bytes_out: 77416.12672424316, total_bytes_in: 77452.55709075928
# [['n0', 'eth1', 77448.94705963135, 77445.13125610352], ['n1', 'eth1', 77669.07524108887, 77405.70449829102], ['n1', 'eth2', 77452.61966705322, 77416.01627349854], ['n2', 'eth1', 77416.12672424316, 77452.55709075928]]
# (BaseWorkerMixin pid=534, ip=10.244.1.2)  Accuracy: 51.1%, Avg loss: 1.687120 
# (BaseWorkerMixin pid=534, ip=10.244.1.2) 
# Loss results: ([2.2104773718839996, 2.064795705163555, 1.8672972439201014, 1.6871196228987093], [61.514005849996465, 67.25277452799492, 72.78321165200032, 79.6563683179993])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.2121841694898667, 2.0697134262437276, 1.8756152831824722, 1.6975195187671928]
# Epoch times for worker 1: [61.38165415500407, 67.28933829200105, 72.69300025900884, 79.70874098099011]
# Job completion time: 298.8358867079951
# Num_workers: 2
# /home/ray/anaconda3/lib/python3.7/site-packages/ray/util/client/worker.py:514: UserWarning: More than 10MB of messages have been created to schedule tasks on the server. This can be slow on Ray Client due to communication overhead over the network. If you're running many fine-grained tasks, consider running them inside a single remote function. See the section on "Too fine-grained tasks" in the Ray Design Patterns document for more details: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.f7ins22n6nyl. If your functions frequently use large objects, consider storing the objects remotely with ray.put. An example of this is shown in the "Closure capture of large / unserializable object" section of the Ray Design Patterns document, available here: https://docs.google.com/document/d/167rnnDFIVRhHhK4mznEIemOtj63IOhtIPvSYaPgI4Fg/edit#heading=h.1afmymq455wu
#   f"{DESIGN_PATTERN_LARGE_OBJECTS_LINK}", UserWarning)
# (BaseWorkerMixin pid=916, ip=10.244.3.3) 2022-04-02 18:49:31,329        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=916, ip=10.244.3.3) 2022-04-02 18:49:31,329        INFO torch.py:247 -- Wrapping provided model in DDP.
# (BaseWorkerMixin pid=534, ip=10.244.1.2) 2022-04-02 18:49:31,320        INFO torch.py:244 -- Moving model to device: cpu
# (BaseWorkerMixin pid=534, ip=10.244.1.2) 2022-04-02 18:49:31,321        INFO torch.py:247 -- Wrapping provided model in DDP.

# job.batch "ray-test-job-2" deleted




# same as above, except with varying tc. Now roughly t=9 mins 10 secs. Note: this should have the same job completion time as the previous run, since the simulation time for tc was only set for 10 minutes (confirmed yes, count_store.txt already exceeded 45 at node 2). 
# At time: Sat Apr  2 20:54:37 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 235324967770, bytes_in: 230942790745
# At time: Sat Apr  2 20:54:37 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 237324734114, bytes_in: 230591006806
# At time: Sat Apr  2 20:54:38 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 340038962750, bytes_in: 337180080397
# At time: Sat Apr  2 20:54:38 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 337183298316, bytes_in: 340035750552
# job.batch/ray-test-job-2 created
# job.batch/ray-test-job-2 condition met

# At time: Sat Apr  2 20:58:53 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 235395459285, bytes_in: 231066345755
# At time: Sat Apr  2 20:58:53 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 237469673597, bytes_in: 230657929348
# At time: Sat Apr  2 20:58:54 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 350184311700, bytes_in: 347323094592
# At time: Sat Apr  2 20:58:54 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 347326320090, bytes_in: 350181092995
# node: n0, int: eth1, total_bytes_out: 537.8075790405273, total_bytes_in: 942.6499176025391
# node: n1, int: eth1, total_bytes_out: 1105.8004989624023, total_bytes_in: 510.57847595214844
# node: n1, int: eth2, total_bytes_out: 77402.86979675293, total_bytes_in: 77385.05702972412
# node: n2, int: eth1, total_bytes_out: 77385.11485290527, total_bytes_in: 77402.82015228271
# [['n0', 'eth1', 537.8075790405273, 942.6499176025391], ['n1', 'eth1', 1105.8004989624023, 510.57847595214844], ['n1', 'eth2', 77402.86979675293, 77385.05702972412], ['n2', 'eth1', 77385.11485290527, 77402.82015228271]]
# (BaseWorkerMixin pid=4446) loss: 1.657133  [28800/30000]
# (BaseWorkerMixin pid=956, ip=10.244.3.3) loss: 1.647803  [28800/30000]
# (BaseWorkerMixin pid=4446) Test Error: 
# (BaseWorkerMixin pid=4446)  Accuracy: 37.2%, Avg loss: 1.842399 
# (BaseWorkerMixin pid=4446) 
# (BaseWorkerMixin pid=956, ip=10.244.3.3) Test Error: 
# (BaseWorkerMixin pid=956, ip=10.244.3.3)  Accuracy: 37.3%, Avg loss: 1.850233 
# (BaseWorkerMixin pid=956, ip=10.244.3.3) 
# Loss results: ([2.2257916031369738, 2.114897647481056, 1.9701532922732603, 1.8423994847923328], [50.859483984007966, 45.68048005500168, 46.00270406198979, 45.96393940200505])
# Num of epochs: 4
# Batch Size: 64
# Epoch times for worker 0: [2.2255237345482892, 2.1169017234425636, 1.9754953475514794, 1.8502331630439515]
# Epoch times for worker 1: [50.80295799400483, 45.596382219999214, 46.05600401999254, 46.013212588994065]
# Job completion time: 207.63937583299412
# Num_workers: 2

# job.batch "ray-test-job-2" deleted
