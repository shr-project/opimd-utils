# -*- coding: utf-8 -*-

import elementary, dbus
import time
import gettext
import ConfigParser
from functools import partial

try:
	cat = gettext.Catalog("opimd-messages")
	_ = cat.gettext
except IOError:
	_ = lambda x: x

CONF_FILE = '/etc/opimd-utils.conf'

opts = {
    'report':'request delivery report',
#    'charset':'force GSM ASCII charset',
#    'store':'store SMS in outbox',
    'class':'send as Class 0',
#    'askcsm':'ask before sending CSM',
  }

optsdef = {
    'report':True,
    'charset':False,
    'store':True,
    'class':False,
    'askcsm':True,
  }

def getDbusObject (bus, busname , objectpath , interface):
        dbusObject = bus.get_object(busname, objectpath)
        return dbus.Interface(dbusObject, dbus_interface=interface)

def dbus_ok():
  pass

def dbus_err(x):
  print "notice: dbus error: "+str(x)

def dbus_sms_ok(x, bus, func_status, a, b):
  message = getDbusObject (bus, "org.freesmartphone.opimd", x, "org.freesmartphone.PIM.Message")
  data = {'MessageSent':1, 'Processing':0}
  ops = loadOpts()
  if ops['report']:
    data['SMS-message-reference']=a
  message.Update(data, reply_handler=dbus_ok, error_handler=dbus_err)
  if callable(func_status):
    func_status('sent')
#  print a
#  print b

def dbus_opimd_ok(to, msg, props, bus, win, func_ok, func_err, func_status, x):
  if callable(func_ok):
    func_ok(x)
  if callable(func_status):
    func_status('stored')
    func_status('sending')
  try:
    ogsmd = getDbusObject (bus, "org.freesmartphone.ogsmd", "/org/freesmartphone/GSM/Device", "org.freesmartphone.GSM.SMS")
    try:
      ogsmd.SendTextMessage(to[0], msg, props['status-report-request'], reply_handler=partial(dbus_sms_ok, x, bus,func_status), error_handler=partial(dbus_gsm_err, to,msg, props, x, bus, win, func_ok, func_err, func_status) )
    except:
      ogsmd.SendMessage(to[0] ,msg, props, reply_handler=partial(dbus_sms_ok, x, bus, func_status), error_handler=partial(dbus_gsm_err, to, msg, props, x, bus, win, func_ok, func_err, func_status) )
  except dbus.exceptions.DBusException, e:
    dbus_gsm_err(to, msg, props, x, bus, win, func_ok, func_err, func_status, e)

def retry_msg(to, text, bus, win, inwin, func_ok, func_err, func_status, *args, **kwargs ):
  inwindelete(inwin, None)
  if callable(func_status):
    func_status('retrying')
  reply(to, text, bus, win, func_ok, func_err, func_status)

def dbus_gsm_err(to, text, props, x, bus, win, func_ok, func_err, func_status, dx):
  message = getDbusObject (bus, "org.freesmartphone.opimd", x, "org.freesmartphone.PIM.Message")
  data = {'Processing':0}
  message.Update(data, reply_handler=dbus_ok, error_handler=dbus_err)

  inwin = elementary.InnerWindow(win)
  inwin.show()
  inwin.style_set("vertical-minimal")
  win.resize_object_add(inwin)
  box = elementary.Box(inwin)
  box.show()
  inwin.content_set(box)
  label = elementary.Label(inwin)
  label.label_set(_("Error while sending message!"))
  label.show()
  box.pack_start(label)
  sc = elementary.Scroller(inwin)
  sc.bounce_set(0, 0)
  sc.show()
  anchor = elementary.AnchorBlock(inwin)
  anchor.text_set(elementary.Entry.utf8_to_markup(str(dx)))
  anchor.show()
  sc.content_set(anchor)
  sc.size_hint_weight_set(1.0, 1.0)
  sc.size_hint_align_set(-1.0, -1.0)
  box.pack_end(sc)

  hbox = elementary.Box(inwin)
  hbox.horizontal_set(1)
  hbox.show()

  retry = elementary.Button(inwin)
  retry.label_set(_("Retry"))
  retry.show()
  retry._callback_add('clicked', partial(retry_msg, to, text, bus, win, inwin, func_ok, func_err, func_status))
  hbox.pack_end(retry)

  hide = elementary.Button(inwin)
  hide.label_set(_("Close"))
  hide.show()
  hide._callback_add('clicked', partial(inwindelete, inwin, func_status))
  hbox.pack_end(hide)  

  box.pack_end(hbox)

  if callable(func_err):
    func_err()
  if callable(func_status):
    func_status('error')

  inwin.activate()

def dbus_opimd_err(to, msg, props, bus, win, func_ok, func_err, func_status, x):
  # TODO: call the same code, as dbus_gsm_err
  if callable(func_status):
    func_status('error')
  print "dbus error! "+str(x)

def send_msg(to, entry, bus, inwin, win, func_ok, func_err, func_status, *args, **kwargs):
  msg = entry.markup_to_utf8(entry.entry_get())
  ops = loadOpts()
  props = {}
  if ops['report']:
    props['status-report-request']=1
  if ops['class']:
    props['message-class']=0

#  ogsmd.SendMessage(to[0] ,msg, props, reply_handler=dbus_sms_ok, error_handler=partial(dbus_gsm_err, to, msg, bus, win, func_ok, func_err) )

  message = {'Recipient':to[0],'Direction':'out','Folder':'SMS','Content':msg, 'MessageSent':0, 'Processing':1, 'Source':'SMS', 'Timestamp':int(time.time()), 'Timezone':time.tzname[time.daylight]}

  for field in props:
    message['SMS-'+field]=props[field]

  if callable(func_status):
    func_status('storing')

  messages = getDbusObject (bus, "org.freesmartphone.opimd", "/org/freesmartphone/PIM/Messages", "org.freesmartphone.PIM.Messages")
  messages.Add(message, reply_handler=partial(dbus_opimd_ok, to, msg, props, bus, win, func_ok, func_err, func_status), error_handler=partial(dbus_opimd_err, to, msg, props, bus, win, func_ok, func_err, func_status))

  inwin.delete()

def inwindelete(win, func_status, *args, **kwargs):
  if callable(func_status):
    func_status('cancelled')
  win.delete()

def saveOpts(optsval):
  parser = ConfigParser.SafeConfigParser()
  parser.read(CONF_FILE)
  section = 'SMS'
  for opt in optsval:
    key = opt
    value = optsval[opt].state_get()
    try:
      parser.set( section, key, str(value) )
    except ConfigParser.NoSectionError:
      parser.add_section( section )
      parser.set( section, key, str(value) )
  parser.write(open(CONF_FILE, 'w'))

def loadOpts():
#  return {'charset':True} # FIXME
  parser = ConfigParser.SafeConfigParser()
  parser.read(CONF_FILE) 
  try:
    options = parser.options( 'SMS' )
  except ConfigParser.NoSectionError:
    return {}
  else:
    ops = {}
    for opt in options:
      try:
        ops[opt] = parser.getboolean('SMS', opt )
      except:
        ops[opt] = optsdef[opt]

    return ops


def hide_opts(pager, optsval, *args, **kwargs):
  saveOpts(optsval)
  pager.content_pop()

def show_opts(pager, *args, **kwargs):
  box = elementary.Box(pager)
  box.show()

  scroller = elementary.Scroller(pager)
  scroller.show()
  scroller.bounce_set(0, 0)
  scroller.size_hint_weight_set(1.0, 1.0)
  scroller.size_hint_align_set(-1.0, -1.0)
  box.pack_start(scroller)

  oframe = elementary.Frame(pager)
  oframe.label_set(_("Options"))
  oframe.show()
  oframe.style_set('pad_small')
  oframe.size_hint_weight_set(1.0, 1.0)
  oframe.size_hint_align_set(-1.0, -1.0)


  obox = elementary.Box(oframe)
  obox.show()

  optsconf = loadOpts()

  optsval = {}

  """
  report = elementary.Check(obox)
  report.label_set('request delivery report')
  report.show()
  report.size_hint_weight_set(1.0, 0.0)
  report.size_hint_align_set(0.0, 0.0)
  obox.pack_end(report)

  charset = elementary.Check(obox)
  charset.label_set('force GSM ASCII charset')
  charset.show()
  charset.size_hint_weight_set(-1.0, 0.0)
  charset.size_hint_align_set(-1.0, 0.0)
  obox.pack_end(charset)

  store = elementary.Check(obox)
  store.label_set('store SMS in outbox')
  store.show()
  store.size_hint_weight_set(-1.0, 0.0)
  store.size_hint_align_set(-1.0, 0.0)
  obox.pack_end(store)

  flash = elementary.Check(obox)
  flash.label_set('send as Class 0')
  flash.show()
  flash.size_hint_weight_set(-1.0, 0.0)
  flash.size_hint_align_set(-1.0, 0.0)
  obox.pack_end(flash)

  csm = elementary.Check(obox)
  csm.label_set('ask before sending CSM')
  csm.show()
  csm.size_hint_weight_set(-1.0, 0.0)
  csm.size_hint_align_set(-1.0, 0.0)
  obox.pack_end(csm)
  """

  for opt in opts:
    chk = elementary.Check(obox)
    chk.label_set(opts[opt])
    chk.show()
    chk.size_hint_weight_set(-1.0, 0.0)
    chk.size_hint_align_set(-1.0, 0.0)
    obox.pack_end(chk)
    try:
      chk.state_set(optsconf[opt])
    except:
      chk.state_set(optsdef[opt])
    optsval[opt] = chk

  button = elementary.Button(pager)
  button.label_set(_("Back"))
  button.show()
  button._callback_add('clicked', partial(hide_opts, pager, optsval))
  button.size_hint_weight_set(-1.0, 0.0)
  button.size_hint_align_set(-1.0, 0.0)
  box.pack_end(button)

  oframe.content_set(obox)
  scroller.content_set(oframe)

  pager.content_push(box)

def update_chars(label, obj, *args, **kwargs):
  label.label_set("(%d)" % len(obj.markup_to_utf8(obj.entry_get())))

def reply(to, text, bus, win, func_ok, func_err, func_status, *args, **kwargs):
  inwin = elementary.InnerWindow(win)
  win.resize_object_add(inwin)
  inwin.show()
#  inwin.style_set("minimal")

  pager = elementary.Pager(inwin)
  inwin.content_set(pager)
  pager.show()

  box = elementary.Box(inwin)
  box.show()

  tbox = elementary.Box(inwin)
  tbox.show()
  tbox.horizontal_set(1)  

  label = elementary.Label(inwin)
  label.label_set(_("To: ")+elementary.Entry.utf8_to_markup(to[1]))
  label.show()
  tbox.pack_start(label)

  chars = elementary.Label(inwin)
  chars.label_set("(%d)" % len(text))
  chars.show()
  tbox.pack_end(chars)

  tbox.size_hint_weight_set(-1.0, 0.0)
  tbox.size_hint_align_set(-1.0, -1.0)

  chars.size_hint_weight_set(1.0, 0.0)
  chars.size_hint_align_set(1.0, -1.0)

  box.pack_start(tbox)
  scroll = elementary.Scroller(inwin)
  entry = elementary.Entry(inwin)
  if text:
    entry.entry_set(entry.utf8_to_markup(text))
  entry._callback_add('changed', partial(update_chars, chars, entry))
  entry.size_hint_weight_set(1.0, 1.0)
  entry.size_hint_align_set(-1.0, -1.0)
  entry.show()
  scroll.content_set(entry)
  scroll.size_hint_weight_set(1.0, 1.0)
  scroll.size_hint_align_set(-1.0, -1.0)
  scroll.show()
  box.pack_end(scroll)

  hbox = elementary.Box(win)
  hbox.size_hint_weight_set(1.0, 0.0)
  hbox.size_hint_align_set(-1.0, 0.0)
  hbox.horizontal_set(1)
  hbox.homogenous_set(1)
  hbox.show()

  opts = elementary.Button(inwin)
  opts.label_set(_("Options"))
  opts.size_hint_weight_set(1.0, 0.0)
  opts.size_hint_align_set(-1.0, 0.0)
  opts.show()
  opts._callback_add('clicked', partial(show_opts, pager))
  hbox.pack_end(opts)

  hide = elementary.Button(inwin)
  hide.label_set(_("Close"))
  hide.size_hint_weight_set(1.0, 0.0)
  hide.size_hint_align_set(-1.0, 0.0)
  hide.show()
  hide._callback_add('clicked', partial(inwindelete, inwin, func_status))
  hbox.pack_end(hide)

  send = elementary.Button(inwin)
  send.label_set(_("Send"))
  send.size_hint_weight_set(1.0, 0.0)
  send.size_hint_align_set(-1.0, 0.0)
  send.show()
  send._callback_add('clicked', partial(send_msg, to, entry, bus, inwin, win, func_ok, func_err, func_status))

  hbox.pack_start(send)

  box.pack_end(hbox)

  box.size_hint_weight_set(-1.0, -1.0)
  box.size_hint_align_set(-1.0, -1.0)

#  inwin.content_set(box)
  pager.content_push(box)
  box.show()
  inwin.activate()

