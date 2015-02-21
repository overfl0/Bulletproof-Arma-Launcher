from multiprocessing import Pool

import kivy
import requests
import os

from time import sleep

def download(path):
    print "iam process:"
    print "downloading to:", path
    sleep(10)
    # with open(os.path.join(path, 'kivy.zip'), 'wb') as handle:
    #
    #     print "get request"
    #     response = requests.get(
    #         'http://kivy.org/downloads/1.8.0/Kivy-1.8.0-py2.7-win32.zip',
    #         stream=True
    #     )
    #
    #     print "request ready"
    #
    #     if not response.ok:
    #         print 'response failed'
    #
    #     for block in response.iter_content(1024):
    #         if not block:
    #             break
    #
    #         handle.write(block)

def on_download_finish(*args, **kwargs):
    print "download finished", args, kwargs

class MainWidgetController(object):
    def __init__(self, widget):
        super(MainWidgetController, self).__init__()
        self.view = widget

    def on_install_button_release(self, btn, image):
        app = kivy.app.App.get_running_app()
        print 'button clicked', str(btn), str(image)
        image.source = app.resource_path('images/installing.png')
        print 'MainWidget ids:', self.view.ids
        self.test_file_download()

    def test_file_download(self):
        pool = Pool(processes=2)
        pool.apply_async(download, (os.getcwd(),), callback=on_download_finish)
        # pool.close()
        # pool.join()
