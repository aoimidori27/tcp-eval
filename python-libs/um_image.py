#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
from logging import info, debug, warn, error

# umic-mesh imports
from um_config import *


class Image(object):
    """Provides access to information about a certain UMIC-Mesh.net image."""
    
    def __init__(self, imagetype):
        """Creates a new Image object on the basis of the imagetype"""

        # object variables
        self._type = None
        self._info = None
        
        # validity check of the imagetype
        if imagetype and imagetype in imageinfos:
            self._type = imagetype
            self._info = imageinfos[self._type]
        else:
            raise ImageException('Invalid "imagetype". Please set it to one of %s.'
                                 % Image.types())                     


    @staticmethod
    def types():
        """Return the names of the possible image types"""
        
        types = imageinfos.keys()
        return list(set(types).difference(["common"]))


    @staticmethod
    def getrepository():
        """Return the common repository url"""

        return imageinfos["common"]["repository"]


    @staticmethod
    def getimageprefix():
        """Return the path prefix where the image is located"""

        return imageinfos["common"]["imageprefix"]

    @staticmethod
    def getbootprefix():
        """Return the path prefix where the boot files is located"""

        return imageinfos["common"]["bootprefix"]


    @staticmethod
    def getsvnprefix():
        """Return the path prefix where the boot checkout is located"""

        return imageinfos["common"]["svnprefix"]


    def gettype(self):
        """Return the type of the image"""

        return self._type


    def getinfo(self):
        """Return the information about the image"""

        return self._info


    def getimagepath(self):
        """Return the imagepath of the image"""

        imagepath = os.path.join(Image.getimageprefix(), self._type)
        return os.path.realpath(imagepath)



class ImageException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
