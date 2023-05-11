import os
from pathlib import Path

import requests
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


app = MyImport()
app.run()
