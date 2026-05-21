# Copy and paste to build a new exe

 cd "C:\Users\zdb08\PycharmProjects\Verba"

 Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

 Remove-Item -Force Verba.spec -ErrorAction SilentlyContinue

 py -m pip install pyinstaller

 py -m PyInstaller --name Verba --windowed --onedir Verba_App\main.py