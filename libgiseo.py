import requests
import urllib
import hashlib
import time
import json

def md5 (string: str):
  return hashlib.md5 (string.encode ()).hexdigest ()

class Manager:
  # token for accessing giseo.rkomi.ru (default null)
  token: str = ''
  # cookies, https://developer.mozilla.org/ru/docs/Web/HTTP/Cookies
  cookies: dict = {}

  def __init__ (self, login: str, password: str):
    self.login = login
    self.password = password
    self.auth ()
    self.studentId = self.getStudentId()
  
  def send (self, path: str, method: str | int = 'GET', params: dict = {}, contentType: str = 'x-www-form-urlencoded', headers: dict = {}, withToken: bool = True, returnJson: bool = True):
    """
    Sending the request to https://giseo.rkomi.ru/webapi

    Parameters
    ----------
    path: str
      path to webapi (PATH_HERE -> https://giseo.rkomi.ru/webapi/PATH_HERE)
    
    method: str = GET
      method of request, GET or POST
    
    params: dict = {}
      request params
    
    contentType: str = x-www-form-urlencoded
      Content Type used in request headers, for example json or x-www-form-urlencoded
    
    headers: dict = {}
      request headers
    
    withToken: bool = True
      if token is need in request, set withToken to True
    
    returnJson: bool = True
      convert response to JSON and return it, otherwise return response
    """
    with requests.Session () as session:
      cookie: list[str] = []
      for name, value in self.cookies.items ():
        cookie.append (f'{name}={value}')

      # https://developer.mozilla.org/ru/docs/Web/HTTP/Headers
      session.headers = {
        **headers,
        'at': self.token if withToken else None,
        'content-type': f'application/{contentType}; charset=UTF-8',
        # cookies are required to access certain addresses
        'cookie': '; '.join (cookie)
      }

      if (method == 'GET'):
        res = session.get (f'https://giseo.rkomi.ru/webapi/{path}', params=params)
      else:
        res = session.post (f'https://giseo.rkomi.ru/webapi/{path}', data=urllib.parse.urlencode (params) if contentType == 'x-www-form-urlencoded' else json.dumps (params))
      
      if (res.status_code == 200):
        # get new cookies from 'set-cookie' header from response and update self.cookies dictionary
        # Set-Cookie header: https://developer.mozilla.org/ru/docs/Web/HTTP/Headers/Set-Cookie
        self.cookies.update (res.cookies.get_dict ())
        return res.json () if returnJson else res
      elif (res.status_code == 401):
        self.auth ()
        return self.send (path, method, params, contentType, headers, withToken, returnJson)
      elif (res.status_code == 409):
        raise Exception ('Incorrect username or password')
  
  def auth (self):
    res: dict = self.send ('auth/getdata', 'POST', {}, 'x-www-form-urlencoded', { 'Referer': 'https://giseo.rkomi.ru/about.html' }, False, True)
    password = md5 (res['salt'] + md5 (self.password))
    data = self.send ('login', 'POST', {
      'LoginType': '1',
      'cid': '2',
      'sid': '11',
      'pid': '-168',
      'cn': '168',
      'sft': '2',
      'scid': '8',
      'UN': self.login,
      'PW': password[:len (self.password)],
      'lt': res['lt'],
      'pw2': password,
      'ver': res['ver']
    }, 'x-www-form-urlencoded', { 'Referer': 'https://giseo.rkomi.ru/about.html' }, False, True)

    self.token = data['at']

  
  def getDiary (self, start: int, end: int):
    """
      Getting Diary records

      Parameters
      ----------
      start: int
        start day of needed diary in UNIX time
      
      end: int
        end day of needed diary in UNIX time
      
      assigns: bool = False
        if assigns setted to True, they will also return
    """

    sDate = time.localtime (start)
    eDate = time.localtime (end)

    return self.send ('student/diary', 'GET', {
      'studentId': self.studentId,
      'vers': 1651766357690,
      'weekStart': f'{sDate.tm_year}-{str (sDate.tm_mon).zfill (2)}-{str (sDate.tm_mday).zfill (2)}',
      'weekEnd': f'{eDate.tm_year}-{str (eDate.tm_mon).zfill (2)}-{str (eDate.tm_mday).zfill (2)}',
      'yearId': 78678,
      'withLaAssigns': False
    })
  
  def getAttachments (self, assignsIds: list[int]):
    """
    Getting attachments of specified assigns IDs

    Parameters
    ----------
    assignsIds: list[int]
      ID of assign
    """

    return self.send (f'student/diary/get-attachments?studentId={self.studentId}', 'POST', {
      'assignId': assignsIds
    }, 'json')

  def getPastMandatory (self, start: int, end: int):
    """
    Получение пропущенных заданий

    Parameters
    ----------
    start: int
      start day of needed diary in UNIX time
      
    end: int
      end day of needed diary in UNIX time
    
    Возвращает
    ----------
      массив просроченных заданий
    """
    sDate = time.localtime (start)
    eDate = time.localtime (end)
    return self.send ('student/diary/pastMandatory', 'GET', {
      'studentId': self.studentId,
      'weekStart': f'{sDate.tm_year}-{str (sDate.tm_mon).zfill (2)}-{str (sDate.tm_mday).zfill (2)}',
      'weekEnd': f'{eDate.tm_year}-{str (eDate.tm_mon).zfill (2)}-{str (eDate.tm_mday).zfill (2)}',
      'yearId': 78678
    })

  def getStudent (self):
    return self.send ('student/diary/init', 'GET')

  def getStudentId(self):
    s = self.getStudent()
    return s['students'][0]['studentId']
