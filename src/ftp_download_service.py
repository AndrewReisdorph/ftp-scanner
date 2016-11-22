"""
Module to service queueing & downloading files from ftp servers
"""

import Queue
import os
import sys
import collections
import threading
import ftplib
import urlparse
import urllib
import json
import uuid

import ftp_downloader

MAX_WORKERS_PER_SERVER = 2

STATUS_TO_NAME = { ftp_downloader.QUEUED     : 'QUEUED',
                   ftp_downloader.DOWNLOADING: 'DOWNLOADING',
                   ftp_downloader.COMPLETE   : 'COMPLETE',
                   ftp_downloader.FAILED     : 'FAILED',
                   ftp_downloader.CANCELLED  : 'CANCELLED' }

DESTINATION_DIR = 'C:\\test'

class FileStatus( object ):
   """
   Class for tracking file status
   """

   def __init__( self, url_obj ):
      """
      Initialize the file status
      @param url_obj: object containing url info
      @type url_obj: object returned from urlparse.urlparse()
      """
      self.status = ftp_downloader.QUEUED
      self.progress = 0.0
      self.transfer_rate_str = ''
      self.error = None
      self.url_obj = url_obj
      self.server = url_obj.netloc
      self.filename = os.path.basename( urllib.unquote( self.url_obj.path ) )
      self.dirname = os.path.dirname( urllib.unquote( self.url_obj.geturl( ) ) )
      self.uid = uuid.uuid4( ).get_hex( )


class DownloadService( object ):
   """
   Background service for monitoring ftp downloads
   """

   def __init__( self ):
      """
      initialize the service
      """
      self.running = False
      self.server_queues = {}       # 'server ip': queue
      self.workers_per_server = {}  # 'server ip': num_workers
      self.download_task_queue = Queue.Queue( )
      self.exit_request = False
      self.status_list = [ ]
      self.downloader_list = [ ]

   def start( self ):
      """
      Start the service
      """
      self.exit_request = False
      dl_worker = threading.Thread( target=self.download_queue_worker )
      dl_worker.start( )
      self.running = True

   def stop( self ):
      """
      Stop the service
      """
      self.exit_request = True

   def add_file_to_queue( self, file_url ):
      """
      Adds a file to the download queue
      @param file_url: full url of the file to download
      @type file_url: string
      """
      self.download_task_queue.put( file_url )

   def download_queue_worker( self ):
      """
      Worker function for managing download queue
      """
      while not self.exit_request:
         # get next file to download from queue
         file_url = self.download_task_queue.get( )

         # parse the url
         parsed_url = urlparse.urlparse( file_url )
         server = parsed_url.netloc

         # create a file status
         status_obj = FileStatus( parsed_url )
         self.status_list.append( status_obj )

         # create a queue for the server if it doesn't exist yet
         if server not in self.server_queues:
            self.server_queues[ server ] = Queue.Queue( )

         if server not in self.workers_per_server:
            self.workers_per_server[ server ] = 0

         # add file to server queue
         self.server_queues[ server ].put( ( parsed_url, status_obj ) )

         # create a new worker for the server if needed
         if self.workers_per_server[ server ] < MAX_WORKERS_PER_SERVER:
            new_server_worker = threading.Thread( target=self.individual_download_worker, args=( server, ) )
            new_server_worker.start( )
      self.running = False

   def individual_download_worker( self, server ):
      """
      Worker for downloading an individual file
      @param server: ip/hostname of server file is being downloaded from
      @type server: string
      """
      # account for this worker
      self.workers_per_server[ server ] += 1
      while not self.exit_request:
         try:
            # check for a pending file
            ( url_obj, status_obj ) = self.server_queues[ server ].get_nowait( )
         except Queue.Empty:
            # if no file is pending in the queue, the thread can be terminated
            break

         # download the file
         monitor = ftp_downloader.ftp_monitor( url_obj, status_obj )
         self.downloader_list.append( monitor )
         monitor.download_file( DESTINATION_DIR )

      # remove worker in count
      self.workers_per_server[ server ] -= 1

   def get_overall_status( self, do_print=True ):
      """
      Queries the file status of each existing downloader
      @return: dictionary of file status info
      """
      statuses = [ ]
      for status_obj in self.status_list:
         status_dict = {'File': status_obj.filename,
                        'Source': status_obj.dirname,
                        'Rate': status_obj.transfer_rate_str,
                        'Progress': status_obj.progress,
                        'Status': STATUS_TO_NAME[ status_obj.status ],
                        'uid': status_obj.uid}
         statuses.append( status_dict )

      return statuses

   def cancel_file_download( self, status_uid ):
      """
      Cancels a file download
      @param status_uid: unique identifier from a file status dictionary
      @type status_uid: string
      @return: True for success, False if the uid was not found
      """
      success = False
      for downloader in self.downloader_list:
         if downloader.status_obj.uid == status_uid:
            downloader.cancel_download( )
            success = True

      return success

   def remove_file_download( self, status_uid ):
      """
      removes a file downloader from status list
      @param status_uid: unique identifier from a file status dictionary
      @type status_uid: string
      """
      # cancel the download first
      if self.cancel_file_download( status_uid ):
         for downloader in self.downloader_list:
            if downloader.status_obj.uid == status_uid:
               self.downloader_list.remove( downloader )
               break

         for status_obj in self.status_list:
            if status_obj.uid == status_uid:
               self.status_list.remove( status_obj )
               break

def test( src_url, dest_dir ):
   ds = DownloadService( )
   ds.start( )
   return (status_obj, monitor)

if __name__ == '__main__':
   import ftp_service_comm
   if len( sys.argv ) > 1:
      port = int( sys.argv[ 1 ] )
   else:
      port = None
   ds = DownloadService( )
   ds.start( )

   net_host = ftp_service_comm.Host( ds, port=port )
   print 'Host running'
   net_host.start_listener( )
