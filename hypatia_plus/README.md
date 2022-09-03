

## Main toolset:
- Obtain satellite and GS position info. 

- Get satellites in range of each GS at this time step, sorted in increasing order of latency. 

- Get ISLs (+grid [find_grid_links or generate_plus_grid_isls] or intra orbital plane [find_orbit_links] or empty isls [generate_empty_isls] for now) at this time step.

- Get ISLs in range (note we do not expect this to change much) of given group of satellites, at this time step.

- Get shortest paths to all satellites in the given group, at this time step. 

- Get link utilization (ISLs and GS-sat link) at this time step.

- Notify k8s cluster scheduler at every time step.

# Steps:
```bash
# Run this command in this directory:
bash main.sh
```