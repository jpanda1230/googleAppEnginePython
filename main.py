import StringIO
import zipfile
from zipfile import ZipFile

import webapp2
import jinja2
import os
from google.appengine.ext import ndb
from google.appengine.api import users
import time
from collections import namedtuple
from google.appengine.ext import ndb
from google.appengine.ext import blobstore, ndb
from google.appengine.ext.ndb import BlobKey
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore

from model import UserInfo, FolderInfo, FileInfo

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


class MainPage(webapp2.RequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        current_folder = self.request.get('current_folder')
        folder = None
        if user:
            user_key = ndb.Key('UserInfo', user.email())
            user_info = user_key.get()
            if user_info is None:
                user_info = UserInfo(id=user.email())
                user_info.email = user.email()
                folder_info = FolderInfo(id=user.email()+"/")
                folder_info.name = "/"
                user_info.folder = folder_info.key
                folder_info.put()
                user_info.put()
                time.sleep(1)

            if len(current_folder) == 0:
                folder = user_info.folder.get()
            else:
                folder_key = ndb.Key('FolderInfo', user.email()+current_folder)
                folder = folder_key.get()


            url = users.create_logout_url(self.request.uri)
            url_string = 'logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_string = 'login'

        template_values = {
            'url': url,
            'url_string': url_string,
            'user': user,
            'upload_url': blobstore.create_upload_url('/upload'),
            'message': self.request.get('message'),
            'current_folder': folder
        }

        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(template_values))
        MainPage.obj = self


class AddFolder(webapp2.RequestHandler):

    def get(self):
        self.redirect("/")

    def post(self):
        user = users.get_current_user()
        current_folder = self.request.get('current_folder')
        folder_name = current_folder + self.request.get('folder_name') + "/"
        folder_key = ndb.Key('FolderInfo', user.email()+folder_name)
        folder = folder_key.get()
        if folder is not None:
            message = "Error: folder path exists (" + folder_name + ")"

        else:
            folder = FolderInfo(id=user.email()+folder_name)
            folder.name = folder_name
            parent = ndb.Key('FolderInfo', user.email()+current_folder).get()
            parent.folders.append(folder.key)
            folder.parent = parent.key
            folder.put()
            parent.put()
            message = "Success: folder added (" + folder_name + ")"

        time.sleep(1)
        self.redirect("/?current_folder=" + current_folder + "&message=" + message)


class DeleteFolder(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        index= self.request.get('index')
        current_folder = self.request.get('current_folder')
        folder_name = self.request.get('folder_name')
        folder_key = ndb.Key('FolderInfo', user.email()+folder_name)
        folder = folder_key.get()
        if folder is None:
            message = "Error: folder doesn't exists (" + folder_name + ")"

        else:
            parent = folder.parent.get()
            del parent.folders[int(index) - 1]
            folder.key.delete()
            parent.put()
            message = "Success: folder deleted (" + folder_name + ")"

        time.sleep(1)
        self.redirect("/?current_folder=" + current_folder + "&message=" + message )


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):

        upload = self.get_uploads()[0]
        blobinfo = blobstore.BlobInfo(upload.key())
        user = users.get_current_user()
        current_folder = self.request.get('current_folder')
        file_name = current_folder +  blobinfo.filename
        file_key = ndb.Key('FileInfo', user.email() + file_name)
        file = file_key.get()
        if file is not None:
            message = "Error: file path exists (" + file_name + ")"
        else:
            file = FileInfo(id=user.email() + file_name)
            file.name = file_name
            file.blob = blobinfo.key()
            parent = ndb.Key('FolderInfo', user.email() + current_folder).get()
            parent.files.append(file.key)
            file.parent = parent.key
            file.put()
            parent.put()
            message = "Success: file uploaded (" + file_name + ")"

        time.sleep(1)
        self.redirect("/?current_folder="+current_folder+"&message="+message)


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        user = users.get_current_user()
        index = self.request.get('index')
        current_folder = self.request.get('current_folder')
        file_name = self.request.get('file_name')
        file_key = ndb.Key('FileInfo', user.email() + file_name)
        file = file_key.get()

        if file is None:
            message = "Error: file doesn't exists (" + file_name + ")"
            self.redirect("/?current_folder=" + current_folder + "&message=" + message)
        else:
            self.send_blob(file.blob, save_as=file_name.replace(current_folder,''))


class DeleteFile(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        index= self.request.get('index')
        current_folder = self.request.get('current_folder')
        file_name = self.request.get('file_name')
        file_key = ndb.Key('FileInfo', user.email()+file_name)
        file = file_key.get()
        if file is None:
            message = "Error: file doesn't exists (" + file_name + ")"
        else:
            parent = file.parent.get()
            del parent.files[int(index) - 1]
            blobstore.delete(file.blob)
            file.key.delete()
            parent.put()
            message = "Success: file deleted (" + file_name + ")"

        time.sleep(1)
        self.redirect("/?current_folder=" + current_folder + "&message=" + message)


class OpenPath(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        current_folder = self.request.get('current_folder')
        open_folder = self.request.get('open_folder')
        folder = ndb.Key('FolderInfo', user.email() + open_folder).get()
        if not folder:
            open_folder+='/'
            folder = ndb.Key('FolderInfo', user.email() + open_folder).get()
            if not folder:
                message = "Error: path not found ("+open_folder+")"
                self.redirect("/?current_folder=" + current_folder + "&message=" + message)
            else:
                self.redirect("/?current_folder=" + open_folder)
        else:
            self.redirect("/?current_folder=" + open_folder)


class ZipDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        user = users.get_current_user()
        index = self.request.get('index')
        current_folder = self.request.get('current_folder')
        folder_key = ndb.Key('FolderInfo', user.email() + current_folder)
        folder = folder_key.get()

        zipstream = StringIO.StringIO()
        zfile = zipfile.ZipFile(file=zipstream, mode='w')

        for file_key in folder.files:
            file = file_key.get()
            start = 0
            size = 1024
            flag = False
            data = []
            while not flag:
                chunk = blobstore.fetch_data(file.blob, start, start+size)
                data.append(chunk)
                if len(chunk)<1024:
                    flag = True
                start+=size+1
            zfile.writestr(file.name.replace(file.parent.get().name,''), "".join(data))

        zfile.close()
        zipstream.seek(0)


        self.response.headers['Content-Type'] = 'application/zip'
        self.response.headers['Content-Disposition'] = \
            'attachment; filename="root'+(folder.name.encode('utf-8'))+'.zip"'
        self.response.out.write(zipstream.getvalue())




