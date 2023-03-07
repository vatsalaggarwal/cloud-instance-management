# cloud-instance-management

Start/stop one GCP instance easily via the command line. At start time, it updates the ssh config so the instance can be logged into easily.

## Setup

Create a `cloud_instance_management/constants.py` with the following contents:

```py
PROJECT_ID = "" # Google Cloud Project ID
INSTANCE_NAME = "" # Instance ID given to the relevant instance
LOCAL_INSTANCE_NAME = "" # Host ID of the relevant instance in the ~/.ssh/config file

```

Note: assumes that ~/.ssh/config has been setup for this instance before.
