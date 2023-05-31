---
description: >-
  A step-by-step tutorial of how to create custom import app without using template from SDK (from scratch).
---

# Create import app from scratch (without import template from SDK)

## Introduction

We recommend to use import template for creating custom import applications using class `sly.app.Import` from Supervisely SDK.
However, if your use case is not covered by our import template, you can create your own app **from scratch**  without the template using basic methods from Supervisely SDK.

In this tutorial, we will create a simple import app with GUI that will upload images from a folder to Supervisely with a following structure:

```text
my_folder
├── cat_1.jpg
├── cat_2.jpg
└── cat_3.jpg
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
TEAM_ID=8                     # ⬅️ change it to your team ID
WORKSPACE_ID=349              # ⬅️ change it to your workspace ID
SLY_APP_DATA_DIR="results/"   # ⬅️ path to directory for advanced debug (your data will be downloaded to this directory)

FOLDER="data/my_folder"       # ⬅️ path to directory with data on local machine
```

## Step 2. How to write an import script

Find source code for this example [here](https://github.com/supervisely-ecosystem/template-import-app/blob/master/src/import-from-scratch.py)

**Step 1. Import libraries**

```python
import os

import supervisely as sly
from dotenv import load_dotenv
from supervisely.app import DialogWindowError
from supervisely.app.widgets import (
    Button,
    Card,
    Checkbox,
    Container,
    Input,
    ProjectThumbnail,
    SelectWorkspace,
    SlyTqdm,
    TeamFilesSelector,
    Text,
)
from tqdm import tqdm
```

**Step 2. Load environment variables**

Load ENV variables for debug, has no effect in production.

```python
IS_PRODUCTION = sly.is_production()
if IS_PRODUCTION is True:
    load_dotenv("local.env")
else:
    load_dotenv("advanced.env")

load_dotenv(os.path.expanduser("~/supervisely.env"))

# Get ENV variables
TASK_ID = sly.env.task_id(raise_not_found=False)
TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
PATH_TO_FOLDER = sly.env.folder(raise_not_found=False)
STORAGE_DIR = sly.app.get_data_dir()
```

**Step 3. Initialize API object**

Create API object to communicate with Supervisely Server. Loads from `supervisely.env` file

```python
api = sly.Api.from_env()
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

**Step 5. Write code for local debugging**

1. Check if we are in debug mode (`IS_PRODUCTION = False`) and create `app` object.
2. Create project and dataset.
3. Check that `PATH_TO_FOLDER` is not empty.
4. Create `progress` object for tqdm.
5. Call `process_import` function (See **Step 8** below).
6. Print result project.

```python
if IS_PRODUCTION is False:
    app = sly.Application()
    project = api.project.create(
        workspace_id=WORKSPACE_ID,
        name="My Project",
        change_name_if_conflict=True
    )
    dataset = api.dataset.create(
        project_id=project.id,
        name="ds0",
        change_name_if_conflict=True
    )
    if PATH_TO_FOLDER is None:
        raise ValueError("Please, specify path to folder in local.env file")

    progress = tqdm
    res_project = process_import(PATH_TO_FOLDER, project.id, dataset.id, progress)
    sly.logger.info(f"Result project: id={res_project.id}, name={res_project.name}")
```

**Step 6. Create GUI app**

In this step we will build GUI for our import app using [Supervisely widgets](https://developer.supervisely.com/app-development/widgets).

We will breakdown our GUI into 4 steps:

1. File selector to select folder with data.
2. Import settings.
3. Destination project settings.
4. Output card with button to start import and info about result project.

Let's take a closer look at each step:

1. Create FileSelector widget to select folder with data and place it into Card widget.
2. Create Checkbox widget to select if we want to remove source files after successful import and place it into Card widget.
3. Create workspace selector and input widget to enter project name. Combine those widgets into Container widget and place it into Card widget. Using workspace selector we can select team and workspace where we want to create project in which data will be imported.
4. Create Button widget to start import process.
5. Create output text to show warnings and info messages.
6. Create progress widget to show progress of import process.
7. Create ProjectThumbnail to show result project with link to it.
8. Combine all button, output text, progress and project thumbnail .
9. Create layout by combining all created cards into one container.
10. Initialize app object with layout as a parameter.

```python
else:
    # Create GUI
    # Step 1: Import Data
    tf_selector = TeamFilesSelector(
        team_id=TEAM_ID, multiple_selection=False, max_height=300, selection_file_type="folder"
    )
    data_card = Card(
        title="Select Data",
        description="Check folder or file in File Browser to import it",
        content=tf_selector,
    )

    # Step 2: Settings
    remove_source_files = Checkbox("Remove source files after successful import", checked=True)
    settings_card = Card(
        title="Settings", description="Select import settings", content=remove_source_files
    )

    # Step 3: Create Project
    ws_selector = SelectWorkspace(default_id=WORKSPACE_ID, team_id=TEAM_ID)
    output_project_name = Input(value="My Project")
    project_creator = Container(widgets=[ws_selector, output_project_name])
    project_card = Card(
        title="Create Project",
        description="Select destination team, workspace and enter project name",
        content=project_creator,
    )

    # Step 4: Output
    start_import_btn = Button(text="Start Import")
    output_text = Text()
    output_text.hide()
    output_progress = SlyTqdm()
    output_progress.hide()
    output_project_thumbnail = ProjectThumbnail()
    output_project_thumbnail.hide()
    output_container = Container(
        widgets=[output_project_thumbnail, output_text, output_progress, start_import_btn]
    )
    output_card = Card(
        title="Output", description="Press button to start import", content=output_container
    )

    # Create app object
    layout = Container(widgets=[data_card, settings_card, project_card, output_card])
    app = sly.Application(layout=layout)

    @start_import_btn.click
    def start_import():
        ...
```

**Step 7. Add button click handler to start import process**

In this step we will create button click handler.
We will get state of all widgets and call `process_import` function (See **Step 8** below).

```python
 @start_import_btn.click
 def start_import():
     try:
        # Lock Cards to prevent changing settings during import
        data_card.lock()
        settings_card.lock()
        project_card.lock()
        output_text.hide()

        # Get project name from input widget
        project_name = output_project_name.get_value()
        if project_name is None or project_name == "":
            output_text.set(text="Please, enter project name", status="error")
            output_text.show()
            return

        # Get remote path to folder from FileSelector widget
        PATH_TO_FOLDER = tf_selector.get_selected_paths()
        if len(PATH_TO_FOLDER) > 0:
            PATH_TO_FOLDER = PATH_TO_FOLDER[0]
            # Specify local path to download
            local_data_path = os.path.join(
                STORAGE_DIR, os.path.basename(PATH_TO_FOLDER)
            )
            # Download file from Supervisely Team Files to local storage
            api.file.download_directory(
                team_id=TEAM_ID, remote_path=PATH_TO_FOLDER, local_save_path=local_data_path
            )
        else:
            # If folder is not selected, show error message
            output_text.set(
                text="Please, specify path to folder in Supervisely Team Files", status="error"
            )
            output_text.show()
            return

        # Create project and dataset
        project = api.project.create(
            workspace_id=WORKSPACE_ID, name=project_name, change_name_if_conflict=True
        )
        dataset = api.dataset.create(
            project_id=project.id, name="ds0", change_name_if_conflict=True
        )

        # Show import progress
        output_progress.show()

        # Read data from local storage and import it to project
        res_project = process_import(local_data_path, project.id, dataset.id, output_progress)

        # Remove source files from Supervisely Team Files if option is checked
        if remove_source_files.is_checked():
            api.file.remove_dir(TEAM_ID, PATH_TO_FOLDER)

         # Set output project after successful import
         api.task.set_output_project(
             task_id=TASK_ID, project_id=res_project.id, project_name=res_project.name
         )

         # Hide progress after successful import
         output_progress.hide()

         # Show result project with info message
         output_project_thumbnail.set(info=res_project)
         output_project_thumbnail.show()
         output_text.set(text="Import is finished", status="success")
         output_text.show()
         
         # Disable button after successful import
         start_import_btn.disable()

         # Log result project
         sly.logger.info(f"Result project: id={res_project.id}, name={res_project.name}")
     except Exception as e:
         data_card.unlock()
         settings_card.unlock()
         project_card.unlock()
         raise DialogWindowError(title="Import error", description=f"Error: {e}")
```

**Step 8. Process import function**

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
