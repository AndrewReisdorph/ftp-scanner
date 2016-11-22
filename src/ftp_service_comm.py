import socket
import struct
import json
import time

MAX_READ = 4096
DEFAULT_PORT = 1024

# commands
ADD_FILE_TO_QUEUE = 'AFTQ'
GET_OVERALL_STATUS = 'GOST'
CANCEL_DOWNLOAD = 'CANC'
REMOVE_FILE_DOWNLOAD = 'REMV'

# connection retries
RETRIES = 5
RETRY_PAUSE_TIME = 3

LENGTH_PACK_STR = '<L'

class Host( object ):
   """
   Class to act as a network host for ftp_download_service
   """

   def __init__( self, dl_service, port=None ):
      """
      init the host
      @param dl_service: ftp download service object
      @type dl_service: ftp_download_service.DownloadService instance
      @param port: port to listen on
      @type port: int
      """
      self.dl_service = dl_service
      if port is None:
         self.port = DEFAULT_PORT
      else:
         self.port = port
      self.cmd_functions = { ADD_FILE_TO_QUEUE: self.add_file_to_queue,
                             GET_OVERALL_STATUS: self.get_overall_status,
                             CANCEL_DOWNLOAD: self.cancel_download,
                             REMOVE_FILE_DOWNLOAD: self.remove_file_download }


   def start_listener( self ):
      """
      Starts the host listener
      """
      while True:
         # create an INET, STREAMing socket
         serversocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
         serversocket.bind(('0.0.0.0', self.port))
         serversocket.listen(1)
         connection, client_address = serversocket.accept()

         # get client's command to run
         data = receive_with_length( connection )

         cmd = data[ 0:4 ]
         arg_str = data[ 4:: ]

         # get desired function handle
         fn_to_call = self.cmd_functions[ cmd ]
         # call desired function
         resp = fn_to_call( arg_str )
         # send response
         send_with_length( connection, resp )

         # close socket
         connection.close( )

   def add_file_to_queue( self, url ):
      """
      add a file to the DL service queue
      @param url: full url of the file to download
      @type url: string
      """
      self.dl_service.add_file_to_queue( url )
      return 'file added'

   def get_overall_status( self, argstr ):
      """
      Ping the status of the dl service
      @param argstr: empty string
      @type argstr: string
      @return: status dictionary serialized as json
      """
      status_dict =  self.dl_service.get_overall_status( )
      return json.dumps( status_dict )

   def cancel_download( self, uid ):
      """
      Cancels a file download
      @param uid: unique identifier from a file status dictionary
      @type uid: string
      @return: True for success, False if the uid was not found
      """
      stat = self.dl_service.cancel_file_download( uid )
      return json.dumps( stat )

   def remove_file_download( self, uid ):
      """
      removes a file downloader from status list
      @param uid: unique identifier from a file status dictionary
      @type uid: string
      """
      self.dl_service.remove_file_download( uid )
      return ''


class Client( object ):
   """
   Class to manage a client connection to a DL service host
   """

   def __init__( self, host_ip, host_port=DEFAULT_PORT ):
      """
      Init the client
      @param host_ip: ip/hostname of the host service
      @type: string
      @param host_port: port the host service is listening on
      @type port: int
      """
      self.host_ip = host_ip
      self.host_port = host_port

   def _connect_to_host( self ):
      """
      establish connection to host
      """
      retryNum = 0
      while retryNum < RETRIES:
         try:
            # create main listener socket
            socketToHost = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            socketToHost.connect( ( self.host_ip, self.host_port ) )
            break
         except socket.error as theE:
            retryNum += 1
            if retryNum == RETRIES:
               raise theE
            print 'Unable to connect to %s:%d.  Retying %d more times.' % ( self.host_ip, self.host_port, RETRIES - retryNum )
            time.sleep( RETRY_PAUSE_TIME )

      return socketToHost

   def add_file_to_queue( self, url ):
      """
      add a file to the DL service queue
      @param url: full url of the file to download
      @type url: string
      """
      socket_to_host = self._connect_to_host( )
      send_buff = ADD_FILE_TO_QUEUE + url
      print 'sending ', send_buff
      send_with_length( socket_to_host, send_buff )
      response = receive_with_length( socket_to_host )
      print response
      socket_to_host.close( )

   def get_overall_status( self ):
      """
      Ping the status of the dl service
      @param argstr: empty string
      @type argstr: string
      @return: status dictionary serialized as json
      """
      socket_to_host = self._connect_to_host( )
      send_buff = GET_OVERALL_STATUS
      send_with_length( socket_to_host, send_buff )
      response = receive_with_length( socket_to_host )
      socket_to_host.close( )

      # parse response
      status_dict = json.loads( response )
      return status_dict

   def cancel_download( self, uid ):
      """
      Ping the status of the dl service
      @param argstr: empty string
      @type argstr: string
      @return: status dictionary serialized as json
      """
      socket_to_host = self._connect_to_host( )
      send_buff = CANCEL_DOWNLOAD + uid
      send_with_length( socket_to_host, send_buff )
      response = receive_with_length( socket_to_host )
      socket_to_host.close( )

      # parse response
      return json.loads( response )

   def remove_file_download( self, uid ):
      """
      Ping the status of the dl service
      @param argstr: empty string
      @type argstr: string
      @return: status dictionary serialized as json
      """
      socket_to_host = self._connect_to_host( )
      send_buff = REMOVE_FILE_DOWNLOAD + uid
      send_with_length( socket_to_host, send_buff )
      response = receive_with_length( socket_to_host )
      socket_to_host.close( )


def receive_with_length( socket_connection ):
   # get the length of the data
   length_pack = socket_connection.recv( 4 )
   length = struct.unpack( LENGTH_PACK_STR, length_pack )[ 0 ]
   bytes_rec = len( length_pack )

   # make sure all bytes were received
   data = ''
   while bytes_rec < length:
      bytes_to_read = MAX_READ if ( length - bytes_rec ) > MAX_READ else ( length - bytes_rec )
      data += socket_connection.recv( bytes_to_read )
      bytes_rec += bytes_to_read

   return data

def send_with_length( socket_connection, buffer ):
   len_resp = struct.pack( LENGTH_PACK_STR, len( buffer )+4 )  # add 4 to account for length header
   # send response
   socket_connection.send( len_resp + buffer )
