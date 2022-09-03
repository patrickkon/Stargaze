import argparse
from typing import Dict
import time

import torch
import ray.train as train
from ray.train.trainer import Trainer
from ray.train.callbacks import JsonLoggerCallback, PrintCallback
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import ToTensor

# Download training data from open datasets.
training_data = datasets.FashionMNIST(
    root="/required-files/kubernetes/example_datasets",
    train=True,
    # download=True,
    transform=ToTensor(),
)

# Download test data from open datasets.
test_data = datasets.FashionMNIST(
    root="/required-files/kubernetes/example_datasets",
    train=False,
    # download=True,
    transform=ToTensor(),
)

SEED = 2147483647

# Define model
class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28 * 28, 512), nn.ReLU(), nn.Linear(512, 512), nn.ReLU(),
            nn.Linear(512, 10), nn.ReLU())

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits


def train_epoch(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset) // train.world_size()
    # print("len dataset: {}".format(len(dataloader.dataset)))
    # print("world size train: {}".format(train.world_size()))
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        # Compute prediction error
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")
    return len(dataloader.dataset), train.world_size() # for reporting purposes


def validate_epoch(dataloader, model, loss_fn):
    size = len(dataloader.dataset) // train.world_size()
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    state = torch.get_rng_state()
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n "
          f"Accuracy: {(100 * correct):>0.1f}%, "
          f"Avg loss: {test_loss:>8f} \n")
    torch.set_rng_state(state)
    return test_loss


def train_func(config: Dict):
    batch_size = config["batch_size"]
    lr = config["lr"]
    epochs = config["epochs"]

    worker_batch_size = batch_size // train.world_size()

    # Create data loaders.
    train_dataloader = DataLoader(training_data, batch_size=worker_batch_size)
    test_dataloader = DataLoader(test_data, batch_size=worker_batch_size)

    train_dataloader = train.torch.prepare_data_loader(train_dataloader)
    test_dataloader = train.torch.prepare_data_loader(test_dataloader)

    # Create model.
    torch.manual_seed(SEED)

    model = NeuralNetwork()
    model = train.torch.prepare_model(model)

    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)

    loss_results = []
    # epoch_time = []
    # data_lengths = []

    for i in range(epochs):
        start_time = time.monotonic()
        dataset_len, world_size = train_epoch(train_dataloader, model, loss_fn, optimizer)
        loss = validate_epoch(test_dataloader, model, loss_fn)
        epoch_time = time.monotonic() - start_time
        # train.report(loss=loss, worker_idx=train.world_rank(), dataset_len=dataset_len, world_size=world_size, elapsed_time=elapsed_time)
        train.report(dataset_len=dataset_len, world_size=world_size, epoch_time=epoch_time)
        loss_results.append(loss)
        # epoch_time.append(elapsed_time)
        # data_lengths.append((dataset_len, world_size))

    return loss_results


def train_fashion_mnist(num_workers=2, use_gpu=False):
    start_time = time.monotonic()
    trainer = Trainer(
        backend="torch", num_workers=num_workers, use_gpu=use_gpu)
    trainer.start()
    config = {
        "lr": 1e-3,
        "batch_size": 64,
        "epochs": 4
    }
    elapsed_time = time.monotonic() - start_time
    print("Trainer setup time: {}".format(elapsed_time))
    # Note: epoch_time_list_per_worker format: [[epoch_1_worker_1, epoch_2_worker_1, ...],  [epoch_1_worker_2, epoch_2_worker_2, ...]]
    # Note: data_lengths_list_per_worker format: [[(epoch_1_datalength_worker1, epoch_1_worldsize_worker1), (epoch_2_datalength_worker1, epoch_2_worldsize_worker1), ...],  [(epoch_1_datalength_worker2, epoch_1_worldsize_worker2), ...]]
    start_time = time.monotonic()
    result = trainer.run(
        train_func=train_func,
        config=config,
        callbacks=[JsonLoggerCallback(), PrintCallback()])
        # callbacks=[JsonLoggerCallback()])
    elapsed_time = time.monotonic() - start_time
    print("Trainer run time: {}".format(elapsed_time))
    start_time = time.monotonic()
    trainer.shutdown()
    elapsed_time = time.monotonic() - start_time
    print("Trainer shutdown time: {}".format(elapsed_time))
    print(f"Loss results: {result}")
    print("Num of epochs: {}".format(config["epochs"]))
    print("Batch Size: {}".format(config["batch_size"]))
    # for index, epoch_times in enumerate(epoch_time_list_per_worker):
    #     # Note: the index may not necessarily match worker ID, or have any particular order. 
    #     print("Epoch times for worker {}: {}".format(index, epoch_times))
    # for index, data_lengths in enumerate(data_lengths_list_per_worker):
    #     # Note: the index may not necessarily match worker ID, or have any particular order. 
    #     print("Data length and world_size for worker {}: {}".format(index, data_lengths))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--address",
        required=False,
        type=str,
        help="the address to use for Ray")
    parser.add_argument(
        "--num-workers",
        "-n",
        type=int,
        default=2,
        help="Sets number of workers for training.")
    parser.add_argument(
        "--use-gpu",
        action="store_true",
        default=False,
        help="Enables GPU training")

    args, _ = parser.parse_known_args()

    import ray
    start_time = time.monotonic()
    ray.init(address=args.address)
    train_fashion_mnist(num_workers=args.num_workers, use_gpu=args.use_gpu)
    elapsed_time = time.monotonic() - start_time
    print("Job completion time: {}".format(elapsed_time))
    if args.num_workers:
        print("Num_workers: {}".format(args.num_workers))
    else:
        print("Num_workers: {}".format(2))