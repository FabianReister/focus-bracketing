import gphoto2 as gp
import logging
import os

# https://github.com/jim-easterbrook/python-gphoto2/blob/master/examples/cam-conf-view-gui.py
def get_camera_model(camera_config):
    # get the camera model
    OK, camera_model = gp.gp_widget_get_child_by_name(
        camera_config, 'cameramodel')
    if OK < gp.GP_OK:
        OK, camera_model = gp.gp_widget_get_child_by_name(
            camera_config, 'model')
    if OK >= gp.GP_OK:
        camera_model = camera_model.get_value()
    else:
        camera_model = ''
    return camera_model

class BracketingRunner(object):

    context = None
    camera = None

    def __init__(self):
        self.connect()
        self.configure()

    def connect(self):
        logging.info("Connecting to camera")
        self.context = gp.gp_context_new()
        #self.camera = gp.check_result(gp.gp_camera_new())
        self.camera = gp.Camera()
        self.camera.init()

        camera_config = self.camera.get_config()
        camera_model = get_camera_model(camera_config)
        #gp.put_camera_capture_preview_mirror(self.camera, camera_config, camera_model)

        #gp.check_result(gp.gp_camera_init(self.camera, self.context))
        #text = gp.check_result(gp.gp_camera_get_summary(self.camera, self.context))

        #print(text)

    def configure(self):
        """
        Sets the camera parameters such that the focus bracketing can be executed

        this includes
        - preview mode (flips the mirror)
        - manual focus

        Furthermore, the camera stores the images directly on the memory card to reduce latency. 

        """

        logging.info("Configuring camera")
        #self.config = gp.check_result(gp.gp_camera_get_config(self.camera, self.context))

        # set-config /main/actions/viewfinder=1
        #viewfinder_config = gp.check_result(gp.gp_widget_get_child_by_name(self.config, 'viewfinder'))
        #gp.gp_widget_set_value(viewfinder_config, 1)

        cfg = self.camera.get_config()

        viewfinder_config = cfg.get_child_by_name('viewfinder')
        viewfinder_config.set_value(1)

        # gp.gp_camera_capture_preview(self.camera, self.context)
        #
        # set-config /main/capturesettings/focusmode2=MF
        focus_mode_config = cfg.get_child_by_name('focusmode2')
        #TODO focus_mode_config.set_value("MF")
        #
        #
        # # set-config /main/capturesettings/liveviewaffocus=Single-servo AF
        focus_config = cfg.get_child_by_name('liveviewaffocus')
        focus_config.set_value("Single-servo AF")

        # store images on SD card
        capture_target = cfg.get_child_by_name('capturetarget')
        capture_target.set_value("Memory card")


        self.camera.set_config(cfg)


    def perform_bracketing(self):

        logging.info("Performing bracketing")
        # set-config /main/actions/manualfocusdrive 10



        for i in range(20):
            cfg = self.camera.get_config()
            focus_drive_config = cfg.get_child_by_name('manualfocusdrive')
            focus_drive_config.set_value(50)
            self.camera.set_config(cfg)

            file_path = gp.check_result(gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, self.context))

            print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
            target = os.path.join('/tmp', file_path.name)
            print('Copying image to', target)
            #camera_file = gp.check_result(gp.gp_camera_file_get(
            #    self.camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))
            #gp.check_result(gp.gp_file_save(camera_file, target))

    def __del__(self):
        logging.info("Closing camera")
        gp.gp_camera_exit(self.camera)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
    callback_obj = gp.check_result(gp.use_python_logging())

    bracketing = BracketingRunner()
    bracketing.perform_bracketing()
