import gphoto2 as gp
import logging
import os
from numbers import Number


class BracketingRunner(object):
    camera: gp.Camera = None
    context: gp.Context = None

    "Number of images that will be created"
    n_images: int = 20

    "List of images created during focus bracketing. They are stored on the camera and can be downloaded."
    file_paths = list()

    def __init__(self):
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

    def perform_focus_step(self, step=50):
        """
        The focus is shifted by applying a fixed number of focus steps.

        :param step:
        :return:
        """

        assert isinstance(step, Number)

        cfg = self.camera.get_config()
        # set-config /main/actions/manualfocusdrive 10
        focus_drive_config = cfg.get_child_by_name('manualfocusdrive')
        focus_drive_config.set_value(step)
        self.camera.set_config(cfg)

    def perform_focus_bracketing(self):
        logging.info("Performing focus bracketing")

        self.file_paths.clear()

        for _ in range(self.n_images):
            self.perform_focus_step()
            file_path = gp.check_result(gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, self.context))
            self.file_paths.append(file_path)

    def download_images(self, path='/tmp'):
        for file_path in self.file_paths:
            # print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
            target = os.path.join(path, file_path.name)
            logging.info('Copying image to', target)
            camera_file = gp.check_result(gp.gp_camera_file_get(
                self.camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))
            gp.check_result(gp.gp_file_save(camera_file, target))

        self.file_paths.clear()

    def __del__(self):
        logging.info("Closing camera")
        gp.gp_camera_exit(self.camera)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
    callback_obj = gp.check_result(gp.use_python_logging())

    bracketing = BracketingRunner()
    bracketing.perform_focus_bracketing()
    bracketing.download_images()
