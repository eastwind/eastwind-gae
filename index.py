import cgi
import datetime
import wsgiref.handlers
import math

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.db import stats

class Package(db.Model):
    author = db.UserProperty()
    title = db.StringProperty()
    blob = db.BlobProperty()
    note = db.StringProperty(multiline=True)
    filename = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class UploadFile(webapp.RequestHandler):
    def post(self):
        pkg = Package()
#        if self.request.POST['blob'].type != 'application/x-gzip':
#            self.response.out.write(self.request.POST['blob'].type)
#            self.response.out.write("Illegal file type!")
#            return
        if not self.request.POST['blob'].filename.endswith('.eastwind'):
            self.response.out.write("Illegal file name!")
            return
        if not users.get_current_user():
            self.response.out.write("You are not logged in!")
            return
        pkg.author = users.get_current_user()
        pkg.filename = self.request.POST['blob'].filename
        pkg.blob = db.Blob(self.request.get('blob'))
        pkg.title = self.request.get('title')
        pkg.note = self.request.get('note')
        pkg.put()
        self.redirect('/')

class DownloadFile(webapp.RequestHandler):
  def get(self):
    id = self.request.get('id')
    pkg = Package.get_by_id(int(id))
    if pkg:
      self.response.headers['Content-Type'] = 'application/x-gzip'
      self.response.headers['Content-Disposition'] = "attachment; filename=" + str(pkg.filename)
      self.response.out.write(pkg.blob)
    else:
      self.response.out.write('Could not find file %s.' % id)

class Index(webapp.RequestHandler):
    def get(self):
        self.response.out.write("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh">
<head>
   <meta http-equiv="Content-Type" content="text/html;charset=UTF-8" />
   <title>Eastwind Exchange Market</title>
   <link rel="stylesheet" href="/stylesheets/reset.css" />
   <link rel="stylesheet" href="/stylesheets/style.css" />
</head>
<body>
   <h1>On the rack</h1>
	<table>
	   <tr>
	      <th>Package</th>
	      <th>Uploader</th>
	   </tr>
        """)

        if self.request.get('page'):
            offset = int(self.request.get('page')) * 10
        else:
            offset = 0
        pkgs = db.GqlQuery("SELECT * "
                           "FROM Package "
                           "ORDER BY date DESC LIMIT 10"
                           "OFFSET %d" % offset)

        for pkg in pkgs:
            self.response.out.write("""
       <tr>
	      <td>
	         <h4><a href='/download?id=%d'>%s</a></h4>
	         <span style="description">%s</span>
	      </td>
	      <td>%s</td>
	   </tr>
            """ % (pkg.key().id(), pkg.title, pkg.note, pkg.author.nickname()))
        page_count = int(math.ceil(float(Package.all().count()) / 10.0))
        self.response.out.write("</table><ul class='page'>")
        for i in range(page_count):
            self.response.out.write("<li><a href='/?page=%d'>%d</a></li>" % (i, i+1))
        self.response.out.write("</ul>")

        self.response.out.write("<h1>Stage your own!</h1>")

        if users.get_current_user():
            self.response.out.write("""
            <form action="/upload" method="post" enctype="multipart/form-
data">
            <table>
                <tr><td><label for="blob">Eastwind package</label></td><td><input type="file" name="blob" size="50"/></td></tr>
                <tr><td><label for="note">Title</label></td><td><input type="text" name="title" value="" /></td></tr>
                <tr><td><label for="note">Note</label></td><td><input type="text" name="note" value="" /></td></tr>
                <tr><td colspan="2"><input type="submit" value="Upload package" /></td></tr>
            </table>
            </form>
            """)
        else:
            self.response.out.write("""
            <div>
            <p>Please <a href="%s">log in</a> before uploading a package</p>
            </div>
            """ % users.create_login_url("/"))

        self.response.out.write("</body></html>")

application = webapp.WSGIApplication([
  ('/', Index),
  ('/upload', UploadFile),
  ('/download', DownloadFile)
], debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

