from windows_toasts import Toast, WindowsToaster
from config import APP_NAME

toaster = WindowsToaster(APP_NAME)

def show_notification(title: str, message: str):
    toast = Toast()
    toast.text_fields = [title, message,]

    toaster.show_toast(toast)