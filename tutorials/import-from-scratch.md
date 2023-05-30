---
description: >-
  A step-by-step tutorial of how to create custom import app without using template from SDK (from scratch).
---

# Create import app from scratch (without import template from SDK)

## Introduction

We recommend to use import template for creating custom import applications using class `sly.app.Import` from Supervisely SDK.
However, if your use case is not covered by our import template, you can create your own app **from scratch**  without the template using basic methods from Supervisely SDK.

In this tutorial, we will create a simple import app that will upload images from a folder or archive to Supervisely with a following structure:

```text
my_folder       my_archive.tar
├── cat_1.jpg       ├── cat_1.jpg
├── cat_2.jpg       ├── cat_2.jpg
└── cat_3.jpg       └── cat_3.jpg
```

You can find the above demo files in the data directory of the template-import-app repo - [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/data/)

We will go through the following steps:

[**Step 1.**](#step-1-how-to-debug-import-app) How to debug import app.

[**Step 2**](#step-2-how-to-write-an-import-script) How to write an import script.

[**Step 3.**](#step-3-advanced-debug) Advanced debug.

[**Step 4.**](#step-4-how-to-run-it-in-supervisely) How to run it in Supervisely.

Everything you need to reproduce [this tutorial is on GitHub](https://github.com/supervisely-ecosystem/template-import-app): [source code](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-from-scratch.py).

Before we begin, please clone the project and set up the working environment - [here is a link with a description of the steps](/README.md#set-up-an-environment-for-development).

## Step 1. How to debug import app

Open `local.env` and set up environment variables by inserting your values here for debugging. Learn more about environment variables in our [guide](https://developer.supervisely.com/getting-started/environment-variables)

For this example, we will use the following environment variables:

```python
TASK_ID=33572                 # ⬅️ requires to use advanced debugging, comment for local debugging
TEAM_ID=8                     # ⬅️ change it to your team ID
WORKSPACE_ID=349              # ⬅️ change it to your workspace ID
PROJECT_ID=18334              # ⬅️ ID of the existing project where your data will be imported (optional)
DATASET_ID=66325              # ⬅️ ID of the existing dataset where your data will be imported (optional)
SLY_APP_DATA_DIR="results/"   # ⬅️ path to directory for advanced debug (your data will be downloaded in this directory)

FOLDER="data/my_folder"       # ⬅️ path to directory with data on local machine
# FOLDER="/data/my_folder"      # ⬅️ path to directory with data on Supervisely Team Files
```

## Step 2. How to write an import script

Find source code for this example [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-from-scratch.py)

**Step 1. Import libraries**

```python
import os
import shutil
import supervisely as sly
from dotenv import load_dotenv
from tqdm import tqdm
```

**Step 2. Load environment variables**

Load ENV variables for debug, has no effect in production

```python
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
```

**Step 3. Init app object and api object to communicate with Supervisely Server**

```python
api = sly.Api.from_env()
app = sly.Application()
```

**Step 4. Get environment variables**

```python
TASK_ID = sly.env.task_id(raise_not_found=False)
TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
PROJECT_ID = sly.env.project_id(raise_not_found=False)
DATASET_ID = sly.env.dataset_id(raise_not_found=False)
PATH_TO_FOLDER = sly.env.folder(raise_not_found=False)
PATH_TO_FILE = sly.env.file(raise_not_found=False)
IS_PRODUCTION = sly.is_production()
STORAGE_DIR = sly.app.get_data_dir()
```

**Step 5. Get or create destination project and dataset**

```python
if PROJECT_ID is None:
    project = api.project.create(
        workspace_id=WORKSPACE_ID, name="My Project", change_name_if_conflict=True
    )
else:
    project = api.project.get_info_by_id(PROJECT_ID)
if DATASET_ID is None:
    dataset = api.dataset.create(project_id=project.id, name="ds0", change_name_if_conflict=True)
else:
    dataset = api.dataset.get_info_by_id(DATASET_ID)
    if PROJECT_ID is not None:
        project_datasets = api.dataset.get_list(project.id)
        if dataset not in project_datasets:
            raise ValueError(
                f"Dataset {dataset.name}(ID {dataset.id}) "
                f"does not belong to project {project.name} (ID {project.id})."
            )
```

**Step 6. Get directory with data**

Download folder from Supervisely Team Files to local storage if debugging in production mode
or get path to local folder if debugging in local mode

```python
if IS_PRODUCTION is True:
    if PATH_TO_FOLDER is not None:
        # specify local path to download
        local_data_path = os.path.join(STORAGE_DIR, os.path.basename(PATH_TO_FOLDER))
        # download file from Supervisely Team Files to local storage
        api.file.download_directory(
            team_id=TEAM_ID, remote_path=PATH_TO_FOLDER, local_save_path=local_data_path
        )
    elif PATH_TO_FILE is not None:
        # specify local path to download
        local_data_path = os.path.join(STORAGE_DIR, os.path.basename(PATH_TO_FILE))
        # download file from Supervisely Team Files to local storage
        api.file.download(
            team_id=TEAM_ID, remote_path=PATH_TO_FOLDER, local_save_path=local_data_path
        )
    else:
        raise ValueError("Please, specify path to folder or file in Supervisely Team Files.")
else:
    if PATH_TO_FOLDER is not None:
        local_data_path = PATH_TO_FOLDER
    elif PATH_TO_FILE is not None:
        local_data_path = PATH_TO_FILE
    else:
        raise ValueError("Please, specify path to folder or file in Supervisely Team Files.")
```

**Step 7. Iterate over files in directory to get images names and paths**

Check if the application was launched from file and unpack archive and get images names and paths

```python
    local_data_dir = PATH_TO_FOLDER
    if PATH_TO_FILE is not None:
        local_data_dir = os.path.join(sly.app.get_data_dir(), sly.fs.get_file_name(PATH_TO_FILE))
        shutil.unpack_archive(PATH_TO_FILE, extract_dir=local_data_dir)

    images_names = []
    images_paths = []
    for file in os.listdir(local_data_dir):
        file_path = os.path.join(local_data_dir, file)
        images_names.append(file)
        images_paths.append(file_path)

```

**Step 8. Iterate over images names and paths and upload them to Supervisely**

Process images and upload them by paths to dataset on Supervisely server


```python
with tqdm(total=len(images_paths)) as pbar:
    for img_name, img_path in zip(images_names, images_paths):
        try:
            # upload image into dataset on Supervisely server
            info = api.image.upload_path(dataset_id=dataset.id, name=img_name, path=img_path)
            sly.logger.trace(f"Image has been uploaded: id={info.id}, name={info.name}")
        except Exception as e:
            sly.logger.warn("Skip image", extra={"name": img_name, "reason": repr(e)})
        finally:
            # update progress bar
            pbar.update(1)
```

**Step 9. Set output project**

```python
res_project = api.project.get_info_by_id(project.id)
if IS_PRODUCTION is True:
    # remove local storage directory with files
    sly.fs.remove_dir(STORAGE_DIR)
    # set output project after successful import
    api.task.set_output_project(
        task_id=TASK_ID, project_id=res_project.id, project_name=res_project.name
    )

sly.logger.info(f"Result project: id={res_project.id}, name={res_project.name}")
```

**Step 10. Shutdown application after import**

```python
app.shutdown()
```

## Step 3. Advanced debug

In addition to the local debug option, this template also includes setting for `Advanced debugging`.

![launch.json]()

This option is useful for final testing and debugging. In this case, data will be downloaded from Supervisely instance Team Files.

![Advanced debug]()

Output of this python program:

```text
{"message": "Application is running on Supervisely Platform in production mode", "timestamp": "2023-05-10T14:17:57.194Z", "level": "info"}
{"message": "Application PID is 19319", "timestamp": "2023-05-10T14:17:57.194Z", "level": "info"}
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 0, "total": 3, "timestamp": "2023-05-10T14:18:01.261Z", "level": "info"}
...
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 3, "total": 3, "timestamp": "2023-05-10T14:18:04.766Z", "level": "info"}
{"message": "Result project: id=21416, name=My Project", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Shutting down [pid argument = 19319]...", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Application has been shut down successfully", "timestamp": "2023-05-10T14:18:05.959Z", "level": "info"}
```

## Step 4. How to run it in Supervisely

Submitting an app to the Supervisely Ecosystem isn’t as simple as pushing code to github repository, but it’s not as complicated as you may think of it either.

Please follow this [link](https://developer.supervisely.com/app-development/basics/add-private-app) for instructions on adding your app. We have produced a step-by-step guide on how to add your application to the Supervisely Ecosystem.