import cgi
import datetime
import wsgiref.handlers

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
        if self.request.get('page'):
            offset = int(self.request.get('page')) * 10
        else:
            offset = 0
        pkgs = db.GqlQuery("SELECT * "
                           "FROM Package "
                           "ORDER BY date DESC LIMIT 10"
                           "OFFSET %d" % offset)

        for pkg in pkgs:
            self.response.out.write("<p><a href='/download?id=%d'>%s</a></p><p>%s<br />By %s</p>" % (pkg.key().id(), pkg.title, pkg.note, pkg.author.nickname()))
        pkg_count = Package.all().count()

        if users.get_current_user():
            self.response.out.write("""
            <div>
            <form action="/upload" method="post" enctype="multipart/form-
data">
                <p><label for="blob">Eastwind package</label><input type="file" name="blob" size="50"/></p>
                <p><label for="note">Title</label><input type="text" name="title" value="" /></p>
                <p><label for="note">Note</label><input type="text" name="note" value="" /></p>
                <p><input type="submit" value="Upload package" /></p>
            </form>
            </div>""")
        else:
            self.response.out.write("""
            <div>
            <p>Please <a href="%s">log in</a> before uploading a package</p>
            </div>
            """ % users.create_login_url("/"))

application = webapp.WSGIApplication([
  ('/', Index),
  ('/upload', UploadFile),
  ('/download', DownloadFile)
], debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

