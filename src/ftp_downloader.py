"""
Module to handle FTP transfers and status
"""

import time
import ftplib
import urllib
import os

NUM_BLOCK_FOR_TIME_CALCULATION = 30

QUEUED = 0
DOWNLOADING = 1
COMPLETE = 2
FAILED = 3
CANCELLED = 4

class Cancelled( Exception ):
   pass

class ftp_monitor( object ):
   """
   Class to handle FTP operations
   """

   def __init__( self, url_obj, status_obj ):
      """
      Initialize the object
      @param url_obj: parsed url
      @type url_obj: urlparse.ParseResult
      @param status_obj: file status object
      @type ftp_download_service.FileStatus
      """

      self.cancel_request = False
      self.bytes_transferred = 0
      self.src_file_size = 0
      self.last_block_time = 0
      self.num_blocks = 0
      self.block_sum = 0

      self.url_obj = url_obj
      # create an ftp connection to the server
      self.ftp_conn = ftplib.FTP( host=url_obj.netloc, user=url_obj.username, passwd=url_obj.password )
      self.ftp_conn.login( )
      self.status_obj = status_obj

   def download_file( self, destination_dir, destination_name=None ):
      """
      Downloads the file
      @param destination_dir: directory to save file
      @type destination_dir: string
      @param destination_name: Name of the file to save
      @type destination_name: string
      """
      src_file_path = urllib.unquote( self.url_obj.path )
      src_file_dir = os.path.dirname( src_file_path )
      if destination_name is None:
         destination_name = os.path.basename( src_file_path )
      self.status_obj.status = DOWNLOADING

      self.ftp_conn.cwd( src_file_dir )
      self.ftp_conn.voidcmd('TYPE I')
      try:
         self.src_file_size = self.ftp_conn.size( src_file_path )
      except:
         print 'Unable to get file size'
         self.src_file_size = None

      if not os.path.isdir( destination_dir ):
         os.makedirs( destination_dir )

      destination_file = os.path.join( destination_dir, destination_name )

      try:
         with open( destination_file, 'wb' ) as fid:
            self.ftp_conn.retrbinary( 'RETR ' + src_file_path, lambda( blk ): self.file_callback( blk, fid ) )
         self.status_obj.status = COMPLETE
      except Cancelled:
         self.status_obj.status = CANCELLED
      except Exception as the_error:
         self.status_obj.status = FAILED
         self.status_obj.error = the_error

   def file_callback( self, block, fid ):
      """
      File callback for ftp download method
      @param block: current block of data
      @type block: binary string
      @param fid: current working file handle
      @type fid: file handle
      """
      if self.cancel_request:
         raise( Cancelled( 'File download cancelled' ) )

      # write the block to the file
      self.bytes_transferred += len( block )
      fid.write( block )

      # calculate progress
      if self.src_file_size is not None:
         self.status_obj.progress = self.bytes_transferred / float( self.src_file_size )
      else:
         self.status_obj.progress = -1.0

      # initialize last_block_time
      if self.last_block_time == 0:
         self.last_block_time = time.time( )

      # keep track of number of blocks read
      self.num_blocks += 1
      # keep track of size of blocks read
      self.block_sum += len( block )

      # calculate transfer rate
      if self.num_blocks >= NUM_BLOCK_FOR_TIME_CALCULATION:
         current_time = time.time( )
         elapsed_time = current_time - self.last_block_time
         if elapsed_time > 0.0:
            self.last_block_time = current_time
            byterate = self.block_sum / elapsed_time
            self.status_obj.transfer_rate_str = convert_byterate_to_str( byterate )
            self.num_blocks = 0
            self.block_sum = 0

   def cancel_download( self ):
      """
      Cancels a current download
      """
      self.cancel_request = True


def convert_byterate_to_str( byterate ):
   """
   Converts a transfer rate to a string
   @param byterate: transfer rate in BYTES per second
   @type byterate: int
   @return: formatted string of transfer rate
   """
   kb_rate = byterate / 1024.0
   mb_rate = kb_rate / 1024.0
   gb_rate = mb_rate / 1024.0

   if gb_rate > 1.0:
      rate = gb_rate
      prefix = 'G'
   elif mb_rate > 1.0:
      rate = mb_rate
      prefix = 'M'
   elif kb_rate > 1.0:
      rate = kb_rate
      prefix = 'K'
   else:
      rate = byterate
      prefix = ''

   return '{: 8.3f} {}B/s'.format( rate, prefix )
