import logging
import os
from numbers import Number
from time import sleep

import click
import gphoto2 as gp
from progressbar import progressbar, streams


class BracketingRunner:
    camera: gp.Camera
    context: gp.Context

    "Number of images that will be created"
    n_images: int

    "List of images created during focus bracketing. They are stored on the camera and can be downloaded."
    file_paths = list()

    "Number of steps the focus motor will perform between two images"
    focus_drive_step: int

    def __init__(self, focus_drive_step: int, n_images: int, out_dir: str):
        # params
        self.focus_drive_step = focus_drive_step
        self.n_images = n_images
        self.out_dir = out_dir

        self.connect()
        self.configure()

    def connect(self):
        logging.info("Connecting to camera")
        self.context = gp.gp_context_new()
        self.camera = gp.Camera()
        self.camera.init()

    def configure(self):
        """
        Sets the camera parameters such that the focus bracketing can be performed

        this includes
        - preview mode (flips the mirror)
        - manual focus

        Furthermore, the camera will store the images directly on the memory card to reduce latency.

        """

        logging.info("Configuring camera")
        cfg = self.camera.get_config()

        viewfinder_config = cfg.get_child_by_name('viewfinder')
        viewfinder_config.set_value(1)

        # set-config /main/capturesettings/focusmode2=MF
        focus_mode_config = cfg.get_child_by_name('focusmode2')
        # TODO focus_mode_config.set_value("MF")

        # set-config /main/capturesettings/liveviewaffocus=Single-servo AF
        focus_config = cfg.get_child_by_name('liveviewaffocus')
        focus_config.set_value("Single-servo AF")

        # store images on SD card
        capture_target = cfg.get_child_by_name('capturetarget')
        capture_target.set_value("Memory card")

        self.camera.set_config(cfg)

    def perform_focus_step(self):
        """
        The focus is shifted by applying a fixed number of focus steps.

        :param step:
        :return:
        """

        assert isinstance(self.focus_drive_step, Number)

        cfg = self.camera.get_config()
        # set-config /main/actions/manualfocusdrive 10
        focus_drive_config = cfg.get_child_by_name('manualfocusdrive')
        focus_drive_config.set_value(self.focus_drive_step)
        self.camera.set_config(cfg)

    def perform_focus_bracketing(self):
        logging.info("Performing focus bracketing")

        self.file_paths.clear()

        logging.info("Waiting 5 minutes to reduce vibration")
        sleep(5*60.)

        for _ in progressbar(range(self.n_images)):
            self.perform_focus_step()
            file_path = gp.check_result(
                gp.gp_camera_capture(
                    self.camera,
                    gp.GP_CAPTURE_IMAGE,
                    self.context,
                ))
            self.file_paths.append(file_path)

    def download_images(self):
        for file_path in self.file_paths:
            # print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
            target = os.path.join(self.out_dir, file_path.name)
            logging.info(f"Copying image to {target}")
            camera_file = gp.check_result(
                gp.gp_camera_file_get(
                    self.camera,
                    file_path.folder,
                    file_path.name,
                    gp.GP_FILE_TYPE_NORMAL,
                ))

            gp.check_result(gp.gp_file_save(camera_file, target))

        self.file_paths.clear()

    def __del__(self):
        logging.info("Closing camera")
        gp.gp_camera_exit(self.camera)


@click.command()
@click.option("-o", "--out-dir", type=click.Path(exists=True), required=True)
@click.option("--images", 'n_images', type=int, default=100)
@click.option("--focus_drive_step", type=int, default=10)
def main(out_dir, n_images, focus_drive_step):
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
    streams.flush()
    gp.check_result(gp.use_python_logging())

    bracketing = BracketingRunner(
        focus_drive_step=focus_drive_step,
        n_images=n_images,
        out_dir=out_dir,
    )

    bracketing.perform_focus_bracketing()
    bracketing.download_images()


if __name__ == "__main__":
    main()
