# Original Code here:
# https://github.com/pytorch/examples/blob/master/mnist/main.py
import argparse
import logging
import os
import time
import torch
import torch.optim as optim
from torch.nn.parallel import DistributedDataParallel

import ray
from ray import tune
from ray.tune.examples.mnist_pytorch import (train, test,
                                             ConvNet)
from ray.tune.integration.torch import (DistributedTrainableCreator,
                                        distributed_checkpoint_dir)
from torchvision import datasets, transforms
from filelock import FileLock

logger = logging.getLogger(__name__)

# We use predownloaded datasets that reside in the k8s worker node already:
mnist_transforms = transforms.Compose(
        [transforms.ToTensor(),
         transforms.Normalize((0.1307, ), (0.3081, ))])
train_dataset = datasets.FashionMNIST(
                "/required-files/kubernetes/example_datasets",
                train=True,
                transform=mnist_transforms)
test_dataset = datasets.FashionMNIST(
                "/required-files/kubernetes/example_datasets",
                train=False,
                transform=mnist_transforms)

# Original code: https://docs.ray.io/en/latest/tune/examples/mnist_pytorch.html
def get_data_loaders(train_dataset, test_dataset):
    # We add FileLock here because multiple workers will want to
    # download data, and this may cause overwrites since
    # DataLoader is not threadsafe.
    with FileLock(os.path.expanduser("~/data.lock")):
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=64,
            shuffle=True)
        test_loader = torch.utils.data.DataLoader(
            test_dataset,
            batch_size=64,
            shuffle=True)
    return train_loader, test_loader

def train_mnist(config, checkpoint_dir=False):
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    train_loader, test_loader = get_data_loaders(train_dataset, test_dataset)
    model = ConvNet().to(device)
    optimizer = optim.SGD(model.parameters(), lr=0.1)

    if checkpoint_dir:
        with open(os.path.join(checkpoint_dir, "checkpoint")) as f:
            model_state, optimizer_state = torch.load(f)

        model.load_state_dict(model_state)
        optimizer.load_state_dict(optimizer_state)

    model = DistributedDataParallel(model)

    for epoch in range(5):
        train(model, optimizer, train_loader, device)
        acc = test(model, test_loader, device)

        if epoch % 3 == 0:
            with distributed_checkpoint_dir(step=epoch) as checkpoint_dir:
                path = os.path.join(checkpoint_dir, "checkpoint")
                torch.save((model.state_dict(), optimizer.state_dict()), path)
        tune.report(mean_accuracy=acc)


def run_ddp_tune(num_workers, num_gpus_per_worker, workers_per_node=None):
    trainable_cls = DistributedTrainableCreator(
        train_mnist,
        num_workers=num_workers,
        num_gpus_per_worker=num_gpus_per_worker,
        num_workers_per_host=workers_per_node)
    config = {
        "batch_size": tune.choice([16, 64])
    }
    analysis = tune.run(
        trainable_cls,
        num_samples=2,
        config=config,
        stop={"training_iteration": 10},
        metric="mean_accuracy",
        mode="max")

    print("Best hyperparameters found were: ", analysis.best_config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num-workers",
        "-n",
        type=int,
        default=2,
        help="Sets number of workers for training.")
    parser.add_argument(
        "--num-gpus-per-worker",
        type=int,
        default=0,
        help="Sets number of gpus each worker uses.")
    parser.add_argument(
        "--cluster",
        action="store_true",
        default=False,
        help="enables multi-node tuning")
    parser.add_argument(
        "--workers-per-node",
        type=int,
        help="Forces workers to be colocated on machines if set.")
    parser.add_argument(
        "--address",
        type=str,
        default=None,
        required=False,
        help="The address of server to connect to if using "
        "Ray Client.")

    args = parser.parse_args()
    start_time = time.monotonic()
    if args.address is not None:
        ray.init(address=args.address)
    else:
        if args.cluster:
            options = dict(address="auto")
        else:
            options = dict(num_cpus=2)
        ray.init(**options)

    run_ddp_tune(
        num_workers=args.num_workers,
        num_gpus_per_worker=args.num_gpus_per_worker,
        workers_per_node=args.workers_per_node)
    elapsed_time = time.monotonic() - start_time
    print("Job completion time: {}".format(elapsed_time))