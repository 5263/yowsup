#!/usr/bin/env python
#husername=''
#hpassword=''
login=''
password=''.decode('base64')
peers= []
fromaddr='script@example.com'
toaddr='script@example.com'
smtpparams={'host':'mail.example.com',\
        'local_hostname':'scriptserver@example.com'}
#import logging
#logging.basicConfig(level=logging.DEBUG)

'''
Copyright (c) <2012> Tarek Galal <tare2.galal@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR
A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)
import datetime, sys

if sys.version_info >= (3, 0):
        raw_input = input

def sendemail(subject="Whatsapp",text='',attachments=(),date=None):
    import smtplib
    import email
    if attachments:
        msg=email.MIMEMultipart.MIMEMultipart()
        if text:
            msgtext=email.MIMEText.MIMEText(text)
            msgtext.set_charset('utf8')
            msg.attach(msgtext)
        for att,mimetype in attachments:
            if mimetype is None:
                mimetype = ('application',"octet-stream")
            part = email.MIMEBase.MIMEBase(*mimetype)
            part.set_payload(att)
            email.Encoders.encode_base64(part)
            #part.add_header('Content-Disposition', 'attachment')
            msg.attach(part)
    else:
        msg=email.MIMEText.MIMEText(text)
        msg.set_charset('utf8')
    msg['From'] = fromaddr
    msg['To'] = toaddr
    try:
        msg['Subject'] = subject.encode('us-ascii')
    except UnicodeEncodeError:
        msg['Subject'] = email.Header.Header(subject,'utf-8')
    if date:
        msg['Date'] = email.Utils.formatdate(date)
    else:
        msg['Date'] = email.Utils.formatdate(localtime=True)


    hmail=smtplib.SMTP(**smtpparams)
    hmail.starttls()
    #hmail.login(husername,hpassword)
    hmail.sendmail(fromaddr,[toaddr], msg.as_string())
    hmail.quit()
from Yowsup.connectionmanager import YowsupConnectionManager
from Yowsup.Media.uploader import MediaUploader


class WhatsappListenerClient:

        def __init__(self, keepAlive = False, sendReceipts = False):
                self.sendReceipts = sendReceipts

                connectionManager = YowsupConnectionManager()
                connectionManager.setAutoPong(keepAlive)

                self.signalsInterface = connectionManager.getSignalsInterface()
                self.methodsInterface = connectionManager.getMethodsInterface()
                self.signalsInterface.registerListener("message_received", self.onMessageReceived)
                #self.signalsInterface.registerListener("auth_success", self.onAuthSuccess)
                #self.signalsInterface.registerListener("auth_fail", self.onAuthFailed)
                #self.signalsInterface.registerListener("disconnected", self.onDisconnected)
                self.signalsInterface.registerListener("image_received", self.onImageReceived)
                self.signalsInterface.registerListener("video_received", self.onVideoReceived)
                self.signalsInterface.registerListener("audio_received", self.onAudioReceived)
                self.signalsInterface.registerListener("location_received", self.onLocationReceived)
                self.signalsInterface.registerListener("vcard_received", self.onVcardReceived)
                self.signalsInterface.registerListener("receipt_messageDelivered", self.onreceipt_messageDelivered)

                self.signalsInterface.registerListener("media_uploadRequestSuccess", self.onUploadRequestSuccess)
                self.signalsInterface.registerListener("media_uploadRequestDuplicate", self.onUploadRequestDuplicate)
#                self.signalsInterface.registerListener("message_received", self.onMessageReceived)
                self.signalsInterface.registerListener("auth_success", self.onAuthSuccess)
                self.signalsInterface.registerListener("auth_fail", self.onAuthFailed)
                self.signalsInterface.registerListener("disconnected", self.onDisconnected)
                self.signalsInterface.registerListener("presence_updated", self.onPresence_updated)


                self.cm = connectionManager
                self.pendinguploads=[]

        def login(self, username, password):
                self.username = username
                self.password = password
                self.methodsInterface.call("auth_login", (username, password))


        def prepareUpload(self,sourcePath,reciever, sender=None):
                sender = sender or self.cm.jid
                import mimetypes
                if sourcePath.lower().startswith('http://'):
                    import urllib2
                    opener = urllib2.build_opener()
                    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                    resp = opener.open(sourcePath)
                    filetype=resp.info().getheader('Content-Type')
                    media=resp.read()
                    filename=sourcePath.rsplit('/',1)[1]
                else:
                    media=open( sourcePath).read()
                    filename = os.path.basename(sourcePath)
                    filetype = mimetypes.guess_type(filename)[0]
                size=len(media)
                mtype,subtype = filetype.split('/',1)
                if mtype=='image':
                    import Image,StringIO
                    #tbsize =128,128
                    tbsize =64,64
                    output= StringIO.StringIO()
                    try:
                        if not sourcePath.lower().startswith('http://'):
                            im=Image.open(sourcePath)
                        else:
                            iminput = StringIO.StringIO(media)
                            im=Image.open(iminput)
                        im.thumbnail(tbsize,Image.ANTIALIAS)
                        #preview=im.tostring('jpeg','RGB')
                        im=im.convert('RGB')
                        im.save(output,format='JPEG')
                        preview= output.getvalue()
                        output.close()
                        import base64
                        preview=base64.b64encode(preview)
                    except:
                        raise
                else:
                    preview=''
                print filename
                print filetype

                import hashlib,base64
                hsh=base64.b64encode(hashlib.sha256(media).digest())
                dict1= {'hash':hsh,'mtype':mtype,'size':size,
                        'sender_jid' : sender, 'reciever_jid': reciever,\
                        'stream':media,'desc':'testdesc',\
                        'preview':preview,'filename':filename,
                        'filetype':filetype}
                self.requestUpload(dict1)
        def sendImageFile(self,*args,**kwargs):
            self.prepareUpload(*args,**kwargs)
        def requestUpload(self,dict1):
            self.pendinguploads.append(dict1)
            self.methodsInterface.call("media_requestUpload", (dict1['hash'],\
                dict1['mtype'],dict1['size']))

        def sendImage(self,url):
            dict1=self.pendinguploads[0]
            imageSendparams=(dict1['reciever_jid'],url,dict1['desc'],\
                    str(dict1['size']),dict1['preview'])
            self.methodsInterface.call("message_imageSend",imageSendparams)
            del self.pendinguploads[0]
        def onUploadSuccess(self, url):
                self.sendImage(url)
        def onProgressUpdated(self,perc):
            import sys
            print '\x1b[10D%2d %% ' % perc,
            #print '%2d' % perc
            #print '.',
            sys.stdout.flush()


        def onUploadRequestSuccess(self, _hash, url, resumeFrom=None):
            dict1=self.pendinguploads[0]
            dict1['url']=url
            print 'resumeFrom ',resumeFrom
            print 'hash ' ,_hash,dict1['hash']
            MU = MediaUploader(dict1['reciever_jid'],dict1['sender_jid'],\
                self.onUploadSuccess, self.onError, self.onProgressUpdated)
            if 'local_path' in dict1.keys():
                MU.uploadfile(dict1['local_path'],url)
            else:
                MU.uploadstream( dict1['stream'], url,dict1['filename'],
                    dict1['filetype'])
        def onError(self,*args):
            print args
            del self.pendinguploads[0]

        def onUploadRequestDuplicate(self,_hash, url):
            print 'duplicate'
            self.sendImage(url)
        def onAuthSuccess(self, username):
            print("Authed %s" % username)
            self.methodsInterface.call("ready")

        def onAuthFailed(self, username, err):
            print("Auth Failed!")

        def onDisconnected(self, reason):
            print("Disconnected because %s" %reason)
            self.methodsInterface.call("auth_login", \
                    (self.username, self.password))
        def onPresence_updated(self,jid,seconds):
        #def onPresenceUpdated(self, jid, lastSeen):
            import time
            formattedDate = datetime.datetime.fromtimestamp(long(time.time()) - seconds).strftime('%d-%m-%Y %H:%M')
            print jid, "LAST SEEN RESULT: %s" % formattedDate, long(time.time())
            print jid,seconds
        def onFallback(self, *args,**kwargs):
                print(str(args),str(kwargs))
                sendemail(subject="Whatsapp ",text=str(args))
        def onreceipt_messageDelivered(self, jid, messageId):
                print "receipt %s %s" % (jid, messageId)
                self.methodsInterface.call("delivered_ack", (jid, messageId))

        def onMediaReceived(self, messageId, jid, preview, url, size, wantsReceipt,mimetype=('application',"octet-stream")):
                attachments=[]
                if preview:
                        attachments.append((preview.decode('base64'),mimetype))
                if url:
                        import urllib2
                        resp = urllib2.urlopen(url)
                        mimetypeurl=resp.info().getheader('Content-Type')
                        attachments.append((resp.read(),\
                                mimetypeurl.split('/',1)))
                sendemail(subject="Whatsapp",text='%s %s\n%s %s' % (size,url,jid,messageId),attachments=attachments)
                if wantsReceipt and self.sendReceipts:
                        self.methodsInterface.call("message_ack", (jid, messageId))
        def onImageReceived(self, messageId, jid, preview, url, size, wantsReceipt,isgroup):
                self.onMediaReceived(messageId, jid, preview, url, size, wantsReceipt,mimetype=('image',"jpeg"))
        def onVideoReceived(self, messageId, jid, preview, url, size, wantsReceipt,isgroup):
                self.onMediaReceived(messageId, jid, preview, url, size, wantsReceipt,mimetype=('image',"jpeg"))
        def onAudioReceived(self, messageId, jid, url, size, wantsReceipt,isgroup):
                self.onMediaReceived(messageId, jid, None, url, size, wantsReceipt,mimetype=('audio',"3ga"))
        def onLocationReceived(self, messageId, jid, name, preview, lat, lon, wantsReceipt,isgroup):
                sendemail(subject="Whatsapp Loc",text='%s\n%s %s\n%s %s' % \
                        (name,lat,lon, jid,messageId),attachments=\
                        ((preview.decode('base64'),('image','jpeg')),))
                if wantsReceipt and self.sendReceipts:
                        self.methodsInterface.call("message_ack", (jid, messageId))
                pass
        def onVcardReceived(self, messageId, jid, name, data, wantsReceipt,isgroup):
                sendemail(subject="Whatsapp vcard",text='%s\n%s %s' % (name,jid,messageId),attachments=((data,('text','vcard')),))
                if wantsReceipt and self.sendReceipts:
                        self.methodsInterface.call("message_ack", (jid, messageId))
                pass
        def onMessageReceived(self, messageId, jid, messageContent, timestamp, wantsReceipt, pushName, isBroadCast):
                print '%s\n%s %s %s' % (messageContent,jid,messageId,pushName)
                sendemail(subject="Whatsapp from %s"%pushName,text='%s\n%s %s %s' % (messageContent,jid,messageId,pushName),date=timestamp)
                if wantsReceipt and self.sendReceipts:
                        self.methodsInterface.call("message_ack", (jid, messageId))

import cmd
class WAPrompt(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt ='(WA) '
    def emptyline(self):
        pass
    def do_EOF(self,line):
        return True
    def do_exit(self,line):
        return True
    def do_ipython(self,line):
        import IPython
        IPython.embed() #damages thes readline histroy
    def do_interact(self,line): #not useful
        import code
        code.interact(local={'wa':wa})#not useful
    def do_media(self,line):
        """sends media to a recepient"""
        rcpt,media = line.split(' ',1)
        wa.sendImageFile(media,'%s@s.whatsapp.net' % rcpt)
    def do_msg(self,line):
        rcpt,msg = line.split(' ',1)
        jid = '%s@s.whatsapp.net' % rcpt
        msgId = wa.methodsInterface.call("message_send", (jid, msg))
    def complete_media(self, text,line, begidx,endidx):
        #print begidx,endidx,text
        if not text:
            return peers
        else:
            return [ b for b in peers if b.startswith(text)]
    complete_reqpresence = complete_media
    def complete_msg(self,text,line,begidx,endidx):
        if not text:
            return peers
        else:
            return [ b for b in peers if b.startswith(text)]
        self.complete_media(*args)
    def do_syncall(self,line):
        from Yowsup.Contacts.contacts import WAContactsSyncRequest
        contacts=inp1[6:].split(',')
        wsync = WAContactsSyncRequest(wa.username, \
            wa.password, contacts)
        result = wsync.send()
        for dict2 in result['c']:
            if dict2['w'] == 1: #using whatsapp
                timestr=datetime.datetime.\
                        fromtimestamp(dict2['t']).\
                        strftime('%Y-%m-%d %H:%M:%S')
                num=dict2['p']
                print '%20s %s %s' %(num,timestr,dict2['s'])
    def do_reqpresence(self,line):
        jid = '%s@s.whatsapp.net' % line.strip()
        wa.methodsInterface.call("presence_request", ( jid,))
    def do_available(self,line):
        wa.methodsInterface.call("presence_sendAvailable")
    def do_unavailable(self,line):
        wa.methodsInterface.call("presence_sendUnavailable")

#wa = WhatsappListenerClient(args['keepalive'], args['autoack'])
if __name__ == '__main__':
    wa = WhatsappListenerClient(True,True)
    wa.login(login, password)
    WAPrompt().cmdloop()


