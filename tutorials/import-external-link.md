---
description: >-
  A step-by-step tutorial of how to use import template to import data from external link.
---

# Import data from archive

## Introduction

In this tutorial, we will create an import app that will upload data from an external link to Supervisely using import app template from SDK.

We uploaded prepared archive with demo data to the template-import-app repo release draft - [demo_data.zip](https://github.com/supervisely-ecosystem/template-import-app/files/11452975/demo_data.zip)

```text
demo_data.zip
├── 000.jpg
├── 001.jpg
├── 002.jpg
├── 003.jpg
└── 004.jpg
```

We will go through the following steps:

[**Step 1.**](#step-1-how-to-debug-import-app) How to debug import app.

[**Step 2**](#step-2-how-to-write-an-import-script) How to write an import script.

[**Step 3.**](#step-3-advanced-debug) Advanced debug.

[**Step 4.**](#step-4-how-to-run-it-in-supervisely) How to run it in Supervisely.

Everything you need to reproduce [this tutorial is on GitHub](https://github.com/supervisely-ecosystem/template-import-app): [source code](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-external-link.py).

Before we begin, please clone the project and set up the working environment - [here is a link with a description of the steps](/README.md#set-up-an-environment-for-development).

## Step 1. How to debug import app

Open `local.env` and set up environment variables by inserting your values here for debugging. Learn more about environment variables in our [guide](https://developer.supervisely.com/getting-started/environment-variables)

For this example, we will use the following environment variables:

**Note:** in this case we will use external link to archive with data instead of path to folder or file

```python
TASK_ID=33572                 # ⬅️ requires to use advanced debugging, comment for local debugging
TEAM_ID=8                     # ⬅️ change it to your team ID
WORKSPACE_ID=349              # ⬅️ change it to your workspace ID
PROJECT_ID=18334              # ⬅️ ID of the existing project where your data will be imported (optional)
DATASET_ID=66325              # ⬅️ ID of the existing dataset where your data will be imported (optional)
REMOVE_SOURCE_FILES=False     # ⬅️ remove source files from Team Files after import (optional)
SLY_APP_DATA_DIR="results/"   # ⬅️ path to directory for advanced debug (your data will be downloaded in this directory)

# FOLDER=                     # ⬅️ path to archive with data on local machine
# FILE=                       # ⬅️ path to archive with data on Supervisely Team Files
```

## Step 2. How to write an import script

Find source code for this example [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-external-link.py)

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

**Step 3. Create class MyImport that inherits from sly.app.Import and reimplement is_path_required() method to return False**

```python
class MyImport(sly.app.Import):
    # override method for external imports outside of Supervisely instance
    def is_path_required(self) -> bool:
        return False

    def process(self) -> int:
        ...
```

**Step 4. Reimplement process method**

```python
class MyImport(sly.app.Import):
    # override method for external imports outside of Team Files
    def is_path_required(self) -> bool:
        return False

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

        # unpack downloaded archive
        local_data_dir = os.path.join(sly.app.get_data_dir(), sly.fs.get_file_name(context.path))
        shutil.unpack_archive(context.path, extract_dir=local_data_dir)

        # list images in directory
        images_names = []
        images_paths = []
        for file in os.listdir(local_data_dir):
            file_path = os.path.join(local_data_dir, file)
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
{"message": "Application PID is 19325", "timestamp": "2023-05-10T14:17:57.194Z", "level": "info"}
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 0, "total": 5, "timestamp": "2023-05-10T14:18:01.261Z", "level": "info"}
...
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 5, "total": 5, "timestamp": "2023-05-10T14:18:04.766Z", "level": "info"}
{"message": "Result project: id=21425, name=My Project", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Shutting down [pid argument = 19325]...", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Application has been shut down successfully", "timestamp": "2023-05-10T14:18:05.959Z", "level": "info"}
```

## Step 4. How to run it in Supervisely

Submitting an app to the Supervisely Ecosystem isn’t as simple as pushing code to github repository, but it’s not as complicated as you may think of it either.

Please follow this [link](https://developer.supervisely.com/app-development/basics/add-private-app) for instructions on adding your app. We have produced a step-by-step guide on how to add your application to the Supervisely Ecosystem.

![Release custom import app]()
