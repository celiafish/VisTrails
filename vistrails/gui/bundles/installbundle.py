###############################################################################
##
## Copyright (C) 2011-2013, NYU-Poly.
## Copyright (C) 2006-2011, University of Utah. 
## All rights reserved.
## Contact: contact@vistrails.org
##
## This file is part of VisTrails.
##
## "Redistribution and use in source and binary forms, with or without 
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice, 
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright 
##    notice, this list of conditions and the following disclaimer in the 
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of the University of Utah nor the names of its 
##    contributors may be used to endorse or promote products derived from 
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################
"""Module with utilities to try and install a bundle if possible."""
from vistrails.core import get_vistrails_application
from vistrails.core.configuration import get_vistrails_configuration
from vistrails.core import debug
from vistrails.core.system import get_executable_path, vistrails_root_directory
from vistrails.core.system import systemType
from vistrails.gui.bundles.utils import guess_system, guess_graphical_sudo
import vistrails.gui.bundles.installbundle # this is on purpose
import subprocess
import os
import sys

##############################################################################

def has_qt():
    try:
        import PyQt4.QtGui
        # Must import this on Ubuntu linux, because PyQt4 doesn't come with
        # PyQt4.QtOpenGL by default
        import PyQt4.QtOpenGL
        return True
    except ImportError:
        return False

pip_installed = True
try:
    import pip
except ImportError:
    pip_installed = False

def hide_splash_if_necessary():
    qt = has_qt()
    # HACK, otherwise splashscreen stays in front of windows
    if qt:
        try:
            get_vistrails_application().splashScreen.hide()
        except:
            pass


def run_install_command_as_root(graphical, cmd, args):
    if type(args) == str:
        cmd += ' ' + args
    elif type(args) == list:
        for package in args:
            if type(package) != str:
                raise TypeError("Expected string or list of strings")
            cmd += ' ' + package
    else:
        raise TypeError("Expected string or list of strings")

    if graphical:
        sucmd, escape = guess_graphical_sudo()
    else:
        debug.warning("VisTrails wants to install package(s) %r" %
                      args)
        if get_executable_path('sudo'):
            sucmd, escape = "sudo %s", False
        elif not systemType == 'Darwin':
            sucmd, escape = "su -c %s", True
        else:
            return False

    if escape:
        sucmd = sucmd % '"%s"' % cmd.replace('\\', '\\\\').replace('"', '\\"')
    else:
        sucmd = sucmd % cmd

    print "about to run: %s" % sucmd
    p = subprocess.Popen(sucmd.split(' '), stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)
    lines = ''
    for line in iter(p.stdout.readline, ""):
        lines += line
        print line,
    result = p.wait()

    if result != 0:
        debug.critical("Error running: %s" % cmd, lines)
                
    return result == 0 # 0 indicates success


def linux_debian_install(package_name):
    qt = has_qt()
    try:
        import apt
        import apt_pkg
    except ImportError:
        qt = False
    hide_splash_if_necessary()

    if qt:
        cmd = vistrails_root_directory()
        cmd += '/gui/bundles/linux_debian_install.py'
    else:
        cmd = '%s install -y' % ('aptitude' if get_executable_path('aptitude') else 'apt-get')

    return run_install_command_as_root(qt, cmd, package_name)

linux_ubuntu_install = linux_debian_install


def linux_fedora_install(package_name):
    qt = has_qt()
    hide_splash_if_necessary()

    if qt:
        cmd = vistrails_root_directory()
        cmd += '/gui/bundles/linux_fedora_install.py'
    else:
        cmd = 'yum -y install'

    return run_install_command_as_root(qt, cmd, package_name)


def pip_install(package_name):
    hide_splash_if_necessary()

    if vistrails.core.system.executable_is_in_path('pip'):
        cmd = 'pip install'
    else:
        cmd = sys.executable + ' -m pip install'
    return run_install_command_as_root(has_qt(), cmd, package_name)

def show_question(which_files, has_distro_pkg, has_pip):
    if has_qt():
        from PyQt4 import QtCore, QtGui
        if type(which_files) == str:
            which_files = [which_files]
        dialog = QtGui.QDialog()
        dialog.setWindowTitle("Required packages missing")
        layout = QtGui.QVBoxLayout()

        label = QtGui.QLabel(
                "One or more required packages are missing: %s. VisTrails can "
                "automatically install them. If you click OK, VisTrails will "
                "need administrator privileges, and you might be asked for "
                "the administrator password." % (" ".join(which_files)))
        label.setWordWrap(True)
        layout.addWidget(label)

        if pip_installed and has_pip:
            use_pip = QtGui.QCheckBox("Use pip")
            use_pip.setChecked(
                not has_distro_pkg or (
                    has_pip and
                    getattr(get_vistrails_configuration(),
                            'installBundlesWithPip')))
            use_pip.setEnabled(has_distro_pkg and has_pip)
            layout.addWidget(use_pip)

            remember_align = QtGui.QHBoxLayout()
            remember_align.addSpacing(20)
            remember_pip = QtGui.QCheckBox("Remember my choice")
            remember_pip.setChecked(False)
            remember_pip.setEnabled(use_pip.isEnabled())
            remember_align.addWidget(remember_pip)
            layout.addLayout(remember_align)
        elif has_pip:
            label = QtGui.QLabel("pip package is available but pip is not installed")
            layout.addWidget(label)
        buttons = QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        QtCore.QObject.connect(buttons, QtCore.SIGNAL('accepted()'),
                               dialog, QtCore.SLOT('accept()'))
        QtCore.QObject.connect(buttons, QtCore.SIGNAL('rejected()'),
                               dialog, QtCore.SLOT('reject()'))
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        hide_splash_if_necessary()
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return False
        else:
            if pip_installed and has_pip:
                if remember_pip.isChecked():
                    setattr(get_vistrails_configuration(), 'installBundlesWithPip',
                            use_pip.isChecked())

                if use_pip.isChecked():
                    return 'pip'
            return 'distro'
    else:
        print "Required package missing"
        print ("A required package is missing, but VisTrails can " +
               "automatically install it. " +
               "If you say Yes, VisTrails will need "+
               "administrator privileges, and you" +
               "might be asked for the administrator password.")
        print "Give VisTrails permission to try to install package? (y/N)"
        v = raw_input().upper()
        if v == 'Y' or v == 'YES':
            if has_distro_pkg:
                return 'distro'
            else:
                return 'pip'


def install(dependency_dictionary):
    """Tries to install a bundle after a py_import() failed.."""

    distro = guess_system()
    files = (dependency_dictionary.get(distro) or
             dependency_dictionary.get('pip'))
    if not files:
        return None
    can_install = ('pip' in dependency_dictionary and pip_installed) or \
                  distro in dependency_dictionary
    if can_install:
        action = show_question(
                files,
                distro in dependency_dictionary,
                'pip' in dependency_dictionary)
        if action == 'distro':
            callable_ = getattr(vistrails.gui.bundles.installbundle,
                                distro.replace('-', '_') + '_install')
            return callable_(files)
        elif action == 'pip':
            if not pip_installed:
                debug.warning("Attempted to use pip, but it is not installed.")
                return False
            return pip_install(dependency_dictionary.get('pip'))
        else:
            return False
