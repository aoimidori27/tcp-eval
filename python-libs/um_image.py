#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
from logging import info, debug, warn, error

# umic-mesh imports
import um_config as config


class Image(object):
    """Provides access to information about a certain UMIC-Mesh.net image."""
    
    def __init__(self, imagetype, imageversion = "default"):
        """
        Creates a new Image object on the basis of the imagetype and the
        optional parameter imageversion.
        """

        # object variables
        self._type = None
        self._info = None
        self._version = None
        
        # validity check of the imagetype
        if imagetype not in Image.gettypes():
            raise ImageException('Invalid "imagetype". Please set it to one of '\
                                 'the following: %s' % Image.gettypes())
        
        self._type = imagetype
        self._info = config.imageinfos[self._type]

        # validity check of the imageversion        
        if not imageversion in self.getversions():
            raise ImageException('Invalid "imageversion". Please set it to one of '\
                                 'the following: %s' % self.getversions())
        
        self._version = imageversion
                   

    @staticmethod
    def getrepository():
        """Return the url of UMIC-Mesh.net repository"""

        return config.imageinfos["common"]["repository"]


    @staticmethod
    def getimageprefix():
        """Return the path prefix where the image is located"""

        return config.imageinfos["common"]["imageprefix"]


    @staticmethod
    def getbootprefix():
        """Return the path prefix where the boot files are located"""

        return config.imageinfos["common"]["bootprefix"]


    @staticmethod
    def getsvnprefix():
        """Return the path prefix where the checkout is located"""

        return config.imageinfos["common"]["svnprefix"]


    @staticmethod
    def gettypes():
        """Return the names of the possible image types"""
        
        types = config.imageinfos.keys()
        return list(set(types).difference(["common"]))
        

    def gettype(self):
        """Return the type of the image"""

        return self._type


    def getinfo(self):
        """Return all information about the image"""

        return self._info


    def getversion(self):
        """Return the current version of the image"""
        
        return self._version


    def getversions(self):
        """Return all possible versions for the image"""
         
        versions = []
        directory = os.path.join(Image.getimageprefix(), self._type)
        
        for name in os.listdir(directory):
            file = os.path.join(directory, name)
            if os.path.isdir(file):
                versions.append(name)
        
        return versions


    def getimagepath(self):
        """Return the full link free path of the image"""

        imagepath = os.path.join(Image.getimageprefix(), self._type, self._version)
        return os.path.realpath(imagepath)



class ImageException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
