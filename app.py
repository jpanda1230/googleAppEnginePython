import webapp2


import main

app = webapp2.WSGIApplication([
('/', main.MainPage),
('/add_folder', main.AddFolder),
('/delete_folder', main.DeleteFolder),
('/upload', main.UploadHandler),
('/download_file', main.DownloadHandler),
('/delete_file', main.DeleteFile),
('/open_path', main.OpenPath),
('/download_all', main.ZipDownloadHandler),
], debug=True)
