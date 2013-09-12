#!/usr/bin/env python2
import web
import os
import time
import config
from urllib import quote

# load config file
paths = config.paths

types = [
    ".h",".cpp",".cxx",".cc",".c",".cs",".html",".js",
    ".php",".java",".py",".rb",".as",".jpeg",".jpg",".png",
    ".gif",".ai",".psd",".mp3",".avi",".rmvb",".mp4",".wmv",
    ".mkv",".doc",".docx",".ppt",".pptx",".xls",".xlsx",
    ".zip",".tar",".gz",".7z",".rar",".pdf",".txt",".exe",
    ".apk", "dir"
]

render = web.template.render('template')

urls = (
    '/favicon.ico',"Ico",
    '/([\w\d]+)/(.*)','Index',
)

class Ico:
    def GET(self):
        return open("static/img/favicon.ico").read()

def getSizeForHuman(size):
    if size < 1024:
        return str(size) + ".0 B"
    if size < 1024 * 1024:
        return "%0.1f KB" % (size/1024.0)
    if size < 1024 * 1024 * 1024:
        return "%0.1f MB" % (size/1024.0/1024.0)
    return "%0.1f GB" % (size/1024.0/1024.0/1024.0)

def handlePath(name, _path):
    if name not in paths:
        raise RuntimeError('Dir not found')
    if os.path.normpath(_path).startswith(('/', '..')):
        raise RuntimeError('How dare you!')
    _path = _path.encode('utf8')
    root, uploadable = paths[name]
    path = os.path.join(root, _path)
    return (_path, path, uploadable)

class Index:
    def GET(self, name, _path):
        try:
            _path, path, uploadable = handlePath(name, _path)
        except RuntimeError as err:
            return web.notfound()
        if os.path.isdir(path):
            items = list()
            for filename in os.listdir(path):
                realname = os.path.join(path, filename)
                item = dict()
                item['name'] = filename
                if os.path.isdir(realname):
                    item['type'] = 'dir'
                else:
                    item['type'] = os.path.splitext(filename)
                if item['type'] not in types:
                    item['type'] = 'general'
                item["time"] = time.strftime("%H:%M:%S %Y-%m-%d",
                        time.localtime(os.path.getmtime(realname))) 
                item['size'] = getSizeForHuman(os.path.getsize(realname))
                item['href'] = name + '/' +  \
                        quote(os.path.join(_path, filename))
                items.append(item)
            return render.layout(sorted(items, key=lambda x: x['name'].lower()), uploadable)
        if os.path.isfile(path):
            web.header('Content-Type','application/octet-stream')
            web.header('Content-disposition', 
                    'attachment; filename=%s' % quote(os.path.basename(path)))
            size = os.path.getsize(path)
            web.header('Content-Length','%s' % size)
            return open(path).read()
        return web.notfound()
            
    def POST(self, name, _path):
        try:
            _path, path, uploadable = handlePath(name, _path)
        except RuntimeError as err:
            return web.notfound()
        if not os.path.isdir(path):
            return web.notfound()
        x = web.input(file={})
        if 'file' in x:
            filepath= x.file.filename.replace('\\','/')     # replaces the windows-style slashes with linux ones.
            filename = filepath.split('/')[-1]              # splits the and chooses the last part (the filename with extension)
            filename = unicode(filename, "utf8")
            with open(os.path.join(path, filename), 'w') as f:
                f.write(x.file.file.read())
        return "<script>parent.location.reload()</script>" 

# start the application
# it's adaptable to both uwsgi start & python start
app = web.application(urls,globals())
application = app.wsgifunc()

if __name__ == "__main__":
    app.run()
    
