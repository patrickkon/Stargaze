import argparse
import ray
import time
import numpy as np

@ray.remote
def map(obj, f):
    return f(obj)

@ray.remote
def sum_results(*elements):
    return np.sum(elements)

def map_reduce_func():
    items = list(range(1000))
    map_func = lambda i : i*2
    remote_elements = [map.remote(i, map_func) for i in items]
    print("mapping")
    # simple reduce
    remote_final_sum = sum_results.remote(*remote_elements)
    result = ray.get(remote_final_sum)
    print("reducing 1")
    # tree reduce
    intermediate_results = [sum_results.remote(
        *remote_elements[i * 20: (i + 1) * 20]) for i in range(5)]
    remote_final_sum = sum_results.remote(*intermediate_results)
    print("reducing 2")
    result = ray.get(remote_final_sum)
    print("return")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "--address",
            required=False,
            type=str,
            help="the address to use for Ray")
    parser.add_argument(
        "--num-mappers", help="number of mapper actors used", default=3, type=int
    )
    parser.add_argument(
        "--num-reducers", help="number of reducer actors used", default=4, type=int
    )

    args, _ = parser.parse_known_args()

    start_time = time.monotonic()
    ray.init(address=args.address)
    print("Result: ", map_reduce_func())
    elapsed_time = time.monotonic() - start_time
    print("Job completion time: {}".format(elapsed_time))
