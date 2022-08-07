# focus-bracketing
gphoto2 based focus bracketing tool

With focus bracketing, a sequence of camera images with a focus shift is generated.
These images can then be combined into a single image with a wider focus range. 

## Installation

    sudo apt install gphoto2 hugin-tools enfuse
    
    pip install -r requirements.txt

## Usage

(1) Connect your camera via USB

(2) Test your connection

    gphoto2 --summary

*This should print some information about your camera.*

(3) Obtain a sequence of images with a focus shift (**focus bracketing**)

    python bracketing_runner.py -o OUT_DIR

*This will capture a sequence of images and download them to OUT_DIR*

(4) Align the images - optional (**image alignment**)

    align_image_stack -m -v -a ./OUT_DIR*.JPG

(5) Combine the images (**focus stacking**)

    enfuse --exposure-weight=0 --saturation-weight=0 --contrast-weight=1 --hard-mask --gray-projector=l-star -o stacked.tif ./OUT_DIR/*.JPG

If you didn't skip (4), then you might need to adjust './OUT_DIR/*.JPG'

## Customization

For customization, see 

    python bracketing_runner.py --help



## Tested cameras

* Nikon D850
