# Background Removal Virtual Camera

This app creates virtual camera without any third-party frameworks. You can make your eye-contacting conference environment without any confusing environment setup such as OBS camera.
You can choose your background from the embedded images as well as your local image.
The installation app is also available.
You can download it on my [GDrive](https://drive.google.com/file/d/1LbQwFXMISyfQKMjPmlgEbi52qYaJGuJv/view?usp=drive_link)

## How to use


### Environment setup:
#### If your os is Linux:
> pip install -r requirements.txt


#### if you are using windows:

The app was devloped on cuda11.8;
> pip install onnxruntime-gpu==1.16.0
> pip install tensorrt-cu11

### Usage
First Set OS environment using set_env.py file.
    - It adds dependencies(ffmpeg, Akvcammanager) into the system environment variable.
    - Create new virtual camera and set required configurations.

Second you can run main.py for the actual GUI application.


### Build binary
Driver 
pyinstaller --icon="res/MBA.ico" --windowed --name "MeetnDriver" --onefile set_env.py

App
pyinstaller --name "Meetn Bonus App" --icon='res/MBA.ico' --onedir --noconfirm --windowed App.py

For the GPU:
pyinstaller --add-binary C:/Users/Administrator/anaconda3/envs/ncu118/Lib/site-packages/onnxruntime/capi/onnxruntime_provid
ers_cuda.dll:./onnxruntime/capi/ --add-binary C:/Users/Administrator/anaconda3/envs/ncu118/Lib/site-packages/onnxruntime/capi/onnxruntime_providers_tensorrt.d
ll:./onnxruntime/capi/  --hidden-import=numpy --hidden-import=numpy.core.multiarray --name "Meetn Bonus App" --icon='res/MBA.ico' --onedir --noconfirm --windowed App.py


Installation file

Refer to 'Inno_Setup/MBA.iss' file. It is Inno setup script.
