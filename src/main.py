import os
import shutil
from pathlib import Path

import requests
import supervisely as sly
from dotenv import load_dotenv

# load ENV variables for debug, has no effect in production
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))


def process_folder(path_to_folder):
    # list images in directory
    images_names = []
    images_paths = []
    for file in os.listdir(path_to_folder):
        file_path = os.path.join(path_to_folder, file)
        images_names.append(file)
        images_paths.append(file_path)
    return images_names, images_paths


def process_archive(path_to_archive):
    local_data_dir = os.path.join(sly.app.get_data_dir(), sly.fs.get_file_name(path_to_archive))
    shutil.unpack_archive(path_to_archive, extract_dir=local_data_dir)
    images_names, images_paths = process_folder(local_data_dir)
    return images_names, images_paths


def process_text_file(path_to_file, progress):
    # read input file, remove empty lines + leading & trailing whitespaces
    with open(path_to_file) as file:
        lines = [line.strip() for line in file.readlines() if line.strip()]

    # process text file and download links
    images_names, images_paths = [], []
    with progress(total=len(lines)) as pbar:
        for index, img_url in enumerate(lines):
            try:
                img_ext = Path(img_url).suffix
                img_name = f"{index:03d}{img_ext}"
                img_path = os.path.join(sly.app.get_data_dir(), img_name)
                # download image
                response = requests.get(img_url)
                with open(img_path, "wb") as file:
                    file.write(response.content)

                images_names.append(img_name)
                images_paths.append(img_path)
            except Exception as e:
                sly.logger.warn("Skip image", extra={"url": img_url, "reason": repr(e)})
            finally:
                pbar.update(1)
    return images_names, images_paths


def upload_images(api, dataset_id, images_names, images_paths, progress):
    # process images and upload them by paths
    with progress(total=len(images_paths)) as pbar:
        for img_name, img_path in zip(images_names, images_paths):
            try:
                # upload image into dataset on Supervisely server
                info = api.image.upload_path(dataset_id=dataset_id, name=img_name, path=img_path)
                sly.logger.trace(f"Image has been uploaded: id={info.id}, name={info.name}")
            except Exception as e:
                sly.logger.warn("Skip image", extra={"name": img_name, "reason": repr(e)})
            finally:
                pbar.update(1)


class MyImport(sly.app.Import):
    # def generate_custom_settings(self):
    #   custom_checkbox = sly.app.widgets.Checkbox("my_checkbox")
    #   return sly.app.widgets.Container(widgets=[custom_checkbox])

    def process(self, context: sly.app.Import.Context):
        # create api object to communicate with Supervisely Server
        api = sly.Api.from_env()

        # get or create project
        project_id = context.project_id
        if project_id is None:
            project = api.project.create(
                workspace_id=context.workspace_id,
                name=context.project_name or "My Project",
                change_name_if_conflict=True,
            )
            project_id = project.id

        # get or create dataset
        dataset_id = context.dataset_id
        if dataset_id is None:
            dataset = api.dataset.create(
                project_id=project_id, name="ds0", change_name_if_conflict=True
            )
            dataset_id = dataset.id

        if context.is_directory:
            images_names, images_paths = process_folder(context.path)
        elif context.is_archive:
            images_names, images_paths = process_archive(context.path)
        elif context.is_text_file:
            images_names, images_paths = process_text_file(context.path)
        upload_images(api, dataset_id, images_names, images_paths, context.progress)
        return project_id


app = MyImport()
app.run()
