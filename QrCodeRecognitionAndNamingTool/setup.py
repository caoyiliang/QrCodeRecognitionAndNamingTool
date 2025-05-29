from cx_Freeze import setup, Executable

setup(
    name="QrCodeRecognitionAndNamingTool",
    version="1.0",
    description="A tool for QR code recognition and PDF renaming",
    executables=[
        Executable(
            "QrCodeRecognitionAndNamingTool.py",
            base=None, 
            icon="logo.ico" 
        )
    ],
)