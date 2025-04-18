# Databricks notebook source
# MAGIC %pip install locust-on-databricks
# MAGIC %restart_python

# COMMAND ----------

# locust-on-databricks aka lod
from lod import LocustRunner

# COMMAND ----------

runner = LocustRunner(locustfile_path="locustfile.py")

runner.distributed().set_initial_swarm(
  host="https://google.com",
  user_count=30,
  spawn_rate=2,
  run_time = "5m"
).start_locust()

# COMMAND ----------

runner.block_until_end_of_swarm(100000)

# COMMAND ----------

# Kill an Existing Swarm
# runner.stop_swarm()

# COMMAND ----------

runner.stop_locust()

# COMMAND ----------

# Optionally Run your Own Swarm
# runner.run_swarm(
#   host="https://google.com",
#   user_count=10,
#   spawn_rate=2,
#   # run_time = "5m"
# )
