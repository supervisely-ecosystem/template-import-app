import os

import supervisely as sly
from dotenv import load_dotenv
from tqdm import tqdm

# load ENV variables for debug, has no effect in production
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))


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


app = MyImport()
app.run()
