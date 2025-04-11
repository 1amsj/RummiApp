import subprocess

def my_scheduled_job():
  print("Scheduled job executed")
  subprocess.Popen(["gnome-terminal"])