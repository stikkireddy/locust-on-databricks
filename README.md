# locust-on-databricks

## Installation

```bash
pip install locust-on-databricks
```

## Usage

### OOTB Examples

For OOTB please look at examples in

1. [01 Locust Test Single Node.py](notebooks/01%20Locust%20Test%20Single%20Node.py)
2. [02 Locust Test Distributed.py](notebooks/02%20Locust%20Test%20Distributed.py)

The dummy example locustfile is here: [locustfile.py](notebooks/locustfile.py)

### API Usage

Construct the runner:

```python
from lod import LocustRunner

runner = LocustRunner(
    locustfile_path="locustfile.py",  # path to your locustfile
    # port=8089, # port is optional
)
```

Construct your initial swarm:

```python
runner = runner.set_initial_swarm(
    host="https://google.com",
    user_count=10,
    spawn_rate=2,
    # run_time = "5m"
)
```

Start your locust server:

```python
runner.start_locust()
```

Wait for running locust swarm to finish

```python
runner.block_until_end_of_swarm(
    timeout_in_seconds=300,
    # check_every_n_seconds=5, # poll every n seconds default is 5s
)
```

Capture results/snapshots into a directory

This will create:

1. request metrics csv
2. failures csv
3. exceptions csv
4. html report

```python
runner.save_artifacts(
    # save_directory="artifacts" # default is artifacts but recommended you save to volumes
    # file_prefix="" # default is empty prefix to your artifacts
)
```

Stop your locust server:

```python
runner.stop_locust()
```

Search for "Access Locust Web UI at" in the output and open the link in your browser.

### Distributed Runner

Construct a distributed runner:

```python
runner = runner
.distributed()
.set_initial_swarm(
    host="https://google.com",
    user_count=10,
    spawn_rate=2,
    # run_time = "5m"
)
```

Construct a distributed runner with custom worker to core ratio:

```python
runner = runner
.distributed(process_to_core_count_ratio=2.0)
.set_initial_swarm(
    host="https://google.com",
    user_count=10,
    spawn_rate=2,
    # run_time = "5m"
)
```

`process_to_core_count_ratio` is defaulted to 2 and it will spin up twice the number of workers as you have cores.
You can tweak this as needed.

### Run and stop new swarms

Run a new swarm:

```python
runner.run_swarm(
    host="https://google.com",
    user_count=10,
    spawn_rate=2,
    # run_time = "5m"
)
```

Stop a running swarm

```python
runner.stop_swarm()
```

## Limitations

**Starting a new swarm in the ui is bugged and the swarm rest api from the ui is not working.**

**To make this project simpler to use at any given time, you can only run one locust cluster and swarm at a time,**
**we do not keep track of pids or any other state.** 

## Disclaimer

locust-on-databricks is not developed, endorsed not supported by Databricks. It is provided as-is; no warranty is
derived from using this package. For more details, please refer to the license.
