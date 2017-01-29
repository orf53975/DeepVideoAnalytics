import shlex,json,os
import subprocess as sp
import indexer
import numpy as np

class WQuery(object):

    def __init__(self,dquery,media_dir):
        self.media_dir = media_dir
        self.dquery = dquery
        self.primary_key = self.dquery.pk
        self.local_path = "{}/queries/{}.png".format(self.media_dir,self.primary_key)

    def find(self,n=10):
        results = {}
        for index_name,index in indexer.INDEXERS.iteritems():
            results[index_name] = []
            index.load_index(path=self.media_dir)
            results[index_name]= index.nearest(image_path=self.local_path,n=n)
        return results

class WVideo(object):

    def __init__(self,dvideo,media_dir):
        self.dvideo = dvideo
        self.key = self.dvideo.key
        self.primary_key = self.dvideo.pk
        self.bucket = self.dvideo.bucket
        self.file_name = self.key.split('/')[-1]
        self.media_dir = media_dir
        self.local_path = "{}/{}/video/{}.mp4".format(self.media_dir,self.primary_key,self.primary_key)
        self.duration = None
        self.width = None
        self.height = None
        self.metadata = {}

    def get_metadata(self):
        command = ['ffprobe','-i',self.local_path,'-print_format','json','-show_format','-show_streams','-v','quiet']
        p = sp.Popen(command,stdout=sp.PIPE,stderr=sp.STDOUT,stdin=sp.PIPE)
        p.wait()
        output, _ = p.communicate()
        self.metadata = json.loads(output)
        try:
            self.duration = float(self.metadata['format']['duration'])
            self.width = float(self.metadata['streams'][0]['width'])
            self.height = float(self.metadata['streams'][0]['height'])
        except:
            raise ValueError,str(self.metadata)

    def extract_frames(self):
        frames = []
        frame_seconds = set()
        for i in range(int(self.duration)):
            if i % 10 == 0:
                frame_seconds.add(i)
                frame_seconds.add(i+1)
        output_dir = "{}/{}/{}/".format(self.media_dir,self.primary_key,'frames')
        for s in frame_seconds:
            fname = "{}.jpg".format(s)
            command = 'ffmpeg -accurate_seek -ss {} -i {} -y -frames:v 1 -vf scale=600:-1 {}/{}'.format(s,
                                                                                                     self.local_path,
                                                                                                     output_dir,fname)
            extract = sp.Popen(shlex.split(command))
            extract.wait()
            if extract.returncode != 0:
                raise ValueError
            f = WFrame(time_seconds=s,video=self)
            if extract.returncode != 0:
                raise ValueError
            frames.append(f)
        return frames

    def index_frames(self,frames):
        results = []
        wframes = [WFrame(video=self, time_seconds=df.time_seconds) for df in frames]
        for index_name,index in indexer.INDEXERS.iteritems():
            index.load()
            results.append(index.index_frames(wframes,self))
        return results


class WFrame(object):

    def __init__(self,time_seconds=None,video=None):
        if video:
            self.time_seconds = time_seconds
            self.video = video
        else:
            self.time_seconds = None
            self.video = None

    def local_path(self):
        return "{}/{}/{}/{}.jpg".format(self.video.media_dir,self.video.primary_key,'frames',self.time_seconds)

