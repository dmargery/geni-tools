#!/usr/bin/python

#----------------------------------------------------------------------
# Copyright (c) 2011 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------

""" The clear-pem-cert.py script.
    This script is meant to help users to remove the passphrase from their 
    protogeni certificate.
"""

import string
import sys, os, shutil, platform
from subprocess import Popen, PIPE
import optparse
import logging

logger = None

def getFileName(filename):
    """ This function takes as input a filename and if it already 
        exists it will ask the user whether to replace it or not 
        and if the file shouldn't be replaced it comes up with a
        unique name
    """
    # If the file exists ask the # user to replace it or not
    filename = os.path.expanduser(filename)
    if os.path.exists(filename):
        (basename, extension) = os.path.splitext(filename)
        valid_ans=['','y', 'n']
        replace_flag = raw_input("File " + filename + " exists, do you want to replace it [Y,n]?").lower()
        while replace_flag not in valid_ans:
            replace_flag = raw_input("Your input has to be 'y' or <ENTER> for yes, 'n' for no:").lower()
        if replace_flag == 'n' :
            i = 1
            if platform.system().lower().find('darwin') != -1 :
                tmp_pk_file = basename + '(' + str(i) + ')' + extension
            else :
                tmp_pk_file = basename + '-' + str(i) + extension
            
            while os.path.exists(tmp_pk_file):
                i = i+1
                if platform.system().lower().find('darwin'):
                    tmp_pk_file = basename + '(' + str(i) + ')' + extension
                else :
                    tmp_pk_file = basename + '-' + str(i) + extension
            filename = tmp_pk_file
    return filename

def parseArgs(argv):
    """Construct an Options Parser for parsing omni-configure command line
    arguments, and parse them.
    """

    parser = optparse.OptionParser()
    parser.add_option("-p", "--cert", default="~/.ssl/geni_cert.pem",
                      help="User certificate file location [DEFAULT: %default]", metavar="FILE")
    parser.add_option("-v", "--verbose", default=False, action="store_true",
                      help="Turn on verbose command summary for omni-configure script")

    if argv is None:
        # prints to stderr
        parser.print_help()
        return

    (opts, args) = parser.parse_args(argv)
    return opts

def configLogging(opts) :
    global logger
    level = logging.INFO
    if opts.verbose :
        level = logging.DEBUG

    logging.basicConfig(level=level)
    logger = logging.getLogger("clearcert")

def clearCert(certFile):
    global logger
    #Check if the certificate has key that is encrypted
    f = open(certFile, 'r')
    text = f.read()
    index = text.find("ENCRYPTED")
    if index == -1 :
        logger.info("Certificate does not have a passphrase. Exit.")
        sys.exit()

    # Copy cert file to a new location
    certdir = os.path.dirname(certFile)
    certname = os.path.splitext(os.path.basename(certFile))[0]
    bakcertfile = os.path.join(certdir, certname + '_enc.pem')
    bakcertfile = getFileName(bakcertfile)

    tmpcertfile = "%s.tmp" % certFile
    logger.debug("Using tmpcertfile: %s", tmpcertfile)
    shutil.copyfile(certFile, bakcertfile)
    logger.info("The encoded certificate file is backed up at %s" % bakcertfile)

    logger.info("Removing passphrase from cert...")
    command = ['openssl', 'rsa']
    command.append('-in')
    command.append(certFile)
    command.append("-out")
    command.append(tmpcertfile)
    logger.debug("Run commnand: %s", command)
    p = Popen(command, stdout=PIPE)
    p.communicate()[0]
    if p.returncode != 0:
        shutil.move(bakcertfile, certFile)
        if os.path.exists(tmpcertfile):
            os.remove(tmpcertfile)
        logger.critical("\n\nError removing passphrase from certificate! \nMake sure you are using the right passphrase.\n")
        sys.exit(-1)
    
    command = ['openssl', 'x509']
    command.append('-in')
    command.append(certFile)
    logger.debug("Run commnand: %s", command)
    p = Popen(command, stdout=PIPE)
    tmpcert = p.communicate()[0]
    if p.returncode != 0:
        shutil.move(bakcertfile, certFile)
        if os.path.exists(tmpcertfile):
            os.remove(tmpcertfile)
        raise Exception("Error removing passphrase from certificate")
    f = open(tmpcertfile,'a')
    f.write("%s" % tmpcert)
    f.close()
    logger.debug("Move tmpcertfile to certfile")
    shutil.move(tmpcertfile, certFile)
    logger.info("Change permissions of %s to 0600", certFile)
    os.chmod(certFile, 0600)

def main():
    global logger
    argv = sys.argv[1:]
    opts = parseArgs(argv)
    configLogging(opts)
    # Expand the cert file to a full path
    logger.debug("Running %s with options %s" %(sys.argv[0], opts))
    opts.cert= os.path.expanduser(opts.cert)
    if not os.path.exists(opts.cert):
        raise Exception("Certificate file %s does not exist" % opts.cert)
    logger.info("\n\tTHIS SCRIPT WILL REPLACE %s WITH AN UNENCREPTED CERT. A BACKUP OF THE ORIGINAL CERT WILL BE CREATED\n" % opts.cert)
    clearCert(opts.cert)


if __name__ == "__main__":
    sys.exit(main())
 
