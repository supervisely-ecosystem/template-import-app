import os
import shutil

import supervisely as sly
from dotenv import load_dotenv
from tqdm import tqdm

# load ENV variables for debug, has no effect in production
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))


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

        # get working directory path (specified in local.env)
        work_dir = sly.app.get_data_dir()

        # link to demo data
        link = "https://github.com/supervisely-ecosystem/template-import-app/releases/download/v0.0.1/demo_data.zip"

        # save path for data
        archive_path = os.path.join(work_dir, "demo_data.zip")

        # download file from link
        try:
            sly.fs.download(url=link, save_path=archive_path)
        except Exception as e:
            sly.logger.error(
                "Couldn't download file from link", extra={"link": link, "reason": repr(e)}
            )
            raise e

        # unpack and remove downloaded archive
        shutil.unpack_archive(archive_path, extract_dir=work_dir)
        sly.fs.silent_remove(archive_path)

        # list images in directory and upload them to Supervisely
        images_paths = [os.path.join(work_dir, image_path) for image_path in os.listdir(work_dir)]
        with tqdm(total=len(images_paths)) as pbar:
            for img_path in images_paths:
                try:
                    img_name = sly.fs.get_file_name_with_ext(img_path)
                    # upload image to dataset on Supervisely server
                    info = api.image.upload_path(dataset_id, img_name, img_path)
                    sly.logger.trace(f"Image has been uploaded: id={info.id}, name={info.name}")
                    os.remove(img_path)
                except Exception as e:
                    sly.logger.warn("Skip image", extra={"path": img_path, "reason": repr(e)})
                finally:
                    # remove local file after upload
                    pbar.update(1)

        return project_id


app = MyImport()
app.run()
