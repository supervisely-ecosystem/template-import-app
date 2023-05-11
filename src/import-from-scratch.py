import os

import supervisely as sly
from dotenv import load_dotenv
from tqdm import tqdm

# load ENV variables for debug, has no effect in production
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

# create api object to communicate with Supervisely Server
api = sly.Api.from_env()

# create app object
app = sly.Application()

# get current context of import
TASK_ID = sly.env.task_id(raise_not_found=False)
TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
PROJECT_ID = sly.env.project_id(raise_not_found=False)
DATASET_ID = sly.env.dataset_id(raise_not_found=False)
PATH_TO_FOLDER = sly.env.folder()
REMOVE_SOURCE_FILES = sly.env.remove_source_files()
IS_PRODUCTION = sly.is_production()
STORAGE_DIR = sly.app.get_data_dir()

# get project and dataset info or create new ones if not specified
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

# download folder from Supervisely Team Files to local storage if debugging in production mode
if IS_PRODUCTION is True:
    # specify local path to download
    local_folder_path = os.path.join(STORAGE_DIR, os.path.basename(PATH_TO_FOLDER))
    # download file from Supervisely Team Files to local storage
    api.file.download_directory(
        team_id=TEAM_ID, remote_path=PATH_TO_FOLDER, local_save_path=local_folder_path
    )
else:
    local_folder_path = PATH_TO_FOLDER

# list images in directory
images_names = []
images_paths = []
for file in os.listdir(local_folder_path):
    file_path = os.path.join(local_folder_path, file)
    images_names.append(file)
    images_paths.append(file_path)

# process images and upload them by paths
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

# remove local storage directory with files
sly.fs.remove_dir(STORAGE_DIR)

if IS_PRODUCTION is True:
    info = api.project.get_info_by_id(project.id)
    api.task.set_output_project(task_id=TASK_ID, project_id=info.id, project_name=info.name)
    # remove source files from Supervisely Team Files after successful import
    if REMOVE_SOURCE_FILES is True:
        api.file.remove(team_id=TEAM_ID, path=PATH_TO_FOLDER)
        sly.fs.remove_dir(PATH_TO_FOLDER)
        sly.logger.info(msg=f"Source directory: '{PATH_TO_FOLDER}' was successfully removed.")
    sly.logger.info(f"Result project: id={info.id}, name={info.name}")

# stop app
app.shutdown()
