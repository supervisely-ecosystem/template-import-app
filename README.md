---
description: >-
  A step-by-step tutorial of how to use import template to import data from folder.
---

# Import data from folder

## Introduction

In this tutorial, we will create a simple import app that will upload images from a folder to Supervisely using import app template from SDK with a following structure:

```text
my_folder
├── cat_1.jpg
├── cat_2.jpg
└── cat_3.jpg
```

<img src="https://github.com/supervisely-ecosystem/template-import-app/assets/48913536/49f242ac-328c-4646-ba5b-60c60f5f755a">

You can find the above demo folder in the data directory of the template-import-app repo - [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/data/)

We will go through the following steps:

[**Step 1.**](#step-1-how-to-debug-import-app) How to debug import app.

[**Step 2**](#step-2-how-to-write-an-import-script) How to write an import script.

[**Step 3.**](#step-3-advanced-debug) Advanced debug.

[**Step 4.**](#step-4-how-to-run-it-in-supervisely) How to run it in Supervisely.

Everything you need to reproduce [this tutorial is on GitHub](https://github.com/supervisely-ecosystem/template-import-app): [source code](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-folder.py).

Before we begin, please clone the project and set up the working environment - [here is a link with a description of the steps](/README.md#set-up-an-environment-for-development).

## Step 1. How to debug import app

Open `local.env` and set up environment variables by inserting your values here for debugging. Learn more about environment variables in our [guide](https://developer.supervisely.com/getting-started/environment-variables)

For this example, we will use the following environment variables:

**local.env:**

```python
TEAM_ID=8                     # ⬅️ change it to your team ID
WORKSPACE_ID=349              # ⬅️ change it to your workspace ID
FOLDER="data/my_folder"       # ⬅️ path to directory with data on local machine
```

**advanced.env:**

```python
TASK_ID=35038                     # ⬅️ requires to use advanced debugging
TEAM_ID=8                         # ⬅️ change it to your team ID
WORKSPACE_ID=349                  # ⬅️ change it to your workspace ID
SLY_APP_DATA_DIR="results/"       # ⬅️ path to directory for local debugging

# Optional. Specify one of the following variables if you want to simulate import from:
# FOLDER = "/data/my_folder"      # ⬅️ path to folder in Team Files
# FILE = "/data/my_archive.zip"   # ⬅️ path to File in Team Files
# PROJECT_ID = 20811              # ⬅️ put your value here
# DATASET_ID = 64686              # ⬅️ put your value here | requires PROJECT_ID
```

## Step 2. How to write an import script

Find source code for this example [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-folder.py)

**Step 1. Import libraries**

```python
import os

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

**Step 3. Create class MyImport that inherits from sly.app.Import with process method**

```python
class MyImport(sly.app.Import):
    def process(self, context: sly.app.Import.Context):
        ...
```

**Step 4. Reimplement process method**

```python
class MyImport(sly.app.Import):
    def process(self, context: sly.app.Import.Context):
        # create api object to communicate with Supervisely Server
        api = sly.Api.from_env()

        # get or create project
        project_id = context.project_id
        if project_id is None:
            project = api.project.create(
                workspace_id=context.workspace_id, name="My Project", change_name_if_conflict=True
            )
            project_id = project.id

        # get or create dataset
        dataset_id = context.dataset_id
        if dataset_id is None:
            dataset = api.dataset.create(
                project_id=project_id, name="ds0", change_name_if_conflict=True
            )
            dataset_id = dataset.id

        # list images in directory
        images_names = []
        images_paths = []
        for file in os.listdir(context.path):
            file_path = os.path.join(context.path, file)
            images_names.append(file)
            images_paths.append(file_path)

        # process images and upload them by paths
        with tqdm(total=len(images_paths)) as pbar:
            for img_name, img_path in zip(images_names, images_paths):
                try:
                    # upload image into dataset on Supervisely server
                    info = api.image.upload_path(
                        dataset_id=dataset_id, name=img_name, path=img_path
                    )
                    sly.logger.trace(f"Image has been uploaded: id={info.id}, name={info.name}")
                except Exception as e:
                    sly.logger.warn("Skip image", extra={"name": img_name, "reason": repr(e)})
                finally:
                    pbar.update(1)

        return project_id
```

**Step 5. Create app object and execute run() method**

```python
app = MyImport()
app.run()
```

## Step 3. Advanced debug

In addition to the local debug option, this template also includes setting for `Advanced debugging`.

![launch.json]()

This option is useful for final testing and debugging. In this case, data will be downloaded from Supervisely instance Team Files and uploaded to specified project or dataset on Supervisely platform, source folder will be removed if specified.

![Advanced debug]()

Output of this python program:

```text
{"message": "Application is running on Supervisely Platform in production mode", "timestamp": "2023-05-10T14:17:57.194Z", "level": "info"}
{"message": "Application PID is 19320", "timestamp": "2023-05-10T14:17:57.194Z", "level": "info"}
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 0, "total": 3, "timestamp": "2023-05-10T14:18:01.261Z", "level": "info"}
...
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 3, "total": 3, "timestamp": "2023-05-10T14:18:04.766Z", "level": "info"}
{"message": "Result project: id=21417, name=My Project", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Shutting down [pid argument = 19320]...", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Application has been shut down successfully", "timestamp": "2023-05-10T14:18:05.959Z", "level": "info"}
```
