import os
import supervisely as sly
from dotenv import load_dotenv
from tqdm import tqdm

from supervisely.app.widgets import (
    Button,
    Input,
    Checkbox,
    TeamFilesSelector,
    ProjectThumbnail,
    Text,
    Card,
    SelectWorkspace,
    Container,
    SlyTqdm,
)

from supervisely.app import DialogWindowError

# load ENV variables for debug, has no effect in production
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

# create api object to communicate with Supervisely Server
api = sly.Api.from_env()

# get current context of import
TASK_ID = sly.env.task_id(raise_not_found=False)
TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
PATH_TO_FOLDER = sly.env.folder(raise_not_found=False)
IS_PRODUCTION = sly.is_production()
STORAGE_DIR = sly.app.get_data_dir()


# Method to process folder with images and upload them to Supervisely server
def process_import(local_data_dir):
    images_names = []
    images_paths = []
    for file in os.listdir(local_data_dir):
        file_path = os.path.join(local_data_dir, file)
        images_names.append(file)
        images_paths.append(file_path)

    with SlyTqdm(total=len(images_paths)) as pbar:
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
    res_project = api.project.get_info_by_id(project.id)
    return res_project


# create GUI
if IS_PRODUCTION is True:
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
    remove_source_files = Checkbox("Remove source files after successful import", value=True)
    settings_card = Card(
        title="Settings", description="Select import settings", content=remove_source_files
    )

    # Step 3: Create Project
    ws_selector = SelectWorkspace(default_id=WORKSPACE_ID, team_id=TEAM_ID)
    project_name = Input(value="My Project")
    project_creator = Container(widgets=[ws_selector, project_name])
    project_card = Card(
        title="Create Project",
        description="Select destination team, workspace and enter project name",
        content=project_creator,
    )

    # Step 4: Output
    start_import_btn = Button(text="Start Import")
    output_project_thumbnail = ProjectThumbnail()
    output_project_thumbnail.hide()
    output_text = Text()
    output_text.hide()
    output_progress = SlyTqdm()
    output_progress.hide()
    output_container = Container(
        widgets=[output_project_thumbnail, output_text, output_progress, start_import_btn]
    )
    output_card = Card(
        title="Output", description="Press button to start import", content=output_container
    )

    # create app object
    layout = Container(widgets=[data_card, settings_card, project_card, output_card])
    app = sly.Application(layout=layout)

    @start_import_btn.click
    def start_import():
        # download folder from Supervisely Team Files to local storage if debugging in production mode
        PATH_TO_FOLDER = tf_selector.get_selected_paths()
        if PATH_TO_FOLDER is not None:
            # specify local path to download
            local_data_path = os.path.join(STORAGE_DIR, os.path.basename(PATH_TO_FOLDER))
            # download file from Supervisely Team Files to local storage
            api.file.download_directory(
                team_id=TEAM_ID, remote_path=PATH_TO_FOLDER, local_save_path=local_data_path
            )
        else:
            raise DialogWindowError(
                title="",
                description="Please, specify path to folder or file in Supervisely Team Files.",
            )

        res_project = process_import(local_data_path)
        # remove local storage directory with files
        sly.fs.remove_dir(STORAGE_DIR)

        # remove source files from Supervisely Team Files if checked
        if remove_source_files.is_checked():
            api.file.remove_dir(TEAM_ID, PATH_TO_FOLDER)

        # set output project after successful import
        api.task.set_output_project(
            task_id=TASK_ID, project_id=res_project.id, project_name=res_project.name
        )
        sly.logger.info(f"Result project: id={res_project.id}, name={res_project.name}")

        # stop app
        app.shutdown()


# if debugging in local mode
if IS_PRODUCTION is False:
    app = sly.Application()
    # get project and dataset info or create new ones if not specified initially
    project = api.project.create(
        workspace_id=WORKSPACE_ID, name="My Project", change_name_if_conflict=True
    )
    dataset = api.dataset.create(project_id=project.id, name="ds0", change_name_if_conflict=True)

    if PATH_TO_FOLDER is None:
        raise ValueError("Please, specify path to folder in local storage.")

    res_project = process_import(PATH_TO_FOLDER)
    sly.logger.info(f"Result project: id={res_project.id}, name={res_project.name}")
    app.shutdown()
