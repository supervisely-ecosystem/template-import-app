---
description: >-
  A step-by-step tutorial of how to use import template to import data from text file.
---

# Import data from text file

## Introduction

In this tutorial, we will create an import app that will upload images from a text file to Supervisely using import app template from SDK with a following structure:

**my_file.txt:**

```text
https://github.com/supervisely-ecosystem/demo-data-for-import-template/releases/download/images/pexels-couleur-2317904.jpg
https://github.com/supervisely-ecosystem/demo-data-for-import-template/releases/download/images/pexels-kammeran-gonzalezkeola-7925859.jpg
https://github.com/supervisely-ecosystem/demo-data-for-import-template/releases/download/images/pexels-stijn-dijkstra-7177188.jpg
https://github.com/supervisely-ecosystem/demo-data-for-import-template/releases/download/images/pexels-taryn-elliott-3889728.jpg
https://github.com/supervisely-ecosystem/demo-data-for-import-template/releases/download/images/pexels-taryn-elliott-9565787.jpg
```

You can find the above demo file in the data directory of the template-import-app repo - [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/data/)

We will go through the following steps:

[**Step 1.**](#step-1-how-to-debug-import-app) How to debug import app.

[**Step 2**](#step-2-how-to-write-an-import-script) How to write an import script.

[**Step 3.**](#step-3-advanced-debug) Advanced debug.

[**Step 4.**](#step-4-how-to-run-it-in-supervisely) How to run it in Supervisely.

Everything you need to reproduce [this tutorial is on GitHub](https://github.com/supervisely-ecosystem/template-import-app): [source code](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-text-file.py).

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
REMOVE_SOURCE_FILES=False     # ⬅️ remove source files from Team Files after import (optional)
SLY_APP_DATA_DIR="results/"   # ⬅️ path to directory for advanced debug (your data will be downloaded in this directory)

FILE="data/my_file.txt"    # ⬅️ path to file with data on local machine
# FILE="/data/my_archive.zip"   # ⬅️ path to file with data on Supervisely Team Files
```

## Step 2. How to write an import script

Find source code for this example [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-text-file.py)

**Step 1. Import libraries**

```python
import os
from pathlib import Path

import requests
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

        # read input file, remove empty lines + leading & trailing whitespaces
        with open(context.path) as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]

        # process text file and remove empty lines
        with tqdm(total=len(lines)) as pbar:
            for index, img_url in enumerate(lines):
                try:
                    img_ext = Path(img_url).suffix
                    img_name = f"{index:03d}{img_ext}"
                    img_path = os.path.join(sly.app.get_data_dir(), img_name)

                    # download image
                    response = requests.get(img_url)
                    with open(img_path, "wb") as file:
                        file.write(response.content)

                    # upload image into dataset on Supervisely server
                    info = api.image.upload_path(dataset_id, img_name, img_path)
                    sly.logger.trace(f"Image has been uploaded: id={info.id}, name={info.name}")

                    # remove local file after upload
                    os.remove(img_path)
                except Exception as e:
                    sly.logger.warn("Skip image", extra={"url": img_url, "reason": repr(e)})
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
{"message": "Application PID is 19323", "timestamp": "2023-05-10T14:17:57.194Z", "level": "info"}
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 0, "total": 3, "timestamp": "2023-05-10T14:18:01.261Z", "level": "info"}
...
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 5, "total": 5, "timestamp": "2023-05-10T14:18:04.766Z", "level": "info"}
{"message": "Result project: id=21420, name=My Project", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Shutting down [pid argument = 19323]...", "timestamp": "2023-05-10T14:18:05.958Z", "level": "info"}
{"message": "Application has been shut down successfully", "timestamp": "2023-05-10T14:18:05.959Z", "level": "info"}
```

## Step 4. How to run it in Supervisely

Submitting an app to the Supervisely Ecosystem isn’t as simple as pushing code to github repository, but it’s not as complicated as you may think of it either.

Please follow this [link](https://developer.supervisely.com/app-development/basics/add-private-app) for instructions on adding your app. We have produced a step-by-step guide on how to add your application to the Supervisely Ecosystem.

![Release custom import app]()
