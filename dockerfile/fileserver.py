from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import SimpleHTTPServer
import sys, os, zipfile
import magic 
import urllib
import socket

PORT = int(sys.argv[1])

def send_head(self):
    """Common code for GET and HEAD commands.

    This sends the response code and MIME headers.

    Return value is either a file object (which has to be copied
    to the outputfile by the caller unless the command was HEAD,
    and must be closed by the caller under all circumstances), or
    None, in which case the caller has nothing further to do.

    """
    path = self.translate_path(self.path)
    download = False
    f = None
    tmp_file = None

    if self.path.endswith('?download'):
        if os.path.isdir(path):

            self.path = self.path.replace("?download","")
            relpath = self.path if self.path[0] != "/" else self.path[1:]
            relpath = urllib.unquote(relpath)
            dirname = relpath[relpath[:relpath.rfind("/")].rfind("/") + 1: -1 ]
            tmp_file = "/tmp/" + dirname + ".zip"
            print "Requested path '" + self.path + "'"
            print "Path: '" + path + "'"
            print "Relative path: '" + relpath + "'"

            zip = zipfile.ZipFile(tmp_file, 'w', allowZip64 = True)
            for root, dirs, files in os.walk(path):
                print "Absolute root: '"  + root + "'"
                print "Relative root: " + root[root.index(relpath) + len(relpath)-1:]
                relroot = root[root.index(relpath) + len(relpath):]
                print "Dirs: " + str(dirs)
                for file in files:
                    print "Filename: " + file
                    print "File to put into zip: '" + os.path.join(relroot, file)  + "'"
                    print "Filename inside zip: '" + dirname + relroot + file + "'"
                    if os.path.join(relpath, file) != os.path.join(relpath, tmp_file):
                        #zip.write(os.path.join(os.path.join(relpath,relroot), file))
                        zip.write(os.path.join(os.path.join(relpath,relroot), file), dirname + "/" +  relroot + "/" + file)
            zip.close()
            path = tmp_file
            filename = dirname + ".zip"
            print filename

        else:
            download = True
    elif os.path.isdir(path):

        if not self.path.endswith('/'):
            # redirect browser - doing basically what apache does
            self.send_response(301)
            self.send_header("Location", self.path + "/")
            self.end_headers()
            return None
        else:

            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)

    print path
    ctype = self.guess_type(path)
    print download
    print ctype
    try:
        alttype = magic.from_file(path)
        if "ASCII" in alttype and not download:
            ctype = "text/plain"
    except:
        print "Not a file"
    try:
        # Always read in binary mode. Opening files in text mode may cause
        # newline translations, making the actual size of the content
        # transmitted *less* than the content-length!
        f = open(path, 'rb')
    except IOError:
        self.send_error(404, "File not found")
        return None
    self.send_response(200)
    self.send_header("Content-type", ctype)
    fs = os.fstat(f.fileno())
    self.send_header("Content-Length", str(fs[6]))
    self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
    if tmp_file is not None:
        self.send_header("Content-Disposition", "attachement; filename=\"" + filename + "\"")
    self.end_headers()
    return f

def list_directory(self, path):

    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    import cgi, urllib

    """Helper to produce a directory listing (absent index.html).

    Return value is either a file object, or None (indicating an
    error).  In either case, the headers are sent, making the
    interface the same as for send_head().

    """
    try:
        list = os.listdir(path)
    except os.error:
        self.send_error(404, "No permission to list directory")
        return None
    list.sort(key=lambda a: a.lower())
    f = StringIO()
    displaypath = cgi.escape(urllib.unquote(self.path))
    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
    f.write("<html>\n<title>%s</title>\n" % displaypath)
    f.write("<head>\n<style>ul{ }\nhtml {background-color: #474747  ;color: #cffff4 ;}\n a:link, a:visited, a:hover, a:active{color: #cffff4 ;text-decoration:none;} h2 a:link, h2 a:visited, h2 a:active {text-decoration:underline;}</style>")
    f.write("</head>\n" )
    print displaypath.split("/")
    breadcrumbs = displaypath.split("/")
    bclinks = []
    for link in breadcrumbs:
        if "" == link:
            continue
        if len(bclinks) == 0:
            bclinks.append("/" + link)
        else:
            bclinks.append(bclinks[-1] + "/" + link)
    links = ""
    for link in bclinks:
        links += "<a href=\"" + link + "\">" + link[link.rfind("/"):] + "</a>" 
    print bclinks
    print links
        
        

    f.write("<body>\n<h2>%s</h2>\n" % links)
    f.write("<a href='%s'>%s</a>\n" % (self.path+"?download",'Download as Zip'))
    f.write("<hr>\n<ul>\n")
    if self.path != "/":
        f.write('<li><a href="%s">%s</a>\n'% (urllib.quote(".."), cgi.escape("Parent directory")))
 
    downloadicon = "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4gUXDSgfSvvAcwAAAmRJREFUeNrt3cFKK0EQhtFM4/u/cly5EQTR6en6q863FSTTda7XCKm+XsN6v9/vn752Xdc17Twuw58NYRn+7JYjmI1lGaifAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAB0oo+d3/z7mvaJV7L898x2n9315EOcgvCX+wJOYP3N67z7da0TD+ECh7+fyd1nt079S4OgxlmsqQ+ePPw7z22dHuZkBBWefTmI2c+8HMjsZ10OJu8Z73wreBuAu15UZwQVn205qKxnKv2HoDtfXCcEVYe/5ScABDnD3/ZfAAQZw9/6O8B0BAnD3/5L4FQEKcN/5F3ANARJw3/sbeAUBGnDf/TvAN0RJA7/UQCdEaQO/3EAHREkD/8IgE4I0od/DEAHBB2GfxRAMoIuwz8OIBFBp+GXAJCEoNvwywBIQNBx+KUAVEbQdfjlAFRE0Hn4r9emzwamv7//Glj34ZcGUAFB9+GXB5COIOHj8BGf109EkLILIWZhQxKCpEUYURs7EhCkbUGJW9lSGUHiCpzInT0VEaTuP4pd2lQJQfLyq+itXRUQpG8+i1/bdhJBh7V3Lfb2nUDQZedhm8WNTyLotPCy1ebOJxB023babnXrTgQdV9223N27A0HXPcdtlzffiaDzkuvW27urbeQCIAzBhPX2I/b3p6yLB6AIgkkXW4y6wePEhQwABEFwpY0kSZIkSZKknrnYIXFoFW8NU2YAACAABIAAEAACQAAIAAEgAASAAFDjPgGzlniHGEO3oAAAAABJRU5ErkJggg=="
    
    for name in list:
        fullname = os.path.join(path, name)
        displayname = linkname = name
        # Append / for directories or @ for symbolic links
        if os.path.isdir(fullname):
            displayname = name + "/"
            linkname = name + "/"
        if os.path.islink(fullname):
            displayname = name + "@"
            # Note: a link to a directory displays with @ and links with /
        f.write('<li><a href="%s?download"><img width="13px" src="data:image/png;base64,%s"></img></a>   <a href="%s">%s</a></li>\n'
                % (urllib.quote(linkname),downloadicon,  cgi.escape(linkname), displayname))
    f.write("</ul>\n<hr>\n</body>\n</html>\n")
    length = f.tell()
    f.seek(0)
    self.send_response(200)
    encoding = sys.getfilesystemencoding()
    self.send_header("Content-type", "text/html; charset=%s" % encoding)
    self.send_header("Content-Length", str(length))
    self.end_headers()
    return f

def do_GET(self):
    """Serve a GET request."""
    f = self.send_head()
    filename = ""
    if f:
        if isinstance(f, file):
            filename = f.name
	self.copyfile(f, self.wfile)
    if f:
        f.close()
    if filename and "zip" in filename:
        os.remove(filename)

def finish(self):
    try:
	if not self.wfile.closed:
            self.wfile.flush()
            self.wfile.close()
    except socket.error:
	pass
    self.rfile.close() 

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
Handler.send_head = send_head
Handler.do_GET = do_GET
Handler.finish = finish
Handler.list_directory = list_directory

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer(('0.0.0.0', PORT), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
