# Databricks notebook source
# MAGIC %pip install locust-on-databricks
# MAGIC %restart_python

# COMMAND ----------

# locust-on-databricks aka lod
from lod import LocustRunner

# COMMAND ----------

runner = LocustRunner(locustfile_path="locustfile.py")

runner.set_initial_swarm(
  host="https://google.com",
  user_count=5,
  spawn_rate=1,
  run_time = "15s"
).start_locust()

# COMMAND ----------

runner.block_until_end_of_swarm(
  timeout_in_seconds=100000
)

# COMMAND ----------

runner.save_artifacts(
  save_directory="artifacts"
)

# COMMAND ----------

runner.display_report_snapshot()

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
