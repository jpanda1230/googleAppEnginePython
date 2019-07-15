from google.appengine.ext import ndb


class FileInfo(ndb.Model):
    name = ndb.StringProperty()
    blob = ndb.BlobKeyProperty()
    parent = ndb.KeyProperty(kind="FolderInfo")

class FolderInfo(ndb.Model):
  name = ndb.StringProperty()
  files = ndb.KeyProperty(kind="FileInfo", repeated=True)
  folders = ndb.KeyProperty(kind="FolderInfo", repeated=True)
  parent = ndb.KeyProperty(kind="FolderInfo")


class UserInfo(ndb.Model):
    email = ndb.StringProperty()
    folder = ndb.KeyProperty(kind="FolderInfo")



