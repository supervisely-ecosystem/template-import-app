# Custom Import

This guide provides an overview of the custom import template and describes the various import scenarios it can cover. The import template is designed to speed up and simplify development of import apps.

## More details about `sly.app.Import`

💻 [Source code](https://github.com/supervisely/supervisely/blob/master/supervisely/app/import_template.py)

`sly.app.Import` class will handle import routines for you:

- ✅ Check that selected team, workspace, project or dataset exist and that you have access to it
- ⬇️ Download your data from Supervisely platform to remote container or local hard drive if you are debugging your app
- 🪄 Automatically detects app context with all required information for creating import app
- ⬆️ Upload your result data to new or existing Supervisely project
- 🧹 Remove source directory from Team Files after successful import
- 🖼️ Show your project on Supervisely platform workspace tasks page

`sly.app.Import` has a `Context` subclass which contains all required information that you need for importing your data from Supervisely platform:

- `Team ID` - shows team id where your data is located
- `Workspace ID` - shows workspace id where your project is located (if `Project ID` is specified) or will be created
- `Project ID` - id of existing project to which data will be imported. None if you import data to new project
- `Dataset ID` - id of existing dataset to which data will be imported. None if you import data to new dataset
- `Path` - path to your data on local machine. None if you import data from external link
- `Is directory` - shows if your data is a directory or file
- `Is on agent` - shows if your data is located on agent or not

`context` variable is passed as an argument to `process` method of class `MyImport` and `context` object will be created automatically when you execute import script.

```python
class MyImport(sly.app.Import):
    def process(self, context: sly.app.Import.Context):
        print(context)
```

Output:

```text
Team ID: 8
Workspace ID: 349
Project ID: 8534
Dataset ID: 22852
Path: /data/my_file.txt
Is directory: False
Is on agent: False
```

If you want to download external data, you should reimplement method `is_path_required` and return `False`:

```python
    def is_path_required(self) -> bool:
        return False
```

## Import Scenarios

The custom import template supports the following import scenarios:

1. [Import without template](/tutorials/import-from-scratch.md): this scenario allows for importing data without applying import template. It provides a basic import functionality where the data is imported using basic methods from Supervisely SDK.

2. [Import from a text file](/tutorials/import-text-file.md): With this scenario, you can import data using a data from text files in various formats like `.csv`, `.txt`, `.xml`, `.yaml`, `.json` from Supervisely Team Files. Assuming text file contains a link to an image, bitmap, numpy array, or bytes.

3. [Import from an archive](/tutorials/import-archive.md): this scenario describes importing data using an archive from Supervisely Team Files. The data can be in various formats, such as `.zip` or `.tar`. The import template engine will download the data and pass the path to the archive to `sly.app.Import.Context`.

4. [Import from a folder](/tutorials/import-folder.md): in this scenario, you can import data using a folder. The import template engine will download specified folder and pass the path to the folder with data to `sly.app.Import.Context`.

5. [Import from an agent folder](/tutorials/import-agent.md): this scenario involves importing data using a folder stored on an agent. The import template engine will download specified folder from the agent and pass the path to the folder with data to `sly.app.Import.Context`.

6. [Import from an external link](/tutorials/import-external-link.md): with this scenario, you can import data hosted externally (Not on Supervisely instance). In this case you will need to implement downloading part on your own.

7. [Import with template using a graphical user interface (GUI)](/tutorials/import-gui.md): This scenario provides a user-friendly graphical interface for importing your data. The GUI allows users to select the desired folder or archive from Team Files or Drag & Drop option and configure import settings easily. It simplifies the import process and provides an intuitive experience for users.

## Set up an environment for development

We advise reading our [from script to supervisely app](../basics/from-script-to-supervisely-app.md) guide if you are unfamiliar with the [file structure](../basics/from-script-to-supervisely-app.md#repository-structure) of a Supervisely app repository because it addresses the majority of the potential questions.

**For both options, you need to prepare a development environment. Follow the steps below:**

**Step 1.** Prepare `~/supervisely.env` file with credentials. [Learn more here.](../../getting-started/basics-of-authentication.md#how-to-use-in-python)

**Step 2.** Fork and clone [repository](https://github.com/supervisely-ecosystem/template-import-app) with source code and create [Virtual Environment](https://docs.python.org/3/library/venv.html).

```bash
git clone https://github.com/supervisely-ecosystem/template-import-app
cd template-import-app
./create_venv.sh
```

**Step 3.** Open repository directory in Visual Studio Code.

```bash
code -r .
```

**Step 4.** Select created virtual environment as python interpreter.

**Step 5.** Open `local.env` and insert your values here. Learn more about environment variables in our [guide](../../getting-started/environment-variables.md)

```python
TASK_ID=33572                 # ⬅️ requires to use advanced debugging, comment for local debugging
TEAM_ID=8                     # ⬅️ change it to your team ID
WORKSPACE_ID=349              # ⬅️ change it to your workspace ID
PROJECT_ID=18334              # ⬅️ ID of the project where your data will be imported (optional)
DATASET_ID=66325              # ⬅️ ID of the dataset where your data will be imported (optional)
SLY_APP_DATA_DIR="results/"   # ⬅️ path to directory for local debugging

# Specify only one of the following variables
FILE="/data/my_file.txt"      # ⬅️ name of the file that will be imported
# FOLDER="/data/my_folder/"   # ⬅️ name of the folder that will be imported
```

Please note that the path you specify in the `SLY_APP_DATA_DIR` variable will be used for saving application results and temporary files (temporary files will be removed at the end).

For example:
- path on your local computer could be `/Users/admin/Downloads/`
- path in the current project folder on your local computer could be `results/`

> Don't forget to add this path to `.gitignore` to exclude it from the list of files tracked by Git.

![Change variables in local.env](https://user-images.githubusercontent.com/79905215/236182190-3438d72e-919f-4a8f-9544-a105e8441a5a.gif)

When running the app from Supervisely platform: Project and Dataset IDs will be automatically detected depending on how you run your application.

## How to debug import template

In this tutorial, we will be using the **Run & Debug** section of the VSCode to debug import app.

Import template has 2 launch options for debugging: `Debug` and `Advanced Debug`.
The settings for these options are configured in the `launch.json` file.

![launch.json](https://github.com/supervisely/developer-portal/assets/79905215/3afd0096-7b66-4462-9fc0-f7098d18fc25)

### 1 - `Debug`

This option is a good starting point. In this case app will import data stored on your local drive, you should provide path to data in `local.env`. Path can be relative from project root or absolute.

```python
FILE="data/my_project.txt"   # ⬅️ path to file that you want to import
# FOLDER=                    # ⬅️ you can specify only one entity: file or folder  
```

Data will be uploaded to specified project or dataset on Supervisely platform, but source folder will not be removed and task will not appear on workspace tasks page.

![Debug]()

Output of this python program:

```text
Processing: 100%|███████████████████████████████████████████████████████████████████| 5/5 [00:10<00:00,  2.03s/it]
```

### 2 - `Advanced Debug`

This option is useful for final testing and debugging. In this case, data will be downloaded from Supervisely instance Team Files and uploaded to specified project or dataset on Supervisely platform, source folder will be removed if specified.

The path you need to specify should lead to a folder or file in Supervisely Team Files. All paths in Team Files start with the "/" symbol. You can find the path to the desired folder or file in the Team Files interface.

```python
FILE="/data/my_project.txt"   # ⬅️ path to file that you want to import
# FOLDER="/data/my_project/   # ⬅️ you can specify only one entity: file or folder  
```

![Advanced Debug]()

Output of this python program:

```text
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 0, "total": 5, "timestamp": "2023-05-09T18:08:54.444Z", "level": "info"}
...
{"message": "progress", "event_type": "EventType.PROGRESS", "subtask": "Processing", "current": 5, "total": 5, "timestamp": "2023-05-09T18:09:04.705Z", "level": "info"}
{"message": "Source directory: '/data/my_project.txt' was successfully removed.", "timestamp": "2023-05-09T18:09:05.849Z", "level": "info"}
{"message": "Result project: id=21357, name=My Project", "timestamp": "2023-05-09T18:09:05.850Z", "level": "info"}
```

## How to run it in Supervisely

Submitting an app to the Supervisely Ecosystem isn’t as simple as pushing code to github repository, but it’s not as complicated as you may think of it either.

Please follow this [link](https://developer.supervisely.com/app-development/basics/add-private-app) for instructions on adding your app. We have produced a step-by-step guide on how to add your application to the Supervisely Ecosystem.
