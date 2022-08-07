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

    def __init__(self, focus_drive_step: int, n_images: int, out_dir: str, stabilization_time: int):
        # params
        self.focus_drive_step = focus_drive_step
        self.n_images = n_images
        self.out_dir = out_dir
        self.stabilization_time = stabilization_time

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
        model_f = -1
        model = self.camera.get_abilities().model
        print(model)
        model_f = model.find("Nikon DSC") # "D850"

        logging.info("Configuring camera")
        cfg = self.camera.get_config()
        try:
            viewfinder_config = cfg.get_child_by_name('viewfinder')
            viewfinder_config.set_value(1)
        except gp.GPhoto2Error:
            pass
        for cfg_child in cfg.get_children():
            if cfg_child.get_name() == 'focusmode2':
                self.camera_type = 'dslr'
                # set-config /main/capturesettings/focusmode2=MF
                focus_mode_config = cfg.get_child_by_name('focusmode2')
                # TODO focus_mode_config.set_value("MF")
                
                # set-config /main/capturesettings/liveviewaffocus=Single-servo AF
                focus_config = cfg.get_child_by_name('liveviewaffocus')
                focus_config.set_value("Single-servo AF")

                # store images on SD card
                capture_target = cfg.get_child_by_name('capturetarget')
                capture_target.set_value("Memory card")
                break
            elif cfg_child.get_name() == 'capturesettings':
                self.camera_type = 'sony_e'  # Sony e-mount (eg A7C)
                # TODO start with autofocus?
                focus_config = cfg.get_child_by_name('capturesettings').get_child_by_name('focusmode')
                focus_config.set_value('Manual')
                
                capture_target = cfg.get_child_by_name('settings').get_child_by_name('capturetarget')
                capture_target.set_value("card")
                
                if model_f != -1:
                    self.camera_type = 'nikon_e'
                    focus_config = cfg.get_child_by_name('liveviewaffocus')
                    focus_config.set_value("Single-servo AF")
                    
                    capture_target = cfg.get_child_by_name('capturetarget')
                    capture_target.set_value("Memory card")
                
                break
        else:
            raise(NotImplementedError('Manual focus for this type of camera'))

        self.camera.set_config(cfg)

    def perform_focus_step(self):
        """
        The focus is shifted by applying a fixed number of focus steps.

        :param step:
        :return:
        """

        assert isinstance(self.focus_drive_step, Number)

        cfg = self.camera.get_config()
        if self.camera_type == 'dslr':
            # set-config /main/actions/manualfocusdrive 10
            focus_drive_config = cfg.get_child_by_name('manualfocusdrive')
        elif self.camera_type == 'sony_e':
            focus_drive_config = cfg.get_child_by_name('actions').get_child_by_name('manualfocus')
        elif self.camera_type == 'nikon_e':
            focus_drive_config = cfg.get_child_by_name('manualfocusdrive')    
        focus_drive_config.set_value(self.focus_drive_step)
        self.camera.set_config(cfg)

    def perform_focus_bracketing(self):
        logging.info("Performing focus bracketing")

        self.file_paths.clear()

        logging.info(f"Waiting {self.stabilization_time} seconds to reduce vibration")
        sleep(self.stabilization_time)

        for _ in progressbar(range(self.n_images)):
            self.perform_focus_step()
            try:
                proc_status = gp.gp_camera_capture(
                        self.camera,
                        gp.GP_CAPTURE_IMAGE,
                        self.context,
                )
                file_path = gp.check_result(proc_status)
                self.file_paths.append(file_path)
            except gp.GPhoto2Error as e:
                print(f'perform_focus_bracketing warning: something went wrong: {e}')


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
@click.option("-n", "--images", 'n_images', type=int, default=100, help='Number of images to capture')
@click.option("-s", "--focus_drive_step", type=int, default=5, help='Focus step between shots')
@click.option("--stabilization_time", type=float, default=5*60, help='Waiting time before start')
def main(out_dir, n_images, focus_drive_step, stabilization_time):
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
    streams.flush()
    gp.check_result(gp.use_python_logging())

    bracketing = BracketingRunner(
        focus_drive_step=focus_drive_step,
        n_images=n_images,
        out_dir=out_dir,
        stabilization_time=stabilization_time
    )

    bracketing.perform_focus_bracketing()
    bracketing.download_images()


if __name__ == "__main__":
    main()
