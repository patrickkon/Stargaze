# Assumptions: start_tc.sh has already been executed
# Run test 1:
# bash restart_tc.sh
python tests/workloads/ray/train_fashion_mnist/execute_train_fashion_mnist.py

# Run test 2:
# bash restart_tc.sh
# python tests/workloads/ray/ddp_mnist_torch/execute_ddp_mnist_torch.py

# # Run test 3:
# bash restart_tc.sh
# python tests/workloads/ray/shuffle/execute_shuffle.py
