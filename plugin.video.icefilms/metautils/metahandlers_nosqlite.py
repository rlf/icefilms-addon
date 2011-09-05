'''
These classes cache non-existant metadata from TheMovieDB and TVDB.
It DOESN'T use sqlite

Currently supports only TheMovieDB, but is scheduled to support TVDB.

It uses themoviedb JSON api class and TVDB XML api class.
They can both be found in the same folder.

*Metahandlers created for Icefilms addon Release v1.0.0

*Credits: Daledude / Anarchintosh 

*Last Updated: 9th/Febuary/2011
    
*To-Do:
- write a clean database function (correct imgs_prepacked by checking if the images actually exist)
  for pre-packed container creator. also retry any downloads that failed.
  also, if  database has just been created for pre-packed container, purge all images are not referenced in database.
- split into two files; containerhandlers.py and metadata.py


'''

import os
from pprint import pprint
import re
import sys
import urllib
import urllib2
import cStringIO
import string
import shutil
import clean_dirs

from TMDB import TMDB

def get_dir(mypath, dirname):
    #...creates sub-directories if they are not found.
    subpath = os.path.join(mypath, dirname)
    if not os.path.exists(subpath):
        os.makedirs(subpath)
    return subpath

def bool2string(myinput):
    #neatens up usage of preparezip flag.
    if myinput is False:
        myoutput = 'false'
        return myoutput
    elif myinput is True:
        myoutput = 'true'
        return myoutput

def Movie_URL_List():
        iceurl='http://www.icefilms.info/'
        mvurl=iceurl+'movies/a-z/'

        finallist=[]

        #Generate A-Z icefilms movie url list and return it
        AZ=list([chr(i) for i in xrange(ord('A'), ord('Z')+1)])
        AZ.append('1')
        for theletter in AZ:
                myurl=mvurl+theletter
                finallist.append(myurl)

        #append the urls of the other categories
        finallist.append(iceurl+'music/a-z/1')
        finallist.append(iceurl+'standup/a-z/1')
        finallist.append(iceurl+'other/a-z/1')

        return finallist

def GetURL(url):
     #print 'processing url: '+url
     req = urllib2.Request(url)
     req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')       
     response = urllib2.urlopen(req)
     link=response.read()
     response.close()
     return link

def cleanUnicode(string):   
    try:
         fixed_string = unicodedata.normalize('NFKD', string).encode('ascii','ignore')
         #print 'THE STRING:',fixed_string
         return fixed_string
    except:
         return string

class MetaContainer:       

    def Create_Icefilms_Container(self,outpath):

        #create container working directory
        workdir=os.path.join(outpath,'Generated Icefilms Container')
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        print 'BUILDING CONTAINER IN:',workdir

        #Initialise meta class, set it to download images.
        meta=MovieMetaData(workdir, preparezip=True)

        #code to scrape A-Z of all movies on icefilms.
        mvinks=Movie_URL_List()
        for myaz in mvinks:
            print 'GETTING METADATA FOR ALL ENTRIES ON: '+myaz
            link=GetURL(myaz)
            match=re.compile('<a name=i id=(.+?)></a><img class=star><a href=/(.+?)>(.+?)<br>').findall(link)

            #For all results run the class
            for imdb_id,url,name in match:
                meta.get_movie_meta(imdb_id)

        print 'Container Making is Finished'

        print 'Cleaning image directory of empty sub-directories [Running clean_dirs.py]'
        cd=clean_dirs.DirCleaner()
        mvcovers=os.path.join(workdir,'meta_caches','themoviedb','covers')
        cd.DelEmptyFolders(mvcovers)

    def _del_metadir(self,path):
        #pass me the path the meta_caches is in

        meta_caches=os.path.join(path,'meta_caches')
        
        #Nuke the old meta_caches folder (if it exists) and install this meta_caches folder.
        #Will only ever delete a meta_caches folder, so is farly safe (won't delete anything it is fed)

        if os.path.exists(meta_caches):
                try:
                    shutil.rmtree(meta_caches)
                except:
                    print 'Failed to delete old meta'
                    return False
                else:
                    print 'deleted old meta'
                    return True

    def _del_path(self,path):

        if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except:
                    print 'Failed to delete old meta'
                    return False
                else:
                    print 'deleted old meta'
                    return True

    def Install_Icefilms_Container(self,workingdir,containerpath,dbtype,installtype):

        #NOTE: This function is handled by higher level functions in the Default.py
        
        if xbmc_imported==True:

            if dbtype=='tvdb' or dbtype=='themoviedb':

                if installtype == 'database' or installtype == 'covers' or installtype == 'backdrops':

                    meta_caches=os.path.join(workingdir,'meta_caches')
                    cachepath=os.path.join(meta_caches,dbtype)

                    if not os.path.exists(meta_caches):
                        #create the meta folders if they do not exist
                        make_dirs(workingdir)

                    if installtype=='database':
                        #delete old db files
                        if dbtype=='themoviedb':
                            try:
                                os.remove(os.path.join(cachepath,'movie_cache.db'))
                            except:
                                pass

                        #extract the db zip to 'themoviedb' or 'TVDB'
                        self._extract_zip(containerpath,cachepath)

                    if installtype=='covers' or installtype=='backdrops':
                        #delete old folders
                        deleted=self._del_path(os.path.join(cachepath,installtype))

                        #extract the covers or backdrops folder zip to 'themoviedb' or 'TVDB'
                        if deleted == True:
                                self._extract_zip(containerpath,cachepath)

                else:
                    print 'not a valid installtype:',installtype
                    return False

            else:
                print 'not a valid dbtype:',dbtype
                return False
        else:                          
            print 'Not running under xbmc :( install container function unavaliable.'

def make_dirs(path):
        # make the necessary directories, without having to initialise the class (and connect to db etc)
        mainpath = get_dir(path, 'meta_caches')

        tvpath = get_dir(mainpath, 'tvdb')
        tvcovers = get_dir(tvpath, 'covers')
        tvbackdrops = get_dir(tvpath, 'backdrops')

        mvpath = get_dir(mainpath, 'themoviedb')
        mvcovers = get_dir(mvpath, 'covers')
        mvbackdrops = get_dir(mvpath, 'backdrops')

class MovieMetaData:
    def __init__(self, path, preparezip=False):
        #this init auto-constructs necessary folder hierarchies.

        self.mainpath = get_dir(path, 'meta_caches')

        # control whether class is being used to prepare pre-packaged .zip
        self.classmode = bool2string(preparezip)

        self.tvpath = get_dir(self.mainpath, 'tvdb')
        self.tvcache = os.path.join(self.tvpath, 'tv_cache.db')
        self.tvcovers = get_dir(self.tvpath, 'covers')
        self.tvbackdrops = get_dir(self.tvpath, 'backdrops')

        self.mvpath = get_dir(self.mainpath, 'themoviedb')
        self.mvcache = os.path.join(self.mvpath, 'movie_cache.db')
        self.mvcovers = get_dir(self.mvpath, 'covers')
        self.mvbackdrops = get_dir(self.mvpath, 'backdrops')

        # connect to db at class init and use it globally
        self.cache = dict()

    # cleanup db when object destroyed
    def __del__(self):
        self.cache = False

    def _downloadimages(self,meta,mediatype,imdb_id):
          
          if mediatype=='movies':
               cover_folder=os.path.join(self.mvcovers,imdb_id)

               if not os.path.exists(cover_folder):
                   os.makedirs(cover_folder)

               cover_name=self._picname(meta['cover_url'])
               cover_path = os.path.join(cover_folder, cover_name)

               self._dl_code(meta['cover_url'],cover_path)
               

               #backdrop_name=self._picname(meta['backdrop_url'])
               #backdrop_path = os.path.join(self.mvbackdrops, backdrop_name)

               
               #self._dl_code(meta['backdrop_url'],backdrop_path)
               
          if mediatype=='tvshow':
               outpath = os.path.join(self.tvimgpath, 'hi')
          if mediatype=='episode':
               pass
   
    def _picformat(self,url):
        #get image format from url (ie .jpg)
        picformat = re.split('\.+', url)
        return picformat[-1]

    def _picname(self,url):
        #get image name from url (ie my_movie_poster.jpg)
        picname = re.split('\/+', url)
        return picname[-1]
         
        
    def _dl_code(self,url,mypath):
        if url.startswith('http://'):
          try:
               req = urllib2.Request(url)
               response = urllib2.urlopen(req)
               data=response.read()
               response.close()
               fh = open(mypath, 'wb')
               fh.write(data)  
               fh.close()
               #return True
          except:
              print 'image download failed: ',url
              #return False
        else:
            if url is not None:
                print 'not a valid url: ',url
            #return False


#--------------------------------Start of Movie cache handling code ----------------#

        
    def get_movie_meta(self, imdb_id):

        # add the tt if not found. integer aware.
        imdb_id=str(imdb_id)
        if not imdb_id.startswith('tt'):
                imdb_id = "tt%s" % imdb_id

        meta = self._cache_lookup_movie_by_imdb(imdb_id)

        if meta is None:
            #print "adding to cache and getting metadata from web"
            meta = self._get_tmdb_meta_data(imdb_id)
            self._cache_save_movie_meta(meta)

            #if creating a metadata container, download the images.
            if self.classmode is 'true':
                self._downloadimages(meta,'movies',imdb_id)

        if meta is not None:

            #if cache row says there are pre-packed images,..
            if meta['imgs_prepacked'] == 'true':

                    #define the image paths
                    cover_path=os.path.join(self.mvcovers,imdb_id,self._picname(meta['cover_url']))
                    #backdrop_path=os.path.join(self.mvbackdrops,imdb_id,self._picname(meta['backdrop_url']))

                    #if paths exist, replace the urls with paths
                    if self.classmode is 'false':              
                        if os.path.exists(cover_path):
                            meta['cover_url'] = cover_path
                        #if os.path.exists(backdrop_path):
                        #    meta['backdrop_url'] = backdrop_path
                        
                    #try some image redownloads if building container
                    elif self.classmode is 'true':                                              
                        if not os.path.exists(cover_path):
                                self._downloadimages(meta,'movies',imdb_id)

                        #if not os.path.exists(backdrop_path):
                        #        self._downloadimages(meta,'movies',imdb_id)

        meta['plot']=cleanUnicode(meta['plot'])    
        #Return the values to XBMC
        return meta
    
    def _cache_lookup_movie_by_imdb(self, imdb_id):
        return self.cache.get(imdb_id)

    def _cache_save_movie_meta(self, meta):
        # use named-parameter binding for lazyness
        self.cache[meta['imdb_id']] = meta

    # this will return a dict. it must also return an empty dict when
    # no movie meta info was found from tmdb because we should cache
    # these "None found" entries otherwise we hit tmdb alot.
    def _get_tmdb_meta_data(self, imdb_id):
        #get metadata text using themoviedb api
        tmdb = TMDB()
        md = tmdb.imdbLookup(imdb_id)
        if md is None:
            # create an empty dict so below will at least populate empty data for the db insert.
            md = {}

        # copy tmdb to our own for conformity and eliminate KeyError.
        # we set a default value for those keys not returned by tmdb.
        meta = {}
        meta['imdb_id'] = imdb_id
        meta['tmdb_id'] = md.get('id', '')
        meta['name'] = md.get('name', '')
        meta['rating'] = md.get('rating', 0)
        meta['duration'] = md.get('runtime', 0)
        meta['plot'] = md.get('overview', '')
        meta['mpaa'] = md.get('certification', '')
        meta['premiered'] = md.get('released', '')
        meta['trailer_url'] = md.get('trailer', '')

        meta['genres'] = ''
        meta['studios'] = ''
        try:
            meta['genres'] = (md.get('genres', '')[0])['name']
        except:
            try:
                meta['genres'] = (md.get('genres', '')[1])['name']
            except:
                try:
                    meta['genres'] = (md.get('genres', '')[2])['name']
                except:
                    try:    
                        meta['genres'] = (md.get('genres', '')[3])['name']
                    except:
                        #print 'genres failed: ',md.get('genres', '')
                        pass

        try:
            meta['studios'] = (md.get('studios', '')[0])['name']
        except:
            try:
                meta['studios'] = (md.get('studios', '')[1])['name']
            except:
                try:
                    meta['studios'] = (md.get('studios', '')[2])['name']
                except:
                    try:    
                        meta['studios'] = (md.get('studios', '')[3])['name']
                    except:
                        #print 'studios failed: ',md.get('studios', '')
                        pass
                        

        #meta['cast'] = md.get('cast', '')
        
        #set whether that database row will be accompanied by pre-packed images.
        meta['imgs_prepacked'] = self.classmode

        # define these early cuz they must exist whether posters do or not
        meta['thumb_url'] = ''
        meta['cover_url'] = ''
        if md.has_key('posters'):
            # find first thumb poster url
            for poster in md['posters']:
                if poster['image']['size'] == 'thumb':
                    meta['thumb_url'] = poster['image']['url']
                    break
            # find first cover poster url
            for poster in md['posters']:
                if poster['image']['size'] == 'cover':
                    meta['cover_url'] = poster['image']['url']
                    break

        meta['backdrop_url'] = ''
        if md.has_key('backdrops'):
            # find first original backdrop url
            for backdrop in md['backdrops']:
                if backdrop['image']['size'] == 'original':
                    meta['backdrop_url'] = backdrop['image']['url']
                    break

        return meta

