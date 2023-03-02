# Stargaze: A LEO Constellation Emulator for Security Experimentation

Stargaze is a first attempt at a low-earth orbit (LEO) constellation emulator geared towards security experimentation, with the ability to deploy real application code within the devices and network connectivity between the devices, along with runtime and management APIs that allow for the manipulation of the constellation in a variety of ways. 

## Introduction
LEO constellations' recent meteoric rise has led to the proposition of many novel use cases and applications, with research also highlighting the broad and unique threat landscape afflicting them. Stargaze runs on a local Kubernetes (k8s) cluster, where each VM (managed by KVM) corresponds to a device (e.g., a LEO satellite, user device, or GS). Stargaze only requires a constellation initialization script provided by the user, which it will ingest to generate a LEO constellation with precomputed (using tools in Hypatia) variations in link latency, bandwidth and connectivity before start-up, according to the configured emulation timescale and timestep granularity. More details can be found here: Stargaze (CPS&IOT '22, colocated with CCS '22). 

## Repository Organization
This repository is split into 3 main folders:
- k8s-emulator: constellation generator. This is the only directory a user needs to access.
- dependencies: external github submodules that Stargaze currently uses.
- hypatia_plus: holds multiple scripts that access our forked Hypatia submodule to extract network information.

## Usage:
Please refer to the README.md in k8s-emulator/

## Disclaimer
As Stargaze is ongoing work, our emulation fidelity still requires significant improvement. Currently, **our code is not production quality and is not fit for production use.** For example, Stargaze does not currently emulate atmospheric attenuation beyond having a coarse-grain static threshold. These will be added incrementally. Please also consider contributing to Stargaze if you have an urgent feature request. Thank you for your patience! 

## Contributing
There's a lot more to build and we welcome all contributions! For a list of feature ideas, please contact @patrickkon directly!

## Citing:
If you feel our paper and code is helpful, please consider citing our paper by:
```
@inproceedings{stargaze,
  title={Stargaze: A LEO Constellation Emulator for Security Experimentation},
  author={Tser Jern Kon, Patrick and Barradas, Diogo and Chen, Ang},
  booktitle={Proceedings of the 3rd Workshop on CPS\&IoT Security and Privacy (co-located with ACM CCS'22)},
  year={2022},
  address={Los Angeles, CA, USA},
}
```

<!-- ### Note:
1. Hypatia submodule is our own modified fork.
2. sh setup_host.sh -->
