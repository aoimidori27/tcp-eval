#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
from logging import info, debug, warn, error

# umic-mesh imports
import um_config as config


class Image(object):
    """Provides access to information about a certain UMIC-Mesh.net image."""

    def __init__(self, image_type, image_version = "default"):
        """Creates a new Image object on the basis of the image type and the
           optional parameter image_version.
        """

        # object variables
        self._type = None
        self._info = None
        self._version = None

        # validity check of the image_type and image_version
        if Image.isValidType(image_type) and \
           Image.isValidVersion(image_type, image_version):
            self._type = image_type
            self._info = config.image_info[self._type]
            self._version = image_version

    @staticmethod
    def repositoryUrl():
        """Return the url of UMIC-Mesh.net repository"""
        return config.image_info["common"]["repository"]

    @staticmethod
    def imagePrefix():
        """Return the prefix of the path where the images are located"""
        return config.image_info["common"]["image_prefix"]

    @staticmethod
    def kernelPrefix():
        """Return the prefix of the path where the kernel files are located"""
        return config.image_info["common"]["kernel_prefix"]

    @staticmethod
    def initrdPrefix():
        """Return the prefix of the path where the initrd images are located"""
        return config.image_info["common"]["initrd_prefix"]

    @staticmethod
    def svnPrefix():
        """Return the prefix of the path where the checkout is located"""
        return config.image_info["common"]["svn_prefix"]

    @staticmethod
    def types():
        """Return the names of all possible image types"""
        types = config.image_info.keys()
        return list(set(types).difference(["common"]))

    @staticmethod
    def isValidType(image_type, raiseError = True):
        """Return true if the image type is valid """

        contained = image_type in Image.types()

        if not contained and raiseError:
            raise ImageValidityException('image_type: %s' %image_type, Image.types())

        return contained

    @staticmethod
    def versions(image_type):
        """Return a list of all possible versions for the given image type"""

        Image.isValidType(image_type)
        versions = []
        directory = os.path.join(Image.imagePrefix(), image_type)

        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isdir(path):
                versions.append(name)

        return versions

    @staticmethod
    def isValidVersion(image_type, image_version, raiseError = True):
        """Return true if the image version is valid for the image type"""

        contained = image_version in Image.versions(image_type)

        if not contained and raiseError:
            raise ImageValidityException("image_version", Image.versions(image_type))

        return contained

    def getType(self):
        """Return the image type of the image"""
        return self._type

    def getSvnMappings(self):
        """Return the svn mappings of the image"""
        return self._info["svn_mappings"]

    def getScriptMappings(self):
        """Return the script mappings of the image"""
        return self._info["script_mappings"]

    def getVersion(self):
        """Return the current version of the image"""
        return self._version

    def getVersions(self):
        """Return all possible versions for the image"""

        versions = []
        directory = os.path.join(Image.imagePrefix(), self._type)

        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isdir(path):
                versions.append(name)

        return versions

    def getImagePath(self, canonical_path = True):
        """If canonical_path is true the method will return the canonical path
           of the image. Otherwise the image path relative to the path prefix
           (Image.imagePrefix()) will be returned
        """

        if canonical_path:
            path = os.path.join(Image.imagePrefix(), self._type, self._version)
            path = os.path.realpath(path)
        else:
            path =  os.path.join(self._type, self._version)

        return path


class ImageException(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self._value = value

    def __str__(self):
        return repr(self._value)


class ImageValidityException(ImageException):
    def __init__(self, value, choices):
        ImageException.__init__(self, value)
        self._choices = choices

    def __str__(self):
        return 'Invalid "%s". Please set it to one of the following: %s' \
                % (self._value, self._choices)

