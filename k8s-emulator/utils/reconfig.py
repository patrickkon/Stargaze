import requests

# Assumes: Some function previously took in new topo.txt and mapping file, generate required per node routing and tc files
# Assumes: isl-reconfig-api pod runs in each node (including GS)

# Generate a HTTP request to each of the pods in Assumption 2, while passing in the files in Assumption 1



URL = "http://192.168.121.58:81/isl-reconfig/upload"
FILE_NAMES = ["test.sh"]
files = [('file', open(f, 'rb')) for f in FILE_NAMES]
# print([line for line in files[0][1]])
r = requests.post(url = URL, files=files)
# print(r.request.headers)
# print(r.request.body)
data = r.json()
print(data)
# print(r.text)

URL = "http://192.168.121.58:81/isl-reconfig/exec"
r = requests.post(url = URL, files=files)
# print(r.request.headers)
# print(r.request.body)
data = r.json()
print(data)
